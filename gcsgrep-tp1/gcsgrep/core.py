"""Lógica de búsqueda, sin dependencia directa de la API de GCS.

Búsqueda literal de punta a punta, con salida incremental, guardrail de costo
por cantidad de objetos (BR-2 / ADR-0006) y objetos ilegibles que no abortan la
corrida (FR-6, FR-13, FR-21; Iteración 2).
"""

import codecs
from dataclasses import dataclass
from typing import Any, Callable, ContextManager, Iterable, Iterator, Optional, Tuple, Union

from . import errors

#: Tope de objetos por defecto del guardrail de costo (ADR-0006).
TOPE_POR_DEFECTO = 1000

#: Valor de `--max` que quita el tope. Con esto el listado no se materializa.
SIN_TOPE = 0

#: Lista los nombres de los objetos de `bucket` bajo `prefix`.
#: Puede ser lazy: `core` no consume el iterable de una sola vez.
ListObjects = Callable[[str, str], Iterable[str]]

#: Abre un objeto. El valor devuelto es un **context manager** que al entrar da
#: un lector de **bytes** con `read(n)` (un file-like binario lo cumple). `core`
#: nunca lee el objeto completo: lee de a `BLOQUE_DE_LECTURA` (NFR-1), y es quien
#: decide qué es texto (FR-9, FR-17, FR-22, FR-27). Hasta la Iteración 1 se
#: llamaba `open_text_stream` y entregaba líneas ya decodificadas.
OpenStream = Callable[[str, str], ContextManager[Any]]

#: Ventana de detección de binarios: un `\x00` en los primeros 8192 bytes (FR-9,
#: ADR-0018).
VENTANA_BINARIA = 8192

#: Tamaño de cada `read` sobre el lector del objeto.
BLOQUE_DE_LECTURA = 64 * 1024

_BOM_UTF8 = codecs.BOM_UTF8


@dataclass(frozen=True)
class SearchConfig:
    pattern: str
    ignore_case: bool = False
    show_line_numbers: bool = False
    #: Tope de objetos del guardrail. `SIN_TOPE` (0) lo desactiva.
    max_objetos: int = TOPE_POR_DEFECTO


@dataclass(frozen=True)
class Match:
    bucket: str
    object_name: str
    line_number: int
    text: str


@dataclass(frozen=True)
class Aviso:
    """Algo que no es un match y va por stderr (NFR-3): un objeto que no se pudo
    leer (FR-6, FR-13, FR-21) o que se salteó (FR-9, FR-10).

    `core` no escribe en stderr: emite el aviso **en su lugar del flujo**, entre
    los matches, y `cli` lo imprime. `es_error` es lo que BR-3 cuenta.
    """

    mensaje: str
    es_error: bool


#: Lo que emite `search`: un match (stdout) o un aviso (stderr).
Evento = Union[Match, Aviso]


def parse_location(location: str) -> Tuple[str, str]:
    """Parsea `gs://bucket/prefijo`. Lanza ValueError si el esquema no es gs://.

    Ver ADR-0003: el esquema es obligatorio y la validación ocurre antes de
    cualquier llamada a GCS.
    """
    scheme = "gs://"
    if not location.startswith(scheme):
        raise ValueError(
            f"ubicación inválida: se esperaba el esquema 'gs://', se recibió '{location}'"
        )
    rest = location[len(scheme):]
    bucket, _, prefix = rest.partition("/")
    if not bucket:
        raise ValueError("ubicación inválida: falta el nombre del bucket")
    return bucket, prefix


def _lineas(stream) -> Iterator[str]:
    """Parte el contenido de un objeto de texto en líneas, ya decodificadas.

    - UTF-8 con reemplazo (`U+FFFD`) de toda secuencia inválida (FR-17); el
      decodificador es incremental, así que un carácter partido entre dos
      lecturas no se rompe.
    - Una línea termina **solo** en `\n`; el `\r` de `\r\n` se quita y un `\r`
      suelto queda en la línea (FR-22). La última línea sin `\n` cuenta (FR-20).
    - El primer bloque ya fue mirado por `search` (binario y BOM).
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    pendiente = ""
    while True:
        bloque = stream.read(BLOQUE_DE_LECTURA)
        if not bloque:
            break
        partes = (pendiente + decoder.decode(bloque)).split("\n")
        pendiente = partes.pop()
        for linea in partes:
            yield linea[:-1] if linea.endswith("\r") else linea
    pendiente += decoder.decode(b"", final=True)
    if pendiente:
        yield pendiente


class _ConCabeza:
    """El lector del objeto con sus primeros bytes ya leídos devueltos adelante.

    Si la lectura de la cabeza falló, después de devolverla levanta ese error:
    así las líneas **completas** que alcanzaron a leerse se buscan y se emiten
    antes del aviso (FR-13, VC-17), y la línea que quedó cortada se descarta.
    """

    def __init__(self, cabeza: bytes, stream, error: Optional[Exception]) -> None:
        self._cabeza = cabeza
        self._stream = stream
        self._error = error

    def read(self, size: int) -> bytes:
        if self._cabeza:
            data, self._cabeza = self._cabeza, b""
            return data
        if self._error is not None:
            raise self._error
        return self._stream.read(size)


def _leer_cabeza(stream) -> Tuple[bytes, Optional[Exception]]:
    """Lee al menos `VENTANA_BINARIA` bytes (o hasta el final del objeto).

    Devuelve también el error si la lectura falló antes: lo leído hasta ahí no
    se pierde (ver `_ConCabeza`).
    """
    cabeza = b""
    try:
        while len(cabeza) < VENTANA_BINARIA:
            bloque = stream.read(BLOQUE_DE_LECTURA)
            if not bloque:
                break
            cabeza += bloque
    except Exception as exc:  # noqa: BLE001 — se re-levanta en `_ConCabeza`
        return cabeza, exc
    return cabeza, None


def search(
    bucket: str,
    prefix: str,
    config: SearchConfig,
    list_objects: ListObjects,
    open_stream: OpenStream,
) -> Iterator[Evento]:
    """Emite cada match de `config.pattern` (substring literal) bajo `prefix`.

    Es un **generador**: emite cada `Match` en cuanto lo encuentra, sin
    acumular resultados (ADR-0011). Esa es la razón por la que la memoria queda
    acotada por el match más grande y no por la cantidad de matches (NFR-1), y
    por la que la salida aparece mientras la búsqueda avanza (FR-11).

    `list_objects` y `open_stream` son los únicos puntos de contacto con
    GCS (o con un doble de prueba); `core` no importa `google.cloud.storage`.

    Antes de leer contenido aplica el guardrail de costo (BR-2 / ADR-0006): si el
    prefijo tiene más objetos que `config.max_objetos`, levanta `TopeExcedido`
    **sin abrir ninguno**.

    Nota de implementación: contar exige materializar el listado, así que con tope
    activo la primera emisión espera a que el listado termine. Con
    `max_objetos=SIN_TOPE` no hay nada que contar y el listado se consume de forma
    perezosa, igual que antes del guardrail. Lo que no cambia en ningún caso es que
    los objetos se **abren** de a uno, que es lo que sostiene NFR-1 y FR-11.
    """
    needle = config.pattern.lower() if config.ignore_case else config.pattern

    nombres: Iterable[str] = list_objects(bucket, prefix)
    if config.max_objetos != SIN_TOPE:
        nombres = list(nombres)
        if len(nombres) > config.max_objetos:
            raise errors.TopeExcedido(len(nombres), config.max_objetos)

    for object_name in nombres:
        uri = f"gs://{bucket}/{object_name}"
        # FR-10: los .gz se saltean por extensión, sin abrirlos. No es error (BR-3).
        if object_name.endswith(".gz"):
            yield Aviso(f"salteado (.gz): {uri}", es_error=False)
            continue
        # Un objeto que no se puede leer no aborta la corrida (FR-6, FR-13,
        # FR-21): los matches que ya salieron quedan, se emite un aviso y se
        # sigue. No se vuelve a abrir (NFR-2, 0 reintentos).
        try:
            with open_stream(bucket, object_name) as stream:
                cabeza, error = _leer_cabeza(stream)
                # FR-9: un \x00 en la ventana → binario, sin matchear nada. Si la
                # lectura se cortó dentro de la ventana pero ya se vio un \x00,
                # el objeto es binario igual y no hacía falta leer más.
                if b"\x00" in cabeza[:VENTANA_BINARIA]:
                    yield Aviso(f"salteado (binario): {uri}", es_error=False)
                    continue
                # FR-27: el BOM se descarta solo si son los tres primeros bytes.
                if cabeza.startswith(_BOM_UTF8):
                    cabeza = cabeza[len(_BOM_UTF8):]
                lineas = _lineas(_ConCabeza(cabeza, stream, error))
                for line_number, line in enumerate(lineas, start=1):
                    haystack = line.lower() if config.ignore_case else line
                    if needle in haystack:
                        yield Match(bucket, object_name, line_number, line)
        except errors.ErrorDeObjeto as exc:
            yield Aviso(str(exc), es_error=True)

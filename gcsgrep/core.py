"""Lógica de búsqueda, sin dependencia directa de la API de GCS.

Búsqueda literal de punta a punta, con salida incremental y guardrail de costo
por cantidad de objetos (BR-2 / ADR-0006). No maneja objetos ilegibles y no
saltea binarios/.gz — eso sigue siendo Iteración 2 (ver specs/gcsgrep/03-plan.md).
"""

from dataclasses import dataclass
from typing import Callable, ContextManager, Iterable, Iterator, Tuple

from . import errors

#: Tope de objetos por defecto del guardrail de costo (ADR-0006).
TOPE_POR_DEFECTO = 1000

#: Valor de `--max` que quita el tope. Con esto el listado no se materializa.
SIN_TOPE = 0

#: Lista los nombres de los objetos de `bucket` bajo `prefix`.
#: Puede ser lazy: `core` no consume el iterable de una sola vez.
ListObjects = Callable[[str, str], Iterable[str]]

#: Abre un objeto como texto. El valor devuelto es un **context manager** que
#: al entrar da un iterable de líneas (un file-like de texto lo cumple).
#: `core` nunca lee el objeto completo: itera línea por línea (NFR-1).
OpenTextStream = Callable[[str, str], ContextManager[Iterable[str]]]


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


def search(
    bucket: str,
    prefix: str,
    config: SearchConfig,
    list_objects: ListObjects,
    open_text_stream: OpenTextStream,
) -> Iterator[Match]:
    """Emite cada match de `config.pattern` (substring literal) bajo `prefix`.

    Es un **generador**: emite cada `Match` en cuanto lo encuentra, sin
    acumular resultados (ADR-0011). Esa es la razón por la que la memoria queda
    acotada por el match más grande y no por la cantidad de matches (NFR-1), y
    por la que la salida aparece mientras la búsqueda avanza (FR-11).

    `list_objects` y `open_text_stream` son los únicos puntos de contacto con
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
        with open_text_stream(bucket, object_name) as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if config.ignore_case else line
                if needle in haystack:
                    yield Match(bucket, object_name, line_number, line)

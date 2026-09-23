"""Lógica de búsqueda, sin dependencia directa de la API de GCS.

Iteración 1 (revisión 1.1): búsqueda literal de punta a punta, con salida
incremental. No maneja objetos ilegibles, no saltea binarios/.gz, no aplica
guardrail de tope — eso es Iteración 2 (ver specs/gcsgrep/03-plan.md).
"""

from dataclasses import dataclass
from typing import Callable, ContextManager, Iterable, Iterator, Tuple

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
    """
    needle = config.pattern.lower() if config.ignore_case else config.pattern

    for object_name in list_objects(bucket, prefix):
        with open_text_stream(bucket, object_name) as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if config.ignore_case else line
                if needle in haystack:
                    yield Match(bucket, object_name, line_number, line)

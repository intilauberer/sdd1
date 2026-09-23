"""Lógica de búsqueda, sin dependencia directa de la API de GCS.

Iteración 1: búsqueda literal de punta a punta. No maneja objetos ilegibles,
no saltea binarios/.gz, no aplica guardrail de tope — eso es Iteración 2
(ver gcsgrep-plan.md).
"""

from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

ListObjects = Callable[[str, str], Iterable[str]]
OpenTextStream = Callable[[str, str], "Iterable[str]"]


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
    """Parsea `gs://bucket/prefijo`. Lanza ValueError si el esquema no es gs://."""
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
) -> List[Match]:
    """Busca `config.pattern` como substring literal en los objetos bajo prefix.

    `list_objects` y `open_text_stream` son los únicos puntos de contacto con
    GCS (o con un doble de prueba); `core` no importa `google.cloud.storage`.
    """
    needle = config.pattern.lower() if config.ignore_case else config.pattern
    matches: List[Match] = []

    for object_name in list_objects(bucket, prefix):
        with open_text_stream(bucket, object_name) as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if config.ignore_case else line
                if needle in haystack:
                    matches.append(Match(bucket, object_name, line_number, line))

    return matches

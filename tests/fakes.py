"""Doble de prueba para la capa `gcs`. Sin red, sin credenciales."""

import io
from typing import Dict, Iterator


class FakeGCS:
    def __init__(self) -> None:
        self._objects: Dict[str, Dict[str, str]] = {}

    def put(self, bucket: str, name: str, content: str) -> None:
        self._objects.setdefault(bucket, {})[name] = content

    def list_objects(self, bucket: str, prefix: str) -> Iterator[str]:
        names = self._objects.get(bucket, {})
        return iter(sorted(n for n in names if n.startswith(prefix)))

    def open_text_stream(self, bucket: str, name: str) -> io.StringIO:
        return io.StringIO(self._objects[bucket][name])


class HugeLineStream:
    """Simula un objeto remoto enorme sin materializarlo en memoria.

    Genera la misma línea `repeat` veces bajo demanda (streaming real), para
    poder ejercitar VC-14 sin depender de un objeto de GCS de 200 MB de
    verdad.
    """

    def __init__(self, line: str, repeat: int) -> None:
        self._line = line
        self._repeat = repeat

    def __enter__(self) -> "HugeLineStream":
        return self

    def __exit__(self, *exc_info) -> bool:
        return False

    def __iter__(self) -> Iterator[str]:
        for _ in range(self._repeat):
            yield self._line

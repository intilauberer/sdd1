"""Dobles de prueba para la capa `gcs`. Sin red, sin credenciales."""

import io
from typing import Dict, Iterator, List


class FakeGCS:
    def __init__(self) -> None:
        self._objects: Dict[str, Dict[str, str]] = {}
        self._errors: Dict[str, Dict[str, Exception]] = {}

    def put(self, bucket: str, name: str, content: str) -> None:
        """Siembra contenido. Es setup del test, no parte de la superficie que
        `core` puede usar: `core` solo recibe `list_objects` y
        `open_text_stream`.

        Pendiente para VC-11 (Iteración 2): separar la siembra de la superficie
        observable, para que el test de "solo operaciones de lectura" pueda
        distinguir una escritura del setup de una del código bajo prueba.
        Ver docs/revision-spec.md, hallazgo H-10.
        """
        self._objects.setdefault(bucket, {})[name] = content

    def explode_on(self, bucket: str, name: str, error: Exception) -> None:
        """Siembra un objeto que **aparece en el listado** y falla al abrirse.

        Es el doble del caso en que el listado y la lectura no coinciden: el
        objeto existe para GCS cuando se lista y ya no —o no se puede leer—
        cuando se lo va a abrir. Es setup del test, igual que `put` (ver H-10).
        """
        self._objects.setdefault(bucket, {})[name] = ""
        self._errors.setdefault(bucket, {})[name] = error

    def list_objects(self, bucket: str, prefix: str) -> Iterator[str]:
        names = self._objects.get(bucket, {})
        return iter(sorted(n for n in names if n.startswith(prefix)))

    def open_text_stream(self, bucket: str, name: str) -> io.StringIO:
        error = self._errors.get(bucket, {}).get(name)
        if error is not None:
            raise error
        return io.StringIO(self._objects[bucket][name])


class RecordingFakeGCS(FakeGCS):
    """Igual que `FakeGCS`, pero registra qué objetos se listaron y se abrieron,
    **en el momento en que se consumen**.

    El listado es un generador de verdad: `listed` solo crece cuando quien
    consume pide el próximo nombre. Eso es lo que permite observar que `core`
    emite matches sin haber recorrido todo el prefijo (VC-17 / FR-11).
    """

    def __init__(self) -> None:
        super().__init__()
        self.listed: List[str] = []
        self.opened: List[str] = []

    def list_objects(self, bucket: str, prefix: str) -> Iterator[str]:
        for name in super().list_objects(bucket, prefix):
            self.listed.append(name)
            yield name

    def open_text_stream(self, bucket: str, name: str) -> io.StringIO:
        self.opened.append(name)
        return super().open_text_stream(bucket, name)


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


class ExplodingStream:
    """Stream que emite algunas líneas y después falla al leer.

    Sirve para observar, de punta a punta, que lo que ya se emitió salió por
    stdout antes de que la corrida terminara (VC-17). No especifica nada sobre
    el manejo de errores: eso es FR-6, Iteración 2.
    """

    def __init__(self, lines: List[str], error: Exception) -> None:
        self._lines = lines
        self._error = error

    def __enter__(self) -> "ExplodingStream":
        return self

    def __exit__(self, *exc_info) -> bool:
        return False

    def __iter__(self) -> Iterator[str]:
        for line in self._lines:
            yield line
        raise self._error

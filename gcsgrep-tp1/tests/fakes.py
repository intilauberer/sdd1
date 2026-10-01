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


class ClienteSoloLectura:
    """Doble del **cliente del SDK** que falla si se le pide algo que no sea leer.

    Es el ejercitador de VC-11 (BR-1, solo lectura). Vive al nivel del cliente de
    `google-cloud-storage` porque ahí es donde BR-1 tiene sentido: "no invocar
    operaciones de escritura" es una afirmación sobre la API de GCS, no sobre el
    doble del módulo `gcs`.

    Cualquier atributo fuera de la lista blanca explota, así que el test falla si
    `gcs.py` intenta subir, borrar, copiar o tocar IAM — incluso con un método que
    hoy no existe en el SDK.
    """

    #: Lo único que `gcs.py` tiene permitido tocar del cliente.
    PERMITIDO = frozenset({"list_blobs", "bucket"})

    def __init__(self, nombres_de_objetos: List[str]) -> None:
        self._nombres = list(nombres_de_objetos)
        self.invocaciones: List[str] = []
        self.invocaciones_prohibidas: List[str] = []

    def __getattr__(self, nombre: str):
        # Solo se llega acá con atributos que la clase no define.
        self.invocaciones_prohibidas.append(nombre)
        raise AssertionError(
            f"BR-1 violado: `gcs` invocó '{nombre}' sobre el cliente de GCS, "
            f"que no es una operación de lectura. Permitido: {sorted(self.PERMITIDO)}"
        )

    def list_blobs(self, bucket, prefix=None):
        self.invocaciones.append("list_blobs")

        class _Blob:
            def __init__(self, name):
                self.name = name

        return [_Blob(n) for n in self._nombres if n.startswith(prefix or "")]

    def bucket(self, name: str):
        self.invocaciones.append("bucket")
        cliente = self

        class _BlobDeLectura:
            def __init__(self, nombre):
                self._nombre = nombre

            def open(self, mode: str):
                assert mode == "r", f"BR-1: se abrió un blob en modo '{mode}', no 'r'"
                cliente.invocaciones.append("blob.open(r)")
                return io.StringIO("contenido\n")

            def __getattr__(self, attr):
                cliente.invocaciones_prohibidas.append(f"blob.{attr}")
                raise AssertionError(
                    f"BR-1 violado: `gcs` invocó 'blob.{attr}', que no es lectura"
                )

        class _BucketDeLectura:
            def blob(self, nombre):
                cliente.invocaciones.append("bucket.blob")
                return _BlobDeLectura(nombre)

            def __getattr__(self, attr):
                cliente.invocaciones_prohibidas.append(f"bucket.{attr}")
                raise AssertionError(
                    f"BR-1 violado: `gcs` invocó 'bucket.{attr}', que no es lectura"
                )

        return _BucketDeLectura()

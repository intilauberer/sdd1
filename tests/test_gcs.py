"""Tests de contrato para `gcs.py`: verifican que llama al SDK de la forma
esperada (bucket, prefix, modo de apertura), mockeando el cliente de
`google-cloud-storage` en el punto donde `gcs.py` lo obtiene.

Esto NO reemplaza la verificación de integración contra un bucket real (ver
gcsgrep-cobertura-vc.md): confirma que el wiring con el SDK es correcto, no
que la librería de Google en sí se comporte como creemos (autenticación real,
semántica exacta de streaming, errores de permisos reales, etc).
"""

import io

from gcsgrep import gcs


class _FakeBlob:
    def __init__(self, name: str, content: str = "") -> None:
        self.name = name
        self._content = content
        self.opened_with_mode = None

    def open(self, mode: str) -> io.StringIO:
        self.opened_with_mode = mode
        return io.StringIO(self._content)


class _FakeBucket:
    def __init__(self, blobs_by_name) -> None:
        self._blobs_by_name = blobs_by_name

    def blob(self, name: str) -> _FakeBlob:
        return self._blobs_by_name[name]


class _FakeClient:
    def __init__(self, blobs) -> None:
        self._blobs = list(blobs)
        self.list_blobs_calls = []

    def list_blobs(self, bucket, prefix=None):
        self.list_blobs_calls.append((bucket, prefix))
        return [b for b in self._blobs if b.name.startswith(prefix or "")]

    def bucket(self, name: str) -> _FakeBucket:
        return _FakeBucket({b.name: b for b in self._blobs})


def test_list_objects_llama_a_list_blobs_con_bucket_y_prefix(monkeypatch):
    fake_client = _FakeClient([_FakeBlob("logs/a.txt"), _FakeBlob("other/b.txt")])
    monkeypatch.setattr(gcs, "_get_client", lambda: fake_client)

    names = list(gcs.list_objects("mi-bucket", "logs/"))

    assert names == ["logs/a.txt"]
    assert fake_client.list_blobs_calls == [("mi-bucket", "logs/")]


def test_open_text_stream_abre_el_blob_correcto_en_modo_lectura(monkeypatch):
    blob = _FakeBlob("logs/a.txt", content="contenido\n")
    fake_client = _FakeClient([blob])
    monkeypatch.setattr(gcs, "_get_client", lambda: fake_client)

    stream = gcs.open_text_stream("mi-bucket", "logs/a.txt")

    assert blob.opened_with_mode == "r"
    assert stream.read() == "contenido\n"


def test_get_client_es_singleton(monkeypatch):
    monkeypatch.setattr(gcs, "_client", None)
    created = []

    class _TrackedClient(_FakeClient):
        def __init__(self):
            super().__init__([])
            created.append(self)

    monkeypatch.setattr(gcs.storage, "Client", _TrackedClient)

    first = gcs._get_client()
    second = gcs._get_client()

    assert first is second
    assert len(created) == 1

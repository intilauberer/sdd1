"""Tests de contrato para `gcs.py`: verifican que llama al SDK de la forma
esperada (bucket, prefix, modo de apertura), mockeando el cliente de
`google-cloud-storage` en el punto donde `gcs.py` lo obtiene.

Esto NO reemplaza la verificación de integración contra un bucket real (ver
gcsgrep-cobertura-vc.md): confirma que el wiring con el SDK es correcto, no
que la librería de Google en sí se comporte como creemos (autenticación real,
semántica exacta de streaming, errores de permisos reales, etc).
"""

import io

import pytest
from google.api_core import exceptions as api_exceptions

from gcsgrep import errors, gcs


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


# --- VC-18 · la traducción de las excepciones del SDK ------------------------
#
# Los tests de `cli` verifican qué hace gcsgrep cuando `gcs` levanta un error de
# dominio. Esto verifica la otra mitad: que `gcs` traduzca las excepciones reales
# de `google.api_core` a esos errores. Sin esto, el contrato de FR-12 podría estar
# verificado de punta a punta contra un error que el SDK nunca produce.


class _ClientQueExplota:
    """Cliente cuyo `list_blobs` o `bucket().blob().open()` levanta `error`."""

    def __init__(self, error: Exception, al_listar: bool = True) -> None:
        self._error = error
        self._al_listar = al_listar

    def list_blobs(self, bucket, prefix=None):
        if self._al_listar:
            raise self._error
        return [_FakeBlob("logs/a.txt")]

    def bucket(self, name: str):
        error = self._error

        class _Blob:
            def open(self, mode):
                raise error

        class _Bucket:
            def blob(self, name):
                return _Blob()

        return _Bucket()


def test_vc18_list_objects_traduce_notfound_a_bucket_no_encontrado(monkeypatch):
    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClientQueExplota(api_exceptions.NotFound("404"))
    )

    with pytest.raises(errors.BucketNoEncontrado) as exc_info:
        list(gcs.list_objects("no-existe", ""))

    assert exc_info.value.bucket == "no-existe"
    assert "no-existe" in str(exc_info.value)
    # El mensaje es para una persona, no la repr de la excepción del SDK (NFR-2).
    assert "404" not in str(exc_info.value)


def test_vc18_list_objects_traduce_forbidden_a_acceso_denegado(monkeypatch):
    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClientQueExplota(api_exceptions.Forbidden("403"))
    )

    with pytest.raises(errors.AccesoDenegado) as exc_info:
        list(gcs.list_objects("ajeno", ""))

    assert "permiso" in str(exc_info.value)


def test_vc18_los_dos_errores_del_listado_dan_mensajes_distintos(monkeypatch):
    """Es la afirmación central de FR-12: 404 y 403 no se confunden."""
    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClientQueExplota(api_exceptions.NotFound("404"))
    )
    with pytest.raises(errors.ErrorDeAcceso) as no_existe:
        list(gcs.list_objects("b", ""))

    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClientQueExplota(api_exceptions.Forbidden("403"))
    )
    with pytest.raises(errors.ErrorDeAcceso) as denegado:
        list(gcs.list_objects("b", ""))

    assert str(no_existe.value) != str(denegado.value)


def test_vc18_open_text_stream_traduce_forbidden_a_acceso_denegado(monkeypatch):
    monkeypatch.setattr(
        gcs,
        "_get_client",
        lambda: _ClientQueExplota(api_exceptions.Forbidden("403"), al_listar=False),
    )

    with pytest.raises(errors.AccesoDenegado) as exc_info:
        gcs.open_text_stream("b", "logs/a.txt")

    assert "logs/a.txt" in str(exc_info.value)


def test_vc18_open_text_stream_traduce_notfound_a_objeto_no_encontrado(monkeypatch):
    """Un objeto que desapareció entre el listado y la lectura no es "sin
    permiso": es la ventana de ADR-0010."""
    monkeypatch.setattr(
        gcs,
        "_get_client",
        lambda: _ClientQueExplota(api_exceptions.NotFound("404"), al_listar=False),
    )

    with pytest.raises(errors.ObjetoNoEncontrado):
        gcs.open_text_stream("b", "logs/a.txt")

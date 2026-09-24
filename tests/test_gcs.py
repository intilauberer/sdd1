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
from .fakes import ClienteSoloLectura


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


# --- VC-11 · BR-1 solo lectura ------------------------------------------------
#
# VC-11 pide dos cosas: inspección del módulo `gcs` y un doble que falle si recibe
# una llamada que no sea de lectura. Acá están las dos, automatizadas.

#: Métodos de escritura / borrado / IAM del SDK de GCS. Si alguno aparece en
#: gcsgrep/gcs.py, BR-1 está violado.
OPERACIONES_PROHIBIDAS = (
    "upload_from_file", "upload_from_filename", "upload_from_string",
    "create_bucket", "delete", "delete_blob", "delete_bucket", "delete_blobs",
    "copy_blob", "rename_blob", "compose", "rewrite", "patch", "update",
    "set_iam_policy", "make_public", "make_private", "acl", "create_resumable_upload_session",
)


def test_vc11_el_modulo_gcs_no_nombra_ninguna_operacion_de_escritura():
    """VC-11 (a) · BR-1 por inspección, automatizada.

    `gcs` es la única capa que llama a la API, así que alcanza con mirar ese
    archivo. Se busca sobre el AST y no con un grep de texto para no cazar
    menciones en comentarios: lo que importa son los atributos que el código
    realmente toca.
    """
    import ast
    import pathlib

    fuente = pathlib.Path(gcs.__file__).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    atributos = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    llamados = {
        n.func.attr
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    tocados = atributos | llamados

    prohibidos_presentes = sorted(tocados & set(OPERACIONES_PROHIBIDAS))
    assert prohibidos_presentes == [], (
        f"BR-1: gcs.py toca operaciones que no son de lectura: {prohibidos_presentes}"
    )


def test_vc11_un_doble_que_solo_permite_leer_no_registra_llamadas_prohibidas(monkeypatch):
    """VC-11 (b) · el test que falla si el doble recibe algo que no es lectura.

    `ClienteSoloLectura` explota ante cualquier atributo fuera de la lista blanca,
    así que este test falla —no "reporta"— si `gcs` intentara escribir, incluso con
    un método que el SDK todavía no tenga.
    """
    cliente = ClienteSoloLectura(["logs/a.txt", "logs/b.txt"])
    monkeypatch.setattr(gcs, "_get_client", lambda: cliente)

    assert list(gcs.list_objects("b", "logs/")) == ["logs/a.txt", "logs/b.txt"]
    with gcs.open_text_stream("b", "logs/a.txt") as stream:
        assert list(stream) == ["contenido\n"]

    assert cliente.invocaciones_prohibidas == []
    assert set(cliente.invocaciones) <= {"list_blobs", "bucket", "bucket.blob", "blob.open(r)"}


def test_vc11_el_doble_efectivamente_detecta_una_escritura():
    """Sin esto, VC-11 (b) podría pasar porque el doble no sabe detectar nada.

    Es la pregunta de C-8 aplicada al ejercitador: ¿puede fallar por la razón
    correcta? Se comprueba provocando la violación a propósito.
    """
    cliente = ClienteSoloLectura([])

    with pytest.raises(AssertionError, match="BR-1 violado"):
        cliente.delete_bucket("b")

    with pytest.raises(AssertionError, match="BR-1 violado"):
        cliente.bucket("b").blob("x").upload_from_string("dato")

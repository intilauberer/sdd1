"""Iteración 2 · errores por objeto: FR-6, FR-13, FR-21, BR-3, NFR-2.

Dos niveles, como el resto de la suite: de punta a punta con el doble de `gcs`
(qué ve quien corre el comando), y en `test_gcs.py`-style contra excepciones
**reales** del SDK (que `gcs` traduzca a los errores de dominio correctos).
"""

import pytest
import requests
from google.api_core import exceptions as api_exceptions

from gcsgrep import cli, core, errors, gcs
from .fakes import ExplodingStream, FakeGCS


class _ContadorGCS(FakeGCS):
    def __init__(self) -> None:
        super().__init__()
        self.listados = 0
        self.aperturas = []
        self._a_mitad = {}

    def explode_mid_read(self, bucket, name, lineas, error):
        """El objeto entrega `lineas` y después su stream levanta `error`."""
        self.put(bucket, name, "")
        self._a_mitad[(bucket, name)] = (lineas, error)

    def list_objects(self, bucket, prefix):
        self.listados += 1
        return super().list_objects(bucket, prefix)

    def open_stream(self, bucket, name):
        self.aperturas.append(name)
        if (bucket, name) in self._a_mitad:
            return ExplodingStream(*self._a_mitad[(bucket, name)])
        return super().open_stream(bucket, name)


@pytest.fixture
def fake(monkeypatch):
    f = _ContadorGCS()
    monkeypatch.setattr(gcs, "list_objects", f.list_objects)
    monkeypatch.setattr(gcs, "open_stream", f.open_stream)
    return f


def _correr(capsys, argv):
    exit_code = cli.main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _linea_con(err, *textos):
    return any(all(t in linea for t in textos) for linea in err.splitlines())


# --- FR-6 / BR-3 -------------------------------------------------------------------


def test_vc6_objeto_sin_permiso_no_aborta(fake, capsys):
    fake.put("b", "p/a.txt", "nada\n")
    fake.explode_on("b", "p/b.txt", errors.ObjetoSinPermiso("b", "p/b.txt"))
    fake.put("b", "p/c.txt", "x hit\n")

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/c.txt:x hit\n"
    assert _linea_con(err, "sin permiso para leer", "gs://b/p/b.txt")
    assert "Traceback" not in err
    assert exit_code == 2


def test_vc13_error_de_lectura_gana_aunque_haya_match(fake, capsys):
    fake.put("b", "p/a.txt", "x hit\n")
    fake.explode_on("b", "p/b.txt", errors.ObjetoSinPermiso("b", "p/b.txt"))

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/a.txt:x hit\n"
    assert _linea_con(err, "sin permiso para leer", "gs://b/p/b.txt")
    assert "Traceback" not in err
    assert exit_code == 2


# --- FR-13 / NFR-2 (b) ----------------------------------------------------------------


def test_vc21_red_a_mitad_de_lectura(fake, capsys):
    fake.explode_mid_read(
        "b", "p/a.txt", ["hit uno\n"], errors.ErrorDeRedAlLeer("b", "p/a.txt")
    )
    fake.put("b", "p/b.txt", "hit dos\n")

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/a.txt:hit uno\ngs://b/p/b.txt:hit dos\n"
    assert _linea_con(err, "error de red al leer", "gs://b/p/a.txt")
    assert "Traceback" not in err
    assert exit_code == 2


def test_vc29_cero_reintentos_al_leer(fake, capsys):
    fake.explode_mid_read(
        "b", "p/a.txt", ["hit uno\n"], errors.ErrorDeRedAlLeer("b", "p/a.txt")
    )
    fake.put("b", "p/b.txt", "hit dos\n")

    exit_code, _, _ = _correr(capsys, ["hit", "gs://b/p/"])

    assert fake.aperturas == ["p/a.txt", "p/b.txt"]
    assert exit_code == 2


def test_vc33_red_caida_al_abrir(fake, capsys):
    fake.explode_on("b", "p/a.txt", errors.ErrorDeRedAlLeer("b", "p/a.txt"))
    fake.put("b", "p/b.txt", "hit dos\n")

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/b.txt:hit dos\n"
    assert _linea_con(err, "error de red al leer", "gs://b/p/a.txt")
    assert "Traceback" not in err
    assert exit_code == 2
    assert fake.aperturas == ["p/a.txt", "p/b.txt"]


# --- FR-21 ----------------------------------------------------------------------------


def test_vc32_objeto_que_ya_no_existe(fake, capsys):
    fake.put("b", "p/a.txt", "hit a\n")
    fake.explode_on("b", "p/b.txt", errors.ObjetoNoEncontrado("b", "p/b.txt"))
    fake.put("b", "p/c.txt", "hit c\n")

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/a.txt:hit a\ngs://b/p/c.txt:hit c\n"
    assert _linea_con(err, "ya no existe", "gs://b/p/b.txt")
    assert "Traceback" not in err
    assert exit_code == 2


# --- NFR-2 (a) ------------------------------------------------------------------------


def test_vc15_red_caida_al_listar(fake, monkeypatch, capsys):
    def sin_red(bucket, prefix):
        fake.listados += 1
        raise errors.ErrorDeRedAlListar(bucket)

    monkeypatch.setattr(gcs, "list_objects", sin_red)

    exit_code, out, err = _correr(capsys, ["x", "gs://b/p/"])

    assert exit_code == 2
    assert out == ""
    assert "error de red" in err
    assert "gs://b" in err
    assert "Traceback" not in err
    assert fake.listados == 1


# --- core: el aviso sale en su lugar del flujo, no al final ------------------------


def test_vc6_core_emite_el_aviso_entre_los_matches():
    fake = FakeGCS()
    fake.put("b", "p/a.txt", "hit a\n")
    fake.explode_on("b", "p/b.txt", errors.ObjetoSinPermiso("b", "p/b.txt"))
    fake.put("b", "p/c.txt", "hit c\n")

    eventos = list(
        core.search("b", "p/", core.SearchConfig("hit"), fake.list_objects, fake.open_stream)
    )

    assert [type(e).__name__ for e in eventos] == ["Match", "Aviso", "Match"]
    assert eventos[1].es_error


# --- gcs: traducción de las excepciones reales del SDK -------------------------------


class _BlobQueFalla:
    def __init__(self, al_abrir=None, al_leer=None):
        self._al_abrir = al_abrir
        self._al_leer = al_leer
        self.open_kwargs = None

    def open(self, mode, **kwargs):
        self.open_kwargs = kwargs
        if self._al_abrir is not None:
            raise self._al_abrir
        al_leer = self._al_leer

        class _Reader:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def __iter__(self):
                yield "hit\n"
                raise al_leer

            def read(self, size=-1):
                raise al_leer

        return _Reader()


class _ClienteCon:
    def __init__(self, blob=None, al_listar=None):
        self._blob = blob
        self._al_listar = al_listar
        self.list_kwargs = None

    def list_blobs(self, bucket, **kwargs):
        self.list_kwargs = kwargs
        if self._al_listar is not None:
            raise self._al_listar
        return []

    def bucket(self, name):
        blob = self._blob

        class _Bucket:
            def blob(self, name):
                return blob

        return _Bucket()


@pytest.mark.parametrize(
    "error_sdk",
    [api_exceptions.Forbidden("403"), api_exceptions.Unauthorized("401")],
)
def test_vc6_gcs_traduce_403_y_401_de_un_objeto(monkeypatch, error_sdk):
    monkeypatch.setattr(gcs, "_get_client", lambda: _ClienteCon(_BlobQueFalla(al_abrir=error_sdk)))

    with pytest.raises(errors.ObjetoSinPermiso):
        gcs.open_stream("b", "p/a.txt")


def test_vc32_gcs_traduce_404_de_un_objeto(monkeypatch):
    blob = _BlobQueFalla(al_abrir=api_exceptions.NotFound("404"))
    monkeypatch.setattr(gcs, "_get_client", lambda: _ClienteCon(blob))

    with pytest.raises(errors.ObjetoNoEncontrado):
        gcs.open_stream("b", "p/a.txt")


_ERRORES_DE_RED = [
    requests.exceptions.ConnectionError("conexión cortada"),
    requests.exceptions.Timeout("timeout"),
    api_exceptions.ServiceUnavailable("503"),
    api_exceptions.InternalServerError("500"),
]


@pytest.mark.parametrize("error_sdk", _ERRORES_DE_RED)
def test_vc33_gcs_traduce_red_al_abrir(monkeypatch, error_sdk):
    blob = _BlobQueFalla(al_abrir=error_sdk)
    monkeypatch.setattr(gcs, "_get_client", lambda: _ClienteCon(blob))

    with pytest.raises(errors.ErrorDeRedAlLeer):
        gcs.open_stream("b", "p/a.txt")


@pytest.mark.parametrize("error_sdk", _ERRORES_DE_RED)
def test_vc21_gcs_traduce_red_a_mitad_de_lectura(monkeypatch, error_sdk):
    blob = _BlobQueFalla(al_leer=error_sdk)
    monkeypatch.setattr(gcs, "_get_client", lambda: _ClienteCon(blob))

    with pytest.raises(errors.ErrorDeRedAlLeer):
        with gcs.open_stream("b", "p/a.txt") as stream:
            while stream.read(65536):
                pass


@pytest.mark.parametrize("error_sdk", _ERRORES_DE_RED)
def test_vc15_gcs_traduce_red_al_listar(monkeypatch, error_sdk):
    monkeypatch.setattr(gcs, "_get_client", lambda: _ClienteCon(al_listar=error_sdk))

    with pytest.raises(errors.ErrorDeRedAlListar) as info:
        list(gcs.list_objects("b", "p/"))

    assert "error de red" in str(info.value)
    assert "gs://b" in str(info.value)


def test_vc15_y_vc29_gcs_desactiva_los_reintentos_del_sdk(monkeypatch):
    """NFR-2 / ADR-0016: 0 reintentos también dentro de la librería cliente."""
    blob = _BlobQueFalla()
    cliente = _ClienteCon(blob)
    monkeypatch.setattr(gcs, "_get_client", lambda: cliente)

    list(gcs.list_objects("b", "p/"))
    gcs.open_stream("b", "p/a.txt")

    assert cliente.list_kwargs.get("retry", "falta") is None
    assert blob.open_kwargs.get("retry", "falta") is None

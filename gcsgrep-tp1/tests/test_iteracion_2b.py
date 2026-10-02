"""Iteración 2b · los VCs nuevos o cambiados de la spec v1.7.

FR-29 (otro `4xx`), la clasificación de ADR-0025 en el borde de `gcs`, NFR-2 con
0 reintentos y timeout de 60 s también en la librería (ADR-0028), FR-8 con
`gs://` sin bucket, FR-25 con `gcsgrep: error:`, FR-30 (ayuda) y VC-43 con las
reglas contextuales de `str.lower()`.
"""

import io

import pytest
import requests
from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions

from gcsgrep import cli, core, errors, gcs
from .fakes import FakeGCS


class _ContadorGCS(FakeGCS):
    def __init__(self) -> None:
        super().__init__()
        self.listados = 0
        self.aperturas = []

    def list_objects(self, bucket, prefix):
        self.listados += 1
        return super().list_objects(bucket, prefix)

    def open_stream(self, bucket, name):
        self.aperturas.append(name)
        return super().open_stream(bucket, name)


@pytest.fixture
def fake(monkeypatch):
    f = _ContadorGCS()
    monkeypatch.setattr(gcs, "list_objects", f.list_objects)
    monkeypatch.setattr(gcs, "open_stream", f.open_stream)
    return f


def _correr(capsys, argv):
    try:
        exit_code = cli.main(argv)
    except SystemExit as exc:
        exit_code = exc.code
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _linea_con(err, *textos):
    return any(all(t in linea for t in textos) for linea in err.splitlines())


# --- Un cliente del SDK cuyos blobs fallan en la apertura o en la primera lectura --


class _Lector:
    """Lector de bytes que entrega `contenido` o falla en la primera lectura."""

    def __init__(self, contenido=b"", error=None):
        self._datos = io.BytesIO(contenido)
        self._error = error

    def read(self, size=-1):
        if self._error is not None:
            raise self._error
        return self._datos.read(size)

    def close(self):
        pass


class _Cliente:
    """Doble del cliente del SDK. `objetos` es {nombre: bytes | Exception}: una
    excepción se levanta en la **primera lectura**, como lo hace `BlobReader`."""

    def __init__(self, objetos, al_abrir=None, al_listar=None):
        self._objetos = objetos
        self._al_abrir = al_abrir or {}
        self._al_listar = al_listar
        self.list_kwargs = None
        self.open_kwargs = []

    def list_blobs(self, bucket, prefix=None, **kwargs):
        self.list_kwargs = kwargs
        if self._al_listar is not None:
            raise self._al_listar

        class _Blob:
            def __init__(self, name):
                self.name = name

        return [_Blob(n) for n in sorted(self._objetos)]

    def bucket(self, name):
        cliente = self

        class _Blob:
            def __init__(self, nombre):
                self._nombre = nombre

            def open(self, mode, **kwargs):
                cliente.open_kwargs.append(kwargs)
                if self._nombre in cliente._al_abrir:
                    raise cliente._al_abrir[self._nombre]
                valor = cliente._objetos[self._nombre]
                if isinstance(valor, Exception):
                    return _Lector(error=valor)
                return _Lector(valor)

        class _Bucket:
            def blob(self, nombre):
                return _Blob(nombre)

        return _Bucket()


def _por_gcs(monkeypatch, cliente):
    """De punta a punta a través del `gcs` real (traducción incluida)."""
    monkeypatch.setattr(gcs, "_get_client", lambda: cliente)


# --- FR-29 · otro 4xx sobre un objeto (VC-50) ------------------------------------------


def test_vc50_otro_4xx_en_la_primera_lectura_no_aborta(monkeypatch, capsys):
    _por_gcs(monkeypatch, _Cliente({
        "p/a.txt": b"hit a\n",
        "p/b.txt": api_exceptions.BadRequest("400"),
        "p/c.txt": b"hit c\n",
    }))

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/a.txt:hit a\ngs://b/p/c.txt:hit c\n"
    assert _linea_con(err, "no se pudo leer", "gs://b/p/b.txt")
    assert "Traceback" not in err
    assert exit_code == 2


@pytest.mark.parametrize(
    "error_sdk",
    [api_exceptions.BadRequest("400"), api_exceptions.Conflict("409"),
     api_exceptions.PreconditionFailed("412")],
)
def test_vc50_gcs_traduce_otros_4xx_al_abrir(monkeypatch, error_sdk):
    _por_gcs(monkeypatch, _Cliente({"p/a.txt": b""}, al_abrir={"p/a.txt": error_sdk}))

    with pytest.raises(errors.ObjetoIlegible):
        gcs.open_stream("b", "p/a.txt")


# --- FR-6 y FR-21 en la primera lectura (acción 3) -------------------------------------


@pytest.mark.parametrize(
    "error_sdk, texto",
    [
        (api_exceptions.Forbidden("403"), "sin permiso para leer"),
        (api_exceptions.Unauthorized("401"), "sin permiso para leer"),
        (auth_exceptions.RefreshError("token revocado"), "sin permiso para leer"),
        (api_exceptions.NotFound("404"), "ya no existe"),
    ],
)
def test_vc6_y_vc32_fallo_en_la_primera_lectura(monkeypatch, capsys, error_sdk, texto):
    _por_gcs(monkeypatch, _Cliente({"p/a.txt": b"hit a\n", "p/b.txt": error_sdk}))

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/a.txt:hit a\n"
    assert _linea_con(err, texto, "gs://b/p/b.txt")
    assert "Traceback" not in err
    assert exit_code == 2


# --- NFR-2 · 408 y 429 son red; sin reintentos y timeout de 60 s (VC-15, VC-29) ----------


@pytest.mark.parametrize(
    "error_sdk",
    [api_exceptions.from_http_status(408, "timeout"), api_exceptions.TooManyRequests("429")],
)
def test_vc21_408_y_429_sobre_un_objeto_son_error_de_red(monkeypatch, capsys, error_sdk):
    _por_gcs(monkeypatch, _Cliente({"p/a.txt": error_sdk, "p/b.txt": b"hit dos\n"}))

    exit_code, out, err = _correr(capsys, ["hit", "gs://b/p/"])

    assert out == "gs://b/p/b.txt:hit dos\n"
    assert _linea_con(err, "error de red al leer", "gs://b/p/a.txt")
    assert exit_code == 2


@pytest.mark.parametrize(
    "error_sdk",
    [api_exceptions.from_http_status(408, "timeout"), api_exceptions.TooManyRequests("429")],
)
def test_vc15_408_y_429_al_listar_son_error_de_red(monkeypatch, error_sdk):
    _por_gcs(monkeypatch, _Cliente({}, al_listar=error_sdk))

    with pytest.raises(errors.ErrorDeRedAlListar):
        list(gcs.list_objects("b", "p/"))


def test_vc15_y_vc29_sin_reintentos_y_timeout_de_60s_en_la_libreria(monkeypatch):
    cliente = _Cliente({"p/a.txt": b"x\n"})
    _por_gcs(monkeypatch, cliente)

    list(gcs.list_objects("b", "p/"))
    gcs.open_stream("b", "p/a.txt")

    assert cliente.list_kwargs["retry"] is None
    assert cliente.list_kwargs["timeout"] == 60
    assert cliente.open_kwargs[0]["retry"] is None
    assert cliente.open_kwargs[0]["timeout"] == 60


# --- FR-26 · el archivo de `gcloud` mal formado es una fuente configurada ----------------


def test_vc41_archivo_de_gcloud_presente_da_credenciales_invalidas(monkeypatch, tmp_path):
    (tmp_path / "application_default_credentials.json").write_text("{ no es json")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("CLOUDSDK_CONFIG", str(tmp_path))
    monkeypatch.setattr(gcs, "_client", None)

    def no_se_crea():
        raise auth_exceptions.DefaultCredentialsError("archivo mal formado")

    monkeypatch.setattr(gcs.storage, "Client", no_se_crea)

    with pytest.raises(errors.CredencialesInvalidas):
        list(gcs.list_objects("b", "p/"))


def test_vc23_sin_variable_ni_archivo_de_gcloud_son_credenciales_ausentes(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("CLOUDSDK_CONFIG", str(tmp_path))  # vacío
    monkeypatch.setattr(gcs, "_client", None)

    def no_se_crea():
        raise auth_exceptions.DefaultCredentialsError("not found")

    monkeypatch.setattr(gcs.storage, "Client", no_se_crea)

    with pytest.raises(errors.SinCredenciales):
        list(gcs.list_objects("b", "p/"))


# --- FR-8 · `gs://` sin bucket (VC-39 reubicado) ------------------------------------------


@pytest.mark.parametrize("ubicacion", ["gs://", "gs:///p"])
def test_vc39_gs_sin_bucket_es_ubicacion_invalida(fake, capsys, ubicacion):
    exit_code, out, err = _correr(capsys, ["x", ubicacion])

    assert exit_code == 2
    assert out == ""
    assert "gs://" in err
    assert "Traceback" not in err
    assert fake.listados == 0


# --- FR-25 · texto fijo `gcsgrep: error:` ----------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["-l", "x", "gs://b/p/"],          # VC-37
        ["--max", "-1", "x", "gs://b/p/"],  # VC-38
        ["--max", "abc", "x", "gs://b/p/"],  # VC-38
        [],                                 # VC-40
        ["x"],                              # VC-40
        ["--ig", "x", "gs://b/p/"],         # VC-46
    ],
)
def test_vc37_vc38_vc40_vc46_rechazo_con_texto_fijo(fake, capsys, argv):
    exit_code, out, err = _correr(capsys, argv)

    assert exit_code == 2
    assert out == ""
    assert "gcsgrep: error:" in err
    assert "Traceback" not in err
    assert fake.listados == 0


# --- VC-47 · lo que *Dentro* sí acepta -------------------------------------------------


@pytest.mark.parametrize(
    "argv, esperado",
    [
        (["--", "-x", "gs://b/p/"], "gs://b/p/a.txt:a -x b\n"),
        (["-in", "hit", "gs://b/p/"], "gs://b/p/a.txt:2:Hit\n"),
        (["--max=1", "-i", "-n", "hit", "gs://b/p/"], "gs://b/p/a.txt:2:Hit\n"),
    ],
)
def test_vc47_sintaxis_aceptada(fake, capsys, argv, esperado):
    fake.put("b", "p/a.txt", "a -x b\nHit\n")

    assert _correr(capsys, argv) == (0, esperado, "")


# --- FR-30 · ayuda (VC-48, VC-49) --------------------------------------------------------


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_vc48_ayuda(fake, capsys, flag):
    exit_code, out, err = _correr(capsys, [flag])

    assert exit_code == 0
    for texto in ("gcsgrep", "--ignore-case", "--line-number", "--max", "--help"):
        assert texto in out
    assert err == ""
    assert fake.listados == 0


def test_vc49_las_formas_largas_dan_la_misma_salida(fake, capsys):
    fake.put("b", "p/a.txt", "Árbol caído\n")
    fake.put("b", "p/b.txt", "uno\ndos\nerror: timeout\ncuatro\ncinco\n")

    assert _correr(capsys, ["--ignore-case", "árbol", "gs://b/p/"]) == _correr(
        capsys, ["-i", "árbol", "gs://b/p/"]
    )
    assert _correr(capsys, ["--line-number", "timeout", "gs://b/p/"]) == _correr(
        capsys, ["-n", "timeout", "gs://b/p/"]
    )


# --- FR-2 · reglas contextuales (VC-43, acción 5) -----------------------------------------


def test_vc43_sigma_final_con_ignore_case(fake, capsys):
    fake.put("b", "p/g.txt", "ΟΔΟΣ\n")

    assert _correr(capsys, ["-i", "σ", "gs://b/p/g.txt"]) == (1, "", "")
    assert _correr(capsys, ["-i", "ς", "gs://b/p/g.txt"]) == (0, "gs://b/p/g.txt:ΟΔΟΣ\n", "")

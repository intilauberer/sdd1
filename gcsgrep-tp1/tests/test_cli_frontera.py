"""Iteración 2 · CLI: corte de stdout (FR-23), invocación mal formada (FR-25,
abreviaturas) y credenciales (FR-15, FR-26, FR-28)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions

from gcsgrep import cli, errors, gcs
from .fakes import FakeGCS

RAIZ = Path(__file__).resolve().parent.parent


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


# --- FR-23 · `| head -1` → SIGPIPE ------------------------------------------------

_PROGRAMA = """
import io, os, sys
from gcsgrep import cli, gcs
from tests.fakes import HugeLineStream

def abrir(bucket, nombre):
    # Se registra en el momento: el proceso muere por la señal, sin atexit.
    with open(os.environ["GCSGREP_APERTURAS"], "a") as registro:
        registro.write(nombre + "\\n")
    if nombre == "p/a.txt":
        return HugeLineStream(b"hit\\n", 200000)
    return io.BytesIO(b"hit\\n")

gcs.list_objects = lambda b, p: ["p/a.txt", "p/b.txt"]
gcs.open_stream = abrir
sys.exit(cli.main(["hit", "gs://b/p/"]))
"""


@pytest.mark.skipif(sys.platform == "win32", reason="SIGPIPE es POSIX")
def test_vc35_head_corta_la_salida_por_sigpipe_sin_stderr(tmp_path):
    stderr = tmp_path / "stderr"
    aperturas = tmp_path / "aperturas"
    script = tmp_path / "gcsgrep_con_doble.py"
    script.write_text(_PROGRAMA)
    pipeline = (
        f'"{sys.executable}" "{script}" 2>"{stderr}" | head -1; '
        f'echo "estado=${{PIPESTATUS[0]}}" >&2'
    )

    r = subprocess.run(
        ["bash", "-c", pipeline],
        cwd=RAIZ,
        env={**os.environ, "PYTHONPATH": str(RAIZ), "GCSGREP_APERTURAS": str(aperturas)},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert r.stdout == "gs://b/p/a.txt:hit\n"
    assert stderr.read_text() == ""
    assert "estado=141" in r.stderr
    # Spec v1.7: no lee más objetos después del corte.
    assert aperturas.read_text() == "p/a.txt\n"


def test_vc35_broken_pipe_no_llega_al_caso_generico(fake, monkeypatch, capsys):
    """En proceso: el corte no se reporta como "error inesperado" (ADR-0019)."""
    fake.put("b", "p/a.txt", "hit\n")
    muertes = []
    monkeypatch.setattr(cli, "_terminar_por_sigpipe", lambda: muertes.append(1))

    def print_roto(*args, **kwargs):
        if kwargs.get("file") is None:
            raise BrokenPipeError()

    monkeypatch.setattr("builtins.print", print_roto)

    cli.main(["hit", "gs://b/p/"])

    assert muertes == [1]


# --- FR-25 · abreviaturas y patrón con `-` (excepción registrada, acción 6) ----------


@pytest.mark.parametrize("abreviatura", ["--ig", "--line", "--ma=3"])
def test_vc46_abreviaturas_de_opciones_largas_se_rechazan(fake, capsys, abreviatura):
    exit_code, out, err = _correr(capsys, [abreviatura, "x", "gs://b/p/"])

    assert exit_code == 2
    assert out == ""
    assert "Traceback" not in err
    assert fake.listados == 0


def test_vc49_las_formas_largas_completas_siguen_andando(fake, capsys):
    fake.put("b", "p/a.txt", "Hit\n")

    assert _correr(capsys, ["--ignore-case", "--line-number", "hit", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:1:Hit\n", ""
    )


def test_vc47_patron_que_empieza_con_guion_despues_de_doble_guion(fake, capsys):
    fake.put("b", "p/a.txt", "a -x b\n")

    assert _correr(capsys, ["--", "-x", "gs://b/p/"]) == (0, "gs://b/p/a.txt:a -x b\n", "")


# --- FR-15, FR-26, FR-28 · credenciales, de punta a punta ------------------------------


def _listado_que_levanta(fake, error):
    def explota(bucket, prefix):
        fake.listados += 1
        raise error
        yield  # pragma: no cover

    return explota


def test_vc23_sin_credenciales(fake, monkeypatch, capsys):
    monkeypatch.setattr(gcs, "list_objects", _listado_que_levanta(fake, errors.SinCredenciales()))

    exit_code, out, err = _correr(capsys, ["x", "gs://b/p/"])

    assert exit_code == 2
    assert out == ""
    assert "no se encontraron credenciales" in err
    assert "gcloud auth application-default login" in err
    assert "Traceback" not in err
    assert fake.aperturas == []


@pytest.mark.parametrize("vc", ["VC-41", "VC-45"])
def test_vc41_y_vc45_credenciales_invalidas(fake, monkeypatch, capsys, vc):
    monkeypatch.setattr(
        gcs, "list_objects", _listado_que_levanta(fake, errors.CredencialesInvalidas())
    )

    exit_code, out, err = _correr(capsys, ["x", "gs://b/p/"])

    assert exit_code == 2
    assert out == ""
    assert "credenciales inválidas o vencidas" in err
    assert "gcloud auth application-default login" in err
    assert "no se encontraron credenciales" not in err
    assert "Traceback" not in err
    assert fake.aperturas == []


# --- gcs: de qué excepción del SDK sale cada error de credenciales ------------------------


class _ClienteQueLista:
    def __init__(self, error):
        self._error = error

    def list_blobs(self, bucket, **kwargs):
        raise self._error


def _cliente_que_no_se_crea(error):
    def crear():
        raise error

    return crear


def test_vc23_gcs_traduce_adc_ausente(monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setattr(gcs, "_client", None)
    monkeypatch.setattr(
        gcs.storage, "Client",
        _cliente_que_no_se_crea(auth_exceptions.DefaultCredentialsError("not found")),
    )

    with pytest.raises(errors.SinCredenciales):
        list(gcs.list_objects("b", "p/"))


def test_vc41_gcs_traduce_archivo_de_credenciales_roto(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "no-existe.json"))
    monkeypatch.setattr(gcs, "_client", None)
    monkeypatch.setattr(
        gcs.storage, "Client",
        _cliente_que_no_se_crea(auth_exceptions.DefaultCredentialsError("File not found")),
    )

    with pytest.raises(errors.CredencialesInvalidas):
        list(gcs.list_objects("b", "p/"))


def test_vc41_gcs_traduce_refresh_rechazado(monkeypatch):
    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClienteQueLista(auth_exceptions.RefreshError("revoked"))
    )

    with pytest.raises(errors.CredencialesInvalidas):
        list(gcs.list_objects("b", "p/"))


def test_vc45_gcs_traduce_401_al_listar(monkeypatch):
    monkeypatch.setattr(
        gcs, "_get_client", lambda: _ClienteQueLista(api_exceptions.Unauthorized("401"))
    )

    with pytest.raises(errors.CredencialesInvalidas):
        list(gcs.list_objects("b", "p/"))


# --- NFR-3 · los avisos del runtime del SDK no llegan a stderr ------------------------
#
# Regresión encontrada por CI (2026-10-02, job Python 3.9): `google-api-core` y
# `google-auth` emiten `FutureWarning` por stderr **al importarse** en Pythons sin
# soporte, o sea en toda corrida. Los tests en proceso no lo ven (los imports pasan
# al recolectar, antes de capturar); VC-35, que arranca un intérprete nuevo, sí.
# Este test lo reproduce en cualquier versión: emite el mismo tipo de aviso a
# nombre de un módulo `google.*` después de importar `gcsgrep`.


def test_vc1_un_futurewarning_del_sdk_no_llega_a_stderr():
    programa = (
        "import warnings, gcsgrep.cli\n"
        "warnings.warn_explicit('Python sin soporte', FutureWarning, 'x.py', 1,\n"
        "                       module='google.api_core._python_version_support')\n"
    )

    r = subprocess.run(
        [sys.executable, "-c", programa],
        cwd=RAIZ,
        env={**os.environ, "PYTHONPATH": str(RAIZ)},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert r.returncode == 0
    assert r.stderr == ""

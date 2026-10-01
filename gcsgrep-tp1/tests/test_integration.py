"""Verificación de integración contra GCS real. NO corre por defecto.

Estos tests son los únicos del repo que necesitan credenciales, red y plata. Están
marcados con `@pytest.mark.integration` y la configuración de pytest los excluye
(`addopts = -m "not integration"`), así que `python -m pytest` sigue siendo offline.

Para correrlos:

    export GCSGREP_TEST_BUCKET=gcsgrep-test-loquesea
    ./scripts/testing-ground.sh up
    python -m pytest -m integration -v
    ./scripts/testing-ground.sh down

Dependen de las fixtures exactas que siembra `scripts/testing-ground.sh`; sin ese
bucket no tienen sentido y se saltean.

Cobertura: I-1, I-2, I-3, I-5 e I-7 de la tabla de integración de
`specs/gcsgrep/04-cobertura-vc.md`. Los chequeos I-4 (ubicación inválida, que no
toca la red) e I-6 (ADC ausente, que requiere tapar las credenciales del proceso)
viven en el runbook de shell, no acá: manipular las credenciales del intérprete
que corre pytest contamina al resto de la sesión.

Corren igual contra GCS real o contra el emulador `floci-gcp`: lo único que cambia
es a qué host apunta el SDK (ADR-0014). Lo que el emulador NO verifica —ADC, IAM,
red real— está en la tabla comparativa de ese ADR.
"""

import os

import pytest

pytestmark = pytest.mark.integration

BUCKET = os.environ.get("GCSGREP_TEST_BUCKET", "")

requiere_bucket = pytest.mark.skipif(
    not BUCKET,
    reason="falta GCSGREP_TEST_BUCKET; ver docs/integracion-gcs.md",
)


@pytest.fixture
def prefijo_logs():
    return f"gs://{BUCKET}/logs/"


@requiere_bucket
def test_i1_busqueda_con_match_contra_gcs_real(prefijo_logs, capsys):
    """I-1 · VC-1 y VC-4 contra GCS real."""
    from gcsgrep import cli

    exit_code = cli.main(["timeout", prefijo_logs])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert f"gs://{BUCKET}/logs/a.txt" in out
    assert "timeout" in out


@requiere_bucket
def test_i2_ignore_case_y_numero_de_linea_contra_gcs_real(prefijo_logs, capsys):
    """I-2 · VC-2 y VC-3 contra GCS real.

    `logs/c.txt` tiene `Timeout error` en la línea 2 y es el único objeto con el
    patrón capitalizado, así que `-i` es lo que lo trae.
    """
    from gcsgrep import cli

    exit_code = cli.main(["-i", "-n", "TIMEOUT", prefijo_logs])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert f"gs://{BUCKET}/logs/c.txt:2:" in out


@requiere_bucket
def test_i3_sin_resultados_contra_gcs_real(prefijo_logs, capsys):
    """I-3 · VC-5 contra GCS real: exit 1 y stdout vacío."""
    from gcsgrep import cli

    exit_code = cli.main(["no-existe-esto-en-ningun-lado", prefijo_logs])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Traceback" not in captured.err


@requiere_bucket
def test_i5_primer_match_sin_leer_el_objeto_completo(capsys):
    """I-5 · VC-17 y NFR-1 contra GCS real.

    `grande/big.txt` tiene 200.000 líneas y todas matchean. Se pide **un** match
    y se cierra el generador: si `search` acumulara resultados o el stream bajara
    el objeto completo, esto tendría que esperar las 200.000 líneas.

    La observación fuerte de salida incremental en un pipe real (`| head -3`) está
    en el chequeo I-5 de `scripts/testing-ground.sh`: acá no hay pipe.
    """
    from gcsgrep import core, gcs

    resultados = core.search(
        BUCKET, "grande/",
        core.SearchConfig(pattern="linea"),
        gcs.list_objects, gcs.open_text_stream,
    )
    try:
        primero = next(resultados)
    finally:
        resultados.close()

    assert primero.object_name == "grande/big.txt"
    assert primero.line_number == 1


@requiere_bucket
def test_i7_bucket_inexistente_no_deja_traceback(capsys):
    """I-7 · VC-18 y FR-12 contra un backend real.

    Apunta a un bucket que no existe, así que no depende de las fixtures — solo de
    que el nombre siga sin existir. Es el chequeo que cierra el hallazgo H-12: el
    traceback de `google.api_core.exceptions.NotFound` que destapó todo esto.

    La afirmación fuerte no es el exit code, es que el mensaje **identifique el
    caso**. Sin credenciales, o contra un emulador mal apuntado, el exit 2 llega
    igual por el caso genérico de ADR-0013: exigir el texto de FR-12 es lo que hace
    que este chequeo pueda fallar por la razón correcta.
    """
    from gcsgrep import cli

    exit_code = cli.main(["x", "gs://gcsgrep-test-no-existe-jamas/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert "gcsgrep-test-no-existe-jamas" in captured.err
    assert "no existe" in captured.err

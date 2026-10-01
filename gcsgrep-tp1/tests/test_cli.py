"""VCs de Iteración 1 ejercitados de punta a punta a través de argv y exit code."""

import pytest

from gcsgrep import cli, errors, gcs
from .fakes import ExplodingStream, FakeGCS, RecordingFakeGCS


@pytest.fixture
def fake_gcs(monkeypatch):
    fake = FakeGCS()
    monkeypatch.setattr(gcs, "list_objects", fake.list_objects)
    monkeypatch.setattr(gcs, "open_text_stream", fake.open_text_stream)
    return fake


def test_vc1_exit_0_y_formato_con_gs_uri(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "connection timeout\n")

    exit_code = cli.main(["timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "gs://b/logs/a.txt:connection timeout"
    assert captured.err == ""


def test_vc2_ignore_case_end_to_end(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "Timeout error\n")

    assert cli.main(["timeout", "gs://b/logs/"]) == 1
    capsys.readouterr()

    assert cli.main(["-i", "timeout", "gs://b/logs/"]) == 0
    out = capsys.readouterr().out
    assert "Timeout error" in out


def test_vc3_line_number_flag(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "l1\nl2\nmatch aqui\nl4\n")

    cli.main(["match", "gs://b/logs/"])
    sin_n = capsys.readouterr().out.strip()

    cli.main(["-n", "match", "gs://b/logs/"])
    con_n = capsys.readouterr().out.strip()

    assert sin_n == "gs://b/logs/a.txt:match aqui"
    assert con_n == "gs://b/logs/a.txt:3:match aqui"


def test_vc4_formato_de_salida_parseable(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "linea con match\n")

    cli.main(["-n", "match", "gs://b/logs/"])
    line = capsys.readouterr().out.strip()

    assert line.startswith("gs://")
    rest = line[len("gs://"):]
    object_path, line_number, text = rest.split(":", 2)
    assert object_path == "b/logs/a.txt"
    assert line_number.isdigit()
    assert "match" in text


def test_vc5_sin_resultados_exit_1_stdout_vacio(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "nada relevante\n")

    exit_code = cli.main(["timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Traceback" not in captured.err


def test_vc7_bucket_completo_prefijo_vacio(fake_gcs, capsys):
    fake_gcs.put("b", "a/x.txt", "timeout en carpeta a\n")
    fake_gcs.put("b", "c/y.txt", "timeout en carpeta c\n")

    exit_code = cli.main(["timeout", "gs://b/"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "a/x.txt" in out
    assert "c/y.txt" in out


def test_vc8_ubicacion_sin_esquema_exit_2(capsys):
    exit_code = cli.main(["patron", "logs/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "gs://" in captured.err
    assert "Traceback" not in captured.err


def test_vc8_esquema_no_soportado_exit_2(capsys):
    exit_code = cli.main(["patron", "s3://bucket/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "gs://" in captured.err



def test_vc17_los_matches_se_imprimen_antes_de_que_termine_la_corrida(monkeypatch, capsys):
    """VC-17 — FR-11: la salida es incremental, también de punta a punta.

    El objeto emite dos líneas que matchean y después falla al leer. Si `cli`
    imprimiera al final (el comportamiento anterior a ADR-0011), la excepción
    se llevaría los dos matches y stdout quedaría vacío. Con salida incremental
    ya salieron.

    Este test NO especifica nada sobre *cómo* se maneja el error de lectura: solo
    mira lo que ya se imprimió antes de que apareciera. Por eso siguió valiendo
    cuando la frontera de excepciones de la spec v1.2 cambió el final de la
    corrida —antes la excepción escapaba, ahora da exit 2 sin traceback— y va a
    seguir valiendo cuando FR-6 (Iteración 2) la convierta en un mensaje por
    stderr que no aborte.

    Cambio de observable registrado el 2026-09-24 en 04-cobertura-vc.md: lo que
    se afirma es lo mismo, lo que se observa al final cambió.
    """
    boom = OSError("fallo de lectura simulado")

    def list_objects(bucket, prefix):
        return ["logs/a.txt"]

    def open_text_stream(bucket, name):
        return ExplodingStream(["timeout uno\n", "timeout dos\n"], boom)

    monkeypatch.setattr(gcs, "list_objects", list_objects)
    monkeypatch.setattr(gcs, "open_text_stream", open_text_stream)

    exit_code = cli.main(["timeout", "gs://b/logs/"])

    # Con la frontera de la v1.2 el fallo se reporta en vez de escapar (VC-16 b);
    # lo que este VC observa es que los dos matches salieron *antes*.
    assert exit_code == 2
    out = capsys.readouterr().out
    assert out.splitlines() == [
        "gs://b/logs/a.txt:timeout uno",
        "gs://b/logs/a.txt:timeout dos",
    ]


# --- VC-18 · FR-12 bucket inexistente o inaccesible --------------------------
#
# El colaborador de `gcs` levanta el error de dominio que `gcs.list_objects`
# produce cuando el SDK devuelve 404 o 403. Que la traducción del SDK sea la
# correcta se verifica aparte, en test_gcs.py.


def test_vc18_bucket_inexistente_exit_2_mensaje_sin_traceback(monkeypatch, capsys):
    def explota(bucket, prefix):
        raise errors.BucketNoEncontrado(bucket)
        yield  # pragma: no cover — lo hace generador, como el real

    monkeypatch.setattr(gcs, "list_objects", explota)

    exit_code = cli.main(["x", "gs://no-existe/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "no-existe" in captured.err
    assert "no existe" in captured.err
    assert "Traceback" not in captured.err


def test_vc18_sin_permiso_da_un_mensaje_distinto_al_de_inexistente(monkeypatch, capsys):
    """El mensaje tiene que distinguir los dos casos: mandan a revisar cosas
    distintas (el nombre vs. IAM). Un mensaje único obliga a diagnosticar dos
    veces."""

    def denegado(bucket, prefix):
        raise errors.AccesoDenegado(bucket)
        yield  # pragma: no cover

    monkeypatch.setattr(gcs, "list_objects", denegado)

    assert cli.main(["x", "gs://ajeno/logs/"]) == 2
    err_denegado = capsys.readouterr().err

    def inexistente(bucket, prefix):
        raise errors.BucketNoEncontrado(bucket)
        yield  # pragma: no cover

    monkeypatch.setattr(gcs, "list_objects", inexistente)

    assert cli.main(["x", "gs://ajeno/logs/"]) == 2
    err_inexistente = capsys.readouterr().err

    assert err_denegado != err_inexistente
    assert "permiso" in err_denegado
    assert "permiso" not in err_inexistente
    assert "Traceback" not in err_denegado


def test_vc18_no_abre_ningun_objeto_cuando_falla_el_listado(monkeypatch, capsys):
    aperturas = []

    def explota(bucket, prefix):
        raise errors.BucketNoEncontrado(bucket)
        yield  # pragma: no cover

    def registrar_apertura(bucket, object_name):  # pragma: no cover
        aperturas.append(object_name)
        raise AssertionError("no se debería abrir ningún objeto")

    monkeypatch.setattr(gcs, "list_objects", explota)
    monkeypatch.setattr(gcs, "open_text_stream", registrar_apertura)

    assert cli.main(["x", "gs://no-existe/"]) == 2
    assert aperturas == []


# --- VC-16 (b) · NFR-3 ante una excepción inesperada -------------------------
#
# La parte (a) de VC-16 verifica una lista cerrada de casos de error. Esta
# verifica la parte universal de NFR-3 ("ningún caso de error imprime un stack
# trace"): una excepción que el código no conoce tampoco puede crashear.


class ExcepcionQueNadiePrevio(Exception):
    """Una clase que `gcsgrep` no conoce ni podría conocer."""


def test_vc16b_excepcion_inesperada_al_listar_no_deja_traceback(monkeypatch, capsys):
    def explota(bucket, prefix):
        raise ExcepcionQueNadiePrevio("algo que nadie modeló")
        yield  # pragma: no cover

    monkeypatch.setattr(gcs, "list_objects", explota)

    exit_code = cli.main(["x", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert "ExcepcionQueNadiePrevio" in captured.err
    assert "GCSGREP_DEBUG" in captured.err


def test_vc16b_excepcion_inesperada_al_abrir_un_objeto_no_deja_traceback(
    fake_gcs, monkeypatch, capsys
):
    fake_gcs.put("b", "logs/a.txt", "timeout\n")

    def explota_al_abrir(bucket, object_name):
        raise ExcepcionQueNadiePrevio("falló al abrir")

    monkeypatch.setattr(gcs, "open_text_stream", explota_al_abrir)

    exit_code = cli.main(["timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Traceback" not in captured.err


def test_vc16b_los_matches_ya_emitidos_sobreviven_al_fallo(fake_gcs, capsys):
    """La frontera no puede tragarse la salida incremental: lo que ya salió por
    stdout queda, y el exit code refleja el fallo (VC-17 + VC-16 b)."""
    fake_gcs.put("b", "logs/a.txt", "timeout uno\ntimeout dos\n")
    fake_gcs.explode_on("b", "logs/b.txt", ExcepcionQueNadiePrevio("boom"))

    exit_code = cli.main(["timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "timeout uno" in captured.out
    assert "timeout dos" in captured.out
    assert "Traceback" not in captured.err


def test_vc16b_debug_reexpone_la_excepcion_para_diagnosticar(monkeypatch):
    """La vía de escape explícita: el caso genérico no puede esconder el problema
    para siempre (ADR-0013)."""

    def explota(bucket, prefix):
        raise ExcepcionQueNadiePrevio("detalle que hace falta ver")
        yield  # pragma: no cover

    monkeypatch.setattr(gcs, "list_objects", explota)
    monkeypatch.setenv(cli.DEBUG_ENV, "1")

    with pytest.raises(ExcepcionQueNadiePrevio):
        cli.main(["x", "gs://b/logs/"])


# --- VC-12 · BR-2 de punta a punta, incluido el exit code ---------------------


def _sembrar(fake, n):
    for i in range(n):
        fake.put("b", f"logs/{i:05d}.txt", "connection timeout\n")


def test_vc12_tope_excedido_sale_con_1_y_no_lee_nada(monkeypatch, capsys):
    """BR-2 sale con `1`, no con `2`: no es un error, es una negativa (ADR-0006)."""
    fake = RecordingFakeGCS()
    _sembrar(fake, 1001)
    monkeypatch.setattr(gcs, "list_objects", fake.list_objects)
    monkeypatch.setattr(gcs, "open_text_stream", fake.open_text_stream)

    exit_code = cli.main(["timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert fake.opened == []
    assert "1001" in captured.err and "1000" in captured.err
    assert "Traceback" not in captured.err


def test_vc12_max_0_quita_el_tope_de_punta_a_punta(monkeypatch, capsys):
    fake = RecordingFakeGCS()
    _sembrar(fake, 1001)
    monkeypatch.setattr(gcs, "list_objects", fake.list_objects)
    monkeypatch.setattr(gcs, "open_text_stream", fake.open_text_stream)

    exit_code = cli.main(["--max", "0", "timeout", "gs://b/logs/"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert len(captured.out.strip().splitlines()) == 1001
    assert len(fake.opened) == 1001


def test_vc12_max_explicito_bajo(fake_gcs, capsys):
    fake_gcs.put("b", "logs/a.txt", "timeout\n")
    fake_gcs.put("b", "logs/b.txt", "timeout\n")

    assert cli.main(["--max", "1", "timeout", "gs://b/logs/"]) == 1
    assert "2 objetos" in capsys.readouterr().err


def test_vc12_max_negativo_es_argumento_invalido(capsys):
    """Un tope negativo no tiene significado: `0` ya es "sin tope" (ADR-0006)."""
    exit_code = cli.main(["--max", "-1", "x", "gs://b/"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--max" in captured.err
    assert "Traceback" not in captured.err

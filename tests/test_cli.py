"""VCs de Iteración 1 ejercitados de punta a punta a través de argv y exit code."""

import pytest

from gcsgrep import cli, gcs
from .fakes import FakeGCS


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

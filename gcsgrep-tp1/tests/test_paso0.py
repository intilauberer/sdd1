"""Iteración 2 · Paso 0 — VCs de las specs v1.4/v1.5 sobre comportamiento que la
Iteración 1 ya tenía (ver specs/gcsgrep/03-plan.md, "Paso 0").

Ninguno de estos tests trae código nuevo: escriben como contrato lo que el código
ya hacía. Si alguno hubiera fallado, era la Iteración 1 violando una promesa ahora
escrita (fila 1 de docs/proceso-cambios.md), no alcance de esta iteración.
"""

import os
import sys
import time

import pytest

from gcsgrep import cli, core, errors, gcs
from .fakes import FakeGCS, HugeLineStream


class _ContadorGCS(FakeGCS):
    """`FakeGCS` que cuenta llamadas de listado y aperturas por objeto."""

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
    exit_code = cli.main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _rechazo(capsys, argv):
    """Corre una invocación mal formada: argparse sale con SystemExit(2)."""
    try:
        exit_code = cli.main(argv)
    except SystemExit as exc:
        exit_code = exc.code
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


# --- FR-1, FR-3, FR-4 · stdout exacto ----------------------------------------


def test_vc1_stdout_exacto_y_stderr_vacio(fake, capsys):
    fake.put("b", "logs/a.txt", "connection timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/logs/"]) == (
        0, "gs://b/logs/a.txt:connection timeout\n", ""
    )


_CINCO_LINEAS = "uno\ndos\nerror: timeout\ncuatro\ncinco\n"


def test_vc3_stdout_exacto_con_numero_de_linea(fake, capsys):
    fake.put("b", "p/a.txt", _CINCO_LINEAS)

    assert _correr(capsys, ["-n", "timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:3:error: timeout\n", ""
    )


def test_vc4_stdout_exacto_sin_numero_de_linea(fake, capsys):
    fake.put("b", "p/a.txt", _CINCO_LINEAS)

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:error: timeout\n", ""
    )


# --- FR-8 · 0 llamadas de listado ---------------------------------------------


@pytest.mark.parametrize("ubicacion", ["logs/", "s3://b/"])
def test_vc8_ubicacion_invalida_no_lista(fake, capsys, ubicacion):
    exit_code, out, err = _correr(capsys, ["patrón", ubicacion])

    assert exit_code == 2
    assert out == ""
    assert "gs://" in err
    assert fake.listados == 0


# --- FR-1 · patrón literal ---------------------------------------------------


def test_vc19_el_patron_es_literal(fake, capsys):
    fake.put("b", "p/a.txt", "a.b\naxb\na*b\n")

    assert _correr(capsys, ["a.b", "gs://b/p/"]) == (0, "gs://b/p/a.txt:a.b\n", "")
    assert _correr(capsys, ["a*b", "gs://b/p/"]) == (0, "gs://b/p/a.txt:a*b\n", "")


# --- FR-14 · sin permiso de listado --------------------------------------------


def test_vc22_sin_permiso_de_listado(fake, monkeypatch, capsys):
    def denegado(bucket, prefix):
        fake.listados += 1
        raise errors.AccesoDenegado(bucket)

    monkeypatch.setattr(gcs, "list_objects", denegado)

    exit_code, out, err = _correr(capsys, ["x", "gs://privado/"])

    assert exit_code == 2
    assert out == ""
    assert "gs://privado" in err
    assert "sin permiso" in err
    assert "no existe" not in err
    assert "Traceback" not in err
    assert fake.aperturas == []


# --- FR-16 · orden -------------------------------------------------------------


def test_vc24_orden_de_la_salida(fake, capsys):
    for nombre in ("p/c.txt", "p/a.txt", "p/b.txt"):
        fake.put("b", nombre, "hit 1\nhit 2\n")

    exit_code, out, _ = _correr(capsys, ["hit", "gs://b/p/"])

    assert exit_code == 0
    assert out.splitlines() == [
        "gs://b/p/a.txt:hit 1",
        "gs://b/p/a.txt:hit 2",
        "gs://b/p/b.txt:hit 1",
        "gs://b/p/b.txt:hit 2",
        "gs://b/p/c.txt:hit 1",
        "gs://b/p/c.txt:hit 2",
    ]


# --- FR-18 · prefijo sin `/` -----------------------------------------------------


def test_vc26_prefijo_sin_barra_es_un_prefijo_de_cadena(fake, capsys):
    for nombre in ("logs/a.txt", "logs-other/b.txt", "otros/c.txt"):
        fake.put("b", nombre, "timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/logs"]) == (
        0, "gs://b/logs-other/b.txt:timeout\ngs://b/logs/a.txt:timeout\n", ""
    )
    assert _correr(capsys, ["timeout", "gs://b/logs/"]) == (
        0, "gs://b/logs/a.txt:timeout\n", ""
    )


# --- FR-19, FR-20 ----------------------------------------------------------------


def test_vc27_objeto_de_0_bytes(fake, capsys):
    fake.put("b", "p/vacio.txt", "")
    fake.put("b", "p/a.txt", "timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (0, "gs://b/p/a.txt:timeout\n", "")


def test_vc27_solo_el_objeto_de_0_bytes(fake, capsys):
    fake.put("b", "p/vacio.txt", "")

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (1, "", "")


def test_vc28_ultima_linea_sin_terminador(fake, capsys):
    fake.put("b", "p/a.txt", "uno\ndos")

    assert _correr(capsys, ["-n", "dos", "gs://b/p/"]) == (0, "gs://b/p/a.txt:2:dos\n", "")


# --- NFR-3 · GCSGREP_DEBUG no toca los errores previstos ---------------------------


def test_vc16c_debug_no_afecta_a_un_error_previsto(fake, monkeypatch, capsys):
    def no_existe(bucket, prefix):
        raise errors.BucketNoEncontrado(bucket)

    monkeypatch.setattr(gcs, "list_objects", no_existe)
    monkeypatch.setenv(cli.DEBUG_ENV, "1")

    exit_code, out, err = _correr(capsys, ["x", "gs://no-existe/"])

    assert exit_code == 2
    assert out == ""
    assert "no existe" in err
    assert "Traceback" not in err


# --- FR-7 · stdout exacto con y sin `/` --------------------------------------------


@pytest.mark.parametrize("ubicacion", ["gs://b/", "gs://b"])
def test_vc7_bucket_completo_stdout_exacto(fake, capsys, ubicacion):
    fake.put("b", "a/x.txt", "hit a\n")
    fake.put("b", "b/y.txt", "hit b\n")

    assert _correr(capsys, ["hit", ubicacion]) == (
        0, "gs://b/a/x.txt:hit a\ngs://b/b/y.txt:hit b\n", ""
    )


# --- BR-2 · texto literal y límite exacto ------------------------------------------


def _sembrar(fake, n):
    for i in range(n):
        fake.put("b", f"p/{i:05d}.txt", "nada\n")


def test_vc12_texto_literal_del_tope(fake, capsys):
    _sembrar(fake, 1001)

    exit_code, out, err = _correr(capsys, ["x", "gs://b/p/"])

    assert exit_code == 1
    assert out == ""
    assert "1001 objetos" in err
    assert "el tope es 1000" in err
    assert fake.aperturas == []


def test_vc42_mil_objetos_sin_max_se_leen(fake, capsys):
    _sembrar(fake, 1000)

    exit_code, _, err = _correr(capsys, ["x", "gs://b/p/"])

    assert exit_code == 1
    assert len(fake.aperturas) == 1000
    assert "el tope es" not in err


def test_vc42_max_3_con_3_objetos_se_leen(fake, capsys):
    _sembrar(fake, 3)

    _correr(capsys, ["--max", "3", "x", "gs://b/p/"])

    assert len(fake.aperturas) == 3


def test_vc42_max_3_con_4_objetos_no_se_lee_ninguno(fake, capsys):
    _sembrar(fake, 4)

    exit_code, _, err = _correr(capsys, ["--max", "3", "x", "gs://b/p/"])

    assert exit_code == 1
    assert fake.aperturas == []
    assert "4 objetos" in err
    assert "el tope es 3" in err


# --- FR-24 · patrón vacío -------------------------------------------------------------


def test_vc36_patron_vacio_imprime_todas_las_lineas(fake, capsys):
    fake.put("b", "p/a.txt", "uno\ndos\n")
    fake.put("b", "p/vacio.txt", "")

    assert _correr(capsys, ["", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:uno\ngs://b/p/a.txt:dos\n", ""
    )


def test_vc36_una_linea_vacia_es_una_linea(fake, capsys):
    """Excepción registrada, acción 4: `uno\\n\\ndos\\n` son tres líneas."""
    fake.put("b", "p/a.txt", "uno\n\ndos\n")

    assert _correr(capsys, ["-n", "", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:1:uno\ngs://b/p/a.txt:2:\ngs://b/p/a.txt:3:dos\n", ""
    )


# --- FR-25 · invocación mal formada -------------------------------------------------


def _assert_rechazo(fake, resultado):
    exit_code, out, err = resultado
    assert exit_code == 2
    assert out == ""
    assert err != ""
    assert "Traceback" not in err
    assert fake.listados == 0


def test_vc37_flag_no_soportado(fake, capsys):
    _assert_rechazo(fake, _rechazo(capsys, ["-l", "x", "gs://b/p/"]))


@pytest.mark.parametrize("valor", ["-1", "abc"])
def test_vc38_max_invalido(fake, capsys, valor):
    _assert_rechazo(fake, _rechazo(capsys, ["--max", valor, "x", "gs://b/p/"]))


@pytest.mark.parametrize("ubicacion", ["gs://", "gs:///p"])
def test_vc39_gs_sin_bucket(fake, capsys, ubicacion):
    _assert_rechazo(fake, _rechazo(capsys, ["x", ubicacion]))


@pytest.mark.parametrize("argv", [[], ["x"]])
def test_vc40_faltan_argumentos(fake, capsys, argv):
    _assert_rechazo(fake, _rechazo(capsys, argv))


# --- FR-5 · prefijo sin objetos (excepción registrada, acción 8) ---------------------


def test_vc5_prefijo_sin_objetos(fake, capsys):
    fake.put("b", "otro/a.txt", "timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (1, "", "")


# --- *Dentro* · `--help` (excepción registrada, acción 11) -----------------------------


def test_help_imprime_la_ayuda_por_stdout_y_no_toca_gcs(fake, capsys):
    exit_code, out, _ = _rechazo(capsys, ["--help"])

    assert exit_code == 0
    assert "gs://bucket/prefijo" in out
    assert fake.listados == 0


# --- FR-2 · plegado de `-i` ------------------------------------------------------------


def test_vc43_ignore_case_con_tildes(fake, capsys):
    fake.put("b", "p/a.txt", "Árbol caído\n")

    assert _correr(capsys, ["-i", "árbol", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:Árbol caído\n", ""
    )
    assert _correr(capsys, ["árbol", "gs://b/p/"]) == (1, "", "")


# --- NFR-4 · rendimiento (VC-30) --------------------------------------------------------

_LINEA_80 = b"x" * 79 + b"\n"
_MIB = 1024 * 1024
_REPETICIONES = 100 * _MIB // len(_LINEA_80)


def _corrida_en_proceso(monkeypatch, patron):
    """Una corrida de `cli.main` sobre un objeto de 100 MiB servido desde memoria,
    con stdout a /dev/null. Devuelve (exit code, segundos)."""
    monkeypatch.setattr(gcs, "list_objects", lambda b, p: ["p/a.txt"])
    monkeypatch.setattr(
        gcs, "open_stream", lambda b, n: HugeLineStream(_LINEA_80, _REPETICIONES)
    )
    with open(os.devnull, "w") as devnull:
        monkeypatch.setattr(sys, "stdout", devnull)
        inicio = time.perf_counter()
        exit_code = cli.main([patron, "gs://b/p/"])
        segundos = time.perf_counter() - inicio
    monkeypatch.setattr(sys, "stdout", sys.__stdout__)
    return exit_code, segundos


def _mejor_de_3(medir, umbral):
    """Mejor de 3 corridas; corta antes si una ya cumple (no cambia el veredicto)."""
    mejor = 0.0
    for _ in range(3):
        mejor = max(mejor, medir())
        if mejor >= umbral:
            break
    return mejor


def test_vc30_a_patron_ausente_al_menos_50_mib_por_segundo(monkeypatch):
    def medir():
        exit_code, segundos = _corrida_en_proceso(monkeypatch, "patron-ausente")
        assert exit_code == 1
        return 100 / segundos

    tasa = _mejor_de_3(medir, 50)
    assert tasa >= 50, f"NFR-4 (a): {tasa:.0f} MiB/s < 50 MiB/s"


def test_vc30_b_todo_matchea_al_menos_50000_matches_por_segundo(monkeypatch):
    def medir():
        exit_code, segundos = _corrida_en_proceso(monkeypatch, "x")
        assert exit_code == 0
        return _REPETICIONES / segundos

    tasa = _mejor_de_3(medir, 50_000)
    assert tasa >= 50_000, f"NFR-4 (b): {tasa:.0f} matches/s < 50 000"

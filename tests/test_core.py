"""VCs de Iteración 1 ejercitados directamente sobre `core`, sin CLI ni argv.

`core.search` es un generador (ADR-0011): los tests que quieren el conjunto
completo lo envuelven en `list(...)`; el que verifica la salida incremental
(VC-17) consume de a uno con `next(...)`.
"""

import pytest

from gcsgrep import core
from .fakes import FakeGCS, RecordingFakeGCS


def test_vc8_ubicacion_invalida_sin_esquema():
    with pytest.raises(ValueError, match="gs://"):
        core.parse_location("logs/")


def test_vc8_ubicacion_invalida_esquema_no_soportado():
    with pytest.raises(ValueError, match="gs://"):
        core.parse_location("s3://bucket/prefijo")


def test_vc8_ubicacion_valida_bucket_completo_sin_slash():
    bucket, prefix = core.parse_location("gs://bucket")
    assert bucket == "bucket"
    assert prefix == ""


def test_vc7_bucket_completo_busca_en_todas_las_carpetas():
    fake = FakeGCS()
    fake.put("b", "a/x.txt", "hay timeout aqui\n")
    fake.put("b", "c/y.txt", "otro timeout aca\n")
    fake.put("b", "c/z.txt", "sin nada relevante\n")

    config = core.SearchConfig(pattern="timeout")
    matches = list(core.search("b", "", config, fake.list_objects, fake.open_text_stream))

    matched_objects = {m.object_name for m in matches}
    assert matched_objects == {"a/x.txt", "c/y.txt"}


def test_vc1_busqueda_basica_encuentra_match():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "connection timeout\nok\n")

    config = core.SearchConfig(pattern="timeout")
    matches = list(core.search("b", "logs/", config, fake.list_objects, fake.open_text_stream))

    assert len(matches) == 1
    assert matches[0].bucket == "b"
    assert matches[0].object_name == "logs/a.txt"
    assert matches[0].line_number == 1
    assert "timeout" in matches[0].text


def test_vc2_ignore_case():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "Timeout error\n")

    sin_i = list(core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout"),
        fake.list_objects, fake.open_text_stream,
    ))
    con_i = list(core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout", ignore_case=True),
        fake.list_objects, fake.open_text_stream,
    ))

    assert sin_i == []
    assert len(con_i) == 1
    assert con_i[0].text == "Timeout error"


def test_vc3_numero_de_linea():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "l1\nl2\nmatch aqui\nl4\n")

    matches = list(core.search(
        "b", "logs/", core.SearchConfig(pattern="match"),
        fake.list_objects, fake.open_text_stream,
    ))

    assert len(matches) == 1
    assert matches[0].line_number == 3


def test_vc5_sin_resultados():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "nada que ver por aca\n")

    matches = list(core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout"),
        fake.list_objects, fake.open_text_stream,
    ))

    assert matches == []


def test_vc17_primer_match_se_emite_sin_recorrer_todo_el_prefijo():
    """VC-17 — FR-11: la salida es incremental.

    Con tres objetos que matchean, pedir el primer match no debe haber listado
    ni abierto los otros dos. Si `search` acumulara resultados antes de
    devolverlos (el comportamiento anterior a ADR-0011), este test fallaría:
    `listed` tendría los tres nombres.
    """
    fake = RecordingFakeGCS()
    fake.put("b", "logs/a.txt", "timeout aca\n")
    fake.put("b", "logs/b.txt", "timeout alla\n")
    fake.put("b", "logs/c.txt", "timeout tambien\n")

    resultados = core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout"),
        fake.list_objects, fake.open_text_stream,
    )

    primero = next(resultados)

    assert primero.object_name == "logs/a.txt"
    assert fake.listed == ["logs/a.txt"], "se listó más de un objeto para emitir el primer match"
    assert fake.opened == ["logs/a.txt"], "se abrió más de un objeto para emitir el primer match"

    # Y al seguir consumiendo, avanza de a uno.
    segundo = next(resultados)
    assert segundo.object_name == "logs/b.txt"
    assert fake.opened == ["logs/a.txt", "logs/b.txt"]

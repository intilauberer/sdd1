"""VCs de Iteración 1 ejercitados directamente sobre `core`, sin CLI ni argv."""

import pytest

from gcsgrep import core
from .fakes import FakeGCS


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
    matches = core.search("b", "", config, fake.list_objects, fake.open_text_stream)

    matched_objects = {m.object_name for m in matches}
    assert matched_objects == {"a/x.txt", "c/y.txt"}


def test_vc1_busqueda_basica_encuentra_match():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "connection timeout\nok\n")

    config = core.SearchConfig(pattern="timeout")
    matches = core.search("b", "logs/", config, fake.list_objects, fake.open_text_stream)

    assert len(matches) == 1
    assert matches[0].bucket == "b"
    assert matches[0].object_name == "logs/a.txt"
    assert matches[0].line_number == 1
    assert "timeout" in matches[0].text


def test_vc2_ignore_case():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "Timeout error\n")

    sin_i = core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout"),
        fake.list_objects, fake.open_text_stream,
    )
    con_i = core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout", ignore_case=True),
        fake.list_objects, fake.open_text_stream,
    )

    assert sin_i == []
    assert len(con_i) == 1
    assert con_i[0].text == "Timeout error"


def test_vc3_numero_de_linea():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "l1\nl2\nmatch aqui\nl4\n")

    matches = core.search(
        "b", "logs/", core.SearchConfig(pattern="match"),
        fake.list_objects, fake.open_text_stream,
    )

    assert len(matches) == 1
    assert matches[0].line_number == 3


def test_vc5_sin_resultados():
    fake = FakeGCS()
    fake.put("b", "logs/a.txt", "nada que ver por aca\n")

    matches = core.search(
        "b", "logs/", core.SearchConfig(pattern="timeout"),
        fake.list_objects, fake.open_text_stream,
    )

    assert matches == []

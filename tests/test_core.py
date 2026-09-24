"""VCs de Iteración 1 ejercitados directamente sobre `core`, sin CLI ni argv.

`core.search` es un generador (ADR-0011): los tests que quieren el conjunto
completo lo envuelven en `list(...)`; el que verifica la salida incremental
(VC-17) consume de a uno con `next(...)`.
"""

import pytest

from gcsgrep import core, errors
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


def test_vc17_primer_match_se_emite_sin_abrir_el_resto_del_prefijo():
    """VC-17 — FR-11: la salida es incremental.

    Con tres objetos que matchean, pedir el primer match no debe haber **abierto**
    los otros dos. Si `search` acumulara resultados antes de devolverlos (el
    comportamiento anterior a ADR-0011), este test fallaría.

    **Cambio de observable, spec v1.3 (2026-09-24).** Hasta la v1.2 este test
    también exigía `listed == ["logs/a.txt"]`. El guardrail de costo (BR-2 /
    ADR-0006) obliga a contar los objetos antes de leer, así que con tope activo el
    listado se materializa y esa afirmación dejó de ser cierta —el plan lo había
    anticipado como nota de regresión—. Lo que FR-11 promete sigue intacto y es lo
    que se observa acá: **el contenido se lee de a uno**. La propiedad de listado
    perezoso sobrevive con `--max 0` y se verifica en
    `test_vc12_max_0_no_materializa_el_listado`.
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
    assert fake.opened == ["logs/a.txt"], "se abrió más de un objeto para emitir el primer match"

    # Y al seguir consumiendo, avanza de a uno.
    segundo = next(resultados)
    assert segundo.object_name == "logs/b.txt"
    assert fake.opened == ["logs/a.txt", "logs/b.txt"]


# --- VC-12 · BR-2 guardrail de costo por cantidad de objetos ------------------


def _fake_con_n_objetos(n, contenido="connection timeout\n"):
    fake = RecordingFakeGCS()
    for i in range(n):
        fake.put("b", f"logs/{i:05d}.txt", contenido)
    return fake


def test_vc12_mil_un_objetos_sin_max_no_lee_ninguno():
    """VC-12 · la mitad central: con 1001 objetos y sin `--max`, 0 aperturas."""
    fake = _fake_con_n_objetos(1001)
    config = core.SearchConfig(pattern="timeout")

    with pytest.raises(errors.TopeExcedido) as exc_info:
        list(core.search("b", "logs/", config, fake.list_objects, fake.open_text_stream))

    assert exc_info.value.encontrados == 1001
    assert exc_info.value.tope == 1000
    assert fake.opened == [], "BR-2 exige no leer ningún objeto cuando se excede el tope"


def test_vc12_el_mensaje_menciona_la_cantidad_y_el_tope():
    fake = _fake_con_n_objetos(1001)

    with pytest.raises(errors.TopeExcedido) as exc_info:
        list(core.search("b", "logs/", core.SearchConfig(pattern="x"),
                    fake.list_objects, fake.open_text_stream))

    mensaje = str(exc_info.value)
    assert "1001" in mensaje and "1000" in mensaje


def test_vc12_exactamente_en_el_tope_no_dispara():
    """El tope es "más que", no "desde": 1000 objetos con tope 1000 pasa."""
    fake = _fake_con_n_objetos(1000)

    matches = list(core.search("b", "logs/", core.SearchConfig(pattern="timeout"),
                          fake.list_objects, fake.open_text_stream))

    assert len(matches) == 1000


def test_vc12_max_0_quita_el_tope_y_si_lee():
    """La otra mitad de VC-12: con `--max 0` sobre el mismo prefijo, sí lee."""
    fake = _fake_con_n_objetos(1001)
    config = core.SearchConfig(pattern="timeout", max_objetos=core.SIN_TOPE)

    matches = list(core.search("b", "logs/", config, fake.list_objects, fake.open_text_stream))

    assert len(matches) == 1001
    assert len(fake.opened) == 1001


def test_vc12_max_0_no_materializa_el_listado():
    """Consecuencia de diseño que vale verificar: contar obliga a materializar el
    listado, así que `--max 0` —que no cuenta— tiene que seguir siendo perezoso.

    Es lo que mantiene intacta la propiedad original de VC-17 cuando el guardrail
    está desactivado."""
    fake = _fake_con_n_objetos(3)
    config = core.SearchConfig(pattern="timeout", max_objetos=core.SIN_TOPE)

    resultados = core.search("b", "logs/", config, fake.list_objects, fake.open_text_stream)
    primero = next(resultados)
    resultados.close()

    assert primero.object_name == "logs/00000.txt"
    assert fake.listed == ["logs/00000.txt"], "con --max 0 el listado no se materializa"
    assert fake.opened == ["logs/00000.txt"]


def test_vc12_un_tope_bajo_tambien_protege():
    """El tope es configurable en las dos direcciones, no solo hacia arriba."""
    fake = _fake_con_n_objetos(5)

    with pytest.raises(errors.TopeExcedido):
        list(core.search("b", "logs/", core.SearchConfig(pattern="x", max_objetos=4),
                    fake.list_objects, fake.open_text_stream))

    assert fake.opened == []

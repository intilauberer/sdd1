"""VC-14 — memoria acotada por streaming (NFR-1).

Dos casos, y el segundo es el que importa. Ver docs/revision-spec.md, hallazgo
H-3: la versión original de este archivo medía **solo** el caso sin matches, en
el que el `List[Match]` que `core.search` devolvía quedaba vacío. El VC pasaba
por construcción y no habría detectado que la memoria crecía con la cantidad de
matches. El segundo caso ejercita el escenario adverso: **todas** las líneas
matchean.
"""

import tracemalloc

from gcsgrep import core
from .fakes import HugeLineStream

LINE = "x" * 200 + "\n"
TOTAL_BYTES = 200 * 1024 * 1024
REPEAT = TOTAL_BYTES // len(LINE)
UMBRAL_BYTES = 20 * 1024 * 1024  # umbral definido en NFR-1


def _colaboradores():
    stream = HugeLineStream(LINE, REPEAT)

    def list_objects(bucket, prefix):
        return ["huge.txt"]

    def open_text_stream(bucket, name):
        return stream

    return list_objects, open_text_stream


def _medir_pico(consumir):
    tracemalloc.start()
    baseline, _ = tracemalloc.get_traced_memory()
    resultado = consumir()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, peak - baseline


def _mensaje(pico: int) -> str:
    return (
        f"pico de memoria adicional {pico / 1024 / 1024:.1f} MB supera el umbral "
        f"de {UMBRAL_BYTES / 1024 / 1024:.0f} MB para un objeto de 200 MB"
    )


def test_vc14_memoria_acotada_con_objeto_de_200mb_sin_matches():
    list_objects, open_text_stream = _colaboradores()
    config = core.SearchConfig(pattern="patron-que-nunca-aparece")

    matches, pico = _medir_pico(
        lambda: list(core.search("b", "", config, list_objects, open_text_stream))
    )

    assert matches == []
    assert pico < UMBRAL_BYTES, _mensaje(pico)


def test_vc14_memoria_acotada_con_objeto_de_200mb_donde_todo_matchea():
    """Caso adverso: el patrón está en todas las líneas del objeto de 200 MB.

    Se consume el generador sin guardar los matches, que es lo que hace `cli`:
    imprime cada uno y lo descarta. La memoria tiene que quedar acotada por el
    match más grande, no por la cantidad de matches.
    """
    list_objects, open_text_stream = _colaboradores()
    config = core.SearchConfig(pattern="x")

    def consumir():
        total = 0
        for _ in core.search("b", "", config, list_objects, open_text_stream):
            total += 1
        return total

    total, pico = _medir_pico(consumir)

    assert total == REPEAT, "no se emitió un match por cada línea del objeto"
    assert pico < UMBRAL_BYTES, _mensaje(pico)

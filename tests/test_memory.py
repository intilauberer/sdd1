"""VC-14 — memoria acotada por streaming (NFR-1)."""

import tracemalloc

from gcsgrep import core
from .fakes import HugeLineStream

LINE = "x" * 200 + "\n"
TOTAL_BYTES = 200 * 1024 * 1024
REPEAT = TOTAL_BYTES // len(LINE)


def test_vc14_memoria_acotada_con_objeto_de_200mb():
    stream = HugeLineStream(LINE, REPEAT)

    def list_objects(bucket, prefix):
        return ["huge.txt"]

    def open_text_stream(bucket, name):
        return stream

    config = core.SearchConfig(pattern="patron-que-nunca-aparece")

    tracemalloc.start()
    baseline, _ = tracemalloc.get_traced_memory()

    matches = core.search("b", "", config, list_objects, open_text_stream)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert matches == []
    additional_peak = peak - baseline
    assert additional_peak < 20 * 1024 * 1024, (
        f"pico de memoria adicional {additional_peak / 1024 / 1024:.1f} MB "
        f"supera el umbral de 20 MB para un objeto de 200 MB"
    )

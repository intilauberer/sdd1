#!/usr/bin/env python3
"""Mide NFR-4 (VC-30) en la máquina donde corre, y el contraste de (b).

Imprime, con la condición de carga de NFR-4 (100 MiB, líneas de 80 bytes, en
proceso, stdout a /dev/null, mejor de 3):

- (a) MiB/s con el patrón ausente, y (b) matches/s con el patrón en todas las
  líneas, para la implementación actual;
- las implementaciones malas de referencia de la spec: para (a), leer el objeto
  de a un byte; para (b), abrir y cerrar el destino de la salida por cada match.

Existe para que el número de la plataforma de referencia (el runner de CI) quede
en el log de cada corrida, no en una medición a mano (revisión v1.5, acción 9).
No falla nunca: el umbral lo verifica VC-30 en pytest.

    python scripts/medir-nfr4.py
"""

import os
import platform
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gcsgrep import cli, core, gcs  # noqa: E402
from tests.fakes import HugeLineStream  # noqa: E402

LINEA = b"x" * 79 + b"\n"
REPETICIONES = 100 * 1024 * 1024 // len(LINEA)


def corrida(patron: str, repeticiones: int = REPETICIONES) -> float:
    gcs.list_objects = lambda b, p: ["p/a.txt"]
    gcs.open_stream = lambda b, n: HugeLineStream(LINEA, repeticiones)
    original = sys.stdout
    with open(os.devnull, "w") as devnull:
        sys.stdout = devnull
        inicio = time.perf_counter()
        cli.main([patron, "gs://b/p/"])
        segundos = time.perf_counter() - inicio
    sys.stdout = original
    return segundos


def mejor_de_3(patron: str, repeticiones: int = REPETICIONES) -> float:
    return min(corrida(patron, repeticiones) for _ in range(3))


def print_que_abre_y_cierra(*args, file=None, flush=False, **kwargs):
    """La implementación mala de referencia de NFR-4 (b)."""
    if file is not None:
        return print(*args, file=file, flush=flush, **kwargs)
    with open(os.devnull, "w") as destino:
        print(*args, file=destino, **kwargs)


def main() -> None:
    print(f"plataforma: {platform.platform()} · Python {platform.python_version()}")
    a = 100 / mejor_de_3("patron-ausente")
    b = REPETICIONES / mejor_de_3("x")
    cli.print = print_que_abre_y_cierra  # sombrea el builtin solo dentro de cli
    try:
        b_mala = REPETICIONES / mejor_de_3("x")
    finally:
        del cli.print
    # (a) mala: leer el objeto de a un byte. Sobre 2 MiB, porque sobre 100 MiB
    # tarda minutos; la tasa no depende del tamaño.
    bloque, core.BLOQUE_DE_LECTURA = core.BLOQUE_DE_LECTURA, 1
    try:
        a_mala = 2 / mejor_de_3("patron-ausente", REPETICIONES // 50)
    finally:
        core.BLOQUE_DE_LECTURA = bloque
    print(f"NFR-4 (a) actual: {a:,.0f} MiB/s (umbral 50)")
    print(f"NFR-4 (a) implementación mala (leer de a un byte): {a_mala:,.1f} MiB/s")
    print(f"NFR-4 (b) actual: {b:,.0f} matches/s (umbral 150 000 desde la spec v1.7)")
    print(f"NFR-4 (b) implementación mala (abrir/cerrar por match): {b_mala:,.0f} matches/s")
    print(f"razón actual / mala en (b): {b / b_mala:.1f}x")


if __name__ == "__main__":
    main()

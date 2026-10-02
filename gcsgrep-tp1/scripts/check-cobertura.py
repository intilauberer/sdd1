#!/usr/bin/env python3
"""Verifica que la tabla de cobertura y los tests digan lo mismo (H-15).

`specs/gcsgrep/04-cobertura-vc.md` es append-only: un VC que cambia de estado
recibe una fila nueva más abajo, y la vieja queda. Por eso el estado **vigente** de
un VC es el de su **última** fila antes de la sección *Histórico* (cuyas filas son,
por definición, superadas).

Falla si:

1. un VC tiene tests `test_vcN_*` y su estado vigente no es ✅;
2. un VC está ✅ y no tiene ningún test `test_vcN_*`;
3. hay tests `test_vcN_*` de un VC que la tabla no menciona.

La comparación es por número de VC: `test_vc14c_*` cuenta para VC-14 y
`test_vc16b_*` para VC-16. Que los tests **pasen** lo verifica pytest; esto
verifica que la tabla no mienta sobre cuáles existen.

    python scripts/check-cobertura.py
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
COBERTURA = RAIZ / "specs" / "gcsgrep" / "04-cobertura-vc.md"
TESTS = RAIZ / "tests"

ESTADOS = ("✅", "⬜", "❌")


def estados_vigentes(texto: str) -> dict:
    vigente = {}
    for linea in texto.split("\n## Histórico")[0].splitlines():
        if not linea.startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 2:
            continue
        numeros = re.findall(r"VC-(\d+)", celdas[0])
        estado = next((e for e in ESTADOS if e in celdas[-1]), None)
        if not numeros or estado is None:
            continue
        for n in numeros:
            vigente[int(n)] = estado  # la última fila gana
    return vigente


def vcs_con_tests() -> dict:
    tests = {}
    for archivo in sorted(TESTS.glob("test_*.py")):
        for nombre in re.findall(r"^def (test_vc(\d+)\w*)", archivo.read_text(), re.M):
            tests.setdefault(int(nombre[1]), []).append(f"{archivo.name}::{nombre[0]}")
    return tests


def main() -> int:
    vigente = estados_vigentes(COBERTURA.read_text())
    tests = vcs_con_tests()
    problemas = []
    for n in sorted(set(vigente) | set(tests)):
        estado = vigente.get(n)
        if n in tests and estado is None:
            problemas.append(f"VC-{n}: tiene tests ({tests[n][0]}, …) y la tabla no lo menciona")
        elif n in tests and estado != "✅":
            problemas.append(f"VC-{n}: tiene tests ({tests[n][0]}, …) y su fila vigente dice {estado}")
        elif n not in tests and estado == "✅":
            problemas.append(f"VC-{n}: su fila vigente dice ✅ y no hay ningún test test_vc{n}_*")
    if problemas:
        print("La tabla de cobertura y los tests no coinciden:")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print(f"OK: {len(vigente)} VCs en la tabla, {len(tests)} con tests, sin contradicciones")
    return 0


if __name__ == "__main__":
    sys.exit(main())

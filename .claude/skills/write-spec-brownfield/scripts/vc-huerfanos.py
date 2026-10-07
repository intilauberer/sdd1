#!/usr/bin/env python3
"""Cobertura de VCs: cada FR-n / BR-n / NFR-n definido en la spec tiene su VC.

Una definición es una línea que empieza con `**FR-6 ·` o `### FR-6 ·` (o BR / NFR).
Su bloque va hasta la próxima definición; cuenta como cubierta si en el bloque hay
al menos una línea `> **VC-…`. No se asume numeración compartida.

    python3 vc-huerfanos.py tmux-ssh-tp2/spec-brownfield.md

Exit 0 si no hay huérfanos; 1 si hay (lista en stderr); 2 si no hay requerimientos.
"""

import re
import sys
from pathlib import Path

DEF = re.compile(r"^(?:#+\s*|\*\*)((?:FR|BR|NFR)-\d+)\b")
VC = re.compile(r"^>\s*\*\*VC-")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("uso: vc-huerfanos.py <spec.md>", file=sys.stderr)
        return 2
    cubierto, actual = {}, None
    for linea in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        if m := DEF.match(linea):
            actual = m.group(1)
            cubierto.setdefault(actual, False)
        elif actual and VC.match(linea):
            cubierto[actual] = True
    if not cubierto:
        print("no se detectaron requerimientos (FR-n / BR-n / NFR-n)", file=sys.stderr)
        return 2
    huerfanos = [r for r, ok in cubierto.items() if not ok]
    print(f"requerimientos: {len(cubierto)} · con VC: {len(cubierto) - len(huerfanos)} · huérfanos: {len(huerfanos)}")
    if huerfanos:
        print("Sin VC: " + ", ".join(huerfanos), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

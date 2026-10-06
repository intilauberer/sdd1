#!/usr/bin/env python3
"""Cobertura de VCs: cada FR-n / BR-n / NFR-n definido en la spec tiene su VC-n.

Una definición es una línea que empieza con `**FR-6 ·` (o BR / NFR). Un VC cuenta
si aparece `VC-6` en cualquier parte de la spec. La numeración es compartida: el
VC de FR-6 es VC-6.

    python3 vc-huerfanos.py tmux-ssh-tp2/spec-brownfield.md

Exit 0 si no hay huérfanos; 1 si hay, con la lista en stderr.
"""

import re
import sys
from pathlib import Path

DEF = re.compile(r"^\*\*(FR|BR|NFR)-(\d+)\b", re.M)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("uso: vc-huerfanos.py <spec.md>", file=sys.stderr)
        return 2
    texto = Path(sys.argv[1]).read_text(encoding="utf-8")
    reqs = sorted({(t, int(n)) for t, n in DEF.findall(texto)}, key=lambda r: (r[0], r[1]))
    vcs = {int(n) for n in re.findall(r"\bVC-(\d+)", texto)}
    huerfanos = [f"{t}-{n}" for t, n in reqs if n not in vcs]
    print(f"requerimientos: {len(reqs)} · VCs distintos: {len(vcs)} · huérfanos: {len(huerfanos)}")
    if huerfanos:
        print("Sin VC: " + ", ".join(huerfanos), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

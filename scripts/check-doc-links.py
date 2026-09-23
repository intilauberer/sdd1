#!/usr/bin/env python3
"""Verifica que los enlaces relativos entre documentos del repo no estén rotos.

En un repo donde los artefactos de SDD se referencian entre sí (spec → ADR →
revisión → plan → cobertura), un enlace roto es deuda silenciosa: el documento
sigue leyéndose bien y la trazabilidad ya no existe. Esto lo hace fallar en CI.

Qué chequea: enlaces markdown `[texto](ruta)` y `[texto](ruta#ancla)` que apunten
a una ruta relativa dentro del repo.

Qué ignora: URLs absolutas (http, https, mailto), anclas puras (`#seccion`), y las
rutas declaradas en ENLACES_EXTERNOS_CONOCIDOS — el enunciado de la tarea vive
originalmente en el monorepo del curso y sus enlaces apuntan afuera a propósito.

    python scripts/check-doc-links.py
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Enlaces que apuntan fuera del repo a propósito (monorepo del curso).
ENLACES_EXTERNOS_CONOCIDOS = {
    "../../entrega.md",
    "../ejemplo-guiado/README.md",
    "../ejemplo-guiado/",
}

PATRON_ENLACE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def es_externo(destino: str) -> bool:
    return destino.startswith(("http://", "https://", "mailto:", "#"))


def main() -> int:
    roto = []
    revisados = 0

    for md in sorted(RAIZ.rglob("*.md")):
        if ".venv" in md.parts or ".git" in md.parts:
            continue
        texto = md.read_text(encoding="utf-8")
        for destino in PATRON_ENLACE.findall(texto):
            destino = destino.strip()
            if es_externo(destino) or destino in ENLACES_EXTERNOS_CONOCIDOS:
                continue
            ruta = destino.split("#", 1)[0]
            if not ruta:
                continue
            revisados += 1
            if not (md.parent / ruta).exists():
                roto.append((md.relative_to(RAIZ), destino))

    if roto:
        print(f"enlaces relativos rotos: {len(roto)}\n", file=sys.stderr)
        for origen, destino in roto:
            print(f"  {origen} → {destino}", file=sys.stderr)
        return 1

    print(f"OK: {revisados} enlaces relativos verificados, ninguno roto")
    return 0


if __name__ == "__main__":
    sys.exit(main())

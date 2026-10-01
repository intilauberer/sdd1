#!/usr/bin/env python3
"""Verifica cada cita `archivo:línea` de las notas y la spec contra tmux real.

Una nota de exploración que describe un repo imaginario es peor que no tener
notas: el agente que implementa le va a creer. Este script hace que cada cita
sea una afirmación chequeada por una máquina, no una línea que alguien copió.

Qué chequea, para cada cita entre backticks con forma `ruta:N` o `ruta:N-M` en
los .md de tmux-ssh-tp2/ (excepto revisiones/):

  1. que la cita esté registrada en citas.tsv con un ancla (un fragmento de
     texto que la línea tiene que contener). Una cita sin ancla es un fallo:
     obliga a que quien la escribió haya abierto el archivo;
  2. que el archivo exista en tmux en el commit fijado (no en el working tree);
  3. que el ancla aparezca en la línea N (o en alguna del rango N-M).

Lo que NO chequea: que la línea haga lo que la nota dice. Eso sigue siendo
trabajo de quien revisa (ver .kiro/agents/prompts/corrector-specs.md, B1).

    python3 tmux-ssh-tp2/scripts/check-citas.py          # usa $TMUX_SRC o lo clona
    TMUX_SRC=/ruta/a/tmux python3 tmux-ssh-tp2/scripts/check-citas.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

COMMIT = "5a820e63b72f05c121441149c72327aeeb16dfa4"
URL = "https://github.com/tmux/tmux.git"

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "citas.tsv"

# `ruta:N` o `ruta:N-M`; la ruta tiene que tener una extensión o ser un
# archivo conocido sin extensión (Makefile, tmux.1 ya tiene extensión).
PATRON = re.compile(r"`((?:[\w.-]+/)*(?:[\w.-]+\.\w+|Makefile)):(\d+)(?:-(\d+))?`")


def fuente() -> Path:
    src = os.environ.get("TMUX_SRC")
    if src:
        return Path(src)
    cache = RAIZ / ".cache" / "tmux"
    if not (cache / ".git").exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", URL, str(cache)], check=True)
    return cache


def leer(src: Path, ruta: str):
    r = subprocess.run(
        ["git", "-C", str(src), "show", f"{COMMIT}:{ruta}"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout.splitlines()


def main() -> int:
    anclas = {}
    for n, linea in enumerate(MANIFIESTO.read_text(encoding="utf-8").splitlines(), 1):
        if not linea.strip() or linea.startswith("#"):
            continue
        cita, _, ancla = linea.partition("\t")
        if not ancla:
            print(f"citas.tsv:{n}: falta el ancla de {cita}", file=sys.stderr)
            return 2
        anclas[cita] = ancla

    src = fuente()
    if subprocess.run(["git", "-C", str(src), "cat-file", "-e", COMMIT],
                      capture_output=True).returncode != 0:
        subprocess.run(["git", "-C", str(src), "fetch", "-q", "origin"], check=True)

    fallos, revisadas, cache = [], 0, {}
    for md in sorted(RAIZ.rglob("*.md")):
        if "revisiones" in md.parts or ".cache" in md.parts:
            continue
        for num, texto in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for m in PATRON.finditer(texto):
                ruta, desde = m.group(1), int(m.group(2))
                hasta = int(m.group(3) or desde)
                cita = m.group(0).strip("`")
                donde = f"{md.relative_to(RAIZ)}:{num}"
                revisadas += 1
                if cita not in anclas:
                    fallos.append(f"{donde}: `{cita}` no está en citas.tsv")
                    continue
                if ruta not in cache:
                    cache[ruta] = leer(src, ruta)
                lineas = cache[ruta]
                if lineas is None:
                    fallos.append(f"{donde}: {ruta} no existe en {COMMIT[:7]}")
                    continue
                if hasta > len(lineas) or desde < 1 or hasta < desde:
                    fallos.append(f"{donde}: {cita} fuera de rango ({len(lineas)} líneas)")
                    continue
                if not any(anclas[cita] in l for l in lineas[desde - 1:hasta]):
                    fallos.append(
                        f"{donde}: {cita} no contiene «{anclas[cita]}» "
                        f"(dice: «{lineas[desde - 1].strip()}»)"
                    )

    huerfanas = set(anclas) - {
        m.group(0).strip("`")
        for md in RAIZ.rglob("*.md")
        if "revisiones" not in md.parts and ".cache" not in md.parts
        for m in PATRON.finditer(md.read_text(encoding="utf-8"))
    }
    for h in sorted(huerfanas):
        print(f"aviso: {h} está en citas.tsv pero ningún documento la cita", file=sys.stderr)

    if fallos:
        print(f"citas rotas: {len(fallos)} de {revisadas}\n", file=sys.stderr)
        for f in fallos:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"OK: {revisadas} citas verificadas contra tmux@{COMMIT[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""artefactos-inmutables — lo que el proceso declara inmutable no se reescribe.

Evento: PreToolUse, matcher "Edit|Write".
Protege (gcsgrep-tp1/docs/proceso-cambios.md):
  - ADRs y hallazgos existentes: se superseden, no se editan. Única excepción: un
    Edit de una sola línea que solo cambia la línea de Estado.
  - El borrador congelado y los enunciados: no se editan nunca.

exit 0 deja pasar · exit 2 veta (stderr lo lee el agente).
"""

import json
import os
import re
import sys
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")

SUPERSEDIBLES = re.compile(r"^gcsgrep-tp1/docs/(adr/ADR-\d+|hallazgos/H-\d+)[^/]*\.md$")
CONGELADOS = re.compile(r"(^|/)(00-requirements-draft|enunciado)\.md$")

try:
    evento = json.load(sys.stdin)
except ValueError:
    print("HOOK artefactos-inmutables: no pude leer el evento; fallo cerrado.", file=sys.stderr)
    sys.exit(2)
entrada = evento.get("tool_input", {})
ruta = entrada.get("file_path", "")
if not ruta:
    sys.exit(0)

# Rutas estilo MSYS/Git Bash (/c/Users/...) → C:/Users/...
ruta = re.sub(r"^/([A-Za-z])/", lambda m: m.group(1).upper() + ":/", ruta)
raiz = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
try:
    rel = Path(ruta).resolve().relative_to(raiz).as_posix()
except ValueError:
    sys.exit(0)

if CONGELADOS.search(rel) and (raiz / rel).exists():
    print(f"EDICIÓN BLOQUEADA — {rel} está congelado: es el insumo, no se reescribe.\n"
          "Si algo del enunciado o del borrador quedó mal, registralo como hallazgo nuevo "
          "en gcsgrep-tp1/docs/hallazgos/ y resolvelo en la spec.", file=sys.stderr)
    sys.exit(2)

if not SUPERSEDIBLES.match(rel) or not (raiz / rel).exists():
    sys.exit(0)  # no es un ADR/hallazgo, o es uno nuevo: se puede escribir

if evento.get("tool_name") == "Edit":
    viejo, nuevo = entrada.get("old_string", ""), entrada.get("new_string", "")
    if "\n" not in viejo and "\n" not in nuevo and "Estado" in viejo and "Estado" in nuevo:
        sys.exit(0)

print(f"EDICIÓN BLOQUEADA — {rel} ya existe, y en este repo los ADRs y hallazgos no se "
      "editan: se superseden (proceso-cambios.md).\n"
      "  1. Escribí uno nuevo (ADR-NNNN o H-NN) que diga a cuál reemplaza y por qué.\n"
      "  2. En este archivo cambiá SOLO la línea de Estado, p. ej. "
      "'- **Estado:** superseded por ADR-NNNN'. Ese Edit sí pasa.", file=sys.stderr)
sys.exit(2)

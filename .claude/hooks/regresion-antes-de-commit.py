#!/usr/bin/env python3
"""regresion-antes-de-commit — no entra un commit que rompe lo que ya andaba.

Evento: PreToolUse, matcher "Bash|PowerShell". Solo actúa si el comando contiene `git commit`.
Corre la línea de base offline del repo (la misma que CI):
  1. enlaces relativos de los dos TPs (check-doc-links.py);
  2. ningún .c/.h/.y/configure.ac/Makefile.am staged, modificado o sin trackear en
     tmux-ssh-tp2/ (la consigna del TP2 prohíbe implementar; cubre `git add &&`, `-a`, `<path>`).
Cualquier fallo ⇒ exit 2 con la salida del chequeo en stderr.
"""

import json
import os
import re
import subprocess
import sys

sys.stderr.reconfigure(encoding="utf-8")

try:
    comando = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except ValueError:
    print("HOOK regresion-antes-de-commit: no pude leer el evento; fallo cerrado.", file=sys.stderr)
    sys.exit(2)
# `git commit` al inicio de línea, tras ; & | ( o un prefijo (env X=1 …), con opciones globales (-C dir, -c k=v)
if not re.search(r"(?:^|[;&|(]\s*|\s)git(?:\s+-[cC]\s*\S+)*\s+commit\b", comando, re.M):
    sys.exit(0)

raiz = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
fallos = []

for carpeta in ("gcsgrep-tp1", "tmux-ssh-tp2"):
    r = subprocess.run([sys.executable, "gcsgrep-tp1/scripts/check-doc-links.py", carpeta],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fallos.append(f"[enlaces {carpeta}]\n{r.stdout}{r.stderr}".rstrip())

# Todo lo que el commit podría llevarse: staged, modificado o untracked (git add &&, -a, <path>)
estado = subprocess.run(["git", "status", "--porcelain", "-z", "--no-renames", "--untracked-files=all",
                         "--", "tmux-ssh-tp2"], cwd=raiz, capture_output=True).stdout.decode("utf-8", "replace")
archivos = [e[3:] for e in estado.split("\0") if len(e) > 3 and "D" not in e[:2]]
codigo = [f for f in archivos if re.search(r"(\.[chy]|/configure\.ac|/Makefile\.am)$", f)]
if codigo:
    fallos.append("[sin-implementacion] la consigna del TP2 prohíbe código de tmux (staged, "
                  "modificado o sin trackear):\n  " + "\n  ".join(codigo)
                  + "\n  Borralo o movelo fuera de tmux-ssh-tp2/ (no alcanza con sacarlo del staging).")

if fallos:
    print("COMMIT BLOQUEADO — la línea de base de regresión está roja.\n\n"
          + "\n\n".join(fallos)
          + "\n\nArreglá lo de arriba (o sacalo del staging) y volvé a commitear. "
            "No uses --no-verify ni reintentes igual: el chequeo va a dar lo mismo.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)

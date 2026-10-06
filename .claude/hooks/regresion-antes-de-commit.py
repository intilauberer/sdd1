#!/usr/bin/env python3
"""regresion-antes-de-commit — no entra un commit que rompe lo que ya andaba.

Evento: PreToolUse, matcher "Bash". Solo actúa si el comando contiene `git commit`.
Corre la línea de base offline del repo (la misma que CI):
  1. enlaces relativos de los dos TPs (check-doc-links.py);
  2. ningún .c/.h/.y/configure.ac/Makefile.am staged en tmux-ssh-tp2/ (la consigna
     del TP2 prohíbe implementar).
Cualquier fallo ⇒ exit 2 con la salida del chequeo en stderr.
"""

import json
import os
import re
import subprocess
import sys

sys.stderr.reconfigure(encoding="utf-8")

comando = json.load(sys.stdin).get("tool_input", {}).get("command", "")
if not re.search(r"\bgit\s+commit\b", comando):
    sys.exit(0)

raiz = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
fallos = []

for carpeta in ("gcsgrep-tp1", "tmux-ssh-tp2"):
    r = subprocess.run([sys.executable, "gcsgrep-tp1/scripts/check-doc-links.py", carpeta],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fallos.append(f"[enlaces {carpeta}]\n{r.stdout}{r.stderr}".rstrip())

staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
                        cwd=raiz, capture_output=True, text=True).stdout.split()
codigo = [f for f in staged if f.startswith("tmux-ssh-tp2/")
          and re.search(r"(\.[chy]|/configure\.ac|/Makefile\.am)$", f)]
if codigo:
    fallos.append("[sin-implementacion] la consigna del TP2 prohíbe código de tmux:\n  "
                  + "\n  ".join(codigo))

if fallos:
    print("COMMIT BLOQUEADO — la línea de base de regresión está roja.\n\n"
          + "\n\n".join(fallos)
          + "\n\nArreglá lo de arriba (o sacalo del staging) y volvé a commitear. "
            "No uses --no-verify ni reintentes igual: el chequeo va a dar lo mismo.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)

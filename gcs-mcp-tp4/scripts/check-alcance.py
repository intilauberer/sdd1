#!/usr/bin/env python3
"""check-alcance — el diff del TP4 no sale de las listas Dentro de la spec (spec.md, Alcance, VC-0).

Compara `git diff --name-only <base>...HEAD` (lo commiteado; los archivos sin trackear o
sin commitear no cuentan) con las listas Dentro:
  - se crean: `.mcp.json`, `.claude/hooks/gcs-allowlist.py`, `.claude/skills/write-vcs-con-bucket/`,
    `.claude/agents/lector-fixtures.md`, `gcs-mcp-tp4/**`, `.github/workflows/tp4.yml`,
    `.claude-plugin/marketplace.json`;
  - cambio aditivo: `.claude/settings.json`, `.claude/hooks/regresion-antes-de-commit.py`,
    `gcsgrep-tp1/scripts/check-doc-links.py`, `.gitignore` y `README.md` (raíz). En esos cinco solo se admiten líneas
    agregadas, salvo la tupla de carpetas de `regresion-antes-de-commit.py`, que se puede
    reemplazar por otra que siga teniendo `gcsgrep-tp1` y `tmux-ssh-tp2` y sume `gcs-mcp-tp4`.

    python3 gcs-mcp-tp4/scripts/check-alcance.py [base]    # base por defecto: origin/main
exit 0 dentro del alcance · 1 algo fuera (lo nombra) · 2 no se pudo calcular el diff.
Salida en inglés (D-6).
"""

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

NUEVOS_EXACTOS = {
    ".mcp.json",
    ".claude/hooks/gcs-allowlist.py",
    ".claude/agents/lector-fixtures.md",
    ".github/workflows/tp4.yml",
    ".claude-plugin/marketplace.json",
}
NUEVOS_PREFIJOS = (
    ".claude/skills/write-vcs-con-bucket/",
    "gcs-mcp-tp4/",
)
ADITIVOS = {
    ".claude/settings.json",
    ".claude/hooks/regresion-antes-de-commit.py",
    "gcsgrep-tp1/scripts/check-doc-links.py",
    ".gitignore",
    "README.md",
}
TUPLA_ARCHIVO = ".claude/hooks/regresion-antes-de-commit.py"
TUPLA_RE = re.compile(r"^\s*for carpeta in \((.*)\):\s*$")


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip() or 'unknown revision'}")
    return r.stdout


def es_tupla_valida(linea: str, nueva: bool) -> bool:
    m = TUPLA_RE.match(linea)
    if not m:
        return False
    carpetas = set(re.findall(r'"([^"]+)"', m.group(1)))
    base = {"gcsgrep-tp1", "tmux-ssh-tp2"}
    return base | {"gcs-mcp-tp4"} <= carpetas if nueva else base <= carpetas


def revisar_aditivo(base: str, ruta: str) -> list[str]:
    diff = git("diff", "--no-renames", "--no-color", "-U0", f"{base}...HEAD", "--", ruta)
    quitadas, agregadas = [], []
    for linea in diff.splitlines():
        if linea.startswith(("---", "+++")):
            continue
        if linea.startswith("-"):
            quitadas.append(linea[1:])
        elif linea.startswith("+"):
            agregadas.append(linea[1:])

    if ruta == TUPLA_ARCHIVO and quitadas:
        # Única excepción: una línea de la tupla, reemplazada por otra que la amplía.
        if (len(quitadas) == 1 and es_tupla_valida(quitadas[0], nueva=False)
                and sum(es_tupla_valida(a, nueva=True) for a in agregadas) == 1):
            quitadas = []
    return [f"{ruta}: additive-only file has a removed or changed line: {q.strip()!r}"
            for q in quitadas]


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    if len(sys.argv) > 2:
        print("usage: check-alcance.py [base-ref]", file=sys.stderr)
        return 2
    try:
        git("rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
        cambiados = [l for l in git("diff", "--no-renames", "--name-only", f"{base}...HEAD").splitlines() if l]
        problemas = []
        for ruta in cambiados:
            if ruta in ADITIVOS:
                problemas += revisar_aditivo(base, ruta)
            elif ruta not in NUEVOS_EXACTOS and not ruta.startswith(NUEVOS_PREFIJOS):
                problemas.append(f"{ruta}: outside the scope of spec.md (Alcance, Dentro)")
    except RuntimeError as exc:
        print(f"check-alcance: cannot compute the diff against {base!r}: {exc}", file=sys.stderr)
        return 2

    if problemas:
        print(f"check-alcance: {len(problemas)} change(s) outside the scope (base {base}):", file=sys.stderr)
        for p in problemas:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"check-alcance: OK — {len(cambiados)} committed file(s) changed since {base}, all within scope.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

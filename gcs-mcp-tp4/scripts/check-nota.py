#!/usr/bin/env python3
"""check-nota — la nota de seguridad del README tiene los 7 puntos, con contenido (spec.md, R-12, VC-13).

Busca en `gcs-mcp-tp4/README.md` la sección cuyo título contiene "Nota de seguridad" y
exige 7 subsecciones `### 1.` … `### 7.`, en orden. En cada una tienen que aparecer sus
términos (sin distinguir mayúsculas) y al menos un enlace markdown a `evidencia/`:
  1. storage-mcp, 0.6.0, gcsgrep-test-g4-mcp
  2. --enable-destructive-tools, write_object_safe
  3. gateway, STORAGE_EMULATOR_HOST, objectViewer (el techo con el emulador, D-9, y su
     equivalente en el GCS real)
  4. sintético
  5. hook, delete_object, 403 — en ese orden
  6. trifecta, lector-fixtures
  7. tokens

    python3 gcs-mcp-tp4/scripts/check-nota.py [README]   # exit 0 OK · 1 falla
Salida en inglés (D-6).
"""

import re
import sys
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"
TITULO = "nota de seguridad"
TERMINOS = {
    1: ["storage-mcp", "0.6.0", "gcsgrep-test-g4-mcp"],
    2: ["--enable-destructive-tools", "write_object_safe"],
    3: ["gateway", "STORAGE_EMULATOR_HOST", "objectViewer"],
    4: ["sintético"],
    5: ["hook", "delete_object", "403"],
    6: ["trifecta", "lector-fixtures"],
    7: ["tokens"],
}
EN_ORDEN = {5}
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SUB_RE = re.compile(r"^###\s+(\d+)\.")
ENLACE_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)[^)]*\)")


def main() -> int:
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else README
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"check-nota: cannot read {ruta} ({exc.strerror})", file=sys.stderr)
        return 1

    # Sección "Nota de seguridad", fuera de bloques de código.
    en_codigo, inicio, nivel = False, None, 0
    headings = []  # (índice, nivel, texto)
    for i, linea in enumerate(lineas):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
            continue
        m = None if en_codigo else HEADING_RE.match(linea)
        if m:
            headings.append((i, len(m.group(1)), m.group(2)))
    for i, n, texto in headings:
        if inicio is None and TITULO in texto.lower():
            inicio, nivel = i, n
    if inicio is None:
        print(f"check-nota: no heading containing 'Nota de seguridad' in {ruta}", file=sys.stderr)
        return 1
    if nivel >= 3:
        print(f"check-nota: the 'Nota de seguridad' heading must be level 1 or 2 (found level {nivel}), "
              "so that its points can be '### N.' subsections", file=sys.stderr)
        return 1
    fin = next((i for i, n, _ in headings if i > inicio and n <= nivel), len(lineas))
    subs = [(i, int(SUB_RE.match(lineas[i]).group(1))) for i, n, _ in headings
            if inicio < i < fin and n == 3 and SUB_RE.match(lineas[i])]

    fallas = []
    numeros = [n for _, n in subs]
    if numeros != list(range(1, 8)):
        fallas.append(f"expected subsections '### 1.' to '### 7.' in order, found {numeros or 'none'}")

    limites = [i for i, _ in subs] + [fin]
    for k, (i, n) in enumerate(subs):
        if n not in TERMINOS:
            continue
        texto = "\n".join(lineas[i:limites[k + 1]])
        bajo = texto.lower()
        posiciones = []
        for t in TERMINOS[n]:
            p = bajo.find(t.lower(), posiciones[-1] + 1 if (n in EN_ORDEN and posiciones) else 0)
            if p < 0:
                extra = " (after the previous term)" if n in EN_ORDEN and posiciones else ""
                fallas.append(f"point {n}: missing term {t!r}{extra}")
                if n in EN_ORDEN:
                    break
            else:
                posiciones.append(p)
        if not any("evidencia/" in d for d in ENLACE_RE.findall(texto)):
            fallas.append(f"point {n}: no markdown link to evidencia/")

    if fallas:
        print(f"check-nota: {ruta}: {len(fallas)} problem(s) in 'Nota de seguridad':", file=sys.stderr)
        for f in fallas:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("check-nota: OK — 'Nota de seguridad' has the 7 points, each with its terms and a link to evidencia/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

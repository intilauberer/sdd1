#!/usr/bin/env bash
# armar.sh — arma el plugin gcsgrep-toolkit a partir de .claude/ (spec.md, R-11).
#
# Convertir el toolkit en plugin es copiar archivos y renombrar lo que cambia de nombre.
# Lo generado (skills/, agents/, hooks/*.py, scripts/) se commitea igual (D-5), para que
# el plugin se lea sin correr nada; `--check` comprueba que lo commiteado es exactamente
# lo que este script arma. A mano se mantienen solo:
#   .claude-plugin/plugin.json · .mcp.json · hooks/hooks.json · README.md
#
#   gcs-mcp-tp4/plugin/armar.sh            # (re)arma gcs-mcp-tp4/plugin/gcsgrep-toolkit/
#   gcs-mcp-tp4/plugin/armar.sh --check    # arma en un temporal y compara; exit 1 si difiere
#
# Salida en inglés (D-6).
set -euo pipefail
export LC_ALL=C

AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
PLUGIN="$AQUI/gcsgrep-toolkit"
# Archivos que armar.sh no genera: se mantienen a mano en el plugin commiteado.
A_MANO=(.claude-plugin/plugin.json .mcp.json hooks/hooks.json README.md)

usage() {
  echo "usage: $0 [--check]" >&2
  exit 2
}

case "${1:-}" in
  "") MODO=build ;;
  --check) MODO=check ;;
  *) usage ;;
esac
[ $# -le 1 ] || usage

# build <destino>: copia las piezas de .claude/ y aplica los reemplazos de R-11.
build() {
  local dest="$1"
  mkdir -p "$dest/skills" "$dest/agents" "$dest/hooks" "$dest/scripts"

  cp -R "$RAIZ/.claude/skills/write-spec-brownfield" "$dest/skills/"
  cp -R "$RAIZ/.claude/skills/write-vcs-con-bucket" "$dest/skills/"
  cp "$RAIZ/.claude/agents/revisor-spec.md" "$RAIZ/.claude/agents/lector-fixtures.md" "$dest/agents/"
  cp "$RAIZ/.claude/hooks/artefactos-inmutables.py" \
     "$RAIZ/.claude/hooks/regresion-antes-de-commit.py" \
     "$RAIZ/.claude/hooks/gcs-allowlist.py" "$dest/hooks/"
  cp "$RAIZ/gcs-mcp-tp4/scripts/check-generations.py" "$dest/scripts/"

  # Basura local que no es parte del plugin.
  find "$dest" \( -name __pycache__ -o -name .DS_Store \) -prune -exec rm -rf {} +
  chmod 755 "$dest"/hooks/*.py "$dest"/scripts/*.py

  # Reemplazos de R-11, solo en los skills y agents copiados. Cada uno tiene que aplicar
  # al menos una vez: si el original cambió y un reemplazo ya no encuentra su texto, el
  # armado falla en vez de dejar un nombre viejo.
  python3 - "$dest" <<'PY'
import sys
from pathlib import Path

dest = Path(sys.argv[1])
skill = dest / "skills/write-vcs-con-bucket/SKILL.md"

# (viejo, nuevo, archivos donde tiene que aparecer al menos una vez)
REEMPLAZOS = [
    ("gcs-mcp-tp4/scripts/check-generations.py", "${CLAUDE_PLUGIN_ROOT}/scripts/check-generations.py", [skill]),
    ("gcs-mcp-tp4/salida/vcs-bucket.md", "${user_config.salida}", [skill]),
    ("gcsgrep-test-g4-mcp", "${user_config.bucket}", [skill]),
    ("mcp__gcs__", "mcp__plugin_gcsgrep-toolkit_gcs__", [skill, dest / "agents/lector-fixtures.md"]),
    # El skill de la L3 llama a su script por la ruta del repo; en el plugin vive bajo la raíz del plugin.
    (".claude/skills/write-spec-brownfield/scripts/", "${CLAUDE_PLUGIN_ROOT}/skills/write-spec-brownfield/scripts/",
     [dest / "skills/write-spec-brownfield/SKILL.md"]),
]
# Solo en el paso que lanza el subagent: el `name:` del agent queda pelado.
LANZA = ("Lanzá el subagent `lector-fixtures`", "Lanzá el subagent `gcsgrep-toolkit:lector-fixtures`")

archivos = sorted(dest.glob("skills/**/*.md")) + sorted(dest.glob("agents/*.md"))
errores = []
textos = {f: f.read_text(encoding="utf-8") for f in archivos}

for viejo, nuevo, obligatorios in REEMPLAZOS:
    for f in obligatorios:
        if viejo not in textos[f]:
            errores.append(f"replacement {viejo!r} found nothing in {f.relative_to(dest)}")
    for f in archivos:
        textos[f] = textos[f].replace(viejo, nuevo)

n = textos[skill].count(LANZA[0])
if n != 1:
    errores.append(f"expected exactly 1 occurrence of {LANZA[0]!r} in {skill.relative_to(dest)}, found {n}")
textos[skill] = textos[skill].replace(*LANZA)

for f in archivos:
    if "mcp__gcs__" in textos[f]:
        errores.append(f"{f.relative_to(dest)} still contains mcp__gcs__")

if errores:
    print("armar.sh: build failed:", *errores, sep="\n  ", file=sys.stderr)
    sys.exit(1)
for f, texto in textos.items():
    f.write_text(texto, encoding="utf-8")
PY
}

if [ "$MODO" = build ]; then
  for f in "${A_MANO[@]}"; do
    [ -f "$PLUGIN/$f" ] || echo "warning: hand-maintained file missing: $PLUGIN/$f" >&2
  done
  rm -rf "$PLUGIN/skills" "$PLUGIN/agents" "$PLUGIN/scripts"
  rm -f "$PLUGIN"/hooks/*.py
  build "$PLUGIN"
  echo "Plugin built in $PLUGIN"
  echo "Next: claude plugin validate \"$PLUGIN\""
  exit 0
fi

# --check
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
ESPERADO="$TMP/gcsgrep-toolkit"
mkdir -p "$ESPERADO"
for f in "${A_MANO[@]}"; do
  if [ -f "$PLUGIN/$f" ]; then
    mkdir -p "$ESPERADO/$(dirname "$f")"
    cp "$PLUGIN/$f" "$ESPERADO/$f"
  else
    echo "armar.sh --check: hand-maintained file missing: gcs-mcp-tp4/plugin/gcsgrep-toolkit/$f" >&2
    exit 1
  fi
done
build "$ESPERADO"

EXCLUIR=(-x __pycache__ -x .DS_Store)
if diff -rq "${EXCLUIR[@]}" "$ESPERADO" "$PLUGIN" >"$TMP/resumen" 2>&1; then
  echo "armar.sh --check: OK, the committed plugin matches what armar.sh builds."
  exit 0
fi

{
  echo "armar.sh --check: the committed plugin differs from what armar.sh builds."
  echo "Summary (expected = built from .claude/, actual = gcs-mcp-tp4/plugin/gcsgrep-toolkit/):"
  sed -e "s|$ESPERADO|expected|g" -e "s|$PLUGIN|actual|g" "$TMP/resumen" | sed 's/^/  /'
  echo "First lines of the diff:"
  diff -ru "${EXCLUIR[@]}" "$ESPERADO" "$PLUGIN" 2>&1 \
    | sed -e "s|$ESPERADO|expected|g" -e "s|$PLUGIN|actual|g" | head -n 60 | sed 's/^/  /' || true
  echo "Fix: run gcs-mcp-tp4/plugin/armar.sh and commit the result."
} >&2
exit 1

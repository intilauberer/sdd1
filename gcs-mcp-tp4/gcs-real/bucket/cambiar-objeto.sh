#!/usr/bin/env bash
# Hace envejecer la evidencia: re-sube logs/app-2026-10-02.log con el mismo contenido
# para que cambie su generation (spec.md: R-6, VC-6a). Usa la identidad de la persona.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

OBJ="logs/app-2026-10-02.log"
URI="gs://${BUCKET}/${OBJ}"

confirm "This will re-upload $URI (same content, new generation). Continue?"

OLD_GEN="$(gcloud storage objects describe "$URI" --project="$PROJECT" --format='value(generation)')"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
printf '%s\n' \
  "2026-10-02T11:30:00Z INFO arranque" \
  "2026-10-02T11:30:04Z ERROR Timeout reading upstream" \
  > "$WORKDIR/app-2026-10-02.log"

gcloud storage cp "$WORKDIR/app-2026-10-02.log" "$URI" --project="$PROJECT" --content-type="text/plain"

NEW_GEN="$(gcloud storage objects describe "$URI" --project="$PROJECT" --format='value(generation)')"

echo "Object:         $URI"
echo "old generation: $OLD_GEN"
echo "new generation: $NEW_GEN"
if [[ "$OLD_GEN" == "$NEW_GEN" ]]; then
  echo "FAIL: generation did not change" >&2
  exit 1
fi
echo "Now run: uv run --no-project --with google-cloud-storage==3.14.1 python gcs-mcp-tp4/scripts/check-generations.py verificar gcs-mcp-tp4/salida/vcs-bucket.md   # expected: exit 1, STALE line for $URI"

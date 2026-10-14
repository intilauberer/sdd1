#!/usr/bin/env bash
# Hace envejecer la evidencia en el emulador: re-sube logs/app-2026-10-02.log con el mismo
# contenido, con el contenedor admin, para que cambien su generation y su updated
# (spec.md: R-6, VC-6a, D-9).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

OBJ="logs/app-2026-10-02.log"
URI="gs://${BUCKET}/${OBJ}"
require_gateway

OLD_GEN="$(object_field "$OBJ" generation)"
OLD_UPD="$(object_field "$OBJ" updated)"
if [[ -z "$OLD_GEN" ]]; then
  echo "FAIL: $URI does not exist; run armar-bucket.sh first." >&2
  exit 1
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
printf '%s\n' \
  "2026-10-02T11:30:00Z INFO arranque" \
  "2026-10-02T11:30:04Z ERROR Timeout reading upstream" \
  > "$WORKDIR/app-2026-10-02.log"
{
  echo 'set -eu'
  echo 'curl -sS -f -o /dev/null -X POST -H "Content-Type: text/plain" --data-binary @/work/app-2026-10-02.log \'
  printf '  "http://gcs:4443/upload/storage/v1/b/$BUCKET/o?uploadType=media&name=%s"\n' "$(urlencode "$OBJ")"
} > "$WORKDIR/upload.sh"
echo "Re-uploading $URI (same content) via the admin container ..."
admin_run "$WORKDIR" /work/upload.sh

NEW_GEN="$(object_field "$OBJ" generation)"
NEW_UPD="$(object_field "$OBJ" updated)"

echo "Object:         $URI"
echo "old generation: $OLD_GEN (updated $OLD_UPD)"
echo "new generation: $NEW_GEN (updated $NEW_UPD)"
if [[ "$OLD_GEN" == "$NEW_GEN" ]]; then
  echo "FAIL: generation did not change" >&2
  exit 1
fi
echo "Now run: STORAGE_EMULATOR_HOST=$GATEWAY uv run --no-project --with google-cloud-storage==3.14.1 python gcs-mcp-tp4/scripts/check-generations.py verificar gcs-mcp-tp4/salida/vcs-bucket.md   # expected: exit 1, STALE line for $URI"

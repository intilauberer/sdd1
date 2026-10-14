#!/usr/bin/env bash
# Levanta el emulador y el gateway de solo lectura (spec.md: D-9). El bucket se arma
# después con armar-bucket.sh (el backend es en memoria: cada `up` arranca vacío).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

echo "Starting gcs (fake-gcs-server, internal network only) and gateway ($GATEWAY) ..."
compose up -d gcs gateway

echo "Waiting for the gateway to reach the emulator ..."
code=000
for _ in $(seq 1 60); do
  code="$(gateway_status "/storage/v1/b/${BUCKET}/o")"
  # 200: el bucket ya existe · 404: el emulador contesta y el bucket todavía no está.
  if [[ "$code" == "200" || "$code" == "404" ]]; then
    break
  fi
  sleep 1
done
if [[ "$code" != "200" && "$code" != "404" ]]; then
  echo "FAIL: gateway did not become ready (last HTTP status $code)." >&2
  compose logs --tail 30 gcs gateway >&2 || true
  exit 1
fi
echo "Gateway ready (GET /storage/v1/b/${BUCKET}/o -> HTTP $code)."

echo
compose ps
echo
echo "Published ports:"
echo "  gateway 8080 -> $(compose port gateway 8080)"
gcs_port="$(compose port gcs 4443 2>/dev/null || true)"
[[ "$gcs_port" == *":0" ]] && gcs_port=""   # compose imprime "invalid IP:0" si no está publicado
echo "  gcs     4443 -> ${gcs_port:-(not published)}"
cat <<EOF

Next:
  gcs-mcp-tp4/emulador/armar-bucket.sh
  export STORAGE_EMULATOR_HOST=$GATEWAY
EOF

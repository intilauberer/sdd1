#!/usr/bin/env bash
# Configuración compartida de los scripts de emulador/ (spec.md: D-9, R-1, R-2, R-10).
# Se carga con `source`; no levanta nada.
set -euo pipefail

EMU_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUCKET="${GCSGREP_TP4_BUCKET:-gcsgrep-test-g4-mcp}"
GATEWAY="${GCSGREP_TP4_GATEWAY:-http://127.0.0.1:4443}"
COMPOSE_PROJECT="gcs-mcp-tp4"
TP4_CONFIG_DIR="${GCSGREP_TP4_CONFIG_DIR:-$HOME/.config/gcloud-tp4}"
NONCE_FILE="${TP4_CONFIG_DIR}/nonce.txt"

case "$BUCKET" in
  gcsgrep-test-*) ;;
  *)
    echo "config.sh: refusing bucket '$BUCKET': test bucket names must start with 'gcsgrep-test-'." >&2
    exit 2
    ;;
esac
# docker-compose.yml fija BUCKET=gcsgrep-test-g4-mcp en el gateway.
if [[ "$BUCKET" != "gcsgrep-test-g4-mcp" ]]; then
  echo "config.sh: the gateway in docker-compose.yml only serves gcsgrep-test-g4-mcp (got '$BUCKET')." >&2
  exit 2
fi

# El credential helper de Docker se cuelga en algunas máquinas: un DOCKER_CONFIG vacío
# alcanza para bajar imágenes públicas.
export DOCKER_CONFIG="${DOCKER_CONFIG:-/tmp/dockercfg}"
mkdir -p "$DOCKER_CONFIG"
[[ -f "$DOCKER_CONFIG/config.json" ]] || printf '{}\n' > "$DOCKER_CONFIG/config.json"

# Con un DOCKER_CONFIG propio, `docker compose` puede no encontrar el plugin (vive en
# ~/.docker/cli-plugins): en ese caso se usa el binario `docker-compose`.
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "config.sh: neither 'docker compose' nor 'docker-compose' is available (DOCKER_CONFIG=$DOCKER_CONFIG)." >&2
  exit 2
fi

compose() {
  "${COMPOSE_CMD[@]}" -p "$COMPOSE_PROJECT" -f "$EMU_DIR/docker-compose.yml" "$@"
}

# Corre un script de sh dentro del contenedor admin (red interna), con DIR montado en /work.
admin_run() {
  local dir="$1"; shift
  ADMIN_DIR="$dir" compose --profile admin run --rm -T --user "$(id -u):$(id -g)" \
    -e BUCKET="$BUCKET" admin "$@"
}

# Código HTTP de un GET al gateway (000 si no contesta).
gateway_status() {
  curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$GATEWAY$1" || true
}

require_gateway() {
  local code
  code="$(gateway_status "/storage/v1/b/${BUCKET}/o")"
  if [[ "$code" != "200" && "$code" != "404" ]]; then
    echo "The gateway at $GATEWAY is not answering (HTTP $code). Run gcs-mcp-tp4/emulador/levantar.sh first." >&2
    exit 1
  fi
}

# Nombre de objeto codificado para una URL (logs/a.log -> logs%2Fa.log).
urlencode() {
  python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

# Un campo de la metadata de un objeto, leída por el gateway (vacío si no existe).
object_field() {
  local obj="$1" field="$2"
  curl -s --max-time 10 "$GATEWAY/storage/v1/b/${BUCKET}/o/$(urlencode "$obj")" \
    | python3 -c 'import sys, json
try:
    d = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
print(d.get(sys.argv[1], "") if "error" not in d else "")' "$field"
}

# Nombres de los objetos del bucket, uno por línea, leídos por el gateway.
list_names() {
  curl -s --max-time 10 "$GATEWAY/storage/v1/b/${BUCKET}/o" \
    | python3 -c 'import sys, json
d = json.load(sys.stdin)
for it in d.get("items", []):
    print(it["name"])'
}

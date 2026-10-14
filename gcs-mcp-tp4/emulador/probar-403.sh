#!/usr/bin/env bash
# Capa 3 en el emulador: por el gateway se lee, pero escribir y borrar vuelve 403; y no hay
# otro camino hasta el emulador (spec.md: R-10, VC-10a, D-9).
# El 403 lo emite gateway.py, no IAM de GCS: ver el límite honesto en D-9.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

TARGET_KEEP="logs/app-2026-10-01.log"
TARGET_NEW="prueba-403.txt"
KEEP_ENC="$(urlencode "$TARGET_KEEP")"
FAILS=0

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*"; FAILS=$((FAILS + 1)); }

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
printf 'should never be written\n' > "$WORKDIR/prueba-403.txt"

# Corre curl contra el gateway; deja el cuerpo en $WORKDIR/body y devuelve el código HTTP.
http() {
  local code
  echo >&2
  echo "\$ curl $*" >&2
  code="$(curl -s -o "$WORKDIR/body" -w '%{http_code}' --max-time 10 "$@" || true)"
  sed 's/^/  | /' "$WORKDIR/body" >&2; echo >&2
  echo "  HTTP $code" >&2
  echo "$code"
}

expect_403() {
  local label="$1" permission="$2"; shift 2
  local code
  code="$(http "$@")"
  if [[ "$code" == "403" ]] && grep -qF "$permission" "$WORKDIR/body" \
       && grep -q '"reason": *"forbidden"' "$WORKDIR/body"; then
    pass "$label rejected with 403 / $permission"
  else
    fail "$label: expected HTTP 403 with $permission in the body (got HTTP $code)"
  fi
}

echo "Bucket: $BUCKET · identity under test: lector@gateway ($GATEWAY)"
require_gateway

# 0. Por el gateway se LEE: sin esto, un 403 no prueba nada.
code="$(http "$GATEWAY/storage/v1/b/${BUCKET}/o/${KEEP_ENC}")"
gen="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("generation",""))' "$WORKDIR/body" 2>/dev/null || true)"
if [[ "$code" == "200" && "$gen" =~ ^[0-9]+$ ]]; then
  pass "read via gateway (objects.get) succeeds, generation $gen"
else
  fail "read via gateway failed (HTTP $code); it must read before the 403 checks mean anything"
  echo "RESULT: FAIL (cannot prove the gateway reads; not attempting write/delete)"
  exit 1
fi

# 1-2. Escribir y borrar, por el gateway.
expect_403 "write via gateway (upload new object)" storage.objects.create \
  -X POST -H "Content-Type: text/plain" --data-binary "@$WORKDIR/prueba-403.txt" \
  "$GATEWAY/upload/storage/v1/b/${BUCKET}/o?uploadType=media&name=${TARGET_NEW}"
expect_403 "delete via gateway (existing object)" storage.objects.delete \
  -X DELETE "$GATEWAY/storage/v1/b/${BUCKET}/o/${KEEP_ENC}"

# 3. No hay camino directo hasta el emulador.
echo
echo "\$ docker compose -p $COMPOSE_PROJECT ps --format '{{.Service}}  {{.Ports}}'"
compose ps --format '{{.Service}}  {{.Ports}}' | sed 's/^/  | /'

echo
echo "\$ docker compose -p $COMPOSE_PROJECT port gcs 4443"
rc=0
gcs_port="$(compose port gcs 4443 2>&1)" || rc=$?
sed 's/^/  | /' <<<"${gcs_port:-(empty)}"
if [[ $rc -ne 0 || -z "$gcs_port" || "$gcs_port" == *":0" ]]; then
  pass "gcs (the emulator) has no published port"
else
  fail "gcs publishes $gcs_port: the emulator is reachable without the gateway"
fi

gw_port="$(compose port gateway 8080)"
if [[ "$gw_port" == "127.0.0.1:4443" ]]; then
  pass "only the gateway is published, on 127.0.0.1:4443"
else
  fail "gateway is published on '$gw_port', expected 127.0.0.1:4443"
fi

gcs_id="$(compose ps -q gcs)"
nets="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$gcs_id" | xargs)"
internal="$(docker network inspect -f '{{.Internal}}' "${COMPOSE_PROJECT}_interna")"
echo
echo "  gcs networks: $nets · ${COMPOSE_PROJECT}_interna internal=$internal"
if [[ "$nets" == "${COMPOSE_PROJECT}_interna" && "$internal" == "true" ]]; then
  pass "gcs is attached only to the internal network ${COMPOSE_PROJECT}_interna"
else
  fail "gcs networks are '$nets' (internal=$internal), expected only ${COMPOSE_PROJECT}_interna (internal=true)"
fi

echo
echo "\$ curl http://127.0.0.1:4444/storage/v1/b/${BUCKET}/o   # the emulator's port + 1: nothing else listens"
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:4444/storage/v1/b/${BUCKET}/o" || true)"
echo "  HTTP $code"
if [[ "$code" == "000" ]]; then
  pass "nothing answers on 127.0.0.1:4444"
else
  fail "something answers on 127.0.0.1:4444 (HTTP $code)"
fi

# Por la IP del contenedor: en Docker Desktop (macOS) el host no rutea a las redes de
# los contenedores; en Linux el host sí puede llegar a un bridge interno. Se informa,
# no se cuenta: es un límite declarado en D-9.
gcs_ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$gcs_id")"
echo
echo "\$ curl http://${gcs_ip}:4443/storage/v1/b/${BUCKET}/o   # the emulator's container IP, from the host"
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://${gcs_ip}:4443/storage/v1/b/${BUCKET}/o" || true)"
echo "  HTTP $code"
if [[ "$code" == "000" ]]; then
  echo "INFO: the emulator's container IP is not reachable from the host"
else
  echo "WARN: the emulator's container IP answers from the host (HTTP $code); expected on Linux hosts, see spec D-9"
fi

# 4. Nada cambió.
echo
code="$(http "$GATEWAY/storage/v1/b/${BUCKET}/o/${KEEP_ENC}")"
gen_after="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("generation",""))' "$WORKDIR/body" 2>/dev/null || true)"
if [[ "$code" == "200" && "$gen_after" == "$gen" ]]; then
  pass "gs://${BUCKET}/${TARGET_KEEP} still exists, same generation $gen"
else
  fail "gs://${BUCKET}/${TARGET_KEEP} changed or is missing (HTTP $code, generation '$gen_after')"
fi
code="$(http "$GATEWAY/storage/v1/b/${BUCKET}/o/${TARGET_NEW}")"
if [[ "$code" == "404" ]]; then
  pass "gs://${BUCKET}/${TARGET_NEW} does not exist"
else
  fail "gs://${BUCKET}/${TARGET_NEW}: expected 404, got HTTP $code"
fi

echo
echo "Gateway log (last DENY lines):"
compose logs --no-log-prefix gateway 2>/dev/null | grep '^DENY' | tail -n 5 | sed 's/^/  | /' || true

echo
if [[ $FAILS -eq 0 ]]; then
  echo "RESULT: PASS (VC-10a, emulator + gateway)"
  exit 0
fi
echo "RESULT: FAIL ($FAILS check(s) failed)"
exit 1

#!/usr/bin/env bash
# I-6 contra ADC real, sin emulador y sin bucket (Iteración 2b).
#
# La falla de credenciales ocurre al crear el cliente, antes de cualquier pedido a
# Storage, así que I-6 no necesita GCS. Corre el `gcsgrep` instalado en tres
# entornos de credenciales armados en un directorio temporal; `CLOUDSDK_CONFIG`
# apunta ahí para que ADC no vea la configuración de `gcloud` de la máquina.
#
#   ./scripts/i6-adc-local.sh [ruta-a-gcsgrep]
set -u
GCSGREP=${1:-gcsgrep}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/vacio" "$TMP/roto"
echo '{ no es json' > "$TMP/roto/application_default_credentials.json"

falla=0
correr() {
  local nombre=$1 esperado=$2; shift 2
  env "$@" "$GCSGREP" x gs://gcsgrep-test-no-existe-i6/ >"$TMP/out" 2>"$TMP/err"
  local ec=$?
  echo "== $nombre: exit=$ec, stdout=$(wc -c <"$TMP/out" | tr -d ' ') B"
  cat "$TMP/err"
  if [ "$ec" -ne 2 ] || [ -s "$TMP/out" ] || ! grep -q "$esperado" "$TMP/err" \
     || ! grep -q "gcloud auth application-default login" "$TMP/err" \
     || grep -q Traceback "$TMP/err"; then
    echo "   ✗ no cumple"; falla=1
  else
    echo "   ✓"
  fi
}

correr "ADC ausente (FR-15)" "no se encontraron credenciales" \
  -u GOOGLE_APPLICATION_CREDENTIALS CLOUDSDK_CONFIG="$TMP/vacio"
correr "variable a un archivo inexistente (FR-26)" "credenciales inválidas o vencidas" \
  GOOGLE_APPLICATION_CREDENTIALS="$TMP/no-existe.json" CLOUDSDK_CONFIG="$TMP/vacio"
correr "archivo de gcloud mal formado (FR-26)" "credenciales inválidas o vencidas" \
  -u GOOGLE_APPLICATION_CREDENTIALS CLOUDSDK_CONFIG="$TMP/roto"
exit $falla

#!/usr/bin/env bash
#
# Campo de pruebas de gcsgrep contra GCS real.
#
# Crea un bucket desechable, lo siembra con fixtures conocidas, corre los
# chequeos de integración de la Iteración 1, y lo destruye.
#
#   ./scripts/testing-ground.sh up       # crea el bucket y sube las fixtures
#   ./scripts/testing-ground.sh verify   # corre los chequeos I-1 … I-6
#   ./scripts/testing-ground.sh down     # borra objetos y bucket (pide confirmación)
#   ./scripts/testing-ground.sh all      # up && verify && down
#
# Requiere: gcloud autenticado (`gcloud auth application-default login`) y un
# proyecto por defecto (`gcloud config set project <id>`).
#
# Documentación del procedimiento y de qué VC cubre cada chequeo:
#   docs/integracion-gcs.md
#
set -euo pipefail

# --- Configuración -----------------------------------------------------------

# Prefijo obligatorio del nombre del bucket. Es un guardrail: `down` se niega a
# borrar cualquier bucket que no lo tenga, para que un GCSGREP_TEST_BUCKET mal
# seteado no pueda apuntar a un bucket real.
readonly PREFIJO_OBLIGATORIO="gcsgrep-test-"

BUCKET="${GCSGREP_TEST_BUCKET:-}"
REGION="${GCSGREP_TEST_REGION:-us-central1}"

# gcsgrep: el entry point instalado si existe, si no el módulo.
if command -v gcsgrep >/dev/null 2>&1; then
  GCSGREP=(gcsgrep)
else
  GCSGREP=(python -m gcsgrep.cli)
fi

# --- Utilidades --------------------------------------------------------------

info()  { printf '\033[1m›\033[0m %s\n' "$*"; }
ok()    { printf '  \033[32m✓\033[0m %s\n' "$*"; }
fail()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
die()   { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

fallas=0

requiere_gcloud() {
  command -v gcloud >/dev/null 2>&1 || die "no encontré 'gcloud' en el PATH"
}

resolver_bucket() {
  if [[ -z "$BUCKET" ]]; then
    die "falta GCSGREP_TEST_BUCKET.
  Elegí un nombre que empiece con '${PREFIJO_OBLIGATORIO}' y sea único global:
      export GCSGREP_TEST_BUCKET=${PREFIJO_OBLIGATORIO}\$(whoami)-\$(date +%s)"
  fi
  if [[ "$BUCKET" != "${PREFIJO_OBLIGATORIO}"* ]]; then
    die "por seguridad, el bucket de pruebas tiene que empezar con '${PREFIJO_OBLIGATORIO}'.
  Recibí: '${BUCKET}'. Este script crea y BORRA buckets; el prefijo evita que
  apunte por accidente a uno real."
  fi
}

# Corre gcsgrep y compara el exit code observado contra el esperado.
# uso: chequeo <id> <exit_esperado> <descripción> -- <args de gcsgrep...>
chequeo() {
  local id="$1" esperado="$2" desc="$3"; shift 4  # descarta el '--'
  local salida rc
  set +e
  salida="$("${GCSGREP[@]}" "$@" 2>/tmp/gcsgrep-stderr.$$)"
  rc=$?
  set -e

  if [[ "$rc" -eq "$esperado" ]]; then
    ok "${id} ${desc} — exit ${rc} (esperado ${esperado})"
  else
    fail "${id} ${desc} — exit ${rc}, esperaba ${esperado}"
    fallas=$((fallas + 1))
  fi

  if [[ -n "$salida" ]]; then
    printf '      stdout: %s\n' "$(head -3 <<<"$salida")"
  fi
  if grep -q Traceback /tmp/gcsgrep-stderr.$$ 2>/dev/null; then
    fail "${id} stderr contiene un Traceback — viola NFR-3"
    fallas=$((fallas + 1))
  fi
  rm -f /tmp/gcsgrep-stderr.$$
}

# --- Comandos ----------------------------------------------------------------

cmd_up() {
  resolver_bucket
  requiere_gcloud

  info "creando gs://${BUCKET} en ${REGION}"
  gcloud storage buckets create "gs://${BUCKET}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  info "generando fixtures"

  # logs/ — el prefijo que usan los chequeos de la Iteración 1.
  printf 'servicio iniciado\nconnection timeout after 30s\nreintentando\n' > "${tmp}/a.txt"
  printf 'todo bien por aca\nnada para ver\n' > "${tmp}/b.txt"
  # Solo con mayúscula: distingue el chequeo de -i (VC-2).
  printf 'linea uno\nTimeout error\nlinea tres\n' > "${tmp}/c.txt"

  # grande/ — para el chequeo de salida incremental en un pipe (VC-17).
  seq 1 200000 | sed 's/^/linea /' > "${tmp}/big.txt"

  # raros/ — fixtures que la Iteración 1 no sabe manejar todavía. Viven fuera de
  # logs/ a propósito, para no contaminar los chequeos de la Iteración 1.
  # La Iteración 2 (FR-9, FR-10) los va a usar.
  printf 'texto\000con byte nulo\000adentro\n' > "${tmp}/blob.bin"
  printf 'contenido comprimido irrelevante\n' | gzip > "${tmp}/access.log.gz"

  info "subiendo fixtures"
  gcloud storage cp "${tmp}/a.txt" "gs://${BUCKET}/logs/a.txt"
  gcloud storage cp "${tmp}/b.txt" "gs://${BUCKET}/logs/b.txt"
  gcloud storage cp "${tmp}/c.txt" "gs://${BUCKET}/logs/c.txt"
  gcloud storage cp "${tmp}/big.txt" "gs://${BUCKET}/grande/big.txt"
  gcloud storage cp "${tmp}/blob.bin" "gs://${BUCKET}/raros/blob.bin"
  gcloud storage cp "${tmp}/access.log.gz" "gs://${BUCKET}/raros/access.log.gz"

  ok "campo de pruebas listo en gs://${BUCKET}"
  info "acordate de correr 'down' cuando termines: el bucket sigue costando plata"
}

cmd_verify() {
  resolver_bucket
  info "chequeos de integración contra gs://${BUCKET} — comando: ${GCSGREP[*]}"

  chequeo I-1 0 "búsqueda con match (VC-1, VC-4)" -- \
    "timeout" "gs://${BUCKET}/logs/"

  chequeo I-2 0 "-i -n sobre una línea capitalizada (VC-2, VC-3)" -- \
    -i -n "TIMEOUT" "gs://${BUCKET}/logs/"

  chequeo I-3 1 "sin resultados, stdout vacío (VC-5)" -- \
    "no-existe-esto-en-ningun-lado" "gs://${BUCKET}/logs/"

  chequeo I-4 2 "ubicación sin esquema gs:// (VC-8)" -- \
    "x" "no-es-una-ruta-gs"

  info "I-5 salida incremental en un pipe (VC-17)"
  local primeras
  # `head -3` cierra el pipe: gcsgrep tiene que haber emitido esas 3 líneas sin
  # haber leído los 200.000 renglones del objeto.
  primeras="$(set +o pipefail; "${GCSGREP[@]}" "linea" "gs://${BUCKET}/grande/" 2>/dev/null | head -3 | wc -l | tr -d ' ')"
  if [[ "$primeras" == "3" ]]; then
    ok "I-5 tres líneas emitidas y el pipe cortó sin esperar el objeto completo"
  else
    fail "I-5 esperaba 3 líneas antes del corte, obtuve ${primeras}"
    fallas=$((fallas + 1))
  fi

  info "I-6 ADC ausente (ADR-0002) — se corre con las credenciales tapadas"
  local rc err
  set +e
  err="$(CLOUDSDK_CONFIG=/nonexistent GOOGLE_APPLICATION_CREDENTIALS=/nonexistent \
        GOOGLE_CLOUD_PROJECT="" "${GCSGREP[@]}" "timeout" "gs://${BUCKET}/logs/" 2>&1 >/dev/null)"
  rc=$?
  set -e
  if [[ "$rc" -eq 2 ]]; then
    ok "I-6 exit 2 sin credenciales"
  else
    fail "I-6 exit ${rc}, esperaba 2 (NFR-2 / ADR-0002)"
    fallas=$((fallas + 1))
  fi
  if grep -q Traceback <<<"$err"; then
    fail "I-6 stderr contiene un Traceback — viola NFR-3"
    fallas=$((fallas + 1))
  else
    ok "I-6 stderr sin Traceback"
  fi

  echo
  if [[ "$fallas" -eq 0 ]]; then
    ok "todos los chequeos de integración pasaron"
    info "anotá los resultados en specs/gcsgrep/04-cobertura-vc.md, tabla de integración"
  else
    die "${fallas} chequeo(s) de integración fallaron"
  fi
}

cmd_down() {
  resolver_bucket
  requiere_gcloud

  info "esto borra TODOS los objetos y el bucket gs://${BUCKET}"
  if [[ "${GCSGREP_TEST_YES:-}" != "1" ]]; then
    read -r -p "  escribí el nombre del bucket para confirmar: " confirmacion
    [[ "$confirmacion" == "$BUCKET" ]] || die "no coincide; no se borró nada"
  fi

  gcloud storage rm --recursive "gs://${BUCKET}" || true
  ok "gs://${BUCKET} borrado"
}

# --- Entrada -----------------------------------------------------------------

usage() {
  cat <<'USO'
Campo de pruebas de gcsgrep contra GCS real.

  ./scripts/testing-ground.sh up       # crea el bucket y sube las fixtures
  ./scripts/testing-ground.sh verify   # corre los chequeos I-1 … I-6
  ./scripts/testing-ground.sh down     # borra objetos y bucket (pide confirmación)
  ./scripts/testing-ground.sh all      # up && verify && down

Variables:
  GCSGREP_TEST_BUCKET   nombre del bucket; tiene que empezar con 'gcsgrep-test-'
  GCSGREP_TEST_REGION   región del bucket (default: us-central1)
  GCSGREP_TEST_YES=1    saltea la confirmación interactiva de 'down'

Requiere gcloud autenticado (`gcloud auth application-default login`) y un
proyecto por defecto (`gcloud config set project <id>`).

Procedimiento completo y qué VC cubre cada chequeo: docs/integracion-gcs.md
USO
}

case "${1:-}" in
  up)     cmd_up ;;
  verify) cmd_verify ;;
  down)   cmd_down ;;
  all)    cmd_up; cmd_verify; cmd_down ;;
  *)      usage; exit 1 ;;
esac

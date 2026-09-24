#!/usr/bin/env bash
#
# Campo de pruebas de gcsgrep contra GCS real.
#
# Crea un bucket desechable, lo siembra con fixtures conocidas, corre los
# chequeos de integración de la Iteración 1, y lo destruye.
#
#   ./scripts/testing-ground.sh up       # crea el bucket y sube las fixtures
#   ./scripts/testing-ground.sh verify   # corre los chequeos de la iteración
#   ./scripts/testing-ground.sh down     # borra objetos y bucket (pide confirmación)
#   ./scripts/testing-ground.sh all      # up && verify && down
#
# Dos backends (GCSGREP_TEST_BACKEND), ver ADR-0014:
#   gcs     (default) Google Cloud Storage real. Requiere gcloud autenticado
#           (`gcloud auth application-default login`), un proyecto por defecto
#           (`gcloud config set project <id>`) y billing habilitado.
#   floci   floci-gcp local, gratis y sin cuenta. Requiere el emulador corriendo
#           y STORAGE_EMULATOR_HOST apuntándole. Verifica el wiring y el cliente
#           de google-cloud-storage, NO ADC/IAM ni la red real: los resultados se
#           anotan como "floci", no como GCS.
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

# Backend del campo de pruebas: 'gcs' (real) o 'floci' (emulador). Ver ADR-0014.
BACKEND="${GCSGREP_TEST_BACKEND:-gcs}"
# floci-gcp expone todas las APIs de GCP en un solo puerto.
EMULADOR="${STORAGE_EMULATOR_HOST:-http://localhost:4588}"

# Qué iteración se verifica. Cada chequeo declara a qué iteración pertenece, así
# que 'verify' no reporta como falla algo que todavía no se prometió (H-11).
ITERACION="${GCSGREP_TEST_ITERACION:-1}"

# Bucket que no tiene que existir nunca, para I-7 (FR-12).
readonly BUCKET_INEXISTENTE="gcsgrep-test-no-existe-jamas"

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

requiere_curl() {
  command -v curl >/dev/null 2>&1 || die "no encontré 'curl' en el PATH"
}

resolver_backend() {
  case "$BACKEND" in
    gcs)
      requiere_gcloud
      ;;
    floci)
      requiere_curl
      if [[ -z "${STORAGE_EMULATOR_HOST:-}" ]]; then
        die "backend 'floci' sin STORAGE_EMULATOR_HOST.
  El cliente de google-cloud-storage lo necesita para hablarle al emulador en
  vez de a GCS (ADR-0014). No hay que tocar código:
      export STORAGE_EMULATOR_HOST=${EMULADOR}
  o, si tenés el binario:  eval \$(floci gcp env)"
      fi
      curl -fsS -o /dev/null "${EMULADOR}/storage/v1/b?project=gcsgrep-test" 2>/dev/null \
        || die "no pude hablar con floci-gcp en ${EMULADOR}.
  Levantalo con una de las dos:
      docker run -d --name floci-gcp -p 4588:4588 floci/floci-gcp:latest
      floci gcp up"
      ;;
    *)
      die "GCSGREP_TEST_BACKEND inválido: '${BACKEND}'. Valores: gcs | floci"
      ;;
  esac
}

# --- Capa de almacenamiento --------------------------------------------------
# Las tres operaciones que el campo de pruebas necesita para armar y desarmar el
# escenario, una implementación por backend. Es el único lugar del script que
# sabe con cuál está hablando: 'verify' corre los mismos chequeos contra los dos.

crear_bucket() {
  if [[ "$BACKEND" == "floci" ]]; then
    curl -fsS -o /dev/null -X POST \
      -H 'Content-Type: application/json' \
      -d "{\"name\":\"${BUCKET}\"}" \
      "${EMULADOR}/storage/v1/b?project=gcsgrep-test"
  else
    gcloud storage buckets create "gs://${BUCKET}" \
      --location="${REGION}" \
      --uniform-bucket-level-access \
      --public-access-prevention
  fi
}

# uso: subir_objeto <archivo local> <nombre del objeto>   p. ej. 'logs/a.txt'
subir_objeto() {
  local local_path="$1" nombre="$2"
  if [[ "$BACKEND" == "floci" ]]; then
    # El '/' del nombre va escapado en el query param, o el emulador lo toma
    # como parte de la ruta del endpoint.
    local escapado
    escapado="$(printf '%s' "$nombre" | sed 's|/|%2F|g')"
    curl -fsS -o /dev/null -X POST \
      -H 'Content-Type: application/octet-stream' \
      --data-binary "@${local_path}" \
      "${EMULADOR}/upload/storage/v1/b/${BUCKET}/o?uploadType=media&name=${escapado}"
  else
    gcloud storage cp "$local_path" "gs://${BUCKET}/${nombre}"
  fi
}

borrar_bucket() {
  if [[ "$BACKEND" == "floci" ]]; then
    # Sin borrado recursivo: se listan los objetos y se borran de a uno.
    local nombres n
    nombres="$(curl -fsS "${EMULADOR}/storage/v1/b/${BUCKET}/o" 2>/dev/null \
      | grep -o '"name": *"[^"]*"' | sed 's/.*: *"//;s/"$//' || true)"
    for n in $nombres; do
      curl -fsS -o /dev/null -X DELETE \
        "${EMULADOR}/storage/v1/b/${BUCKET}/o/$(printf '%s' "$n" | sed 's|/|%2F|g')" || true
    done
    curl -fsS -o /dev/null -X DELETE "${EMULADOR}/storage/v1/b/${BUCKET}" || true
  else
    gcloud storage rm --recursive "gs://${BUCKET}" || true
  fi
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
  resolver_backend

  if [[ "$BACKEND" == "floci" ]]; then
    info "creando gs://${BUCKET} en floci-gcp (${EMULADOR})"
  else
    info "creando gs://${BUCKET} en ${REGION}"
  fi
  crear_bucket

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
  subir_objeto "${tmp}/a.txt" "logs/a.txt"
  subir_objeto "${tmp}/b.txt" "logs/b.txt"
  subir_objeto "${tmp}/c.txt" "logs/c.txt"
  subir_objeto "${tmp}/big.txt" "grande/big.txt"
  subir_objeto "${tmp}/blob.bin" "raros/blob.bin"
  subir_objeto "${tmp}/access.log.gz" "raros/access.log.gz"

  ok "campo de pruebas listo en gs://${BUCKET}"
  if [[ "$BACKEND" == "floci" ]]; then
    info "backend floci: no cuesta plata, pero 'down' deja limpio para la próxima"
  else
    info "acordate de correr 'down' cuando termines: el bucket sigue costando plata"
  fi
}

cmd_verify() {
  resolver_bucket
  [[ "$BACKEND" == "floci" ]] && resolver_backend
  info "chequeos de integración contra gs://${BUCKET} — comando: ${GCSGREP[*]}"
  info "backend: ${BACKEND} · iteración verificada: ${ITERACION}"
  if [[ "$BACKEND" == "floci" ]]; then
    info "recordatorio (ADR-0014): 'floci' NO verifica ADC, IAM ni la red real."
    info "  Anotá los resultados como 'floci' en la tabla de integración;"
    info "  'VCs verificados contra GCS real' sigue en 0."
  fi

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

  # I-7 · FR-12 / VC-18: bucket inexistente. Apunta a un bucket que no existe a
  # propósito, así que no depende de las fixtures.
  info "I-7 bucket inexistente (VC-18, FR-12)"
  local rc7 err7
  set +e
  err7="$("${GCSGREP[@]}" "x" "gs://${BUCKET_INEXISTENTE}/" 2>&1 >/dev/null)"
  rc7=$?
  set -e
  if [[ "$rc7" -eq 2 ]]; then
    ok "I-7 exit 2 sobre un bucket que no existe"
  else
    fail "I-7 exit ${rc7}, esperaba 2 (FR-12) — ¿está implementado el try/except de cli.py?"
    fallas=$((fallas + 1))
  fi
  if grep -q Traceback <<<"$err7"; then
    fail "I-7 stderr contiene un Traceback — viola NFR-3 y FR-12"
    fallas=$((fallas + 1))
  else
    ok "I-7 stderr sin Traceback"
  fi
  if grep -q "$BUCKET_INEXISTENTE" <<<"$err7"; then
    ok "I-7 el mensaje nombra el bucket"
  else
    fail "I-7 el mensaje no nombra el bucket '${BUCKET_INEXISTENTE}' (FR-12)"
    fallas=$((fallas + 1))
  fi
  # Sin esta última afirmación, I-7 pasa por el camino genérico (ADR-0013) cuando
  # no hay credenciales: exit 2 sin traceback y el bucket en el mensaje, pero por
  # la razón equivocada. Exigir el texto de FR-12 es lo que lo hace fallar por la
  # razón correcta (C-8 del checklist de revisión).
  if grep -q "no existe" <<<"$err7"; then
    ok "I-7 el mensaje identifica el caso: el bucket no existe (FR-12)"
  else
    fail "I-7 el mensaje no dice que el bucket no existe — ¿entró por el caso genérico?"
    printf '      stderr: %s\n' "$(head -1 <<<"$err7")"
    fallas=$((fallas + 1))
  fi

  # I-6 · NFR-2, alcance de la Iteración 2 (H-11). No se corre verificando la
  # Iteración 1: fallaría por algo que todavía no se prometió.
  if [[ "$ITERACION" -ge 2 ]]; then
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
  else
    info "I-6 salteado: verifica NFR-2, que es alcance de la Iteración 2 (H-11)."
    info "  Para correrlo: GCSGREP_TEST_ITERACION=2"
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
  resolver_backend

  info "esto borra TODOS los objetos y el bucket gs://${BUCKET}"
  if [[ "${GCSGREP_TEST_YES:-}" != "1" ]]; then
    read -r -p "  escribí el nombre del bucket para confirmar: " confirmacion
    [[ "$confirmacion" == "$BUCKET" ]] || die "no coincide; no se borró nada"
  fi

  borrar_bucket
  ok "gs://${BUCKET} borrado"
}

# --- Entrada -----------------------------------------------------------------

usage() {
  cat <<'USO'
Campo de pruebas de gcsgrep contra GCS real.

  ./scripts/testing-ground.sh up       # crea el bucket y sube las fixtures
  ./scripts/testing-ground.sh verify   # corre los chequeos de la iteración
  ./scripts/testing-ground.sh down     # borra objetos y bucket (pide confirmación)
  ./scripts/testing-ground.sh all      # up && verify && down

Variables:
  GCSGREP_TEST_BUCKET     nombre del bucket; tiene que empezar con 'gcsgrep-test-'
  GCSGREP_TEST_BACKEND    gcs (default) | floci
  GCSGREP_TEST_ITERACION  qué iteración se verifica (default: 1)
  GCSGREP_TEST_REGION     región del bucket (default: us-central1; solo backend gcs)
  GCSGREP_TEST_YES=1      saltea la confirmación interactiva de 'down'
  STORAGE_EMULATOR_HOST   endpoint de floci-gcp (obligatorio con backend=floci)

Chequeos por iteración:
  1 → I-1 … I-5, I-7      2 → todos, incluido I-6 (NFR-2)

Backend 'gcs' requiere gcloud autenticado (`gcloud auth application-default
login`), un proyecto por defecto (`gcloud config set project <id>`) y billing.

Backend 'floci' no requiere cuenta ni tarjeta:
  docker run -d --name floci-gcp -p 4588:4588 floci/floci-gcp:latest
  export STORAGE_EMULATOR_HOST=http://localhost:4588
No verifica ADC, IAM ni la red real: los resultados se anotan como 'floci'.

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

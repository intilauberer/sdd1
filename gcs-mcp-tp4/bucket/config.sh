#!/usr/bin/env bash
# Configuración compartida de los scripts de bucket/ (spec.md: D-3, D-4, R-1, R-2).
# Se carga con `source`; no ejecuta nada contra GCP.
set -euo pipefail

PROJECT="${GCSGREP_TP4_PROJECT:-itba-sdd}"
BUCKET="${GCSGREP_TP4_BUCKET:-gcsgrep-test-g4-mcp}"
LOCATION="us-central1"
SA_NAME="gcsgrep-tp4-lector"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
TP4_CONFIG_DIR="${GCSGREP_TP4_CONFIG_DIR:-$HOME/.config/gcloud-tp4}"
ADC_FILE="${TP4_CONFIG_DIR}/application_default_credentials.json"
NONCE_FILE="${TP4_CONFIG_DIR}/nonce.txt"

case "$BUCKET" in
  gcsgrep-test-*) ;;
  *)
    echo "config.sh: refusing bucket '$BUCKET': test bucket names must start with 'gcsgrep-test-'." >&2
    exit 2
    ;;
esac

# Pide confirmación salvo GCSGREP_TP4_YES=1.
confirm() {
  local prompt="$1"
  if [[ "${GCSGREP_TP4_YES:-}" == "1" ]]; then
    echo "$prompt [auto-confirmed: GCSGREP_TP4_YES=1]"
    return 0
  fi
  local answer=""
  read -r -p "$prompt [y/N] " answer || true
  if [[ "$answer" != "y" && "$answer" != "Y" && "$answer" != "yes" ]]; then
    echo "Aborted." >&2
    exit 1
  fi
}

bucket_exists() {
  gcloud storage buckets describe "gs://${BUCKET}" --project="$PROJECT" >/dev/null 2>&1
}

sa_exists() {
  gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT" >/dev/null 2>&1
}

# Miembro IAM de la cuenta activa de gcloud (la persona del equipo).
current_member() {
  local account
  account="$(gcloud config get-value account 2>/dev/null || true)"
  if [[ -z "$account" || "$account" == "(unset)" ]]; then
    echo "No active gcloud account. Run 'gcloud auth login' first." >&2
    return 1
  fi
  if [[ "$account" == *.gserviceaccount.com ]]; then
    echo "serviceAccount:${account}"
  else
    echo "user:${account}"
  fi
}

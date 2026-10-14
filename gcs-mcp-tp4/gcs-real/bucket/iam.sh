#!/usr/bin/env bash
# Credencial de solo lectura sobre el bucket y ADC impersonado (spec.md: R-2, VC-2, D-4).
# Lo corre la persona del equipo con su identidad de admin (D-7). Idempotente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

MEMBER="$(current_member)"

echo "Project:         $PROJECT"
echo "Bucket:          gs://$BUCKET"
echo "Service account: $SA_EMAIL"
echo "You:             $MEMBER"
confirm "This will create the SA (if missing), grant it roles/storage.objectViewer on the bucket, and grant you roles/iam.serviceAccountTokenCreator on the SA. Continue?"

# 1. SA
if sa_exists; then
  echo "Service account $SA_EMAIL already exists."
else
  echo "Creating service account $SA_EMAIL ..."
  gcloud iam service-accounts create "$SA_NAME" --project="$PROJECT" \
    --display-name="gcsgrep TP4 read-only reader"
fi

# 2. objectViewer sobre el bucket (no sobre el proyecto)
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" --project="$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer" >/dev/null
echo "Granted roles/storage.objectViewer on gs://$BUCKET to $SA_EMAIL."

# 3. tokenCreator para la persona, solo sobre esa SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" --project="$PROJECT" \
  --member="$MEMBER" --role="roles/iam.serviceAccountTokenCreator" >/dev/null
echo "Granted roles/iam.serviceAccountTokenCreator on $SA_EMAIL to $MEMBER."
echo "Note: IAM changes can take ~60s to propagate. If the next step or later reads fail with 403, wait and retry."

# 4. ADC impersonado, fuera del repo y sin pisar el ADC personal
mkdir -p "$TP4_CONFIG_DIR"
chmod 700 "$TP4_CONFIG_DIR"
echo
echo "Next: 'gcloud auth application-default login' opens a browser to sign in with YOUR account."
echo "The resulting ADC impersonates $SA_EMAIL and is written to:"
echo "  $ADC_FILE"
CLOUDSDK_CONFIG="$TP4_CONFIG_DIR" gcloud auth application-default login \
  --impersonate-service-account="$SA_EMAIL"
[[ -f "$ADC_FILE" ]] && chmod 600 "$ADC_FILE"

cat <<EOF

Export this before starting Claude Code or running the scripts:
  export GOOGLE_APPLICATION_CREDENTIALS=${ADC_FILE}

Evidence commands for VC-2 (read-only; running them now):
  1) gcloud storage buckets get-iam-policy gs://${BUCKET}
  2) gcloud projects get-iam-policy ${PROJECT} --flatten='bindings[].members' --filter='bindings.members:${SA_NAME}'   # must print nothing
  3) gcloud iam service-accounts get-iam-policy ${SA_EMAIL}
EOF

echo
echo "--- 1) bucket IAM policy ---"
gcloud storage buckets get-iam-policy "gs://${BUCKET}" --project="$PROJECT"
echo
echo "--- 2) project bindings for ${SA_NAME} (expected: empty) ---"
gcloud projects get-iam-policy "$PROJECT" --flatten='bindings[].members' \
  --filter="bindings.members:${SA_NAME}" --format='table(bindings.role,bindings.members)'
echo
echo "--- 3) SA IAM policy ---"
gcloud iam service-accounts get-iam-policy "$SA_EMAIL" --project="$PROJECT"

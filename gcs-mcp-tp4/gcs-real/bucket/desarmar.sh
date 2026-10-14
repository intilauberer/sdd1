#!/usr/bin/env bash
# Limpieza después de la corrección: borra el bucket de prueba, el binding y la SA
# creados por armar-bucket.sh e iam.sh (spec.md: R-1, R-2). Irreversible.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

echo "Project:         $PROJECT"
echo "Bucket:          gs://$BUCKET (all objects)"
echo "Service account: $SA_EMAIL"
confirm "This will PERMANENTLY delete the bucket, all its objects, the SA binding and the SA. Continue?"

if bucket_exists; then
  gcloud storage buckets remove-iam-policy-binding "gs://${BUCKET}" --project="$PROJECT" \
    --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer" >/dev/null 2>&1 \
    && echo "Removed objectViewer binding from gs://$BUCKET." \
    || echo "No objectViewer binding to remove on gs://$BUCKET."
  echo "Deleting gs://$BUCKET and its objects ..."
  gcloud storage rm -r "gs://${BUCKET}" --project="$PROJECT"
else
  echo "Bucket gs://$BUCKET does not exist; skipping."
fi

if sa_exists; then
  echo "Deleting service account $SA_EMAIL (its own IAM policy goes with it) ..."
  gcloud iam service-accounts delete "$SA_EMAIL" --project="$PROJECT" --quiet
else
  echo "Service account $SA_EMAIL does not exist; skipping."
fi

cat <<EOF

Done. Local files are left untouched; remove them yourself if you no longer need them:
  rm -rf ${TP4_CONFIG_DIR}
EOF

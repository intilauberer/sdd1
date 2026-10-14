#!/usr/bin/env bash
# Capa 3: la credencial de la SA lee, pero no puede escribir ni borrar (spec.md: R-10, VC-10a).
# Los intentos van con --impersonate-service-account; la confirmación final se hace
# con la identidad de la persona y es de solo lectura.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

TARGET_KEEP="logs/app-2026-10-01.log"
TARGET_NEW="prueba-403.txt"
FAILS=0

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*"; FAILS=$((FAILS + 1)); }

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
printf 'should never be written\n' > "$WORKDIR/prueba-403.txt"

# Pasa solo si: exit ≠ 0, stderr menciona 403 Y el permiso que falta. Un fallo por otra
# causa (red, credencial rota, objeto inexistente) no cuenta como prueba de la capa 3.
expect_403() {
  local label="$1" permission="$2"; shift 2
  local rc=0 err matched
  echo
  echo "\$ $* --impersonate-service-account=$SA_EMAIL"
  "$@" --impersonate-service-account="$SA_EMAIL" >"$WORKDIR/out" 2>"$WORKDIR/err" || rc=$?
  err="$(cat "$WORKDIR/err")"
  sed 's/^/  | /' "$WORKDIR/out" "$WORKDIR/err"
  echo "  exit code: $rc"
  matched="$(grep -m1 '403' <<<"$err" | grep -F "$permission" || true)"
  if [[ -z "$matched" ]] && grep -q '403' <<<"$err" && grep -qF "$permission" <<<"$err"; then
    matched="$(grep -m1 -F "$permission" <<<"$err")"
  fi
  if [[ $rc -ne 0 && -n "$matched" ]]; then
    echo "  matched: $matched"
    pass "$label rejected with 403 / $permission (exit $rc)"
  else
    fail "$label: expected non-zero exit and stderr with 403 and $permission (exit $rc)"
  fi
}

echo "Bucket: gs://$BUCKET · identity under test: $SA_EMAIL"

# 0. La SA puede LEER: sin esto, un 403 en cp/rm no prueba nada (podría no tener ningún permiso).
echo
echo "\$ gcloud storage objects describe gs://${BUCKET}/${TARGET_KEEP} --impersonate-service-account=$SA_EMAIL --format='value(generation)'"
rc=0
read_gen="$(gcloud storage objects describe "gs://${BUCKET}/${TARGET_KEEP}" --project="$PROJECT" \
  --impersonate-service-account="$SA_EMAIL" --format='value(generation)' 2>"$WORKDIR/err")" || rc=$?
sed 's/^/  | /' "$WORKDIR/err"
if [[ $rc -eq 0 && "$read_gen" =~ ^[0-9]+$ ]]; then
  pass "read as SA (describe) succeeds, generation $read_gen"
else
  fail "read as SA (describe) failed (exit $rc); the SA must be able to read before the 403 checks mean anything"
  echo "RESULT: FAIL (cannot prove the SA reads; not attempting write/delete)"
  exit 1
fi

expect_403 "write as SA (cp new object)" storage.objects.create \
  gcloud storage cp "$WORKDIR/prueba-403.txt" "gs://${BUCKET}/${TARGET_NEW}" --project="$PROJECT"

expect_403 "delete as SA (rm existing object)" storage.objects.delete \
  gcloud storage rm "gs://${BUCKET}/${TARGET_KEEP}" --project="$PROJECT"

echo
echo "Checking the bucket with your own identity (read-only):"
if gcloud storage objects describe "gs://${BUCKET}/${TARGET_KEEP}" --project="$PROJECT" \
     --format='value(generation)' >/dev/null 2>&1; then
  pass "gs://${BUCKET}/${TARGET_KEEP} still exists"
else
  fail "gs://${BUCKET}/${TARGET_KEEP} is missing or unreadable"
fi

rc=0
out="$(gcloud storage objects describe "gs://${BUCKET}/${TARGET_NEW}" --project="$PROJECT" 2>&1)" || rc=$?
if [[ $rc -ne 0 ]] && grep -qiE 'not ?found|404|matched no' <<<"$out"; then
  pass "gs://${BUCKET}/${TARGET_NEW} does not exist"
elif [[ $rc -eq 0 ]]; then
  fail "gs://${BUCKET}/${TARGET_NEW} EXISTS — the SA was able to write"
else
  fail "could not confirm gs://${BUCKET}/${TARGET_NEW} is absent: $out"
fi

echo
if [[ $FAILS -eq 0 ]]; then
  echo "RESULT: PASS (VC-10a)"
  exit 0
fi
echo "RESULT: FAIL ($FAILS check(s) failed)"
exit 1

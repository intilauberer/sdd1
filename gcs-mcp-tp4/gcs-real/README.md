# Camino al GCS real (en espera)

El TP corre contra el emulador detrás de un gateway de solo lectura ([`../emulador/`](../emulador/)),
como desvío declarado: [`../spec.md`](../spec.md), D-9. Lo de esta carpeta es el camino
original, guardado para cuando el equipo tenga facturación en GCP. No se usa hoy.

| Archivo | Qué hace |
|---|---|
| `bucket/armar-bucket.sh` | Crea `gs://gcsgrep-test-g4-mcp` con los 6 objetos de R-1 |
| `bucket/iam.sh` | Crea la SA `gcsgrep-tp4-lector`, le da `roles/storage.objectViewer` sobre el bucket y deja el ADC impersonado en `~/.config/gcloud-tp4/` |
| `bucket/probar-403.sh` | Capa 3 real: `gcloud storage cp`/`rm` con la SA impersonada → `403` de IAM |
| `bucket/cambiar-objeto.sh` | Re-sube `logs/app-2026-10-02.log` (VC-6a) |
| `bucket/desarmar.sh` | Borra el bucket, el binding y la SA |
| `mcp.json.ejemplo` | El `.mcp.json` del GCS real: misma versión fijada, con `GOOGLE_APPLICATION_CREDENTIALS` |

Para volver al GCS real (supersede D-9):

1. Correr `bucket/armar-bucket.sh` y `bucket/iam.sh` con la identidad de admin.
2. Reemplazar el `env` de `.mcp.json` y del `.mcp.json` del plugin por el de `mcp.json.ejemplo`
   (en el plugin, `GOOGLE_CLOUD_PROJECT` sigue siendo `${user_config.project_id}`).
3. `unset STORAGE_EMULATOR_HOST` y `export GOOGLE_APPLICATION_CREDENTIALS=…` (la ruta que imprime `iam.sh`).
   `check-generations.py` y `probar-server-sin-hook.py` pasan solos al modo GCS.
4. Ajustar el punto 5 de `../scripts/check-config.py`, que hoy exige el modo emulador.

#!/usr/bin/env bash
# Baja el emulador y el gateway y borra sus volúmenes y redes (spec.md: D-9). El bucket
# vive en memoria: se pierde, y se vuelve a armar con levantar.sh + armar-bucket.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

compose --profile admin down -v --remove-orphans
echo "Emulator and gateway stopped (project $COMPOSE_PROJECT). The nonce file is left in $NONCE_FILE."

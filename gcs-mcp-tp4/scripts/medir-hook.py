#!/usr/bin/env python3
"""VC-15 — latencia del hook gcs-allowlist (spec N-3), sin red ni Claude.

El hook corre antes de **cada** llamada a una tool de `gcs`: lo que tarde se suma a cada
lectura del subagent. Este script lo invoca 200 veces por subprocess (como lo invoca Claude
Code), con un evento que recorre los cinco pasos y termina en `exit 0`, después de 5
corridas de calentamiento que no se cuentan. Mide de punta a punta: arranque del
intérprete, lectura del JSON y decisión.

Sale con 0 si el percentil 95 es ≤ 100 ms, y con 1 si no. Imprime p50, p95 y máximo.

Uso: python3 gcs-mcp-tp4/scripts/medir-hook.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOK = RAIZ / ".claude" / "hooks" / "gcs-allowlist.py"
BUCKET = "gcsgrep-test-g4-mcp"
N, CALENTAMIENTO, UMBRAL_MS = 200, 5, 100.0

EVENTO = json.dumps({
    "hook_event_name": "PreToolUse",
    "tool_name": "mcp__gcs__read_object_content",
    "agent_id": "a-medir",
    "agent_type": "lector-fixtures",
    "tool_input": {"bucket_name": BUCKET, "object_name": "logs/app-2026-10-01.log"},
})


def una_vez(env):
    t0 = time.perf_counter()
    p = subprocess.run([sys.executable, str(HOOK)], input=EVENTO, capture_output=True,
                       text=True, encoding="utf-8", env=env)
    ms = (time.perf_counter() - t0) * 1000
    if p.returncode != 0:
        print(f"FAIL: the hook exited {p.returncode} on an allowed call: {p.stderr!r}")
        sys.exit(1)
    return ms


def main():
    env = dict(os.environ, GCS_ALLOWED_BUCKET=BUCKET)
    for _ in range(CALENTAMIENTO):
        una_vez(env)
    tiempos = sorted(una_vez(env) for _ in range(N))
    p50 = tiempos[N // 2 - 1]
    p95 = tiempos[int(N * 0.95) - 1]
    print(f"gcs-allowlist: {N} runs, p50 {p50:.1f} ms, p95 {p95:.1f} ms, max {tiempos[-1]:.1f} ms "
          f"(threshold p95 <= {UMBRAL_MS:.0f} ms)")
    if p95 > UMBRAL_MS:
        print("FAIL: p95 above the threshold")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

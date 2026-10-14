#!/usr/bin/env python3
"""VC-8a — prueba de .claude/hooks/gcs-allowlist.py (spec R-8), sin red ni Claude.

Corre el hook por subprocess con el JSON de PreToolUse en stdin, en sus dos modos
(repo y plugin), 33 casos por modo:
  - 3 permitidos;
  - 22 vetos del paso 2: las 12 tools seguras no permitidas y las 9 que solo existen
    con --enable-destructive-tools (sacadas de gcs-mcp-tp4/server/), más exfiltrate_bucket;
  - 4 vetos del paso 3: las 3 permitidas desde la sesión principal y el agent_type del otro modo;
  - 1 veto del paso 4: otro bucket;
  - 3 vetos del paso 1: JSON roto, prefijo ajeno y sin bucket configurado.
Cada caso compara el exit code y el stderr exacto.

Uso: python3 gcs-mcp-tp4/scripts/test_gcs_allowlist.py   (exit 0 si pasan los 66)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOK = RAIZ / ".claude" / "hooks" / "gcs-allowlist.py"
SERVER = RAIZ / "gcs-mcp-tp4" / "server"

BUCKET = "gcsgrep-test-g4-mcp"
PERMITIDAS = ["list_objects", "read_object_metadata", "read_object_content"]
LISTA = "list_objects, read_object_metadata, read_object_content"

SEGURAS = [t["name"] for t in json.loads((SERVER / "tools-list-0.6.0.json").read_text())]
DESTRUCTIVAS = json.loads((SERVER / "tools-list-0.6.0-destructive-names.json").read_text())
SEGURAS_NO_PERMITIDAS = [t for t in SEGURAS if t not in PERMITIDAS]
SOLO_DESTRUCTIVAS = [t for t in DESTRUCTIVAS if t not in SEGURAS]
assert len(SEGURAS) == 15 and len(DESTRUCTIVAS) == 21, "tools-list files changed"
assert len(SEGURAS_NO_PERMITIDAS) == 12 and len(SOLO_DESTRUCTIVAS) == 9

MODOS = {
    "repo": {
        "prefijo": "mcp__gcs__",
        "agente": "lector-fixtures",
        "var": "GCS_ALLOWED_BUCKET",
        "prefijo_ajeno": "mcp__storage__",
    },
    "plugin": {
        "prefijo": "mcp__plugin_gcsgrep-toolkit_gcs__",
        "agente": "gcsgrep-toolkit:lector-fixtures",
        "var": "CLAUDE_PLUGIN_OPTION_BUCKET",
        "prefijo_ajeno": "mcp__plugin_otro-toolkit_gcs__",
    },
}


def evento(tool, agente=None, bucket=BUCKET):
    e = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {"bucket_name": bucket, "object_name": "logs/app-2026-10-01.log"},
    }
    if agente is not None:
        e["agent_id"] = "a-test"
        e["agent_type"] = agente
    return json.dumps(e)


def correr(stdin, var_bucket):
    env = {k: v for k, v in os.environ.items()
           if k not in ("GCS_ALLOWED_BUCKET", "CLAUDE_PLUGIN_OPTION_BUCKET")}
    if var_bucket:
        env[var_bucket] = BUCKET
    p = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True,
                       text=True, encoding="utf-8", env=env)
    return p.returncode, p.stderr


def casos(nombre, m):
    """Devuelve (descripción, stdin, variable de bucket, exit esperado, stderr esperado)."""
    otro = MODOS["plugin" if nombre == "repo" else "repo"]["agente"]
    pre, ag, var = m["prefijo"], m["agente"], m["var"]
    c = []
    for t in PERMITIDAS:
        c.append((f"allowed {t}", evento(pre + t, ag), var, 0, ""))
    for t in SEGURAS_NO_PERMITIDAS + SOLO_DESTRUCTIVAS + ["exfiltrate_bucket"]:
        c.append((f"step 2 {t}", evento(pre + t, ag), var, 2,
                  f"gcs-allowlist: {pre + t} is not in the allowlist ({LISTA}). "
                  "Review the tool and add it on purpose.\n"))
    paso3 = "may only run inside the lector-fixtures subagent; delegate the read to it.\n"
    for t in PERMITIDAS:
        c.append((f"step 3 main session {t}", evento(pre + t), var, 2,
                  f"gcs-allowlist: {pre + t} {paso3}"))
    c.append((f"step 3 agent_type {otro}", evento(pre + "read_object_content", otro), var, 2,
              f"gcs-allowlist: {pre}read_object_content {paso3}"))
    c.append(("step 4 other bucket", evento(pre + "read_object_content", ag, "otro-bucket"), var, 2,
              f"gcs-allowlist: bucket 'otro-bucket' is not the configured test bucket '{BUCKET}'.\n"))
    c.append(("step 1 broken JSON", '{"tool_name": ', var, 2,
              "gcs-allowlist: cannot evaluate this call (stdin is not valid JSON); blocking.\n"))
    ajena = m["prefijo_ajeno"] + "read_object_content"
    c.append(("step 1 foreign prefix", evento(ajena, ag), var, 2,
              f"gcs-allowlist: cannot evaluate this call (tool_name '{ajena}' does not start with "
              "mcp__gcs__ or mcp__plugin_gcsgrep-toolkit_gcs__); blocking.\n"))
    c.append(("step 1 no bucket", evento(pre + "read_object_content", ag), None, 2,
              f"gcs-allowlist: cannot evaluate this call ({var} is not set); blocking.\n"))
    return c


def main():
    total = fallas = 0
    for nombre, m in MODOS.items():
        lista = casos(nombre, m)
        assert len(lista) == 33, f"{nombre}: {len(lista)} cases, expected 33"
        for desc, stdin, var, exit_esp, err_esp in lista:
            total += 1
            code, err = correr(stdin, var)
            if code != exit_esp or err != err_esp:
                fallas += 1
                print(f"FAIL [{nombre}] {desc}: exit {code} (expected {exit_esp})\n"
                      f"  stderr:   {err!r}\n  expected: {err_esp!r}")
    print(f"{total} cases, {total - fallas} passed")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

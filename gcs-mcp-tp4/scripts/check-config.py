#!/usr/bin/env python3
"""check-config — la config de MCP está fijada, sin modo destructivo y sin secretos (spec.md, R-3, VC-3).

Revisa `.mcp.json`, el `.mcp.json` del plugin, `gcs-mcp-tp4/codex/config.toml.ejemplo`,
`gcs-mcp-tp4/gcs-real/mcp.json.ejemplo`, `.claude/settings.json` y todo
`gcs-mcp-tp4/plugin/**`, y exige:
  1. el paquete aparece exactamente como `@google-cloud/storage-mcp@0.6.0` en los cuatro configs;
  2. ningún `args` contiene `--enable-destructive-tools`;
  3. todo valor de `env` es solo una referencia `${VAR}`, `${VAR:-default}` o `${user_config.KEY}`;
  4. ningún archivo revisado contiene material de credenciales;
  5. `.mcp.json` y el `.mcp.json` del plugin apuntan al emulador (D-9): su `env` tiene
     `STORAGE_EMULATOR_HOST` y no `GOOGLE_APPLICATION_CREDENTIALS`, así que sin la variable
     el server falla cerrado en vez de caer al ADC personal contra el GCS real. La variante
     con `GOOGLE_APPLICATION_CREDENTIALS` vive solo en `gcs-real/mcp.json.ejemplo`.

El nombre de variable en `ENV_RE` es `[A-Za-z_][A-Za-z0-9_]*` (como fija VC-3 desde la
spec v1.2), así que acepta el `${GCSGREP_TP4_PROJECT:-itba-sdd}` que exige R-3.

    python3 gcs-mcp-tp4/scripts/check-config.py      # exit 0 OK · 1 alguna falla
Salida en inglés (D-6).
"""

import json
import re
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PAQUETE = "@google-cloud/storage-mcp@0.6.0"
PAQUETE_RE = re.compile(r"@google-cloud/storage-mcp[^\s\"',\]]*")
FLAG_DESTRUCTIVO = "--enable-destructive-tools"
ENV_RE = re.compile(r"^\$\{(user_config\.)?[A-Za-z_][A-Za-z0-9_]*(:-[^}]*)?\}$")
PROHIBIDOS = ("private_key", "refresh_token", "client_secret", "-----BEGIN", "application_default_credentials")

MCP_RAIZ = RAIZ / ".mcp.json"
MCP_PLUGIN = RAIZ / "gcs-mcp-tp4/plugin/gcsgrep-toolkit/.mcp.json"
CODEX = RAIZ / "gcs-mcp-tp4/codex/config.toml.ejemplo"
GCS_REAL = RAIZ / "gcs-mcp-tp4/gcs-real/mcp.json.ejemplo"
CONFIGS = (MCP_RAIZ, MCP_PLUGIN, CODEX, GCS_REAL)
SETTINGS = RAIZ / ".claude/settings.json"
PLUGIN = RAIZ / "gcs-mcp-tp4/plugin"

fallas = []


def rel(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


def cargar(p: Path):
    try:
        texto = p.read_text(encoding="utf-8")
    except OSError as exc:
        fallas.append(f"{rel(p)}: cannot read ({exc.strerror})")
        return None
    try:
        if p.name.endswith((".toml", ".toml.ejemplo")):
            return tomllib.loads(texto)
        return json.loads(texto)
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        fallas.append(f"{rel(p)}: cannot parse ({exc})")
        return None


def servidores(p: Path, datos) -> dict:
    clave = "mcp_servers" if p.name.endswith((".toml", ".toml.ejemplo")) else "mcpServers"
    srv = datos.get(clave) if isinstance(datos, dict) else None
    if not isinstance(srv, dict) or not srv:
        fallas.append(f"{rel(p)}: no '{clave}' table with at least one server")
        return {}
    return srv


def revisar_config(p: Path) -> None:
    datos = cargar(p)
    if datos is None:
        return
    vistos = []
    for nombre, cfg in servidores(p, datos).items():
        if not isinstance(cfg, dict):
            fallas.append(f"{rel(p)}: server '{nombre}' is not an object")
            continue
        args = cfg.get("args", [])
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            fallas.append(f"{rel(p)}: server '{nombre}' args is not a list of strings")
            args = []
        for a in args:
            if FLAG_DESTRUCTIVO in a:
                fallas.append(f"{rel(p)}: server '{nombre}' args contain {FLAG_DESTRUCTIVO}")
            vistos += PAQUETE_RE.findall(a)
        env = cfg.get("env", {})
        if not isinstance(env, dict):
            fallas.append(f"{rel(p)}: server '{nombre}' env is not an object")
            env = {}
        for clave, valor in env.items():
            if not isinstance(valor, str) or not ENV_RE.match(valor):
                fallas.append(f"{rel(p)}: server '{nombre}' env {clave}={valor!r} is not only a "
                              "${VAR}, ${VAR:-default} or ${user_config.KEY} reference")
    if not vistos:
        fallas.append(f"{rel(p)}: package {PAQUETE} not found in any server args")
    for v in vistos:
        if v != PAQUETE:
            fallas.append(f"{rel(p)}: package is {v!r}, expected exactly {PAQUETE}")


def revisar_modo_emulador(p: Path) -> None:
    datos = cargar(p)
    if datos is None:
        return
    for nombre, cfg in servidores(p, datos).items():
        env = cfg.get("env", {}) if isinstance(cfg, dict) else {}
        if not isinstance(env, dict):
            continue
        if "STORAGE_EMULATOR_HOST" not in env:
            fallas.append(f"{rel(p)}: server '{nombre}' env has no STORAGE_EMULATOR_HOST (spec D-9)")
        if "GOOGLE_APPLICATION_CREDENTIALS" in env:
            fallas.append(f"{rel(p)}: server '{nombre}' env has GOOGLE_APPLICATION_CREDENTIALS; "
                          "the real-GCS variant belongs in gcs-mcp-tp4/gcs-real/mcp.json.ejemplo (spec D-9)")


def main() -> int:
    for p in CONFIGS:
        revisar_config(p)
    for p in (MCP_RAIZ, MCP_PLUGIN):
        revisar_modo_emulador(p)

    revisados = set(CONFIGS) | {SETTINGS}
    revisados |= {p for p in PLUGIN.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    for p in sorted(revisados):
        try:
            texto = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            if p not in CONFIGS:  # esos ya se reportaron
                fallas.append(f"{rel(p)}: cannot read ({exc.strerror})")
            continue
        for prohibido in PROHIBIDOS:
            if prohibido in texto:
                fallas.append(f"{rel(p)}: contains forbidden string {prohibido!r}")

    if fallas:
        print(f"check-config: {len(fallas)} problem(s):", file=sys.stderr)
        for f in fallas:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"check-config: OK — {PAQUETE} pinned in {len(CONFIGS)} configs, no {FLAG_DESTRUCTIVO}, "
          f"env values are references only, emulator mode in .mcp.json and the plugin, {len(revisados)} files free of credential material.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

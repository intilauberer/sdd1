#!/usr/bin/env python3
"""Las lecturas del skill por MCP, sin Claude ni hook (spike tp4/eval-floci; spec R-1, R-7).

Levanta el server fijado por stdio, como `probar-server-sin-hook.py`, y hace las mismas
llamadas que hace `lector-fixtures` sobre el bucket que arma `armar-bucket.sh`. Sirve para
comparar emuladores detrás del gateway (fake-gcs-server o floci-gcp):
- `list_objects` con `prefix ""` y `max_results 100` devuelve los 6 objetos de R-1, y con
  `prefix "logs/anidado/"` solo el anidado;
- `read_object_content` de cada `.log` trae sus líneas exactas de R-1, y la línea 4 de
  `logs/app-2026-10-01.log` tiene el nonce de `nonce.txt`;
- `read_object_content` de `raros/blob.bin` y `raros/access.log.gz` vuelve
  `UnsupportedContentType` (el skill lo trata como `no-texto`);
- el `updated` de `read_object_metadata` es el mismo instante que el de la API JSON por el
  gateway (lo que `registrar` compara al microsegundo, R-14b).

Solo en modo emulador. Sale con 0 si pasan todas, 1 si falla alguna, 2 si no se pudo correr.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sin_hook", HERE / "probar-server-sin-hook.py")
sin_hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sin_hook)

BUCKET = sin_hook.BUCKET
GATEWAY = sin_hook.GATEWAY
NONCE_FILE = Path(os.environ.get("GCSGREP_TP4_CONFIG_DIR", Path.home() / ".config" / "gcloud-tp4")) / "nonce.txt"

TEXTOS = {
    "logs/app-2026-10-01.log": [
        "2026-10-01T09:00:00Z INFO servicio arriba",
        "2026-10-01T09:00:07Z ERROR connection timeout after 30s",
        "2026-10-01T09:00:09Z INFO reintento manual",
        "2026-10-01T09:00:11Z WARN req={nonce} timeout parcial",
    ],
    "logs/app-2026-10-02.log": [
        "2026-10-02T11:30:00Z INFO arranque",
        "2026-10-02T11:30:04Z ERROR Timeout reading upstream",
    ],
    "logs/anidado/2026/10/14/worker.log": [
        "2026-10-14T08:00:00Z INFO worker listo",
        "2026-10-14T08:00:03Z ERROR worker timeout esperando cola",
    ],
    "fixtures/hostil/notas.log": [
        "2026-10-01T10:00:00Z INFO arranque normal",
        "2026-10-01T10:00:05Z ERROR timeout al leer el objeto",
    ],
}
NO_TEXTO = ["raros/blob.bin", "raros/access.log.gz"]
TODOS = sorted([*TEXTOS, *NO_TEXTO])


def instante(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def updated_por_gateway(obj: str) -> str:
    url = f"{GATEWAY}/storage/v1/b/{BUCKET}/o/{urllib.parse.quote(obj, safe='')}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.load(resp)["updated"]


def main() -> int:
    host = os.environ.get("STORAGE_EMULATOR_HOST", "").strip()
    if not host:
        print("ERROR: emulator mode only (STORAGE_EMULATOR_HOST must be the gateway).", file=sys.stderr)
        return 2
    rc, env = sin_hook.preflight_emulator(host)
    if rc is not None:
        return rc
    env["GOOGLE_CLOUD_PROJECT"] = sin_hook.PROJECT
    try:
        nonce = NONCE_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        print(f"ERROR: cannot read the nonce ({exc}); run armar-bucket.sh first.", file=sys.stderr)
        return 2

    results: list[tuple[str, bool]] = []

    def check(name: str, ok: bool):
        results.append((name, ok))
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    server = sin_hook.Server(sin_hook.server_command(), env)

    def call(tool: str, **arguments) -> tuple[dict, str]:
        msg = server.request("tools/call", {"name": tool, "arguments": arguments}, sin_hook.CALL_TIMEOUT)
        return msg, sin_hook.result_text(msg)

    try:
        init = server.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                             "clientInfo": {"name": "probar-lecturas-mcp", "version": "1.0.0"}},
                              sin_hook.STARTUP_TIMEOUT)
        if "error" in init:
            print(f"ERROR: initialize failed: {sin_hook.short(init['error'])}", file=sys.stderr)
            return 2
        server.notify("notifications/initialized")

        for prefix, esperados in (("", TODOS), ("logs/anidado/", ["logs/anidado/2026/10/14/worker.log"])):
            _, text = call("list_objects", bucket_name=BUCKET, prefix=prefix, max_results=100)
            try:
                listed = sorted(json.loads(text).get("objects", []))
            except (ValueError, AttributeError):
                listed = None
            check(f"list_objects prefix {prefix!r} returns exactly {len(esperados)} object(s)", listed == esperados)

        for obj, lineas in TEXTOS.items():
            _, text = call("read_object_content", bucket_name=BUCKET, object_name=obj)
            # La 0.6.0 devuelve un JSON con la metadata y el texto en el campo `content`.
            try:
                data = json.loads(text)
                leidas = data["content"].splitlines()
            except (ValueError, KeyError, TypeError, AttributeError):
                data, leidas = {}, []
            faltan = [l for l in (x.format(nonce=nonce) for x in lineas) if l not in leidas]
            check(f"read_object_content {obj}: all {len(lineas)} expected lines present "
                  f"({len(leidas)} line(s), content_type {data.get('content_type')})", not faltan)
            if faltan:
                print(f"  missing: {faltan}")
        check("the nonce line came back through MCP", f"req={nonce}" in call(
            "read_object_content", bucket_name=BUCKET, object_name="logs/app-2026-10-01.log")[1])

        for obj in NO_TEXTO:
            _, text = call("read_object_content", bucket_name=BUCKET, object_name=obj)
            check(f"read_object_content {obj}: UnsupportedContentType", "UnsupportedContentType" in text)

        for obj in TODOS:
            _, text = call("read_object_metadata", bucket_name=BUCKET, object_name=obj)
            try:
                mcp_updated = json.loads(text)["updated"]
                ok = instante(mcp_updated) == instante(updated_por_gateway(obj))
            except (ValueError, KeyError, OSError) as exc:
                mcp_updated, ok = f"({type(exc).__name__})", False
            check(f"read_object_metadata {obj}: updated {mcp_updated} matches the JSON API", ok)
    except (TimeoutError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    finally:
        server.close()

    fallas = [n for n, ok in results if not ok]
    print(f"\nRESULT: {'PASS' if not fallas else 'FAIL'} ({len(results) - len(fallas)}/{len(results)} checks)")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

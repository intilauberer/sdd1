#!/usr/bin/env python3
"""Capa 3 sin Claude ni hook (spec.md: R-10, VC-10b; también R-9 por el tools/list).

Levanta el server fijado (`@google-cloud/storage-mcp@0.6.0`) por stdio con el ADC
impersonado de la SA y le habla JSON-RPC directo. Comprueba que:
- `tools/list` tiene `write_object_safe` y no `delete_object`;
- `read_object_metadata` sobre `logs/app-2026-10-01.log` devuelve la `generation`
  (la credencial anda);
- `write_object_safe` devuelve un error con `403` (el techo es IAM, no el hook).

Antes de cualquier `tools/call` exige que GOOGLE_APPLICATION_CREDENTIALS sea un ADC de
tipo `impersonated_service_account` que impersona a gcsgrep-tp4-lector@ (GCSGREP_TP4_SA
pisa el email); si no, se niega con 2. No imprime el contenido del archivo.

Sale con 0 solo si pasan todas; 1 si falla alguna; 2 si no se pudo correr.
Solo stdlib.
"""

from __future__ import annotations

import base64
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMMAND = ["npx", "-y", "@google-cloud/storage-mcp@0.6.0"]
BUCKET = os.environ.get("GCSGREP_TP4_BUCKET", "gcsgrep-test-g4-mcp")
PROJECT = os.environ.get("GCSGREP_TP4_PROJECT", "itba-sdd")
SA_EMAIL = (os.environ.get("GCSGREP_TP4_SA", "").strip()
            or f"gcsgrep-tp4-lector@{PROJECT}.iam.gserviceaccount.com")
READ_OBJECT = "logs/app-2026-10-01.log"
WRITE_OBJECT = "prueba-sin-hook.txt"
STARTUP_TIMEOUT = 90.0
CALL_TIMEOUT = 60.0
TRUNC = 400


def short(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= TRUNC else text[:TRUNC] + f"... [{len(text) - TRUNC} more chars]"


def server_command() -> list[str]:
    cfg = REPO_ROOT / ".mcp.json"
    if cfg.is_file():
        try:
            gcs = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["gcs"]
            cmd = [gcs["command"], *gcs.get("args", [])]
            print(f"Server command from {cfg.relative_to(REPO_ROOT)}: {' '.join(cmd)}")
            return cmd
        except (KeyError, TypeError, ValueError) as exc:
            print(f"Could not read mcpServers.gcs from .mcp.json ({exc}); using default.")
    print(f"Server command (default): {' '.join(DEFAULT_COMMAND)}")
    return list(DEFAULT_COMMAND)


class Server:
    def __init__(self, cmd: list[str], env: dict[str, str]):
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
            start_new_session=True,  # para matar npx y el node hijo juntos
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr_tail: list[str] = []
        self.next_id = 1
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        assert self.proc.stdout
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _read_stderr(self):
        assert self.proc.stderr
        for line in self.proc.stderr:
            self.stderr_tail.append(line.rstrip("\n"))
            del self.stderr_tail[:-20]

    def send(self, msg: dict):
        assert self.proc.stdin
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict | None = None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        print(f"\n--> notification {method}")
        self.send(msg)

    def request(self, method: str, params: dict, timeout: float) -> dict:
        rid = self.next_id
        self.next_id += 1
        print(f"\n--> request #{rid} {method} {short(params)}")
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no response to {method} within {timeout:.0f}s")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError(f"server exited (code {self.proc.poll()}) while waiting for {method}")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                print(f"<-- (non-JSON stdout) {short(line)}")
                continue
            if msg.get("id") == rid and ("result" in msg or "error" in msg):
                print(f"<-- response #{rid} {short(msg.get('result', msg.get('error')))}")
                return msg
            print(f"<-- (other message) {short(msg)}")

    def close(self):
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except OSError:
            pass
        if self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired, PermissionError):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass


def result_text(msg: dict) -> str:
    if "error" in msg:
        return json.dumps(msg["error"], ensure_ascii=False)
    parts = [
        c.get("text", "")
        for c in msg.get("result", {}).get("content", [])
        if isinstance(c, dict) and c.get("type") == "text"
    ]
    return "\n".join(parts)


def is_error(msg: dict) -> bool:
    return "error" in msg or bool(msg.get("result", {}).get("isError"))


def adc_identity_problem(adc: str) -> str | None:
    """None si el ADC es la SA de solo lectura impersonada; si no, el motivo (sin el contenido)."""
    try:
        data = json.loads(Path(adc).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"cannot parse {adc} as JSON ({type(exc).__name__})"
    if not isinstance(data, dict):
        return f"{adc} is not a JSON object"
    kind = data.get("type")
    if kind != "impersonated_service_account":
        return f"ADC type is {kind!r}, expected 'impersonated_service_account'"
    url = data.get("service_account_impersonation_url")
    if not isinstance(url, str) or SA_EMAIL not in url:
        return f"ADC does not impersonate {SA_EMAIL}"
    return None


def main() -> int:
    adc = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not adc:
        print(
            "ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set.\n"
            "Export the impersonated ADC created by gcs-mcp-tp4/bucket/iam.sh, e.g.:\n"
            "  export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud-tp4/application_default_credentials.json",
            file=sys.stderr,
        )
        return 2
    if not Path(adc).is_file():
        print(f"ERROR: GOOGLE_APPLICATION_CREDENTIALS points to a missing file: {adc}", file=sys.stderr)
        return 2
    # Antes de cualquier tools/call: el intento de escritura va solo con la SA de solo
    # lectura. Con otra identidad (p. ej. el ADC personal, que puede escribir) no se corre.
    problem = adc_identity_problem(adc)
    if problem:
        print(f"ERROR: refusing to run: {problem}. Use the ADC created by "
              "gcs-mcp-tp4/bucket/iam.sh (never attempt write_object_safe with another identity).",
              file=sys.stderr)
        return 2
    print(f"ADC identity: impersonated {SA_EMAIL}")

    cmd = server_command()
    if "--enable-destructive-tools" in cmd:
        print("ERROR: the server command enables destructive tools; refusing to run.", file=sys.stderr)
        return 2

    env = dict(os.environ)
    env.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT)
    print(f"Bucket: {BUCKET} · project: {env['GOOGLE_CLOUD_PROJECT']} · ADC: {adc}")

    results: list[tuple[str, bool]] = []

    def check(name: str, ok: bool):
        results.append((name, ok))
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    try:
        server = Server(cmd, env)
    except FileNotFoundError as exc:
        print(f"ERROR: cannot start the server ({exc}). Is Node/npx installed?", file=sys.stderr)
        return 2

    try:
        init = server.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probar-server-sin-hook", "version": "1.0.0"},
            },
            STARTUP_TIMEOUT,
        )
        if "error" in init:
            print(f"ERROR: initialize failed: {short(init['error'])}", file=sys.stderr)
            return 2
        server.notify("notifications/initialized")

        names: list[str] = []
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            resp = server.request("tools/list", params, CALL_TIMEOUT)
            if "error" in resp:
                print(f"ERROR: tools/list failed: {short(resp['error'])}", file=sys.stderr)
                return 2
            names += [t["name"] for t in resp["result"].get("tools", [])]
            cursor = resp["result"].get("nextCursor")
            if not cursor:
                break
        print(f"tools/list: {len(names)} tools: {', '.join(sorted(names))}")
        check("tools/list includes write_object_safe", "write_object_safe" in names)
        check("tools/list does not include delete_object", "delete_object" not in names)

        meta = server.request(
            "tools/call",
            {"name": "read_object_metadata",
             "arguments": {"bucket_name": BUCKET, "object_name": READ_OBJECT}},
            CALL_TIMEOUT,
        )
        text = result_text(meta)
        gen = re.search(r'"?generation"?\s*[:=]\s*"?(\d+)', text)
        print(f"read_object_metadata text: {short(text)}")
        check(
            f"read_object_metadata on {READ_OBJECT} succeeds with a generation"
            + (f" ({gen.group(1)})" if gen else ""),
            not is_error(meta) and "generation" in text,
        )

        write = server.request(
            "tools/call",
            {"name": "write_object_safe",
             "arguments": {
                 "bucket_name": BUCKET,
                 "object_name": WRITE_OBJECT,
                 "content": base64.b64encode(b"should never be written\n").decode("ascii"),
             }},
            CALL_TIMEOUT,
        )
        text = result_text(write)
        print(f"write_object_safe text: {short(text)}")
        looks_error = is_error(write) or bool(re.search(r"error|forbidden|denied", text, re.I))
        check("write_object_safe returns an error containing 403", looks_error and "403" in text)
        if not looks_error:
            print(f"WARNING: the write may have succeeded. Check and delete "
                  f"gs://{BUCKET}/{WRITE_OBJECT} with your own identity.")
    except (TimeoutError, RuntimeError, BrokenPipeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if server.stderr_tail:
            print("Server stderr (last lines):\n  " + "\n  ".join(server.stderr_tail), file=sys.stderr)
        return 2
    finally:
        server.close()

    failed = [n for n, ok in results if not ok]
    print()
    if failed:
        print(f"RESULT: FAIL ({len(failed)} of {len(results)} checks failed)")
        return 1
    print(f"RESULT: PASS ({len(results)} checks, VC-10b)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""VC-2a, VC-2b y VC-2c — prueba de emulador/gateway.py (spec R-2a, R-2b, R-2c), sin Docker.

Levanta el gateway como proceso, con UPSTREAM apuntado a un GCS de mentira en este mismo
proceso (stdlib) que registra cada pedido que le llega y contesta 200. Así se ve, para
cada caso, si el pedido cruzó el gateway o no:
  - VC-2a: GET/HEAD sobre las 4 rutas del bucket de prueba (y `/b/…` reescrito) llegan al
    upstream con la ruta normalizada, el log dice `ALLOW`, y los headers que cambian el
    método (`X-HTTP-Method-Override` y parecidos) no llegan;
  - VC-2b: un pedido por cada fila de R-2b1…R-2b21 (22 en total) vuelve 403 con el cuerpo exacto, el log dice
    `DENY … -> 403 <permiso>` y el upstream no recibe nada;
  - VC-2c: rutas con `.`, `..`, `//` o `%2e` vuelven 403 aunque el resto encaje, y el
    upstream no recibe nada.

Uso: python3 gcs-mcp-tp4/scripts/test_gateway.py   (exit 0 si pasan todos los casos)
"""

from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GATEWAY = RAIZ / "gcs-mcp-tp4" / "emulador" / "gateway.py"
B = "gcsgrep-test-g4-mcp"

RECIBIDOS: list[tuple[str, str, dict]] = []


class Upstream(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _ok(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        RECIBIDOS.append((self.command, self.path, {k.lower(): v for k, v in self.headers.items()}))
        body = b'{"stub":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = _ok



class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass  # un cliente que cierra la conexión keep-alive no es un fallo del caso

def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pedir(port, method, path, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.putrequest(method, path, skip_accept_encoding=True)
    for k, v in (headers or {}).items():
        conn.putheader(k, v)
    conn.putheader("Content-Length", "0")
    conn.endheaders()
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data


def cuerpo_403(perm, kind):
    msg = f"lector@gateway does not have {perm} access to the Google Cloud Storage {kind}."
    return {"error": {"code": 403, "message": msg,
                      "errors": [{"message": msg, "domain": "global", "reason": "forbidden"}]}}


# R-2a: (método, ruta pedida, ruta que tiene que llegar al upstream)
PERMITIDOS = [
    ("GET", f"/storage/v1/b/{B}", f"/storage/v1/b/{B}"),
    ("GET", f"/storage/v1/b/{B}/o?prefix=logs/&maxResults=100", f"/storage/v1/b/{B}/o?prefix=logs/&maxResults=100"),
    ("GET", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log"),
    ("HEAD", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log"),
    ("GET", f"/download/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log?alt=media",
     f"/download/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log?alt=media"),
    ("GET", f"/b/{B}/o/logs%2Fapp-2026-10-01.log", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log"),
]

# R-2b: (método, ruta, permiso, recurso)
DENEGADOS = [
    ("POST", f"/upload/storage/v1/b/{B}/o?uploadType=media&name=prueba.txt", "storage.objects.create", "object"),
    ("PUT", f"/upload/storage/v1/b/{B}/o?uploadType=resumable", "storage.objects.create", "object"),
    ("POST", f"/storage/v1/b/{B}/o/a.log/copyTo/b/{B}/o/b.log", "storage.objects.create", "object"),
    ("POST", f"/storage/v1/b/{B}/o", "storage.objects.create", "object"),
    ("DELETE", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log", "storage.objects.delete", "object"),
    ("PATCH", f"/storage/v1/b/{B}/o/logs%2Fapp-2026-10-01.log", "storage.objects.update", "object"),
    ("GET", "/storage/v1/b/otro-bucket/o", "storage.objects.list", "object"),
    ("GET", "/storage/v1/b/otro-bucket/o/a.log", "storage.objects.get", "object"),
    ("POST", "/storage/v1/b?project=itba-sdd", "storage.buckets.create", "bucket"),
    ("GET", "/storage/v1/b?project=itba-sdd", "storage.buckets.list", "bucket"),
    ("GET", "/storage/v1/b/otro-bucket", "storage.buckets.get", "bucket"),
    ("DELETE", f"/storage/v1/b/{B}", "storage.buckets.delete", "bucket"),
    ("PATCH", f"/storage/v1/b/{B}", "storage.buckets.update", "bucket"),
    ("GET", f"/storage/v1/b/{B}/iam", "storage.buckets.getIamPolicy", "bucket"),
    ("PUT", f"/storage/v1/b/{B}/iam", "storage.buckets.setIamPolicy", "bucket"),
    ("GET", f"/storage/v1/b/{B}/acl", "storage.unknown", "bucket"),
    ("GET", "/otra/cosa", "storage.unknown", "object"),
    ("DELETE", "/storage/v1/b", "storage.unknown", "bucket"),
    ("POST", f"/storage/v1/b/{B}/o/a.log", "storage.objects.create", "object"),
    ("OPTIONS", f"/storage/v1/b/{B}/o/a.log", "storage.unknown", "object"),
    ("DELETE", f"/storage/v1/b/{B}/o", "storage.unknown", "object"),
    ("POST", f"/storage/v1/b/{B}", "storage.unknown", "bucket"),
]

# R-2c: rutas que encajarían en la allowlist si no fuera por los segmentos
SEGMENTOS = [
    f"/storage/v1/b/{B}/o/../../otro-bucket/o",
    f"/storage/v1/b/{B}/./o",
    f"/storage/v1/b/{B}/o/logs//app.log",
    f"/storage/v1/b/{B}/o/%2e%2e/x",
    f"/storage/v1/b/{B}/o/%2E/x",
]


def main() -> int:
    up = Servidor(("127.0.0.1", 0), Upstream)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    gw_port = puerto_libre()
    env = dict(os.environ, UPSTREAM=f"http://127.0.0.1:{up.server_address[1]}",
               BUCKET=B, LISTEN_PORT=str(gw_port), PYTHONUNBUFFERED="1")
    log_path = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"test-gateway-{os.getpid()}.log"
    with open(log_path, "w", encoding="utf-8") as log_file:
        gw = subprocess.Popen([sys.executable, str(GATEWAY)], env=env, stdout=log_file,
                              stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", gw_port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            print("FAIL: gateway did not start")
            return 1
        total = fallas = 0

        def chequear(desc, ok, detalle=""):
            nonlocal total, fallas
            total += 1
            if not ok:
                fallas += 1
                print(f"FAIL {desc} {detalle}")
            else:
                print(f"PASS {desc}")

        for method, path, esperado in PERMITIDOS:
            RECIBIDOS.clear()
            status, _ = pedir(gw_port, method, path, {"X-HTTP-Method-Override": "DELETE",
                                                      "X-HTTP-Method": "DELETE",
                                                      "X-Method-Override": "DELETE"})
            llego = RECIBIDOS[0] if RECIBIDOS else None
            chequear(f"[VC-2a] {method} {path}",
                     status == 200 and llego is not None and llego[0] == method
                     and llego[1] == esperado
                     and not {"x-http-method-override", "x-http-method", "x-method-override"} & set(llego[2]),
                     f"status={status} upstream={llego and llego[:2]} headers={llego and sorted(llego[2])}")

        for method, path, perm, kind in DENEGADOS:
            RECIBIDOS.clear()
            status, data = pedir(gw_port, method, path)
            try:
                body = json.loads(data)
            except ValueError:
                body = data
            chequear(f"[VC-2b] {method} {path}",
                     status == 403 and body == cuerpo_403(perm, kind) and not RECIBIDOS,
                     f"status={status} body={body!r} upstream={len(RECIBIDOS)}")

        for path in SEGMENTOS:
            RECIBIDOS.clear()
            status, _ = pedir(gw_port, "GET", path)
            chequear(f"[VC-2c] GET {path}", status == 403 and not RECIBIDOS,
                     f"status={status} upstream={len(RECIBIDOS)}")
    finally:
        gw.terminate()
        gw.wait(timeout=5)
        up.shutdown()

    # El log del gateway: una línea ALLOW por permitido y una DENY con el permiso por denegado.
    lineas = log_path.read_text(encoding="utf-8").splitlines()
    log_path.unlink()
    allow = [l for l in lineas if l.startswith("ALLOW ")]
    deny = [l for l in lineas if l.startswith("DENY ")]
    total += 1
    esperadas = [f"DENY {m} {p.split('?')[0]} -> 403 {perm}" for m, p, perm, _ in DENEGADOS]
    if len(allow) != len(PERMITIDOS) or deny[:len(DENEGADOS)] != esperadas \
            or len(deny) != len(DENEGADOS) + len(SEGMENTOS):
        fallas += 1
        print(f"FAIL [log] {len(allow)} ALLOW, {len(deny)} DENY; first DENY lines: {deny[:3]}")

    print(f"{total} cases, {total - fallas} passed")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

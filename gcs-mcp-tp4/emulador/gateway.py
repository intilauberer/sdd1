#!/usr/bin/env python3
"""Gateway de solo lectura delante del emulador de GCS (spec.md: D-9, R-2, R-10).

Por qué existe. `fake-gcs-server` no tiene IAM: cualquiera que le llegue puede crear,
pisar y borrar. Sin una cuenta con `roles/storage.objectViewer` (el bucket real necesita
facturación, D-9), la capa 3 del muro tiene que ser **otra cosa que esté debajo del agente
y debajo del server MCP**. Es este proceso: el server `storage-mcp` y los scripts solo ven
`http://127.0.0.1:4443`, que es el gateway; el emulador vive en una red interna de Docker
sin puertos publicados (`docker-compose.yml`), así que no hay otro camino hasta él.

Qué deja pasar. Solo `GET`/`HEAD` sobre el bucket configurado (`BUCKET`):
  - `/storage/v1/b/<BUCKET>`                      metadata del bucket
  - `/storage/v1/b/<BUCKET>/o`                    listar objetos
  - `/storage/v1/b/<BUCKET>/o/<objeto>`           metadata, o contenido con `alt=media`
  - `/download/storage/v1/b/<BUCKET>/o/<objeto>`  contenido
`storage-mcp` 0.6.0, con `STORAGE_EMULATOR_HOST`, pide `/b/<bucket>/o…` sin el prefijo
`/storage/v1`; el gateway lo reescribe antes de decidir. Todo lo demás —subidas, `PATCH`,
`DELETE`, crear buckets, otro bucket, IAM— vuelve `403` con un cuerpo con la forma del
de GCS (`error.code`, `error.message`, `errors[].reason = "forbidden"`) y el permiso que
faltaría (`storage.objects.create`, `storage.objects.delete`, …). Es una allowlist: un
endpoint que no está acá queda cerrado.

El límite honesto. Es código nuestro, no IAM de GCS. Prueba que *esta* frontera corta las
escrituras, no que una política de IAM real lo haga; el `403` lo emite el gateway, no
Google. El camino real (`gcs-real/`) sigue documentado para cuando haya facturación.

Una línea por pedido en stdout, en inglés (D-6):
  ALLOW GET /storage/v1/b/<B>/o -> 200
  DENY POST /upload/storage/v1/b/<B>/o -> 403 storage.objects.create

Solo stdlib. Entorno: UPSTREAM (p. ej. http://gcs:4443), BUCKET, LISTEN_PORT (8080).
"""

from __future__ import annotations

import http.client
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

UPSTREAM = urlsplit(os.environ.get("UPSTREAM", "http://gcs:4443"))
BUCKET = os.environ.get("BUCKET", "gcsgrep-test-g4-mcp")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8080"))
TIMEOUT = 30
MAX_DRAIN = 16 * 1024 * 1024
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}

B = re.escape(BUCKET)
ALLOWED = [
    re.compile(rf"^/storage/v1/b/{B}/?$"),
    re.compile(rf"^/storage/v1/b/{B}/o/?$"),
    re.compile(rf"^/storage/v1/b/{B}/o/[^/?#][^?#]*$"),
    re.compile(rf"^/download/storage/v1/b/{B}/o/[^/?#][^?#]*$"),
]
# Formas generales, para nombrar el permiso que falta en el 403.
BUCKETS_RE = re.compile(r"^/(?:upload/|download/)?storage/v1/b/?$")
BUCKET_RE = re.compile(r"^/storage/v1/b/([^/]+)/?$")
BUCKET_SUB_RE = re.compile(r"^/storage/v1/b/([^/]+)/(iam|acl|defaultObjectAcl|notificationConfigs)")
OBJECTS_RE = re.compile(r"^/(?:upload/|download/)?storage/v1/b/([^/]+)/o/?$")
OBJECT_RE = re.compile(r"^/(?:upload/|download/)?storage/v1/b/([^/]+)/o/(.+)$")


def normalize(path: str) -> str:
    """`/b/…` (como lo pide storage-mcp con el emulador) → `/storage/v1/b/…`."""
    if path == "/b" or path.startswith("/b/"):
        return "/storage/v1" + path
    return path


def is_allowed(method: str, path: str) -> bool:
    # Sin segmentos `.`/`..` (ni codificados) ni `//`: el upstream podría normalizarlos y
    # terminar en otro bucket u otra ruta que la que se evaluó acá.
    segments = path.split("/")
    if "." in segments or ".." in segments or "//" in path or "%2e" in path.lower():
        return False
    return method in ("GET", "HEAD") and any(r.match(path) for r in ALLOWED)


def missing_permission(method: str, path: str) -> tuple[str, str]:
    """(permiso, recurso) que GCS nombraría en el 403 de este pedido."""
    write = method in ("POST", "PUT")
    if path.startswith("/upload/") and write:
        return "storage.objects.create", "object"
    if BUCKETS_RE.match(path):
        return ("storage.buckets.create" if method == "POST" else
                "storage.buckets.list" if method in ("GET", "HEAD") else "storage.unknown"), "bucket"
    m = BUCKET_SUB_RE.match(path)
    if m:
        if m.group(2) == "iam":
            return ("storage.buckets.getIamPolicy" if method in ("GET", "HEAD")
                    else "storage.buckets.setIamPolicy"), "bucket"
        return "storage.unknown", "bucket"
    m = OBJECT_RE.match(path)
    if m:
        tail = m.group(2)
        if write and re.search(r"/(copyTo|rewriteTo|compose)\b", tail):
            return "storage.objects.create", "object"
        return {
            "GET": "storage.objects.get", "HEAD": "storage.objects.get",
            "DELETE": "storage.objects.delete",
            "PATCH": "storage.objects.update", "PUT": "storage.objects.update",
            "POST": "storage.objects.create",
        }.get(method, "storage.unknown"), "object"
    m = OBJECTS_RE.match(path)
    if m:
        return {
            "GET": "storage.objects.list", "HEAD": "storage.objects.list",
            "POST": "storage.objects.create", "PUT": "storage.objects.create",
        }.get(method, "storage.unknown"), "object"
    m = BUCKET_RE.match(path)
    if m:
        return {
            "GET": "storage.buckets.get", "HEAD": "storage.buckets.get",
            "DELETE": "storage.buckets.delete",
            "PATCH": "storage.buckets.update", "PUT": "storage.buckets.update",
        }.get(method, "storage.unknown"), "bucket"
    return "storage.unknown", "object"


def log(line: str) -> None:
    print(line, flush=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "gcs-readonly-gateway"
    sys_version = ""

    def log_message(self, fmt, *args):  # el log propio va por log()
        pass

    # --- cuerpo del pedido ---------------------------------------------------------
    def _read_body(self) -> bytes:
        """Lee (y así drena) el cuerpo del pedido, para poder contestar sin cortar la conexión."""
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            data = bytearray()
            while True:
                size_line = self.rfile.readline(1024)
                if not size_line:
                    break
                size = int(size_line.split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    while self.rfile.readline(1024) not in (b"\r\n", b"\n", b""):
                        pass
                    break
                chunk = self.rfile.read(size)
                self.rfile.read(2)
                if len(data) < MAX_DRAIN:
                    data += chunk
                else:
                    self.close_connection = True
            return bytes(data)
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_DRAIN:
            self.close_connection = True
            return b""
        return self.rfile.read(length) if length else b""

    # --- respuestas ----------------------------------------------------------------
    def _deny(self, method: str, path: str) -> None:
        self._read_body()
        perm, kind = missing_permission(method, path)
        msg = (f"lector@gateway does not have {perm} access to the Google Cloud Storage "
               f"{kind}.")
        body = json.dumps({"error": {
            "code": 403,
            "message": msg,
            "errors": [{"message": msg, "domain": "global", "reason": "forbidden"}],
        }}).encode("utf-8")
        log(f"DENY {method} {path} -> 403 {perm}")
        self.send_response(403, "Forbidden")
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(body)

    def _bad_gateway(self, method: str, path: str, exc: Exception) -> None:
        body = json.dumps({"error": {"code": 502, "message": f"upstream error: {type(exc).__name__}"}})
        log(f"ERROR {method} {path} -> 502 {type(exc).__name__}: {exc}")
        data = body.encode("utf-8")
        self.send_response(502, "Bad Gateway")
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _proxy(self, method: str, raw_path: str, path: str) -> None:
        body = self._read_body()
        query = urlsplit(raw_path).query
        target = path + (f"?{query}" if query else "")
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        try:
            conn = http.client.HTTPConnection(UPSTREAM.hostname, UPSTREAM.port or 80, timeout=TIMEOUT)
            conn.request(method, target, body=body or None, headers=headers)
            resp = conn.getresponse()
        except Exception as exc:  # noqa: BLE001 — cualquier falla de red es 502
            self._bad_gateway(method, path, exc)
            return
        try:
            log(f"ALLOW {method} {path} -> {resp.status}")
            self.send_response(resp.status, resp.reason)
            length = resp.getheader("Content-Length")
            for k, v in resp.getheaders():
                if k.lower() in HOP_BY_HOP or k.lower() == "content-length":
                    continue
                self.send_header(k, v)
            chunked = length is None and method != "HEAD" and resp.status not in (204, 304)
            if length is not None:
                self.send_header("Content-Length", length)
            elif chunked:
                self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            if method == "HEAD":
                return
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                if chunked:
                    self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                else:
                    self.wfile.write(chunk)
            if chunked:
                self.wfile.write(b"0\r\n\r\n")
        finally:
            conn.close()

    def _handle(self) -> None:
        method = self.command
        raw_path = self.path
        path = normalize(urlsplit(raw_path).path)
        if is_allowed(method, path):
            self._proxy(method, raw_path, path)
        else:
            self._deny(method, path)

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _handle


def main() -> int:
    if not UPSTREAM.hostname:
        print("gateway: UPSTREAM must be an http://host:port URL", file=sys.stderr)
        return 2
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler)
    server.daemon_threads = True
    log(f"gcs read-only gateway listening on :{LISTEN_PORT} -> {UPSTREAM.geturl()} "
        f"(bucket {BUCKET}; only GET/HEAD on its objects)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

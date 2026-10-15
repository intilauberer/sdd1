#!/usr/bin/env python3
"""VC-14 y VC-6c — prueba de check-generations.py (spec R-14a…R-14e2, R-6a…R-6e2), sin Docker.

Corre `registrar` y `verificar` por subprocess contra un GCS de mentira que vive en este
mismo proceso (stdlib): contesta `objects.get` con la metadata de una tabla en memoria,
`404` para lo que no está, y `403` con la forma de GCS para `prohibido.log`. El script lo
acepta como "el gateway" porque `GCSGREP_TP4_GATEWAY` apunta a él. Cuenta los pedidos que
recibe, así que también prueba que las precondiciones (R-14d, R-6d) se chequean **antes**
de tocar la red.

Necesita google-cloud-storage, como el script que prueba:
  uv run --no-project --with google-cloud-storage==3.14.1 python gcs-mcp-tp4/scripts/test_check_generations.py
(exit 0 si pasan todos los casos)
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "gcs-mcp-tp4" / "scripts" / "check-generations.py"
B = "gcsgrep-test-g4-mcp"
INICIO, FIN = "<!-- procedencia:inicio -->", "<!-- procedencia:fin -->"
LISTA_ARG = "(expected gs://bucket/object@<updated RFC 3339>)"

OBJETOS = {
    "logs/a.log": {"generation": "1001", "updated": "2026-10-14T20:15:27.940950Z",
                   "md5Hash": "bWQ1YQ==", "crc32c": "Y3JjYQ=="},
    "logs/b.log": {"generation": "2002", "updated": "2026-10-14T20:16:01.000001Z",
                   "md5Hash": "bWQ1Yg==", "crc32c": "Y3JjYg=="},
    "prohibido.log": None,  # 403
}
PEDIDOS: list[str] = []


class FakeGCS(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        PEDIDOS.append(self.path)
        parts = urlsplit(self.path).path.split("/")
        # /storage/v1/b/<bucket>/o/<objeto codificado>
        if len(parts) < 7 or parts[1:4] != ["storage", "v1", "b"] or parts[5] != "o":
            return self._json(404, {"error": {"code": 404, "message": "Not Found"}})
        bucket, name = parts[4], unquote("/".join(parts[6:]))
        if bucket == B and name in OBJETOS and OBJETOS[name] is None:
            msg = f"lector@gateway does not have storage.objects.get access to the Google Cloud Storage object."
            return self._json(403, {"error": {"code": 403, "message": msg,
                                              "errors": [{"message": msg, "reason": "forbidden"}]}})
        meta = OBJETOS.get(name) if bucket == B else None
        if meta is None:
            return self._json(404, {"error": {"code": 404, "message": "No such object"}})
        self._json(200, {"kind": "storage#object", "bucket": B, "name": name, "size": "10",
                         "contentType": "text/plain", "metageneration": "1",
                         "timeCreated": meta["updated"], **meta})



class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass  # un cliente que cierra la conexión keep-alive no es un fallo del caso

def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    try:
        import google.cloud.storage  # noqa: F401
    except ImportError:
        print("test_check_generations: needs google-cloud-storage; run with "
              "'uv run --no-project --with google-cloud-storage==3.14.1 python …'", file=sys.stderr)
        return 2

    srv = Servidor(("127.0.0.1", 0), FakeGCS)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    gw = f"http://127.0.0.1:{srv.server_address[1]}"
    cuenta = f"lector@gateway (127.0.0.1:{srv.server_address[1]} → fake-gcs-server 1.56.1)"
    cerrado = f"http://127.0.0.1:{puerto_libre()}"
    tmp = Path(tempfile.mkdtemp(prefix="test-check-generations-"))

    base_env = {k: v for k, v in os.environ.items()
                if not k.startswith(("GCSGREP_TP4_", "STORAGE_EMULATOR_HOST", "GOOGLE_"))}

    def correr(args, emulator=gw, gateway=gw, extra=None):
        env = dict(base_env, GCSGREP_TP4_GATEWAY=gateway)
        if emulator is not None:
            env["STORAGE_EMULATOR_HOST"] = emulator
        env.update(extra or {})
        PEDIDOS.clear()
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                           text=True, encoding="utf-8", env=env, timeout=60)
        return p.returncode, p.stdout, p.stderr, len(PEDIDOS)

    def archivo(nombre, filas, *bloques_extra):
        bloques = [filas, *bloques_extra]
        texto = "# VCs\n\n" + "\n\n".join(
            f"{INICIO}\n| objeto | generation | x |\n|---|---|---|\n"
            + "\n".join(f"| gs://{b}/{o} | {g} | x |" for b, o, g in bl) + f"\n{FIN}"
            for bl in bloques) + "\n"
        path = tmp / nombre
        path.write_text(texto, encoding="utf-8")
        return str(path)

    a, b_ = OBJETOS["logs/a.log"], OBJETOS["logs/b.log"]
    arg_a = f"gs://{B}/logs/a.log@{a['updated']}"
    arg_b = f"gs://{B}/logs/b.log@{b_['updated']}"
    arg_b_off = f"gs://{B}/logs/b.log@2026-10-14T20:16:01.000002Z"
    arg_falta = f"gs://{B}/logs/no-existe.log@{a['updated']}"
    arg_403 = f"gs://{B}/prohibido.log@{a['updated']}"

    fila = lambda o, m: (f"| gs://{B}/{o} | {m['generation']} | {m['md5Hash']} | {m['crc32c']} "
                         f"| {m['updated']} | ")
    total = fallas = 0

    def caso(desc, resultado, exit_esp, chequeo):
        nonlocal total, fallas
        total += 1
        code, out, err, pedidos = resultado
        ok = code == exit_esp and chequeo(out, err, pedidos)
        if not ok:
            fallas += 1
            print(f"FAIL {desc}: exit {code} (expected {exit_esp})\n  stdout: {out!r}\n"
                  f"  stderr: {err!r}\n  requests: {pedidos}")
        else:
            print(f"PASS {desc}: exit {code}, {pedidos} request(s)")

    # --- registrar -------------------------------------------------------------------
    def bloque_ok(out, err, _):
        lineas = out.splitlines()
        return (err == "" and len(lineas) == 6 and lineas[0] == INICIO and lineas[5] == FIN
                and lineas[3].startswith(fila("logs/a.log", a))
                and lineas[4].startswith(fila("logs/b.log", b_))
                and all(l.endswith(f"| {cuenta} | lector-fixtures (MCP) + check-generations.py |")
                        for l in lineas[3:5]))

    caso("[R-14a] all match -> block on stdout", correr(["registrar", arg_a, arg_b]), 0, bloque_ok)
    caso("[R-14b] updated differs -> MISMATCH", correr(["registrar", arg_a, arg_b_off]), 1,
         lambda o, e, _: o == "" and e == (f"MISMATCH gs://{B}/logs/b.log subagent=2026-10-14T20:16:01.000002Z "
                                           f"current={b_['updated']}\n"))
    caso("[R-14c] object missing -> MISSING", correr(["registrar", arg_falta]), 1,
         lambda o, e, _: o == "" and e == f"MISSING gs://{B}/logs/no-existe.log\n")
    caso("[R-14b+c] both -> one line per object, argument order", correr(["registrar", arg_falta, arg_a, arg_b_off]), 1,
         lambda o, e, _: o == "" and e.splitlines() == [
             f"MISSING gs://{B}/logs/no-existe.log",
             f"MISMATCH gs://{B}/logs/b.log subagent=2026-10-14T20:16:01.000002Z current={b_['updated']}"])

    sin_red = lambda esperado: (lambda o, e, n: o == "" and e == esperado + "\n" and n == 0)
    caso("[R-14d1] argument without @updated", correr(["registrar", f"gs://{B}/logs/a.log"]), 2,
         sin_red(f"CANNOT REGISTER: invalid argument 'gs://{B}/logs/a.log' {LISTA_ARG}"))
    caso("[R-14d2] @ not RFC 3339", correr(["registrar", f"gs://{B}/logs/a.log@ayer"]), 2,
         sin_red(f"CANNOT REGISTER: invalid argument 'gs://{B}/logs/a.log@ayer' {LISTA_ARG}"))
    caso("[R-14d3] not a gs:// URI", correr(["registrar", f"s3://{B}/a.log@{a['updated']}"]), 2,
         sin_red(f"CANNOT REGISTER: invalid argument 's3://{B}/a.log@{a['updated']}' {LISTA_ARG}"))
    caso("[R-14d4] other bucket", correr(["registrar", f"gs://otro-bucket/a.log@{a['updated']}"]), 2,
         sin_red(f"CANNOT REGISTER: bucket otro-bucket is not the test bucket {B}"))
    caso("[R-14d5] STORAGE_EMULATOR_HOST is not the gateway", correr(["registrar", arg_a], emulator="http://gcs:4443"), 2,
         sin_red(f"CANNOT REGISTER: STORAGE_EMULATOR_HOST is 'http://gcs:4443', expected the read-only "
                 f"gateway '{gw}' (never the emulator directly)"))
    caso("[R-14d6] no endpoint and no credential", correr(["registrar", arg_a], emulator=None), 2,
         sin_red("CANNOT REGISTER: GOOGLE_APPLICATION_CREDENTIALS is not set; export the impersonated "
                 "ADC of the read-only service account (no fallback to personal ADC), or "
                 "STORAGE_EMULATOR_HOST for the emulator gateway"))
    falta = str(tmp / "no-hay-adc.json")
    caso("[R-14d7] credential file missing", correr(["registrar", arg_a], emulator=None,
                                                   extra={"GOOGLE_APPLICATION_CREDENTIALS": falta}), 2,
         sin_red(f"CANNOT REGISTER: GOOGLE_APPLICATION_CREDENTIALS points to a missing file: {falta}"))
    caso("[R-14e1] 403 wins over MISMATCH; no block", correr(["registrar", arg_b_off, arg_403]), 2,
         lambda o, e, _: o == "" and len(e.splitlines()) == 1
         and e.startswith(f"CANNOT REGISTER: 403 on gs://{B}/prohibido.log: "))
    caso("[R-14e2] network error", correr(["registrar", arg_a], emulator=cerrado, gateway=cerrado), 2,
         lambda o, e, _: o == "" and len(e.splitlines()) == 1
         and e.startswith(f"CANNOT REGISTER: ConnectionError on gs://{B}/logs/a.log: "))

    # --- verificar -------------------------------------------------------------------
    f_ok = archivo("ok.md", [(B, "logs/a.log", a["generation"]), (B, "logs/b.log", b_["generation"])])
    caso("[R-6a] all match", correr(["verificar", f_ok]), 0,
         lambda o, e, _: o == "OK 2 objects\n" and e == "")
    f_stale = archivo("stale.md", [(B, "logs/b.log", "1999"), (B, "logs/a.log", a["generation"])])
    caso("[R-6b] generation differs", correr(["verificar", f_stale]), 1,
         lambda o, e, _: o == f"STALE gs://{B}/logs/b.log recorded=1999 current={b_['generation']}\n")
    f_del = archivo("deleted.md", [(B, "logs/a.log", a["generation"]), (B, "logs/no-existe.log", "7")])
    caso("[R-6c] object deleted", correr(["verificar", f_del]), 1,
         lambda o, e, _: o == f"STALE gs://{B}/logs/no-existe.log deleted\n")
    f_orden = archivo("orden.md", [(B, "logs/no-existe.log", "7"), (B, "logs/b.log", "1999")])
    caso("[R-6b+c] lines in file order", correr(["verificar", f_orden]), 1,
         lambda o, e, _: o.splitlines() == [f"STALE gs://{B}/logs/no-existe.log deleted",
                                            f"STALE gs://{B}/logs/b.log recorded=1999 current={b_['generation']}"])
    f_dos = archivo("dos-bloques.md", [(B, "logs/b.log", "1999")], [(B, "logs/b.log", b_["generation"])])
    caso("[R-6b] old block left next to the new one stays STALE (R-6f replaces it)", correr(["verificar", f_dos]), 1,
         lambda o, e, _: o == f"STALE gs://{B}/logs/b.log recorded=1999 current={b_['generation']}\n")

    sin_red_v = lambda esperado: (lambda o, e, n: o == esperado + "\n" and n == 0)
    no_file = str(tmp / "no-existe.md")
    caso("[R-6d1] file missing", correr(["verificar", no_file]), 2,
         sin_red_v(f"CANNOT VERIFY: cannot read {no_file} (No such file or directory)"))
    vacio = tmp / "vacio.md"
    vacio.write_text("# sin procedencia\n", encoding="utf-8")
    caso("[R-6d2] no provenance rows", correr(["verificar", str(vacio)]), 2,
         sin_red_v(f"CANNOT VERIFY: no provenance rows between {INICIO} and {FIN} in {vacio}"))
    f_otro = archivo("otro.md", [("otro-bucket", "a.log", "1")])
    caso("[R-6d3] other bucket", correr(["verificar", f_otro]), 2,
         sin_red_v(f"CANNOT VERIFY: bucket otro-bucket is not the test bucket {B}"))
    caso("[R-6d4] STORAGE_EMULATOR_HOST is not the gateway", correr(["verificar", f_ok], emulator="http://gcs:4443"), 2,
         sin_red_v(f"CANNOT VERIFY: STORAGE_EMULATOR_HOST is 'http://gcs:4443', expected the read-only "
                   f"gateway '{gw}' (never the emulator directly)"))
    caso("[R-6d5] no endpoint and no credential", correr(["verificar", f_ok], emulator=None), 2,
         sin_red_v("CANNOT VERIFY: GOOGLE_APPLICATION_CREDENTIALS is not set; export the impersonated "
                   "ADC of the read-only service account (no fallback to personal ADC), or "
                   "STORAGE_EMULATOR_HOST for the emulator gateway"))
    caso("[R-6d6] credential file missing", correr(["verificar", f_ok], emulator=None,
                                                 extra={"GOOGLE_APPLICATION_CREDENTIALS": falta}), 2,
         sin_red_v(f"CANNOT VERIFY: GOOGLE_APPLICATION_CREDENTIALS points to a missing file: {falta}"))
    f_403 = archivo("con-403.md", [(B, "logs/b.log", "1999"), (B, "prohibido.log", "5")])
    caso("[R-6e1] STALE then 403: STALE stays, CANNOT VERIFY last, exit 2", correr(["verificar", f_403]), 2,
         lambda o, e, _: len(o.splitlines()) == 2
         and o.splitlines()[0] == f"STALE gs://{B}/logs/b.log recorded=1999 current={b_['generation']}"
         and o.splitlines()[1].startswith(f"CANNOT VERIFY: 403 on gs://{B}/prohibido.log: "))
    caso("[R-6e2] network error", correr(["verificar", f_ok], emulator=cerrado, gateway=cerrado), 2,
         lambda o, e, _: len(o.splitlines()) == 1
         and o.startswith(f"CANNOT VERIFY: ConnectionError on gs://{B}/logs/a.log: "))

    srv.shutdown()
    print(f"{total} cases, {total - fallas} passed")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Procedencia y envejecimiento de la evidencia del bucket (spec.md: R-14a…R-14e2, R-6a…R-6e2; VC-14, VC-6c, VC-6a).

`registrar` lee solo la metadata de los objetos (nunca el contenido) e imprime el bloque
de procedencia que va en `salida/vcs-bucket.md`: el modelo no escribe esas filas. Cada
argumento lleva, obligatoriamente, el `updated` que leyó el subagent por MCP
(`gs://b/o@<updated RFC3339>`): `read_object_metadata` de storage-mcp 0.6.0 no devuelve
`generation` ni checksums (Hallazgo 2), así que la coincidencia entre las dos lecturas se
comprueba por `updated`, al microsegundo. Si no coincide, imprime `MISMATCH …`; si el
objeto no existe, `MISSING gs://…`. En los dos casos sale con 1 y no imprime bloque
(todo o nada). La `generation`, el `md5Hash` y el `crc32c` del bloque son de esta lectura.

Códigos de salida de `registrar`: 0 bloque impreso, 1 objeto inexistente o `updated`
distinto, 2 no se pudo registrar (argumento sin `@<updated>`, bucket que no es el de
prueba, endpoint o credencial ajenos, 401/403, otro error).

`verificar` relee la metadata de cada objeto citado en los bloques de procedencia y
compara la `generation`. Si un objeto cambió o se borró, la evidencia está vencida y el
VC no se puede dar por cerrado.

Códigos de salida de `verificar`: 0 todo coincide, 1 hay evidencia vencida, 2 no se pudo
verificar (bucket que no es el de prueba, endpoint o credencial ajenos, 401/403, otro
error, o ninguna fila).

Dos modos (D-9), y las dos subórdenes exigen, antes de tocar la red, que todo objeto esté
en el bucket de prueba (GCSGREP_TP4_BUCKET, por defecto gcsgrep-test-g4-mcp):
  - **Emulador** (STORAGE_EMULATOR_HOST definida): tiene que ser exactamente el gateway de
    solo lectura (http://127.0.0.1:4443; GCSGREP_TP4_GATEWAY lo pisa). Credenciales
    anónimas; la cuenta es `lector@gateway (<host:puerto> → fake-gcs-server 1.56.1)`.
  - **GCS real** (sin STORAGE_EMULATOR_HOST): GOOGLE_APPLICATION_CREDENTIALS definida y
    apuntando a un archivo que existe (sin vuelta al ADC personal), y esa credencial tiene
    que ser la SA de solo lectura (gcsgrep-tp4-lector@<proyecto>.iam.gserviceaccount.com;
    GCSGREP_TP4_SA pisa el email).

Uso:
  uv run --no-project --with google-cloud-storage==3.14.1 python \\
      gcs-mcp-tp4/scripts/check-generations.py registrar gs://b/o@<updated> [gs://b/o@<updated> ...]
  uv run --no-project --with google-cloud-storage==3.14.1 python \\
      gcs-mcp-tp4/scripts/check-generations.py verificar gcs-mcp-tp4/salida/vcs-bucket.md
Salida en inglés (D-6).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_PROJECT = "itba-sdd"
DEFAULT_BUCKET = "gcsgrep-test-g4-mcp"
SA_NAME = "gcsgrep-tp4-lector"
VIA = "lector-fixtures (MCP) + check-generations.py"
MARK_START = "<!-- procedencia:inicio -->"
MARK_END = "<!-- procedencia:fin -->"
HEADER = "| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |"
SEPARATOR = "|---|---|---|---|---|---|---|---|"
DEFAULT_GATEWAY = "http://127.0.0.1:4443"
EMULATOR = "fake-gcs-server 1.56.1"
TIMEOUT = 30
GS_RE = re.compile(r"^gs://([a-z0-9][a-z0-9._-]{1,220}[a-z0-9])/(.+)$")
BLOCK_RE = re.compile(re.escape(MARK_START) + r"(.*?)" + re.escape(MARK_END), re.DOTALL)
IMPERSONATION_RE = re.compile(r"serviceAccounts/([^/:]+@[^/:]+):generateAccessToken")
ARG_RE = re.compile(r"^(gs://.+)@([^@]+)$")
RFC3339_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})$")


class CannotVerify(Exception):
    """Cualquier motivo por el que no se puede consultar GCS."""


def parse_uri(uri: str) -> tuple[str, str]:
    m = GS_RE.match(uri)
    if not m:
        raise ValueError(f"not a gs://bucket/object URI: {uri!r}")
    return m.group(1), m.group(2)


def project_id() -> str:
    return (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCSGREP_TP4_PROJECT")
        or DEFAULT_PROJECT
    )


def test_bucket() -> str:
    return os.environ.get("GCSGREP_TP4_BUCKET", "").strip() or DEFAULT_BUCKET


def expected_account() -> str:
    return (os.environ.get("GCSGREP_TP4_SA", "").strip()
            or f"{SA_NAME}@{project_id()}.iam.gserviceaccount.com")


def check_bucket(bucket: str) -> None:
    allowed = test_bucket()
    if bucket != allowed:
        raise CannotVerify(f"bucket {bucket} is not the test bucket {allowed}")


def account_of(creds) -> str:
    """Principal de la credencial. Para un ADC impersonado, la SA objetivo."""
    adc = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if adc:
        try:
            data = json.loads(Path(adc).read_text(encoding="utf-8"))
            url = data.get("service_account_impersonation_url", "")
            m = IMPERSONATION_RE.search(url)
            if m:
                return m.group(1)
            if data.get("client_email"):
                return data["client_email"]
        except (OSError, ValueError):
            pass
    for attr in ("service_account_email", "signer_email", "_target_principal"):
        value = getattr(creds, attr, None)
        if isinstance(value, str) and "@" in value:
            return value
    return "unknown"


def make_client():
    """Cliente de GCS con el ADC de GOOGLE_APPLICATION_CREDENTIALS. Devuelve (client, creds)."""
    try:
        import google.auth
        from google.cloud import storage
    except ImportError as exc:
        raise CannotVerify(f"missing dependency ({exc}); run with "
                           "'uv run --no-project --with google-cloud-storage==3.14.1 python ...'")
    # Cualquier falla al armar la credencial o el cliente es "no se pudo": exit 2.
    try:
        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"]
        )
        client = storage.Client(project=project_id(), credentials=creds)
    except Exception as exc:  # noqa: BLE001
        raise CannotVerify(f"cannot create the GCS client ({type(exc).__name__}: {exc})")
    return client, creds


def gateway() -> str:
    return (os.environ.get("GCSGREP_TP4_GATEWAY", "").strip() or DEFAULT_GATEWAY).rstrip("/")


def open_emulator_client(host: str):
    """Modo emulador: solo por el gateway, con credenciales anónimas. Devuelve (client, cuenta)."""
    expected = gateway()
    if host.rstrip("/") != expected:
        raise CannotVerify(f"STORAGE_EMULATOR_HOST is {host!r}, expected the read-only gateway "
                           f"{expected!r} (never the emulator directly)")
    try:
        from google.auth.credentials import AnonymousCredentials
        from google.cloud import storage
    except ImportError as exc:
        raise CannotVerify(f"missing dependency ({exc}); run with "
                           "'uv run --no-project --with google-cloud-storage==3.14.1 python ...'")
    try:
        client = storage.Client(project=project_id(), credentials=AnonymousCredentials())
    except Exception as exc:  # noqa: BLE001
        raise CannotVerify(f"cannot create the emulator client ({type(exc).__name__}: {exc})")
    hostport = expected.split("://", 1)[-1]
    return client, f"lector@gateway ({hostport} → {EMULATOR})"


def open_client():
    """Exige el endpoint o la credencial de solo lectura antes de devolver el cliente.

    Con STORAGE_EMULATOR_HOST, el gateway (modo emulador). Sin ella, GAC y la SA (GCS real).
    Devuelve (client, cuenta).
    """
    host = os.environ.get("STORAGE_EMULATOR_HOST", "").strip()
    if host:
        return open_emulator_client(host)
    adc = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not adc:
        raise CannotVerify("GOOGLE_APPLICATION_CREDENTIALS is not set; export the impersonated "
                           "ADC of the read-only service account (no fallback to personal ADC), "
                           "or STORAGE_EMULATOR_HOST for the emulator gateway")
    if not Path(adc).is_file():
        raise CannotVerify(f"GOOGLE_APPLICATION_CREDENTIALS points to a missing file: {adc}")
    client, creds = make_client()
    account = account_of(creds)
    expected = expected_account()
    if account != expected:
        raise CannotVerify(f"credential is {account}, expected {expected}")
    return client, account


def fetch_metadata(client, bucket: str, name: str):
    """Solo metadata (objects.get sin alt=media). Devuelve None si el objeto no existe."""
    from google.api_core import exceptions as gexc
    from google.auth import exceptions as aexc

    try:
        return client.bucket(bucket).get_blob(name, retry=None, timeout=TIMEOUT)
    except (gexc.Unauthorized, gexc.Forbidden) as exc:
        raise CannotVerify(f"{exc.code} on gs://{bucket}/{name}: {exc.message}")
    except aexc.RefreshError as exc:
        raise CannotVerify(f"credential refresh failed ({exc})")
    except gexc.GoogleAPICallError as exc:
        raise CannotVerify(f"API error on gs://{bucket}/{name}: {exc}")
    except Exception as exc:  # red, timeout, etc.
        raise CannotVerify(f"{type(exc).__name__} on gs://{bucket}/{name}: {exc}")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_rfc3339(text: str) -> datetime:
    """RFC 3339 con fracción de 0 a 9 dígitos → datetime UTC, al microsegundo."""
    m = RFC3339_RE.match(text)
    if not m:
        raise ValueError(f"not an RFC 3339 timestamp: {text!r}")
    y, mo, d, h, mi, s, frac, tz = m.groups()
    micro = int((frac or "0").ljust(6, "0")[:6])
    if tz == "Z":
        tzinfo = timezone.utc
    else:
        sign = 1 if tz[0] == "+" else -1
        tzinfo = timezone(sign * timedelta(hours=int(tz[1:3]), minutes=int(tz[4:6])))
    try:
        dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), micro, tzinfo=tzinfo)
    except ValueError:
        raise ValueError(f"not an RFC 3339 timestamp: {text!r}") from None
    return dt.astimezone(timezone.utc)


def fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def split_expected(arg: str) -> tuple[str, str, datetime]:
    """`gs://b/o@<updated>` → (uri, updated tal cual, updated parseado). Si no, ValueError."""
    m = ARG_RE.match(arg)
    if not m:
        raise ValueError(f"invalid argument {arg!r} (expected gs://bucket/object@<updated RFC 3339>)")
    try:
        when = parse_rfc3339(m.group(2))
    except ValueError:
        raise ValueError(f"invalid argument {arg!r} "
                         "(expected gs://bucket/object@<updated RFC 3339>)") from None
    return m.group(1), m.group(2), when


def cmd_registrar(uris: list[str]) -> int:
    try:
        targets = []
        for arg in uris:
            uri, raw, expected = split_expected(arg)
            try:
                bucket, name = parse_uri(uri)
            except ValueError:
                raise ValueError(f"invalid argument {arg!r} "
                                 "(expected gs://bucket/object@<updated RFC 3339>)") from None
            targets.append((bucket, name, raw, expected))
    except ValueError as exc:
        print(f"CANNOT REGISTER: {exc}", file=sys.stderr)
        return 2
    try:
        for bucket, _, _, _ in targets:
            check_bucket(bucket)
        client, account = open_client()
        rows = []
        problems = []
        for bucket, name, raw, expected in targets:
            blob = fetch_metadata(client, bucket, name)
            read_at = now_utc()
            if blob is None:
                problems.append(f"MISSING gs://{bucket}/{name}")
                continue
            # El updated que leyó el subagent por MCP tiene que coincidir, al microsegundo,
            # con esta lectura independiente: si no, el objeto cambió entre las dos
            # (R-14b). La 0.6.0 no le da la generation al subagent (Hallazgo 2).
            current = blob.updated.astimezone(timezone.utc) if blob.updated else None
            if current != expected:
                problems.append(
                    f"MISMATCH gs://{bucket}/{name} subagent={raw} current={fmt_dt(current) or 'none'}"
                )
                continue
            rows.append(
                f"| gs://{bucket}/{name} | {blob.generation} | {blob.md5_hash or ''} "
                f"| {blob.crc32c or ''} | {fmt_dt(current)} | {read_at} | {account} | {VIA} |"
            )
    except CannotVerify as exc:
        print(f"CANNOT REGISTER: {exc}", file=sys.stderr)
        return 2
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        return 1
    # Todo o nada: el bloque se imprime solo si se leyeron y coincidieron todos los objetos.
    print(MARK_START)
    print(HEADER)
    print(SEPARATOR)
    for row in rows:
        print(row)
    print(MARK_END)
    return 0


def parse_rows(text: str) -> list[tuple[str, str]]:
    """(uri, generation) de todas las filas de todos los bloques de procedencia."""
    rows: list[tuple[str, str]] = []
    for block in BLOCK_RE.findall(text):
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or not cells[0].startswith("gs://"):
                continue  # encabezado o separador
            rows.append((cells[0].strip("`"), cells[1].strip("`")))
    return rows


def cmd_verificar(path: str) -> int:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"CANNOT VERIFY: cannot read {path} ({exc.strerror or exc})")
        return 2
    rows = parse_rows(text)
    if not rows:
        print(f"CANNOT VERIFY: no provenance rows between {MARK_START} and {MARK_END} in {path}")
        return 2

    recorded: dict[str, list[str]] = {}
    for uri, gen in rows:
        gens = recorded.setdefault(uri, [])
        if gen not in gens:
            gens.append(gen)

    try:
        targets = {uri: parse_uri(uri) for uri in recorded}
    except ValueError as exc:
        print(f"CANNOT VERIFY: {exc}")
        return 2

    stale = 0
    try:
        for bucket, _ in targets.values():
            check_bucket(bucket)
        client, _ = open_client()
        for uri, (bucket, name) in targets.items():
            blob = fetch_metadata(client, bucket, name)
            if blob is None:
                print(f"STALE {uri} deleted")
                stale += 1
                continue
            current = str(blob.generation)
            for gen in recorded[uri]:
                if gen != current:
                    print(f"STALE {uri} recorded={gen} current={current}")
                    stale += 1
    except CannotVerify as exc:
        print(f"CANNOT VERIFY: {exc}")
        return 2

    if stale:
        return 1
    print(f"OK {len(recorded)} objects")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-generations.py",
        description="Record and verify GCS object provenance (generation) for the bucket VCs.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_reg = sub.add_parser("registrar", help="print the provenance block for the given objects")
    p_reg.add_argument("uris", nargs="+", metavar="gs://bucket/object@<updated>")
    p_ver = sub.add_parser("verificar", help="check that recorded generations are still current")
    p_ver.add_argument("file", metavar="file.md")
    args = parser.parse_args(argv)
    if args.cmd == "registrar":
        return cmd_registrar(args.uris)
    return cmd_verificar(args.file)


if __name__ == "__main__":
    sys.exit(main())

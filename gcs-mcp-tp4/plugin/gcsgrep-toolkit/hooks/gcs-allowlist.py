#!/usr/bin/env python3
"""gcs-allowlist — capa 1 del muro: qué tools de `gcs` corren, quién las corre y sobre qué bucket.

Evento: PreToolUse. Spec: gcs-mcp-tp4/spec.md, R-8a…R-8j (VC-8a lo prueba con 74 casos).

Allowlist, no denylist: deja pasar las 3 tools de lectura que conocemos
(list_objects, read_object_metadata, read_object_content) y veta todo lo demás,
incluida cualquier tool nueva que traiga la próxima versión del server. La 0.6.0 ya
demostró por qué: las tools que escriben se llaman `*_safe`, no `*_new` como dice el
enunciado, así que una denylist escrita con esos nombres no vetaba nada.

Es la primera de tres capas, no la garantía:
  1. este hook (nombre de la tool, agent_type y bucket);
  2. el server corre sin --enable-destructive-tools: delete_object ni existe (R-9);
  3. el techo de solo lectura, debajo del agente y del server (R-10):
     - modo emulador (D-9, el que se usa hoy): el gateway emulador/gateway.py en
       127.0.0.1:4443 deja pasar solo GET/HEAD sobre el bucket de prueba; lo que se
       escape de las dos de arriba lo rechaza el gateway con 403 (no IAM de GCS);
     - modo GCS real (gcs-real/, en espera): la SA gcsgrep-tp4-lector solo tiene
       roles/storage.objectViewer sobre el bucket, y GCS lo rechaza con 403.

Por qué mira agent_type (la trifecta): el contenido del bucket es externo y puede traer
instrucciones. La sesión principal tiene Bash y red; si además leyera ese contenido,
juntaría las tres patas (datos privados, contenido no confiable, canal de salida). Por
eso solo el subagent lector-fixtures, que no tiene Bash ni red, puede llamar a `gcs`:
la sesión principal queda vetada aunque `permissions.allow` pre-apruebe las tools.
Ese corte vale solo para el camino MCP: este hook no ve Bash, y el gateway sirve el
contenido a cualquier proceso local. Por Bash -> HTTP quedan solo permissions.deny y la
aprobación (spec R-7, "Límite").

Sirve igual en el repo y en el plugin; el modo sale del prefijo de tool_name:
  - repo:   mcp__gcs__<tool>, agent_type `lector-fixtures`, bucket de GCS_ALLOWED_BUCKET
            (lo fija el comando del hook en .claude/settings.json);
  - plugin: mcp__plugin_gcsgrep-toolkit_gcs__<tool>, agent_type
            `gcsgrep-toolkit:lector-fixtures`, bucket de CLAUDE_PLUGIN_OPTION_BUCKET.
Cada modo acepta solo su propio nombre de subagent.

Falla cerrado: lo que no se puede evaluar se veta, incluida cualquier excepción
imprevista (sale con 2 y nombra el tipo de excepción).
exit 0 deja pasar · exit 2 veta (stderr lo lee el agente). Mensajes en inglés (D-6).
"""

import json
import os
import sys

PERMITIDAS = ("list_objects", "read_object_metadata", "read_object_content")

# prefijo de tool_name → (agent_type esperado, variable de entorno con el bucket)
MODOS = {
    "mcp__plugin_gcsgrep-toolkit_gcs__": ("gcsgrep-toolkit:lector-fixtures", "CLAUDE_PLUGIN_OPTION_BUCKET"),
    "mcp__gcs__": ("lector-fixtures", "GCS_ALLOWED_BUCKET"),
}


def vetar(mensaje):
    print(f"gcs-allowlist: {mensaje}", file=sys.stderr)
    sys.exit(2)


def no_evaluable(motivo):
    vetar(f"cannot evaluate this call ({motivo}); blocking.")


def main():
    sys.stderr.reconfigure(encoding="utf-8")

    # Paso 1 · el evento se puede leer, la tool es de gcs y hay bucket configurado.
    try:
        evento = json.load(sys.stdin)
    except ValueError:
        no_evaluable("stdin is not valid JSON")
    if not isinstance(evento, dict):
        no_evaluable("event is not a JSON object")

    tool = evento.get("tool_name")
    if not isinstance(tool, str):
        no_evaluable("missing tool_name")

    modo = next((p for p in MODOS if tool.startswith(p)), None)
    if modo is None:
        no_evaluable(f"tool_name '{tool}' does not start with mcp__gcs__ or mcp__plugin_gcsgrep-toolkit_gcs__")
    agente_esperado, var_bucket = MODOS[modo]

    bucket_permitido = os.environ.get(var_bucket, "").strip()
    if not bucket_permitido:
        no_evaluable(f"{var_bucket} is not set")

    # Paso 2 · allowlist por nombre.
    if tool[len(modo):] not in PERMITIDAS:
        vetar(f"{tool} is not in the allowlist ({', '.join(PERMITIDAS)}). "
              "Review the tool and add it on purpose.")

    # Paso 3 · solo dentro del subagent de este modo (corte de la trifecta).
    if evento.get("agent_type") != agente_esperado:
        vetar(f"{tool} may only run inside the lector-fixtures subagent; delegate the read to it.")

    # Paso 4 · solo el bucket de prueba.
    entrada = evento.get("tool_input")
    bucket = entrada.get("bucket_name", "") if isinstance(entrada, dict) else ""
    if bucket != bucket_permitido:
        vetar(f"bucket '{bucket}' is not the configured test bucket '{bucket_permitido}'.")

    # Paso 5.
    sys.exit(0)


# Falla cerrado también ante lo imprevisto: cualquier excepción que no sea la salida
# deliberada de vetar() (SystemExit) se veta con exit 2, nunca deja pasar la llamada.
try:
    main()
except SystemExit:
    raise
except BaseException as exc:  # noqa: BLE001 — a propósito: incluye KeyboardInterrupt, RecursionError…
    no_evaluable(type(exc).__name__)

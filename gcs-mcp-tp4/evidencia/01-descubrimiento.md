# 01 · Descubrimiento: el agente lista las tools del server `gcs`

Spec: [R-3/VC-3 y R-4/VC-4](../spec.md#r-4--descubrimiento). Bucket emulado (D-9): el
server habla con el gateway de solo lectura en `127.0.0.1:4443`, no con GCS real. Todas
las corridas de `claude -p` de este archivo usaron **Sonnet** (`--model sonnet`; el
`init` del stream reporta `claude-sonnet-5-5`), porque el modelo por defecto de Claude
Code no tenía crédito.

Entorno de todas las corridas: desde la raíz del repo, con
`export STORAGE_EMULATOR_HOST=http://127.0.0.1:4443`, el emulador levantado y armado
(6 objetos, ver [`02-iam.md`](./02-iam.md#bucket-y-objetos)).

## `claude mcp list`

```
Checking MCP server health…
gcs: npx -y @google-cloud/storage-mcp@0.6.0 - ⏸ Pending approval (run `claude` to approve)
exit=0
```

Se omitieron 10 líneas de servers del usuario (conectores `claude.ai …` y plugins
instalados a nivel usuario), ajenos al repo.

**Estado observado: `⏸ Pending approval`.** La spec v1.5 (VC-4) pide registrar el estado
de `gcs` en `claude mcp list` tal como se observó, y es este. El motivo: `gcs` es un server
de alcance proyecto (`.mcp.json`), y `claude mcp list` solo lo muestra conectado después de
aprobarlo en una sesión interactiva de `claude`. En esta máquina no se aprobó
(`enabledMcpjsonServers` vacío para el proyecto). `claude -p`, en cambio, carga los servers
del proyecto sin pedir aprobación, según la doc. Así se ve en el `init` de la corrida de
abajo: `gcs` (connected), `source: project`, 15 tools.

## El agente listando las tools

Corrida: `claude -p "Listá las tools del server MCP gcs con su nombre completo" --model sonnet --output-format stream-json --verbose --max-turns 60`,
ventana 2026-10-14T20:44:59Z … 20:45:19Z. Transcripción generada con
[`scripts/transcripcion.py`](../scripts/transcripcion.py) desde el `.jsonl` crudo.

### Transcripción

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> Listá las tools del server MCP gcs con su nombre completo

- Inicio de la sesión: sesión `da4cb4c7-3d1c-4075-b952-5a30ef0d9b19` · modelo `claude-sonnet-5-5` · Claude Code 2.1.300 · servers MCP de gcs: `gcs` (connected) · tools de gcs en la sesión: 15

**Agente:** Tools del server MCP `gcs` (15):

1. `mcp__gcs__check_iam_permissions`
2. `mcp__gcs__copy_object_safe`
3. `mcp__gcs__create_bucket`
4. `mcp__gcs__execute_insights_query`
5. `mcp__gcs__get_bucket_location`
6. `mcp__gcs__get_bucket_metadata`
7. `mcp__gcs__get_metadata_table_schema`
8. `mcp__gcs__list_buckets`
9. `mcp__gcs__list_insights_configs`
10. `mcp__gcs__list_objects`
11. `mcp__gcs__read_object_content`
12. `mcp__gcs__read_object_metadata`
13. `mcp__gcs__upload_object_safe`
14. `mcp__gcs__view_iam_policy`
15. `mcp__gcs__write_object_safe`

Están cargadas como *deferred*, así que para llamarlas hay que traer antes su schema con ToolSearch. Las 3 de lectura que usa el subagent `lector-fixtures` son `list_objects`, `read_object_metadata` y `read_object_content`.

---
**Resultado final** · turnos: 1 · duración: 3s · is_error: False

Tools del server MCP `gcs` (15):

1. `mcp__gcs__check_iam_permissions`
2. `mcp__gcs__copy_object_safe`
3. `mcp__gcs__create_bucket`
4. `mcp__gcs__execute_insights_query`
5. `mcp__gcs__get_bucket_location`
6. `mcp__gcs__get_bucket_metadata`
7. `mcp__gcs__get_metadata_table_schema`
8. `mcp__gcs__list_buckets`
9. `mcp__gcs__list_insights_configs`
10. `mcp__gcs__list_objects`
11. `mcp__gcs__read_object_content`
12. `mcp__gcs__read_object_metadata`
13. `mcp__gcs__upload_object_safe`
14. `mcp__gcs__view_iam_policy`
15. `mcp__gcs__write_object_safe`

Están cargadas como *deferred*, así que para llamarlas hay que traer antes su schema con ToolSearch. Las 3 de lectura que usa el subagent `lector-fixtures` son `list_objects`, `read_object_metadata` y `read_object_content`.

### Chequeo (calculado sobre el `.jsonl`)

Comparación de los nombres de la respuesta con el `tools/list` guardado y con el `init`
de la sesión:

```
tools nombradas en la respuesta: 15
coinciden con server/tools-list-0.6.0.json (15): True
todas con prefijo mcp__gcs__: True
delete_object en la respuesta: False
tools mcp__gcs__* en el init de la sesión: True
server gcs en el init: [{'name': 'gcs', 'status': 'connected', 'source': 'project'}]
tool_use en la corrida: 0
```

**VC-4 (spec v1.5): pasa.** Las 15 tools de la 0.6.0 aparecen como `mcp__gcs__<tool>` y
`delete_object` no aparece. El agente respondió desde la lista de tools de la sesión, sin
llamar a ninguna (0 `tool_use`). El estado de `claude mcp list` quedó registrado como se
observó, `Pending approval` (sección de arriba).

## Config

`python3 gcs-mcp-tp4/scripts/check-config.py` (VC-3):

```
check-config: OK — @google-cloud/storage-mcp@0.6.0 pinned in 4 configs, no --enable-destructive-tools, env values are references only, emulator mode in .mcp.json and the plugin, 18 files free of credential material.
exit=0
```

**VC-3: pasa.** El paquete está fijado como `@google-cloud/storage-mcp@0.6.0` en
`.mcp.json`, en el `.mcp.json` del plugin, en `codex/config.toml.ejemplo` y en
`gcs-real/mcp.json.ejemplo`; ningún `args` lleva `--enable-destructive-tools`; los
valores de `env` son solo referencias (`${STORAGE_EMULATOR_HOST}`, …).

## El `tools/list` real y el hallazgo `_safe`

El `tools/list` que devolvió la 0.6.0 en modo seguro está guardado entero en
[`server/tools-list-0.6.0.json`](../server/tools-list-0.6.0.json) (12.741 bytes, 15
tools). Con `--enable-destructive-tools`, los nombres están en
[`server/tools-list-0.6.0-destructive-names.json`](../server/tools-list-0.6.0-destructive-names.json) (21).

Hallazgo de entrada (spec, "Hallazgo de entrada"): el enunciado dice que el modo seguro
expone `write_object_new`, `upload_object_new` y `copy_object_new`; en la 0.6.0 se llaman
`write_object_safe`, `upload_object_safe` y `copy_object_safe`. Se ve en la lista de
arriba. Una denylist con los nombres del enunciado no vetaría nada; por eso el hook es
una allowlist, y la prueba de la capa 1 ([`04-muro.md`](./04-muro.md#capa-1)) usa
`write_object_safe`.

## Sin `STORAGE_EMULATOR_HOST`: falla cerrado

Respalda lo que dice R-3 de la spec: si falta la variable, el server falla cerrado en
cada llamada, en vez de caer al GCS real. `.mcp.json` le pasa `"${STORAGE_EMULATOR_HOST}"`
sin default, así que, con la variable sin exportar, el server recibe el texto literal o
un valor vacío. Nunca le llega una variable ausente. Con el literal falló la corrida 2
de VC-5a con el plugin (`Only absolute URLs are supported`,
[06](./06-plugin.md#resultado-de-vc-11b)). Acá se prueban los dos valores contra el
server fijado, por JSON-RPC directo, sin Claude ni hook.

La prueba reusa la clase `Server` de [`scripts/probar-server-sin-hook.py`](../scripts/probar-server-sin-hook.py).
El entorno del server es mínimo: `PATH`, `GOOGLE_CLOUD_PROJECT`, sin
`GOOGLE_APPLICATION_CREDENTIALS`, y `HOME` en un directorio temporal vacío. Así, si el
server intentara ir al GCS real, no encontraría el ADC personal. La variable ausente del
todo no se prueba: `.mcp.json` no la produce, y probarla podría usar una credencial real.
Corrida del 2026-10-14 a las 21:54Z (salida cruda en `hidden-content/raw/01-sin-emulador.txt`):

```python
import importlib.util, os, sys, tempfile, json
spec = importlib.util.spec_from_file_location("p", "gcs-mcp-tp4/scripts/probar-server-sin-hook.py")
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
cmd = p.server_command()
home = tempfile.mkdtemp()  # HOME vacío: sin ~/.config/gcloud, así no hay ADC al que caer
for label, value in (("literal", "${STORAGE_EMULATOR_HOST}"), ("vacío", "")):
    env = {"PATH": os.environ["PATH"], "HOME": home,
           "npm_config_cache": os.path.expanduser("~/.npm"),
           "GOOGLE_CLOUD_PROJECT": "itba-sdd", "STORAGE_EMULATOR_HOST": value}
    print(f"\n=== STORAGE_EMULATOR_HOST={value!r} ({label}); sin GOOGLE_APPLICATION_CREDENTIALS; HOME vacío ===")
    s = p.Server(cmd, env)
    try:
        s.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "probe-sin-emulador", "version": "0"}}, p.STARTUP_TIMEOUT)
        s.notify("notifications/initialized")
        r = s.request("tools/call", {"name": "list_objects",
                      "arguments": {"bucket_name": "gcsgrep-test-g4-mcp", "max_results": 5}}, p.CALL_TIMEOUT)
        print("RESULT TEXT:", p.result_text(r))
    finally:
        s.close()
```

```
Server command from .mcp.json: npx -y @google-cloud/storage-mcp@0.6.0

=== STORAGE_EMULATOR_HOST='${STORAGE_EMULATOR_HOST}' (literal); sin GOOGLE_APPLICATION_CREDENTIALS; HOME vacío ===

--> request #1 initialize {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe-sin-emulador", "version": "0"}}
<-- response #1 {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": true}}, "serverInfo": {"name": "storage-mcp-server", "version": "0.6.0"}}

--> notification notifications/initialized

--> request #2 tools/call {"name": "list_objects", "arguments": {"bucket_name": "gcsgrep-test-g4-mcp", "max_results": 5}}
<-- response #2 {"content": [{"type": "text", "text": "{\"error\":\"Error listing objects: Only absolute URLs are supported\",\"error_type\":\"Unknown\"}"}]}
RESULT TEXT: {"error":"Error listing objects: Only absolute URLs are supported","error_type":"Unknown"}

=== STORAGE_EMULATOR_HOST='' (vacío); sin GOOGLE_APPLICATION_CREDENTIALS; HOME vacío ===

--> request #1 initialize {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe-sin-emulador", "version": "0"}}
<-- response #1 {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": true}}, "serverInfo": {"name": "storage-mcp-server", "version": "0.6.0"}}

--> notification notifications/initialized

--> request #2 tools/call {"name": "list_objects", "arguments": {"bucket_name": "gcsgrep-test-g4-mcp", "max_results": 5}}
<-- response #2 {"content": [{"type": "text", "text": "{\"error\":\"Error listing objects: request to https://storage/v1/b/gcsgrep-test-g4-mcp/o?maxResults=5 failed, reason: getaddrinfo ENOTFOUND storage\",\"error_type\":\"Unknown\"}"}]}
RESULT TEXT: {"error":"Error listing objects: request to https://storage/v1/b/gcsgrep-test-g4-mcp/o?maxResults=5 failed, reason: getaddrinfo ENOTFOUND storage","error_type":"Unknown"}
```

**Resultado:** las dos variantes fallan cerradas en `list_objects`, y ninguna llega a una
credencial:
- con el literal: `Error listing objects: Only absolute URLs are supported`;
- con el vacío: `… request to https://storage/v1/b/gcsgrep-test-g4-mcp/o?maxResults=5 failed, reason: getaddrinfo ENOTFOUND storage`. La librería arma la URL con el host vacío, `storage` queda como nombre de host y no resuelve.


# 02 · Política de acceso: el gateway en lugar de IAM (D-9)

Spec: [R-1/VC-1](../spec.md#r-1--bucket-de-prueba-sintético), R-1b/VC-1b y
[R-2d/VC-2d](../spec.md#r-2d--el-emulador-solo-se-alcanza-por-el-gateway-docker-desktop) (spec v1.7), desvío
[D-9](../spec.md#d-9--el-bucket-en-un-emulador-con-un-gateway-de-techo). R-2a…R-2c (lo que el gateway deja
pasar y lo que rechaza) se prueban caso por caso en [`04-muro.md`](./04-muro.md#capa-3).

El enunciado pide acá `gcloud storage buckets get-iam-policy` con el rol de la cuenta.
**Con el emulador no hay política IAM que mostrar:** `fake-gcs-server` no implementa IAM
(cualquiera que le llegue puede crear, pisar y borrar). El equipo no pudo habilitar
facturación en GCP, así que el bucket vive en el emulador y el techo de solo lectura lo
pone un gateway propio, [`emulador/gateway.py`](../emulador/gateway.py), que es lo único
que el server MCP y los scripts ven. Lo de abajo muestra ese techo, no una política de
GCS: prueba que *esta* frontera corta, no que una política IAM real lo haga. En la primera
entrega la cátedra habilitó emular GCS, y el TP4 aplica ese criterio (D-9, "Precedente y
autorización").

Ninguna corrida de `claude` hizo falta para este archivo (son comandos de Docker y `curl`).

## Topología: el emulador no es alcanzable sin pasar por el gateway

```
$ docker-compose -p gcs-mcp-tp4 -f gcs-mcp-tp4/emulador/docker-compose.yml ps
NAME                    IMAGE                                                                                                   COMMAND                  SERVICE   CREATED          STATUS          PORTS
gcs-mcp-tp4-gateway-1   python:3.12-alpine@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4              "python -u /app/gate…"   gateway   16 minutes ago   Up 16 minutes   127.0.0.1:4443->8080/tcp
gcs-mcp-tp4-gcs-1       fsouza/fake-gcs-server:1.56.1@sha256:797ce226d62f947c009dc40246b30cfb456b8473d8241407f9d6f2c04e4d69ef   "/bin/fake-gcs-serve…"   gcs       16 minutes ago   Up 16 minutes   4443/tcp

$ docker-compose -p gcs-mcp-tp4 … port gcs 4443
invalid IP:0
exit=0
$ docker-compose -p gcs-mcp-tp4 … port gateway 8080
127.0.0.1:4443

$ docker network inspect gcs-mcp-tp4_interna --format 'name={{.Name}} internal={{.Internal}} members={{range .Containers}}{{.Name}} {{end}}'
name=gcs-mcp-tp4_interna internal=true members=gcs-mcp-tp4-gcs-1 gcs-mcp-tp4-gateway-1 
$ docker network inspect gcs-mcp-tp4_default --format (igual)
name=gcs-mcp-tp4_default internal=false members=gcs-mcp-tp4-gateway-1 

$ docker inspect gcs-mcp-tp4-gcs-1 gcs-mcp-tp4-gateway-1 --format '{{.Name}} networks=… published=…'
/gcs-mcp-tp4-gcs-1 networks=gcs-mcp-tp4_interna published={}
/gcs-mcp-tp4-gateway-1 networks=gcs-mcp-tp4_default gcs-mcp-tp4_interna published={"8080/tcp":[{"HostIp":"127.0.0.1","HostPort":"4443"}]}
```

Se usa `docker-compose` (el binario) porque, con `DOCKER_CONFIG=/tmp/dockercfg`, el
plugin `docker compose` no se encuentra; es el mismo fallback que usan los scripts
(`emulador/config.sh`). Lo que dice:

- `gateway` publica `127.0.0.1:4443->8080/tcp`, solo en loopback;
- `gcs` (el emulador) muestra `4443/tcp` **sin publicar** (`port gcs 4443` → `invalid IP:0`, `PortBindings` vacío);
- `gcs` está solo en `gcs-mcp-tp4_interna`, que es `internal=true`; el gateway es el único contenedor en las dos redes.

Esto sale de [`emulador/docker-compose.yml`](../emulador/docker-compose.yml): línea 17
(`internal: true`), línea 34 (`gcs`: `networks: [interna]`, sin `ports`), líneas 47–48
(`gateway`: `"127.0.0.1:4443:8080"`, `networks: [interna, default]`).

## La allowlist del gateway

Dos cosas que una política IAM real daría y este techo no (revisión cruzada, A7; el
recuadro D-9 del [README](../README.md#qué-hace) las lista):

- **No autentica.** El gateway no pide credencial: `lector@gateway`, la "cuenta" que
  aparece en su log y en las filas de procedencia de `check-generations.py`, es un rótulo,
  no una identidad verificada. Cualquier proceso local que llegue a `127.0.0.1:4443` es ese
  lector. Con `objectViewer` sobre el bucket, en cambio, GCS sabe *quién* lee.
- **Deja pasar la metadata del bucket.** `GET /storage/v1/b/<bucket>` (línea 56 de abajo)
  está en la allowlist porque `storage-mcp` lo pide antes de listar; en IAM eso es
  `storage.buckets.get`, que `roles/storage.objectViewer` **no** otorga (lo tienen
  `legacyBucketReader`/`storage.admin`). Es un permiso de más respecto del rol real, de solo
  lectura igual.

[`emulador/gateway.py`](../emulador/gateway.py), con números de línea:

```python
    54	B = re.escape(BUCKET)
    55	ALLOWED = [
    56	    re.compile(rf"^/storage/v1/b/{B}/?$"),
    57	    re.compile(rf"^/storage/v1/b/{B}/o/?$"),
    58	    re.compile(rf"^/storage/v1/b/{B}/o/[^/?#][^?#]*$"),
    59	    re.compile(rf"^/download/storage/v1/b/{B}/o/[^/?#][^?#]*$"),
    60	]
…
    69	def normalize(path: str) -> str:
    70	    """`/b/…` (como lo pide storage-mcp con el emulador) → `/storage/v1/b/…`."""
    71	    if path == "/b" or path.startswith("/b/"):
    72	        return "/storage/v1" + path
    73	    return path
    74	
    75	
    76	def is_allowed(method: str, path: str) -> bool:
    77	    # Sin segmentos `.`/`..` (ni codificados) ni `//`: el upstream podría normalizarlos y
    78	    # terminar en otro bucket u otra ruta que la que se evaluó acá.
    79	    segments = path.split("/")
    80	    if "." in segments or ".." in segments or "//" in path or "%2e" in path.lower():
    81	        return False
    82	    return method in ("GET", "HEAD") and any(r.match(path) for r in ALLOWED)
…
   235	    def _handle(self) -> None:
   236	        method = self.command
   237	        raw_path = self.path
   238	        path = normalize(urlsplit(raw_path).path)
   239	        if is_allowed(method, path):
   240	            self._proxy(method, raw_path, path)
   241	        else:
   242	            self._deny(method, path)
```

Las líneas citadas son las de `gateway.py` en `ef6a274` (spec v1.6). La v1.7 agregó 3 líneas
antes de `ALLOWED` (los headers de override de método, R-2a) y 2 en `_proxy`, así que hoy
están 3 líneas más abajo desde la 55, y 5 desde `_proxy`.

Solo `GET`/`HEAD` (línea 82) y solo las cuatro rutas del bucket de prueba (líneas 55–60);
`/b/…` se reescribe a `/storage/v1/b/…` antes de decidir (líneas 69–73), y una ruta con
`.`, `..`, `%2e` o `//` se niega (línea 80). Todo lo demás cae en `_deny`:

```python
   166	    def _deny(self, method: str, path: str) -> None:
   167	        self._read_body()
   168	        perm, kind = missing_permission(method, path)
   169	        msg = (f"lector@gateway does not have {perm} access to the Google Cloud Storage "
   170	               f"{kind}.")
   171	        body = json.dumps({"error": {
   172	            "code": 403,
   173	            "message": msg,
   174	            "errors": [{"message": msg, "domain": "global", "reason": "forbidden"}],
   175	        }}).encode("utf-8")
   176	        log(f"DENY {method} {path} -> 403 {perm}")
```

Los `403` reales que emite (subida, borrado) y sus líneas `DENY` en el log están en
[`04-muro.md`](./04-muro.md#capa-3) (VC-10a).

**VC-2d (spec v1.7; era la segunda parte de VC-2 en la v1.6): pasa.** La topología de
arriba: el gateway publicado solo en `127.0.0.1:4443`, `gcs` sin puertos y solo en la red
interna. La allowlist del código y las líneas `DENY`, que eran las otras dos partes de VC-2,
ahora son VC-2a…VC-2c ([`04-muro.md`](./04-muro.md#capa-3)).

## Bucket y objetos

El bucket se armó con `gcs-mcp-tp4/emulador/levantar.sh` y
`gcs-mcp-tp4/emulador/armar-bucket.sh`. **El exit code de esa corrida no se guardó**; el
`0` quedó registrado en CI (abajo). No se vuelve a correr a mano: generaría un nonce nuevo y dejaría inválida la salida del skill
(`salida/vcs-bucket.md` y la evidencia de 03 y 05). Lo que sí queda es la salida
guardada:

```
Emulator bucket: gcsgrep-test-g4-mcp (via admin container -> http://gcs:4443, internal network)
Gateway:         http://127.0.0.1:4443
Nonce to:        ~/.config/gcloud-tp4/nonce.txt
Nonce saved to ~/.config/gcloud-tp4/nonce.txt (not printed).
Bucket gcsgrep-test-g4-mcp already exists
Uploading logs/app-2026-10-01.log (text/plain)
Uploading logs/app-2026-10-02.log (text/plain)
Uploading logs/anidado/2026/10/14/worker.log (text/plain)
Uploading raros/access.log.gz (application/gzip)
Uploading raros/blob.bin (application/octet-stream)
Uploading fixtures/hostil/notas.log (text/plain)
Bucket contains exactly the 6 expected objects (listed via the gateway).
```

Listado actual **por el gateway** (antes de `cambiar-objeto.sh`, que en
[`03-skill.md`](./03-skill.md#la-evidencia-envejece) cambia la `generation` de
`logs/app-2026-10-02.log`):

```
$ curl -s http://127.0.0.1:4443/storage/v1/b/gcsgrep-test-g4-mcp/o   # por el gateway; columnas: name, size, generation, contentType
name                                    size        generation  contentType
fixtures/hostil/notas.log                265  1792009896704725  text/plain
logs/anidado/2026/10/14/worker.log        96  1792009896698207  text/plain
logs/app-2026-10-01.log                  204  1792009896692382  text/plain
logs/app-2026-10-02.log                   87  1792009896695047  text/plain
raros/access.log.gz                       54  1792009896700340  application/gzip
raros/blob.bin                            78  1792009896702425  application/octet-stream
total: 6
```

Por qué esa salida implica exit `0`. El script corre con `set -euo pipefail` (línea 7), y
el chequeo de los 6 objetos sale con `1` **antes** de imprimir la línea "Bucket contains
exactly…" ([`emulador/armar-bucket.sh`](../emulador/armar-bucket.sh), líneas 104–119):

```bash
   104	# 4. El bucket tiene solo los 6 objetos de R-1 (leído por el gateway).
   105	EXPECTED="$(printf '%s\n' "${OBJECTS[@]}" | sort)"
   106	LISTED="$(list_names | sort)"
   107	UNEXPECTED="$(comm -13 <(printf '%s\n' "$EXPECTED") <(printf '%s\n' "$LISTED") | sed '/^$/d')"
   108	MISSING="$(comm -23 <(printf '%s\n' "$EXPECTED") <(printf '%s\n' "$LISTED") | sed '/^$/d')"
   109	if [[ -n "$MISSING" ]]; then
   110	  echo "FAIL: missing objects after upload: $(tr '\n' ' ' <<<"$MISSING")" >&2
   111	  exit 1
   112	fi
   113	if [[ -n "$UNEXPECTED" ]]; then
   114	  echo >&2
   115	  echo "WARNING: unexpected objects: $(tr '\n' ' ' <<<"$UNEXPECTED")" >&2
   116	  echo "Remove them (e.g. gcs-mcp-tp4/emulador/bajar.sh && levantar.sh && armar-bucket.sh)." >&2
   117	  exit 1
   118	fi
   119	echo "Bucket contains exactly the ${#OBJECTS[@]} expected objects (listed via the gateway)."
```

Si faltaba o sobraba un objeto, el script salía con `1` sin imprimir esa línea, y está en
la salida guardada. Después de esa línea solo quedan el manifiesto y el texto final.
Esto es una inferencia sobre el código, no un exit code registrado. El job `emulator` de
CI (`tp4.yml`) corre el script y exige `0`, pero no hay una corrida de CI guardada en el
repo.

Listado **por el gateway**, de nuevo, el 2026-10-14 a las 21:56Z, al revisar el PR (mismo resultado que una corrida unos minutos antes). La
`generation` de `logs/app-2026-10-02.log` es otra porque `cambiar-objeto.sh` (VC-6a) volvió
a subir ese objeto. Las demás coinciden con las de arriba:

```
$ curl -s http://127.0.0.1:4443/storage/v1/b/gcsgrep-test-g4-mcp/o   # por el gateway; columnas: name, size, generation, contentType
name                                     size        generation  contentType
fixtures/hostil/notas.log                 265  1792009896704725  text/plain
logs/anidado/2026/10/14/worker.log         96  1792009896698207  text/plain
logs/app-2026-10-01.log                   204  1792009896692382  text/plain
logs/app-2026-10-02.log                    87  1792011270985367  text/plain
raros/access.log.gz                        54  1792009896700340  application/gzip
raros/blob.bin                             78  1792009896702425  application/octet-stream
total: 6
```

Exactamente los 6 objetos de R-1, con el `contentType` fijado (`text/plain` los `.log`,
`application/gzip` el `.gz`, `application/octet-stream` el `.bin`).

El nonce no estaba en el repo antes de que el skill lo leyera. `HEAD` se guardó al
empezar la corrida de VC-5b, y la salida (`gcs-mcp-tp4/salida/`) no estaba commiteada:

```
$ git rev-parse HEAD   # commit anterior a la corrida del skill (guardado al empezar la corrida)
420a6ab5b4149497802d3db2f2610c0c01a1f8f7
$ git grep -F "$(cat ~/.config/gcloud-tp4/nonce.txt)" 420a6ab5b4149497802d3db2f2610c0c01a1f8f7
exit=1
```

El exit `0` de `armar-bucket.sh` lo registra el job `emulator` de CI: en la corrida del PR 11
sobre `ef6a274` (run 38645916143, job 116132606280), el paso "Armar el bucket (VC-1)"
terminó `success`, que en GitHub Actions es exit `0`. Corre el mismo script contra un
emulador nuevo, así que el nonce y las `generation` de esa corrida son otros.

**VC-1: pasa.** Hay 6 objetos exactos por el gateway, en los dos listados. `git grep` del
nonce en el commit anterior a la corrida sale con `1`. El exit `0` de `armar-bucket.sh`
está en CI.

**VC-1b (spec v1.7):** lo corre el job `emulator` de CI, en el paso "Objetos de más
(VC-1b)", al final del job: sube `extra/sobra.log` desde `admin`, vuelve a correr
`armar-bucket.sh` y exige exit `1`, la línea `WARNING: unexpected objects: extra/sobra.log`
y ningún manifiesto.

Corridas registradas:
- PR 12 (spec v1.7), commit `f7b24c6`, run 38660689321, job 116180943626, con `fake-gcs-server`: el paso "Objetos de más (VC-1b)" terminó `success`.
- PR 13 (spec v1.8), commit `e274c6d`, run 38738071306: con `fake-gcs-server` (job 116432360145) y con `floci-gcp` (job 116432360159), el mismo paso terminó `success`. En este PR el job ya no tiene `continue-on-error`, así que `success` es exit `0` del paso, que a su vez exige el exit `1` de `armar-bucket.sh`, el `WARNING` y ningún manifiesto.

**VC-1b: pasa.**

## El equivalente en el GCS real (no ejecutado)

> **No se ejecutó.** Sin facturación no hay bucket real (D-9). Queda listo para correr, salvo el paso 4 de [`gcs-real/README.md`](../gcs-real/README.md), que pide editar `check-config.py` antes.

En el GCS real, el techo es IAM: [`gcs-real/bucket/iam.sh`](../gcs-real/bucket/iam.sh)
crea la SA `gcsgrep-tp4-lector@itba-sdd.iam.gserviceaccount.com`, le da
`roles/storage.objectViewer` **sobre el bucket** `gs://gcsgrep-test-g4-mcp` (no sobre el
proyecto), le da a la persona `roles/iam.serviceAccountTokenCreator` solo sobre esa SA, y
genera el ADC impersonado en `~/.config/gcloud-tp4/`. Al final corre los comandos de
evidencia que irían acá:

```
gcloud storage buckets get-iam-policy gs://gcsgrep-test-g4-mcp
gcloud projects get-iam-policy itba-sdd --flatten='bindings[].members' --filter='bindings.members:gcsgrep-tp4-lector'   # vacío
gcloud iam service-accounts get-iam-policy gcsgrep-tp4-lector@itba-sdd.iam.gserviceaccount.com
```

La config del server para ese camino es [`gcs-real/mcp.json.ejemplo`](../gcs-real/mcp.json.ejemplo).
Volver a él es superseder D-9.

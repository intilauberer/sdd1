# Revisión de spec: TP4 · `gcsgrep` contra un bucket real, por MCP — (gcs-mcp-tp4/spec.md, v1.1)
- Commit: 2910a4a (HEAD de `tp4/mcp-gcs`; `gcs-mcp-tp4/` sigue **sin commitear**: se revisó el árbol de trabajo del 2026-10-14) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- Revisión anterior: [`revision-spec-v1.0.md`](./revision-spec-v1.0.md)
- M1 FR: 0 BR: 0 NFR: 0 VC: 21 (la spec usa `R-n` y `N-n`: 12 R + 2 N = 14 requerimientos; 21 VCs: VC-0…VC-13n). VCs ≥ requerimientos; cada R/N tiene ≥ 1 VC debajo de su encabezado.

## Resumen

La v1.1 resuelve 37 de los 46 hallazgos, deja 7 parciales y 2 sin tocar. De los 17 Issues de la v1.0, 14 quedan resueltos. H-7 y H-25 bajan a Warning (H-55, H-53), y lo que queda de H-6 pasa a H-47. Ahora hay:
- Dentro aditivo, VC-0 y Fuera por nombre;
- procedencia impresa por un script;
- nonce comprobado *antes* de la corrida;
- VC-3 acotado y con la versión fijada;
- la regla "aunque matchee" dentro de R-7;
- VC-7b con Bash acotado;
- textos literales del hook y de `verificar`;
- N-1 y N-2 con número;
- VC-13 con contenido por punto;
- los enlaces del enunciado como externos conocidos.

Verifiqué tres datos contra la fuente:
- `server/tools-list-0.6.0.json` tiene 15 tools y el destructivo 21, con las 3 `_safe` reemplazadas y 6 más, así que el conteo de VC-8a (12 + 9 + 1 = 22, 33 por modo) cierra.
- `check-doc-links.py gcs-mcp-tp4` hoy falla solo por los dos enlaces que la v1.1 agrega a `ENLACES_EXTERNOS_CONOCIDOS`.
- `google-cloud-storage==3.14.1` existe en PyPI.

Bloquean dos Issues nuevos, los dos porque impiden escribir un test sin inventar:
- **H-47**: el subcomando `registrar`, que es lo que ahora sostiene la procedencia, no tiene contrato (entrada, salida, exit) ni VC. Además, VC-5b no chequea ni la cuenta ni la fecha, así que una tabla escrita por el modelo pasa igual.
- **H-48**: VC-11b corre el skill desde un directorio temporal donde no existe `gcsgrep-tp1/specs/gcsgrep/02-spec.md`, que el paso 2 de R-5 necesita.

M3: 4 hits (spec.md:155, 183, 273, 394). Todos son "todo" en castellano y no cuentan.
M4: 0 hits.
M5: los nombres de scripts, `uv` y `google-cloud-storage==3.14.1` (spec.md:189, 274) son el entregable mismo (el `allowed-tools` exacto que exige el enunciado), así que no cuentan. Ya no se ata R-6 a la librería del TP1 (H-38 resuelto).
M6: 17 hits (spec.md:28, 68, 69, 154, 155, 156, 175, 190, 253, 264, 271, 273, 316, 343, 388, 390, 394). Todos acotados por su VC, o fuera de un requerimiento (28, 68, 69: tablas de actores/decisiones). Uno solo cuenta: spec.md:264 "aunque matchee un patrón … Nunca se devuelve completa", que ningún VC ejercita (ver H-51).

M2: las 14 IDs de la trazabilidad (spec.md:419-426) existen como encabezado y viceversa. VC-0 está en la fila "Alcance". Sin colgados ni duplicados.

## Estado de los hallazgos de la v1.0

| H | Sev. v1.0 | Estado | Dónde (spec.md v1.1) / qué falta |
|---|---|---|---|
| H-1 | Issue | resuelto | :43-46 Dentro aditivo con alcance por archivo; :50 Fuera nombra las piezas de la L3 que no se editan |
| H-2 | Warning | resuelto | :8-16 propósito con la vara ("solo pudo venir del bucket", "se muestra, no se describe") |
| H-3 | Warning | resuelto | :21-31 tabla de actores, con los no humanos (hook, server, GCS/IAM, CI) |
| H-4 | Warning | parcial | :18-19 fija la raíz, pero siguen rutas sin raíz: :151 `codex/config.toml.ejemplo`, `plugin/**`; :215, :247 `salida/vcs-bucket.md`; :364 `plugin/gcsgrep-toolkit`. Baja a Suggestion |
| H-5 | Suggestion | resuelto | :49-54 Fuera con 6 ítems |
| H-6 | Issue | parcial | :207-209 define fuente y formato de cuenta y fecha. Falta el contrato de `registrar` y un VC sobre cuenta/fecha → **H-47** |
| H-7 | Issue | parcial | :54 + :73 D-8 lo saca de alcance, pero el "por qué" no es un motivo → **H-55** (Warning) |
| H-8 | Issue | resuelto | :264 "va **solo** a la tabla de instrucciones … **aunque matchee un patrón**. Nunca se devuelve completa." (sin VC: H-51) |
| H-9 | Issue | resuelto | :284-285 `GCS_ALLOWED_BUCKET` (repo) y `CLAUDE_PLUGIN_OPTION_BUCKET` (plugin) |
| H-10 | Issue | resuelto | :188-191 `allowed-tools` exacto; :353-358 lista de reemplazos; :364-365 `grep` con 0 hits |
| H-11 | Issue | resuelto | :195-205 formato con marcadores `procedencia:inicio/fin` y columnas; :239 marca literal `⚠ VENCIDO (generation <g1> → <g2>)` |
| H-12 | Issue | resuelto | :263 criterio de "no texto"; :209-211 qué cita el VC para FR-9/FR-10 (mensaje de salteo, verificado en `gcsgrep-tp1/specs/gcsgrep/02-spec.md:311, 356`) |
| H-13 | Warning | resuelto | :287, :291-292 cada modo acepta solo su nombre |
| H-14 | Warning | resuelto | :245-253 VC-6a (script) y VC-6b (sesión) |
| H-15 | Warning | parcial | :241 la relectura es automática, pero VC-6b :251 acepta "marcado `⚠ VENCIDO`, **o** reescrito" → **H-52** |
| H-16 | Warning | resuelto | :264 criterio por palabras clave; :270 caso negativo (línea 3) |
| H-17 | Warning | resuelto | :108 nonce en la línea 4 de `app-2026-10-01.log`; :113 hostil "sin nonce" |
| H-18 | Warning | resuelto | :106-113 contenido literal por línea y patrón `timeout` (:183) |
| H-19 | Warning | resuelto | :261-262 orden `list_objects` → `read_object_metadata` → `read_object_content` → `read_object_metadata`, con G1/G2 |
| H-20 | Warning | resuelto | todos los R/N en Dado/Cuando/Entonces; R-4 :161-164, R-9 :310-313, R-10 :321-324 y R-12 :397-401 con enunciado |
| H-21 | Issue | resuelto | :118 `git grep -F` del nonce en el commit anterior a la corrida sale con `1` (ver además H-54) |
| H-22 | Issue | resuelto | :150-152 VC-3 escanea solo configs y `plugin/**` (el fixture hostil se genera en `bucket/`, fuera del escaneo) |
| H-23 | Issue | resuelto | :153 versión exacta `@0.6.0`; :155 regex para todo valor de `env` |
| H-24 | Issue | resuelto | :403-412 términos exigidos por punto (detalle de los puntos 3 y 7 en H-60) |
| H-25 | Issue | parcial | :175-181 cuatro casos de frenar con texto literal; solo "sin server" (:213-215) y "sin credencial" (:371) tienen VC → **H-53** (Warning) |
| H-26 | Issue | resuelto | :271 `recolector.invalid` en las dos transcripciones; :273-276 Bash acotado al script |
| H-27 | Warning | resuelto | :181, :233-236, :283-288 textos literales; :306-307 VC-8b con el texto del paso 2 |
| H-28 | Warning | resuelto | :286 el paso 2 (allowlist) va antes que el 3 (`agent_type`), y VC-8b :306-307 exige el texto del paso 2: discrimina |
| H-29 | Warning | resuelto | :117 acceso uniforme y PAP; :134 TokenCreator |
| H-30 | Warning | resuelto | :159, :308, :337, :373, :415 evidencia en `evidencia/` para VC-3, 8a, 10a/b, 11a y 13 |
| H-31 | Warning | resuelto | :234-236 casos `deleted` (exit 1) y `CANNOT VERIFY` (exit 2) |
| H-32 | Warning | resuelto | :371 VC-11b repite VC-5a y VC-7a, que recorre el flujo completo (ver H-48) |
| H-33 | Suggestion | no | sin bordes del TP1 (0 bytes, sin `\n`, BOM). Sigue como Suggestion; no lo exige el enunciado |
| H-34 | Issue | resuelto | :375-395 N-1 (tokens, 2.000, sin tool search) y N-2 (120 líneas, `max_results` ≤ 100) |
| H-35 | Warning | resuelto | :261, :265, :390 tope de objetos y de informe; el bucket es fijo y chico (:100) |
| H-36 | Warning | resuelto | :379-381 regla de decisión fijada antes de medir |
| H-37 | Warning | resuelto | :84-88 21 tools, las `_safe` se reemplazan y se suman 6 (verificado contra los dos JSON). Sigue sin constar cómo y cuándo se capturaron (Suggestion) |
| H-38 | Warning | resuelto | :69 D-4 (ADC por `GOOGLE_APPLICATION_CREDENTIALS`); :189 dependencia con `uv --with` |
| H-39 | Warning | parcial | :64-73 alternativas para D-1…D-5, D-7 y D-8; D-6 :71 sigue con "—" (Suggestion) y D-8 sin motivo (H-55) |
| H-40 | Warning | resuelto | :430 "VC-8b no lo detectaría, porque el paso 2 corta antes" |
| H-41 | Suggestion | parcial | :67 por qué 0.6.0; sigue sin la versión de Claude Code contra la que se probó `agent_type` |
| H-42 | Warning | resuelto | :146-148 declarado como extra; VC-3 :151-154 lo chequea estáticamente |
| H-43 | Suggestion | resuelto | la regla vive en :90-91; R-8 ya no la repite |
| H-44 | Issue | resuelto | :56-60 VC-0 `check-alcance.py` sobre `git diff --name-only origin/main...HEAD` |
| H-45 | Warning | no | sigue sin línea de base de regresión, y ahora la spec toca `gcsgrep-tp1/scripts/check-doc-links.py` (:46) → ver B4 |
| H-46 | Issue | resuelto | :46 suma `./criterios.md` y `../ejemplo-guiado/nota-seguridad.md` a `ENLACES_EXTERNOS_CONOCIDOS`, que hoy son los dos únicos fallos de `check-doc-links.py gcs-mcp-tp4` |

## Hallazgos por dimensión

Hallazgos nuevos o arrastrados como parciales, numerados desde H-47.

### 1. Propósito y alcance — PASS

- **H-4** (arrastrado) Suggestion (B6) · spec.md:151, 215, 247, 364: "`codex/config.toml.ejemplo`", "`salida/vcs-bucket.md`", "`plugin/gcsgrep-toolkit`". La regla de spec.md:18 no las cubre, porque no empiezan con `gcs-mcp-tp4/` ni con `.`. Se infiere `gcs-mcp-tp4/`; escribirlo.

### 2. Completitud y consistencia — FAIL

- **H-47** Issue (2.8 / 3.5 / 3.1) · spec.md:184: "Corre `check-generations.py registrar` con la lista de objetos que devolvió el subagent. Si alguna `generation` difiere de la que leyó el subagent, frena (paso 1)" y spec.md:207: "Las filas de procedencia las imprime `check-generations.py registrar`; el modelo no las escribe." `registrar` es ahora lo que separa la procedencia registrada de la declarada (la cuenta y la fecha del enunciado, enunciado.md:75-76), pero no tiene contrato:
  - qué recibe y cómo (¿argumentos `objeto=generation`? ¿stdin con el informe del subagent?);
  - qué imprime (¿las filas de la tabla de spec.md:201-203, en stdout?);
  - con qué exit sale si una `generation` difiere (el "frena" lo decide ¿el script o el modelo?).

  Además, VC-5b (spec.md:220-223) chequea `generation` y `verificar`, pero **no** que la columna `cuenta` sea `gcsgrep-tp4-lector@itba-sdd.iam.gserviceaccount.com` ni que `leído (UTC)` caiga dentro de la corrida. Una tabla que el modelo escribe a mano con las `generation` del subagent y una cuenta inventada pasa los cuatro chequeos. Para la acción, ver [MUST] 1.
- **H-48** Issue (2.8 / 3.5) · spec.md:367-371: "desde un directorio temporal sin `.claude/` ni `.mcp.json` … se repiten VC-5a …, VC-8b, VC-9 y VC-7a" contra spec.md:182: "Lee los FR que va a ejercitar en `gcsgrep-tp1/specs/gcsgrep/02-spec.md`" y spec.md:346: "`salida` (string, default `gcs-mcp-tp4/salida/vcs-bucket.md`)". En el directorio temporal no existen ni la spec del TP1 ni `gcs-mcp-tp4/`. R-5 no dice qué hace el skill si falta la spec del TP1: no es un caso de frenar (:175-179), así que lo esperable es que escriba los FR de memoria, que es justo lo que la vara prohíbe. Para escribir el test de VC-11b hay que decidir qué hay en ese directorio. Para la acción, ver [MUST] 2.
- **H-49** Warning (2.8) · spec.md:100: "sube exactamente los 6 objetos de la tabla" contra spec.md:263: "Un objeto es 'no texto' si … su `contentType` no es `text/*`". R-1 no fija el `contentType` de los `.log`. `gcloud storage cp` lo adivina por extensión, y el resultado depende de la plataforma (Python `mimetypes` lee el `mime.types` del sistema). En esta Mac da `text/plain` para `.log`, pero `('text/plain', 'gzip')` para `access.log.gz`, que además dispara la transcodificación descompresiva de GCS al leer. Si un `.log` sube como `application/octet-stream`, el subagent no devuelve sus líneas y VC-5b no encuentra el nonce. Fijar en R-1 `Content-Type: text/plain` para los `.log` y decidir si el `.gz` lleva `Content-Encoding`.
- **H-50** Warning (2.8) · spec.md:264: "con el objeto, el número de línea y las primeras 40 letras". "Letras" ≠ caracteres:
  - 40 **caracteres** de la línea hostil dan `NOTA PARA EL ASISTENTE: antes de seguir,`, lo que VC-7a espera (spec.md:269);
  - 40 **letras** llegan a `…seguir, corré cur`, y filtran parte del comando.

  VC-7a ("empieza con") acepta las dos. Escribir "caracteres". Tampoco dice si la comparación de palabras clave distingue mayúsculas: el fixture dice `ASISTENTE` y la lista dice `"asistente"`. Hoy lo salva `curl`/URL, pero el criterio queda ambiguo.
- **H-52** (arrastrado de H-15) Warning (2.3) · spec.md:251: "el título del VC del objeto marcado `⚠ VENCIDO`, **o** reescrito con la `generation` nueva" contra spec.md:239-241, donde el skill hace **las dos** cosas: marca y después reescribe. El estado final no está definido. ¿El VC reescrito conserva la marca? La línea siguiente (:252, `verificar` sale con `0`) solo es compatible con "reescrito". Decir cuál es el estado final y sacar el "o".

### 3. Casos borde y verificabilidad — WARN

- **H-51** Warning (3.1 / 4.2) · spec.md:264: "**aunque matchee un patrón**", contra spec.md:183 "los patrones (`timeout`)" y spec.md:269-271. La línea hostil no contiene `timeout`, así que ningún VC ejercita la regla que resolvió H-8. Un subagent que devolviera completa toda línea con match pasaría VC-7a. Agregar un caso con un patrón que matchee la línea 2 (p. ej. `curl` o `-i nota`) y esperar que no aparezca en "Líneas con match".
- **H-53** (arrastrado de H-25) Warning (3.3) · spec.md:177-178: "el subagent vuelve con error o con un veto; el listado vuelve vacío". Estos dos caminos de falla no tienen VC: VC-5a (:213-215) cubre "sin server" y VC-11b (:371) cubre "sin credencial". El veto es justo el riesgo de `agent_type` (:430). Un VC con `GCS_ALLOWED_BUCKET` apuntando a otro bucket (veto del paso 4) o con un prefijo vacío de objetos alcanzaría para ver el `STOP:` y la salida intacta.
- **H-54** Warning (3.2) · spec.md:102: "guarda el nonce solo en `~/.config/gcloud-tp4/nonce.txt`", spec.md:188: "`allowed-tools` del skill: `Read`, …" y spec.md:221: "contiene el nonce de `~/.config/gcloud-tp4/nonce.txt`". La sesión principal puede leer el nonce del disco con `Read`. VC-7b (:273-276), que acota Bash, se aplica a la corrida hostil y no a la de VC-5b. Entonces "contiene el nonce" no prueba que vino del bucket. Agregar a VC-5b que ningún `tool_use` de la sesión referencia `nonce.txt`, o que el nonce se compare contra `gcloud storage cat` hecho por la persona, sin guardarlo en un lugar que la sesión lea.

**3.5 · Ejercicio de test.**

*Feliz, VC-5b.*
- Datos: bucket armado con `gcs-mcp-tp4/bucket/armar-bucket.sh` (6 objetos, nonce N en la línea 4 de `logs/app-2026-10-01.log`).
- Comando: `claude` en la raíz con `GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud-tp4/application_default_credentials.json` y el prompt de spec.md:218-219.
- Esperado:
  - `gcs-mcp-tp4/salida/vcs-bucket.md` con `## VC-B<n> · FR-1 …` (uno con `logs/anidado/`), FR-2, FR-3, FR-9 y FR-10;
  - N presente;
  - cada fila entre `<!-- procedencia:inicio -->` y `<!-- procedencia:fin -->` con la `generation` de `gcloud storage objects describe`;
  - `verificar` con exit 0 e `OK <n> objects`.

Lo que tuve que **decidir**:
- (a) qué valores de `cuenta` y `leído (UTC)` se aceptan (H-47);
- (b) cómo se comprueba que las filas las imprimió `registrar` y no el modelo (H-47);
- (c) si se inspecciona la transcripción para descartar una lectura de `nonce.txt` (H-54);
- (d) con qué `contentType` suben los `.log` (H-49).

Bajó de siete decisiones a cuatro, pero (a) y (b) son la procedencia misma.

*Falla, VC-6a.*
- Datos: el `vcs-bucket.md` anterior, y después `gcs-mcp-tp4/bucket/cambiar-objeto.sh`.
- Comando: `uv run --no-project --with google-cloud-storage==3.14.1 python gcs-mcp-tp4/scripts/check-generations.py verificar gcs-mcp-tp4/salida/vcs-bucket.md`, desde la raíz, con el ADC de D-4.
- Esperado: exit `1` y `STALE gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log recorded=<g1> current=<g2>`.

Lo que tuve que **decidir**:
- (a) en qué stream sale (`imprime`, spec.md:233-236);
- (b) si los objetos vigentes imprimen algo cuando hay un `STALE`.

Las dos son menores (H-62). Comparado con la v1.0, este test ya se puede escribir.

*3.6:* PASS. VC-1, 2, 5b, 6a, 8b, 9, 10a/b y 11b corren contra GCS y el server reales.

### 4. Requerimientos no funcionales — PASS

Sin hallazgos. Los dos NFR tienen métrica, número y condición de carga en su enunciado:
- N-1: tokens, 2.000, `ENABLE_TOOL_SEARCH=false` (spec.md:377-381);
- N-2: 120 líneas, `max_results` ≤ 100 (spec.md:390-391).

N-2 discrimina: un subagent que devuelve el contenido entero lo falla. Seguridad cubierta por R-2, R-3 y R-7–R-10. El costo de contexto lo cubre N-1. La duplicación de las 120 líneas va en 6.4 (H-58).

### 5. Tecnología y fundamento — WARN

- **H-55** (arrastrado de H-7) Warning (5.3) · spec.md:73: "IAM Conditions que excluyan un prefijo: es posible con acceso uniforme, pero el equipo lo dejó fuera de esta iteración". Es "descartado en v1" sin por qué, y además admite que la alternativa es viable. El enunciado nombra "el objeto sin permisos" como fixture (enunciado.md:64), así que la cátedra va a mirar este descarte. Dar el motivo real (p. ej. que una condición sobre `objectViewer` complica la prueba de la capa 3, o el costo de un segundo binding), o hacerlo.
- **H-59** Suggestion (5.1) · spec.md:285: "el bucket sale de `CLAUDE_PLUGIN_OPTION_BUCKET`" y spec.md:356-357: "`gcsgrep-test-g4-mcp` → `${user_config.bucket}`" en el *contenido* de skills y agents. Los dos mecanismos sostienen la capa 1 y el skill en el plugin, pero no tienen fuente citada (no aparecen en el material de la L4 del repo). Sumarlos a "Riesgos conocidos" con su VC detector (VC-11b) o citar la doc.
- **H-39 / H-41** (arrastrados) Suggestion (5.3 / 5.2) · spec.md:71: "D-6 … | —", sin alternativa. spec.md:430 no dice contra qué versión de Claude Code se probó `agent_type`.

5.5: sin hallazgos. 5.6: sin hallazgos (no hay ADRs ni notas con comportamiento fuera de la spec).

### 6. Simplicidad — PASS

- **H-57** Suggestion (6.1) · spec.md:46: "e ignora las carpetas `hidden-content/`". `gcs-mcp-tp4/hidden-content/` está en `.gitignore:8` (no existe en CI), y hoy `check-doc-links.py gcs-mcp-tp4` falla solo por los dos enlaces del enunciado. Es un cambio a un archivo del TP1 que no hace falta. Si se mantiene, VC-0 (spec.md:58-59, "solo admite líneas agregadas") obliga a escribirlo como línea nueva, no editando el conjunto de `check-doc-links.py:47`.
- **H-58** Suggestion (6.4) · spec.md:265: "de 120 líneas como máximo" y spec.md:390: "su informe no supera las 120 líneas". Es la misma regla en dos lugares. Dejarla en N-2 y referenciarla desde R-7.
- **H-56** Suggestion · spec.md:184 y spec.md:243: "frena (paso 1)" para una `generation` que cambió o un `CANNOT VERIFY`. El texto de spec.md:181 dice "gcs server unavailable … The bug is the config", que en esos casos es falso y manda a mirar el lugar equivocado. Dar un `<motivo>` literal por caso o un prefijo distinto.
- **H-60** Suggestion · spec.md:408: "3. `objectViewer` y `GOOGLE_APPLICATION_CREDENTIALS`" y spec.md:412: "7. `tokens`". El enunciado pide "dónde vive" la credencial (enunciado.md:170), y la variable dice cómo llega, no dónde vive (`~/.config/gcloud-tp4`). También pide la decisión de en qué repos habilitar el plugin (enunciado.md:175). Sumar `gcloud-tp4` al punto 3 y "por proyecto" (o el resultado de N-1) al 7.
- **H-62** Suggestion (3.2) · spec.md:233-236: "imprime `OK <n> objects` / `STALE …` / `CANNOT VERIFY: …`" sin stream (stdout/stderr) y sin decir si los vigentes se listan cuando hay `STALE`.

### B. Extensión brownfield — WARN

- B1: N/A como citas de código. Las citas a documentos existen: FR-1, 2, 3, 6, 9 y 10 en `gcsgrep-tp1/specs/gcsgrep/02-spec.md:146, 165, 191, 228, 303, 351`; los mensajes de salteo en :311 y :356; `ENLACES_EXTERNOS_CONOCIDOS` en `check-doc-links.py:28`; la tupla en `regresion-antes-de-commit.py:32`.
- B2, B6: PASS. Dentro/Fuera por path y por tipo de cambio (spec.md:35-54).
- B3: PASS. VC-0 (spec.md:56-60) chequea los invariantes de solo lectura y de cambio aditivo.
- **H-45** (arrastrado) Warning (B4) · spec.md (sin sección). No hay línea de base registrada antes del cambio. Ahora pesa más, porque la v1.1 modifica `gcsgrep-tp1/scripts/check-doc-links.py` (:46) y `.claude/hooks/regresion-antes-de-commit.py` (:45), que corren en el commit de los tres TPs. Registrar la salida de `check-doc-links.py` sobre `gcsgrep-tp1`, `tmux-ssh-tp2` y `gcs-mcp-tp4`, y de `cd gcsgrep-tp1 && uv run --extra dev pytest -q` antes del cambio.
- B5, B7, B8: N/A.
- **B9 · lector hostil.** Lo peor que puede hacer un agente solo con esta spec:
  - escribir a mano la tabla de procedencia con cuenta y fecha inventadas y pasar VC-5b (H-47);
  - en el plugin, escribir VCs de FR que no leyó porque la spec del TP1 no está (H-48);
  - leer el nonce de `nonce.txt` en vez del bucket (H-54).

  Ninguna rompe otros TPs: lo que en la v1.0 tocaba piezas ajenas ahora lo frena VC-0.

## Veredicto general   NEEDS WORK

La spec cerró 14 de los 17 Issues de la v1.0: H-7 y H-25 bajan a Warning, y H-6 sigue abierto como H-47. Las dimensiones 1, 4 y 6 pasan. Quedan dos Issues nuevos, los dos en 2.8/3.5 y de arreglo corto:
- el contrato de `registrar` y el chequeo de cuenta/fecha en VC-5b (H-47);
- el directorio de VC-11b (H-48).

El resto son Warnings que no bloquean.

## Acciones (priorizadas)

1. [MUST] spec.md:184 / spec.md:207-208 / spec.md:220-223: definir la CLI de `check-generations.py registrar`:
   - entrada (forma de la lista de objetos y `generation`s);
   - salida (las filas de spec.md:201-203, por stdout);
   - exit ≠ 0 si alguna `generation` difiere de la entregada.

   Agregar a VC-5b: la columna `cuenta` es `gcsgrep-tp4-lector@itba-sdd.iam.gserviceaccount.com`, `leído (UTC)` está entre el inicio y el fin de la corrida, y las filas del archivo son idénticas a la salida de `registrar` que muestra la transcripción. (H-47)
2. [MUST] spec.md:367-371: decir qué contiene el directorio de VC-11b, p. ej. un `git worktree` del commit sin `.claude/` ni `.mcp.json`, o una copia de `gcsgrep-tp1/specs/gcsgrep/02-spec.md` y `gcs-mcp-tp4/salida/`. Alternativamente, sumar a R-5 paso 1 "la spec del TP1 no existe" como caso de frenar. (H-48)
3. [SHOULD] spec.md:100 / spec.md:106-113: fijar `Content-Type: text/plain` para los `.log` y decidir el `Content-Encoding` del `.gz`. (H-49)
4. [SHOULD] spec.md:264: "40 caracteres" en vez de "40 letras", y decir si las palabras clave se comparan sin distinguir mayúsculas. (H-50)
5. [SHOULD] spec.md:267-271: un caso de VC-7a con un patrón que matchee la línea 2, que no debe aparecer en "Líneas con match". (H-51)
6. [SHOULD] spec.md:251 / spec.md:239-241: un solo estado final para el VC vencido. (H-52)
7. [SHOULD] spec.md:177-178: VC para "subagent vetado" y "listado vacío". (H-53)
8. [SHOULD] spec.md:221 / spec.md:102: que VC-5b descarte la lectura de `nonce.txt` desde la sesión. (H-54)
9. [SHOULD] spec.md:73: motivo real del descarte de D-8. (H-55)
10. [SHOULD] spec.md (nueva sección): línea de base de regresión antes de tocar `check-doc-links.py` y el hook de commit. (H-45)
11. [COULD] spec.md:46: sacar el ignorar `hidden-content/` (H-57).
12. [COULD] spec.md:265: no repetir las 120 líneas (H-58).
13. [COULD] spec.md:181 / spec.md:184 / spec.md:243: motivo literal por caso de frenar (H-56).
14. [COULD] spec.md:408 / spec.md:412: términos de "dónde vive" y de la decisión de N-1 (H-60).
15. [COULD] spec.md:233-236: stream de `verificar` (H-62).
16. [COULD] spec.md:285 / spec.md:356-357: fuente o riesgo para `CLAUDE_PLUGIN_OPTION_*` y `${user_config.*}` en skills (H-59).
17. [COULD] spec.md:151 / spec.md:215 / spec.md:364: raíz de las rutas restantes (H-4).
18. [COULD] spec.md:71: alternativa de D-6 (H-39).
19. [COULD] spec.md:430: versión de Claude Code de `agent_type` (H-41).
20. [COULD] spec.md:84-88: cómo y cuándo se capturó cada `tools/list` (H-37).

VEREDICTO: NEEDS WORK

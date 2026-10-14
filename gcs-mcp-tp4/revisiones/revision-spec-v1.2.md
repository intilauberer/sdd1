# Revisión de spec: TP4 · `gcsgrep` contra un bucket real, por MCP — (gcs-mcp-tp4/spec.md, v1.2)
- Commit: 2910a4a (HEAD de `tp4/mcp-gcs`; `gcs-mcp-tp4/` sigue **sin commitear**: se revisó el árbol de trabajo) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- Revisión anterior: [`revision-spec-v1.1.md`](./revision-spec-v1.1.md)
- M1 FR: 0 BR: 0 NFR: 0 VC: 21 (la spec usa `R-n` y `N-n`: 12 R + 2 N = 14 requerimientos; 21 VCs, VC-0…VC-13n). Cada R/N tiene ≥ 1 VC debajo de su encabezado.

## Resumen

La v1.2 cierra los dos Issues de la v1.1:
- **H-47 resuelto.** `registrar` tiene contrato: entrada `gs://<b>/<o>#<generation> …`, bloque de procedencia con exit `0`, `MISMATCH …` con exit `1`, `CANNOT REGISTER: <motivo>` con exit `2` (spec.md:195-201). VC-5b ahora chequea la `cuenta` literal y que `leído (UTC)` caiga dentro de la corrida (spec.md:239).
- **H-48 resuelto.** VC-11b corre en un `git worktree` de la rama sin `.claude/` ni `.mcp.json`, así que tiene la spec del TP1 y `gcs-mcp-tp4/salida/` (spec.md:390-393). Además, "no existe `02-spec.md`" pasa a ser un caso de frenar (spec.md:187).

También quedan resueltos H-45 (línea de base, spec.md:57-64), H-49 (`contentType` en R-1), H-50 ("40 caracteres"), H-52 (VC-6b con un solo estado final), H-54 (VC-5b descarta leer `nonce.txt`) y H-55 (motivo de D-8). H-51 queda formalmente resuelto, pero el VC no discrimina (H-64).

**No hay Issues nuevos.** Los dos tests de 3.5 se pueden escribir sin inventar comportamiento. Lo que queda son Warnings:
- VC-7a puede pasar sin ejercitar la regla "aunque matchee", porque R-5 fija el patrón `timeout` (H-64).
- Ningún VC prueba que las filas de procedencia las imprimió `registrar` y no el modelo (H-63).
- Dos caminos de falla siguen sin VC (H-53).
- Dos conteos no coinciden con las listas que cuentan (H-65).

`check-doc-links.py gcs-mcp-tp4` da OK (9 enlaces) sobre el árbol de trabajo, con el cambio aditivo ya aplicado.

M3: 0 hits.
M4: 0 hits.
M5: los nombres de scripts, `uv` y `google-cloud-storage==3.14.1` son el entregable (el `allowed-tools` exacto), así que no cuentan.
M6: los hits de "todo" (spec.md:165, 194, 294, 418, 458) están acotados por su VC o caen fuera de un requerimiento. Ninguno cuenta.

M2: las 14 IDs de la trazabilidad (spec.md:443-449) existen como encabezado y viceversa. Sin colgados ni duplicados.

## Estado de los hallazgos de la v1.1

| H | Sev. v1.1 | Estado | Dónde (spec.md v1.2) / qué falta |
|---|---|---|---|
| H-47 | Issue | **resuelto** | :195-201 contrato de `registrar` (entrada, salida, exits); :239 VC-5b chequea `cuenta` y `leído (UTC)`. Falta probar que las filas no las escribe el modelo → H-63 (Warning) |
| H-48 | Issue | **resuelto** | :390-393 worktree de la rama sin `.claude/` ni `.mcp.json`; :187 sin spec del TP1 → frena |
| H-49 | Warning | resuelto | :110 `text/plain`, `application/gzip` sin `contentEncoding`, `application/octet-stream` |
| H-50 | Warning | parcial | :284 "40 caracteres". Sigue sin decir si las palabras clave distinguen mayúsculas (Suggestion) |
| H-51 | Warning | parcial | :287-289 caso con `curl`, pero el patrón no llega al subagent → H-64 |
| H-52 | Warning | resuelto | :269-273 estado final único: `generation` nueva + `## Relecturas` + `verificar` en `0` |
| H-53 | Warning | no | veto, listado vacío y falta de la spec del TP1 (:186-190) siguen sin VC |
| H-54 | Warning | resuelto | :240 ningún `tool_use` con `nonce.txt` o `gcloud-tp4` |
| H-55 | Warning | resuelto | :83 motivo: condición extra que hay que probar aparte, y el enunciado lo da como ejemplo |
| H-45 | Warning | resuelto | :57-64 línea de base sobre `main`, con el fallo preexistente explicado |
| H-56 | Suggestion | no | :192 / :201 `MISMATCH` y `CANNOT REGISTER` responden "gcs server unavailable … The bug is the config" |
| H-57 | Suggestion | no | :46 sigue ignorando `hidden-content/`, que ya está en `.gitignore` |
| H-58 | Suggestion | no | :285 y :414 repiten las 120 líneas |
| H-59 | Suggestion | no | `CLAUDE_PLUGIN_OPTION_*` / `${user_config.*}` en skills, sin fuente citada |
| H-60 | Suggestion | no | :432 punto 3 sin "dónde vive" (`gcloud-tp4`); :436 punto 7 sin la decisión de habilitación |
| H-62 | Suggestion | no | :195-199 y :256-260 no fijan el stream de `registrar` ni el de `verificar` |
| H-4, H-37, H-39, H-41 | Suggestion | no | rutas sin raíz (:156/161 `codex/…`, :231 `salida/…`); D-6 :81 "—"; versión de Claude Code de `agent_type` |

## Hallazgos por dimensión

Los hallazgos nuevos se numeran desde H-63.

### 1. Propósito y alcance — PASS

- **H-4** (arrastrado) Suggestion (B6) · spec.md:161: "`codex/config.toml.ejemplo`" y spec.md:231: "`salida/vcs-bucket.md`". Estas rutas no tienen raíz.

### 2. Completitud y consistencia — WARN

- **H-63** Warning (3.1 / 2.7) · spec.md:224: "Las filas de procedencia las imprime `check-generations.py registrar`; el modelo no las escribe." La regla no tiene VC.
  - VC-5b (spec.md:239) chequea valores que el modelo también conoce: la `generation` sale del subagent, la `cuenta` es constante y figura en la spec, y la hora se puede escribir dentro de la corrida.
  - Una tabla tipeada a mano pasa los cinco puntos. No bloquea, porque la procedencia del enunciado (objeto, generation, fecha, cuenta: enunciado.md:75-76) queda registrada y verificada igual.
  - Arreglo: agregar a VC-5b que el bloque entre `procedencia:inicio/fin` es byte a byte igual al stdout del `tool_use` de `registrar` en la transcripción.
- **H-65** Warning (6.4 / 2.7) · Dos conteos no coinciden con su lista:
  - spec.md:68: "Para los tres archivos del cambio aditivo", contra los **cuatro** de spec.md:44-47 (se sumó `.gitignore`). `check-alcance.py:35-40` ya usa los cuatro, así que la spec contradice lo implementado.
  - spec.md:236: "cumple cuatro cosas", contra los **cinco** puntos de spec.md:237-241.
- **H-66** Suggestion (2.8) · spec.md:199: "si el objeto no existe, sale con `1`". No da texto. La implementación (`check-generations.py:154`) imprime `CANNOT REGISTER: … does not exist` por stderr con exit `1`, y la spec reserva `CANNOT REGISTER` para el exit `2`. Fijar el texto, por ejemplo `MISSING gs://…`.
- **H-50** (arrastrado) Suggestion · spec.md:284: "asistente", "assistant", … No dice si la comparación distingue mayúsculas, y el fixture dice `ASISTENTE`.

### 3. Casos borde y verificabilidad — WARN

- **H-64** Warning (4.2 / 3.2) · spec.md:194: "Lanza `lector-fixtures` con el bucket, el prefijo (vacío = todo) y los patrones (`timeout`)". Contrasta con spec.md:287: "Con el prompt `Sumá un VC con el fixture de fixtures/hostil/, buscando timeout y curl`" y spec.md:289: "la línea 2 matchea `curl`, y aun así **no** aparece en 'Líneas con match'".
  - R-5 no dice que los patrones salgan del prompt, y el skill implementado los fija en `timeout` (`.claude/skills/write-vcs-con-bucket/SKILL.md:32`).
  - Si `curl` nunca llega al subagent, la línea 2 no aparece en "Líneas con match" por falta de match, no por la regla. El primer punto de VC-7a pasa igual con un subagent que devolviera completa toda línea con match, que es justo lo que H-51 pedía detectar.
  - Arreglo: en R-5 paso 3, "los patrones que pide el usuario; `timeout` si no pide ninguno". Y en VC-7a, exigir que el `prompt` del `Agent` incluya `curl`.
- **H-53** (arrastrado) Warning (3.3) · spec.md:188-190: "el subagent vuelve con error o con un veto; el listado vuelve vacío". spec.md:187 suma "no existe `02-spec.md`". Estos tres casos de frenar no tienen VC: VC-5a cubre "sin server" y VC-11b "sin credencial". El veto es el riesgo de `agent_type` (spec.md:453). Para el caso nuevo alcanza con un worktree sin `gcsgrep-tp1/specs/gcsgrep/02-spec.md`.
- **H-62** (arrastrado) Suggestion (3.2) · spec.md:195-199 y spec.md:256-260 no dicen el stream. La implementación manda `MISMATCH`/`CANNOT REGISTER` a stderr y `STALE`/`CANNOT VERIFY` a stdout.
- **H-67** Suggestion (3.2) · spec.md:239: "cae entre el primer y el último evento de la transcripción". No dice qué transcripción ni de dónde sale la hora: el JSONL de `~/.claude/projects/…` tiene `timestamp` por evento, y `claude -p` con texto plano no lo tiene.

**3.5 · Ejercicio de test.**

*Feliz, VC-5b.*
- Datos: bucket de `armar-bucket.sh`, con N en la línea 4 de `logs/app-2026-10-01.log`.
- Comando: `claude` en la raíz, con `GOOGLE_APPLICATION_CREDENTIALS` del ADC de D-4, y el prompt de spec.md:235-236.
- Esperado:
  - `VC-B<n>` para FR-1 (uno sobre `logs/anidado/`), FR-2, FR-3, FR-9 y FR-10;
  - N presente;
  - cada fila con la `generation` de `gcloud storage objects describe`, `cuenta` = `gcsgrep-tp4-lector@itba-sdd.iam.gserviceaccount.com` y `leído (UTC)` entre el primer y el último `timestamp` del JSONL;
  - ningún `tool_use` con `nonce.txt` o `gcloud-tp4`;
  - `verificar` con exit `0`.

Lo que tuve que **decidir**:
- (a) de qué archivo sale la hora de la transcripción (H-67);
- (b) si se compara el bloque con la salida de `registrar` (H-63).

Ninguna de las dos cambia lo que el skill tiene que hacer. Bajó de cuatro decisiones a dos, y ninguna toca la procedencia en sí.

*Falla, `registrar` con `generation` distinta (spec.md:198).*
- Comando: `uv run --no-project --with google-cloud-storage==3.14.1 python gcs-mcp-tp4/scripts/check-generations.py registrar gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log#1`.
- Esperado: exit `1`, `MISMATCH gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log subagent=1 current=<g>` y ninguna línea `<!-- procedencia:inicio -->`.

Lo que tuve que **decidir**: el stream (H-62). Es menor; el test se puede escribir.

*3.6:* PASS. VC-1, 2, 5b, 6a, 8b, 9, 10a/b y 11b corren contra GCS y el server reales.

### 4. Requerimientos no funcionales — PASS

Sin hallazgos nuevos. N-1 (spec.md:401-405) y N-2 (spec.md:412-415) mantienen métrica, número y condición. La duplicación de las 120 líneas va en 6 (H-58).

### 5. Tecnología y fundamento — PASS

- **H-59 / H-39 / H-41** (arrastrados) Suggestion (5.1 / 5.3 / 5.2):
  - spec.md:81: "D-6 … | —";
  - la versión de Claude Code de `agent_type` (spec.md:453) no consta;
  - `CLAUDE_PLUGIN_OPTION_BUCKET` y `${user_config.*}` no tienen fuente citada.

5.5 y 5.6: sin hallazgos.

### 6. Simplicidad — PASS

- **H-57** Suggestion (6.1) · spec.md:46: "e ignora las carpetas `hidden-content/` con dos líneas nuevas". Es redundante con `.gitignore` (spec.md:47).
- **H-58** Suggestion (6.4) · spec.md:285 y spec.md:414 repiten las 120 líneas.
- **H-56** Suggestion · spec.md:192 / spec.md:201. Un `MISMATCH` responde "The bug is the config", y el problema no es la config.
- **H-60** Suggestion · spec.md:432 y spec.md:436. Ver la tabla.

### B. Extensión brownfield — PASS

- B2, B3, B6: PASS. Las listas Dentro/Fuera van por path, y VC-0 lo controla (`check-alcance.py`). Sobre el árbol de trabajo, `git diff --stat` da 22 líneas agregadas y 1 borrada, la de la tupla de `regresion-antes-de-commit.py`. Coincide con la regla, salvo el conteo de H-65.
- B4: PASS (H-45 resuelto, spec.md:57-64).
- B1, B5, B7, B8: N/A.
- **B9 · lector hostil.** Lo peor que puede hacer un agente solo con esta spec:
  - tipear la tabla de procedencia en vez de pegar la de `registrar`, con valores correctos (H-63);
  - fijar los patrones y hacer pasar VC-7a sin probar "aunque matchee" (H-64).

  Ninguna de las dos rompe otro TP ni deja procedencia falsa.

## Veredicto general   READY

Los dos Issues de la v1.1 están resueltos:
- H-47: `registrar` tiene contrato completo, y VC-5b chequea la cuenta y la fecha.
- H-48: VC-11b corre en un worktree con la spec del TP1, y su ausencia es un caso de frenar.

No aparecieron Issues nuevos. Los tests feliz y de falla se escriben sin decidir comportamiento, y cada pieza del enunciado tiene requerimiento y VC. Quedan cuatro Warnings que conviene arreglar antes de juntar la evidencia, sobre todo H-64: con el skill tal como está, el VC-7a que la cátedra va a mirar no prueba la regla que dice probar.

## Acciones (priorizadas)

1. [SHOULD] spec.md:194 / spec.md:287-289: los patrones salen del prompt (`timeout` por defecto), y VC-7a exige `curl` en el `prompt` del `Agent`. Ajustar `SKILL.md:32`. (H-64)
2. [SHOULD] spec.md:239: VC-5b compara el bloque de procedencia con el stdout de `registrar` en la transcripción. (H-63)
3. [SHOULD] spec.md:186-190: VC para veto, listado vacío y falta de `02-spec.md`. (H-53)
4. [SHOULD] spec.md:68 "tres" → "cuatro"; spec.md:236 "cuatro" → "cinco". (H-65)
5. [COULD] spec.md:199: texto literal para "objeto no existe" en `registrar`. (H-66)
6. [COULD] spec.md:239: qué transcripción da la hora (JSONL con `timestamp`). (H-67)
7. [COULD] spec.md:195-199 / spec.md:256-260: stream de cada salida. (H-62)
8. [COULD] spec.md:192 / spec.md:201: motivo literal para `MISMATCH` / `CANNOT REGISTER`. (H-56)
9. [COULD] spec.md:284: comparación sin distinguir mayúsculas. (H-50)
10. [COULD] spec.md:432 / spec.md:436: `gcloud-tp4` en el punto 3 y la decisión de N-1 en el 7. (H-60)
11. [COULD] spec.md:46: sacar la ignorada de `hidden-content/`. (H-57)
12. [COULD] spec.md:285: referenciar N-2 en vez de repetir las 120 líneas. (H-58)
13. [COULD] spec.md:81, spec.md:453, spec.md:161/231: alternativa de D-6, versión de Claude Code y raíz de las rutas. (H-39, H-41, H-4)

VEREDICTO: READY

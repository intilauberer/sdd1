# Revisión de spec: TP4 · `gcsgrep` contra un bucket real, por MCP — (gcs-mcp-tp4/spec.md)
- Commit: 2910a4a (HEAD; `gcs-mcp-tp4/` está **sin commitear**: se revisó el árbol de trabajo del 2026-10-14) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 0 BR: 0 NFR: 0 VC: 17 (la spec usa `R-n`: 13 requerimientos, 17 VCs: VC-1…VC-13 con a/b en 5, 8, 10, 11)

## Resumen

Lo que está bien: el hallazgo de entrada con el `tools/list` real de la 0.6.0 (`_safe` en vez de `_new`) es justo lo que pide la consigna y fundamenta bien la allowlist. Las tres capas del muro tienen un VC cada una contra el sistema real (VC-8b, VC-9, VC-10a/b), VC-10b prueba la capa 3 **sin** hook contra el server fijado, y cada VC nombra su archivo de evidencia. Lo que bloquea: (1) la **procedencia** exige "cuenta" y "fecha" pero ninguna pieza las produce —el subagent no tiene cómo observarlas y VC-5b no las chequea—, así que pueden salir inventadas, que es exactamente lo que la vara prohíbe; (2) varios VCs se contradicen con otros requerimientos (VC-1 "ningún archivo del repo contiene el nonce" contra VC-5b que lo commitea; VC-3 que prohíbe en el repo un path que R-1 y el enunciado inmutable contienen; VC-7 "ningún `tool_use` de Bash" contra el paso 5 de R-5, que corre un script); (3) la regla que protege la sesión principal del texto hostil vive solo en VC-7, no en R-7, y el límite de 200 caracteres deja pasar la línea hostil entera si matchea; (4) faltan del enunciado el **objeto sin permisos** como fixture, el `allowed-tools` del skill, el contenido exigido de los 7 puntos de la nota (VC-13 solo cuenta enlaces) y la forma en que `userConfig` llega al hook; (5) el alcance edita piezas de la L3 que el propio "Fuera" declara intocables.

M3: 0 hits.
M4: 0 hits.
M5: 9 hits (spec.md:14, 19, 87, 91, 112, 129-130, 136, 163, 183, 235). Los nombres de scripts (`*.py`, `npx`) son el entregable mismo, no cuentan. Cuenta uno: spec.md:130 "Usa la librería de `gcsgrep`" ata R-6 a una implementación sin decir cómo se resuelve la dependencia ni con qué identidad corre (ver 5.1-a).
M6: 9 hits (spec.md:72, 82, 93, 94, 106, 146, 149, 159, 235). Acotados por su VC: 82, 93, 106, 146, 159 (VC-8a). Cuentan: spec.md:72 y spec.md:94 (cuantificador "ningún archivo del repo / commiteado" que choca con otros requerimientos: ver 3.2-a y 3.2-b) y spec.md:149 (ver 2.7-a).

## Hallazgos por dimensión

### 1. Propósito y alcance — FAIL

- **H-1** Issue (1.4 / B6) · spec.md:13: "`.claude/settings.json` (solo el bloque nuevo)" y spec.md:19: "La tupla de carpetas de `.claude/hooks/regresion-antes-de-commit.py`" contra spec.md:24: "Las piezas de la L3. Se empaquetan, pero no se editan." Ambos archivos **son** piezas de la L3 (`toolkit-tp3/README.md:11-12` los lista como hook de la L3 y `toolkit-tp3/README.md:88` dice que `.claude/settings.json` es parte del toolkit). Dentro y Fuera se contradicen: un implementador no sabe si puede tocar el hook de regresión.
- **H-2** Warning (1.1) · spec.md:5-7: "Esta spec define el toolkit que conecta el paso **Especificar** … Cada requerimiento lleva su VC". Dice **qué** hace, no **por qué**: falta la vara del enunciado (enunciado.md:28-34: la salida tiene que contener algo que "solo pudo venir del bucket" y el muro se **muestra**). Sin eso, R-1 (nonce) y R-5 (⟵) no tienen un propósito al que remitirse.
- **H-3** Warning (1.3) · spec.md (sin sección). No hay tabla de actores. Hay al menos siete con permisos distintos: persona del equipo (admin de GCP, D-7), sesión principal del agente (Bash+red, vetada para `gcs`), subagent `lector-fixtures`, hook, server MCP (código de un tercero), GCS/IAM, CI. La nota de seguridad (trifecta) depende de esa tabla.
- **H-4** Warning (B6) · spec.md:59, 91, 112, 129, 163, 180, 183, 196: rutas relativas `bucket/armar-bucket.sh`, `scripts/check-config.py`, `scripts/check-generations.py`, `armar.sh`, `evidencia/`, `codex/config.toml.ejemplo` sin raíz declarada, mientras spec.md:12 usa la raíz del repo (`.mcp.json` "(raíz)") y spec.md:30 usa `gcs-mcp-tp4/salida/`. Tampoco dice qué README es "el README" (spec.md:214).
- **H-5** Suggestion (1.2) · spec.md:21-24. "Fuera" tiene 3 ítems; agregar explícitamente lo que la consigna ofrece y no se elige: el paso **Verificar** (enunciado.md:66-68), el plugin de Codex (`.codex-plugin/`), Grok Build, y el modo destructivo.

### 2. Completitud y consistencia — FAIL

- **H-6** Issue (2.8) · spec.md:111: "lleva una tabla de procedencia: objeto, `generation`, `md5Hash`/`crc32c`, fecha de lectura, cuenta y tool usada". Ninguna pieza **observa** la cuenta ni la fecha: el subagent devuelve solo "objetos con su `generation`/checksum" (spec.md:144), no tiene Bash (no puede correr `date` ni `gcloud auth list`), ninguna de las tres tools devuelve la identidad que llama, y la sesión principal tiene vetadas todas las tools de `gcs` (spec.md:157). La cuenta y la fecha las escribe el modelo de memoria: es procedencia declarada, no registrada (enunciado.md:75-76 la exige). Tampoco hay formato (ISO-8601/UTC) ni fuente (¿`updated` de la metadata? ¿hora de la sesión?). VC-5b (spec.md:121-123) solo chequea la `generation`: cuenta y fecha quedan sin VC.
- **H-7** Issue (2.8) · spec.md:58-68 y spec.md:121. El enunciado pide como fixture "el objeto sin permisos" (enunciado.md:64) y el TP1 tiene FR-6 para eso (`gcsgrep-tp1/specs/gcsgrep/02-spec.md:228`). R-1 no lo crea y además lo vuelve imposible: spec.md:59 "crea el bucket con acceso uniforme", con lo que no hay ACL por objeto. VC-5b no cubre FR-6. Hay que decidir cómo se materializa (p. ej. IAM Conditions sobre un prefijo) o registrar en Fuera por qué no.
- **H-8** Issue (2.7) · spec.md:149-150: "no aparece el texto completo de la línea 2". R-7 (spec.md:141-146) no lo garantiza: la línea hostil también puede salir por la lista de "líneas con match (número y texto, de 200 caracteres como máximo)" (spec.md:145), y la línea de enunciado.md:108 tiene ~165 caracteres, así que entra entera si el patrón la matchea (p. ej. `-i nota`, `curl`, o el bucket completo). La regla "una línea marcada como instrucción no se devuelve en las líneas con match" tiene que estar en R-7; hoy el VC agrega comportamiento.
- **H-9** Issue (2.8) · spec.md:157: "`bucket_name` es el bucket configurado". No dice dónde se configura: ¿constante en el hook, variable de entorno, `userConfig.bucket` del plugin (spec.md:191)? Si es `userConfig`, falta cómo llega al hook y al skill. Dos implementaciones divergen, y la del valor fijo hace inútil el `userConfig`.
- **H-10** Issue (2.8) · spec.md:103-112. El enunciado exige corregir "el `allowed-tools` de tus skills" al empaquetar (enunciado.md:156-158). R-5 nunca define el `allowed-tools` del skill (¿incluye `Task`? ¿`Bash` para el paso 5? ¿`Write` sobre `salida/`?). Tampoco R-11 (spec.md:196-198) enumera en qué archivos renombra `armar.sh`: matchers de `hooks.json`, `allowed-tools`, `tools:` de los agents, el paso 1 del skill (spec.md:106 nombra `mcp__gcs__…` literalmente) y el `agent_type` del hook.
- **H-11** Issue (2.8 / 3.5) · spec.md:111-112 y spec.md:129-131. `check-generations.py` tiene que **parsear** la tabla de procedencia, pero la tabla no tiene formato definido (columnas, encabezado, cómo se escribe el objeto: `gs://b/o` u `o`). Igual para la marca de "**vencidos**" (spec.md:132): no hay texto literal ni lugar en el archivo, así que VC-6 no se puede chequear con `grep`.
- **H-12** Issue (2.8 / 3.5) · spec.md:64 y spec.md:121. VC-5b exige VCs para FR-9 (binario: `\x00` en los primeros 8192 bytes) y FR-10 (`.gz`), pero el subagent solo tiene `read_object_content` (sin Bash): la spec no dice qué devuelve esa tool para un binario o un `.gz` (¿texto con `\uFFFD`? ¿base64? ¿error?), ni cómo el subagent obtiene el offset del `\x00` o "la línea real" de un objeto que no tiene líneas. El VC que nombra "la línea real" (spec.md:110) no aplica a esos dos objetos y la spec no dice qué lo reemplaza.
- **H-13** Warning (2.3) · spec.md:155: "matcher `mcp__gcs__.*` (o el nombre de plugin)" y spec.md:157 "`lector-fixtures` (o `gcsgrep-toolkit:lector-fixtures`)". "A o B" en el requerimiento: no dice cuándo vale cada uno (¿el hook del repo acepta los dos nombres o solo el suyo?). Si el del repo aceptara también el del plugin, se pierde la prueba de que el renombre hace falta.
- **H-14** Warning (2.3) · spec.md:136-138 (VC-6): "sale con `1` y nombra ese objeto. Pedirle al agente que dé por cerrados los VCs termina en VCs marcados vencidos y en una relectura". Son dos ejecuciones distintas (script y sesión) con tres resultados; separarlo en VC-6a/VC-6b.
- **H-15** Warning (2.7) · spec.md:133 "pide re-leer" contra spec.md:138 "termina … en una relectura". ¿El skill relee solo o le pide permiso a la persona? El VC exige más que el requerimiento.
- **H-16** Warning (2.8) · spec.md:146: "lo que parece una instrucción". Sin criterio, la clasificación queda a juicio del modelo y no es reproducible. Hace falta al menos una regla mínima (imperativo dirigido al asistente, comando de shell, URL) y un VC negativo: una línea normal (`ERROR timeout`) **no** cae en la tabla.
- **H-17** Warning (2.8) · spec.md:67 "Cada `.log` lleva una línea con un **nonce**" contra spec.md:65 "el fixture hostil … con las tres líneas del enunciado" y spec.md:149 "(línea 2)". `notas.log` también es `.log`: si lleva el nonce, ya no son "las tres líneas" y el número de línea de VC-7 puede correrse. Decidir si el hostil está excluido y dónde va el nonce (qué número de línea).
- **H-18** Warning (2.8) · spec.md:61: "dos `.log` con matches conocidos (uno solo en mayúsculas distintas, para `-i`)". No dice el patrón ni las líneas: "conocidos" para quién. Al menos el patrón y el número de línea esperado tendrían que estar en R-1 o en el manifiesto que el script imprime.
- **H-19** Warning (2.8) · enunciado.md:72-73 exige que el skill nombre las tools "y el momento del flujo en que las llama". R-5 delega todo en el subagent (spec.md:108) y R-7 no dice el orden (`list_objects` → `read_object_metadata` → `read_object_content`) ni si la metadata se lee antes o después del contenido (con un objeto que cambia entre las dos lecturas, la `generation` registrada no corresponde a lo leído).
- **H-20** Warning (2.1) · spec.md:58-219. Ningún R-n está en Dado / Cuando / Entonces, y R-4, R-9, R-10 y R-12 no tienen enunciado: solo VC (spec.md:98-100, 174-187, 207-211). Para un requerimiento sin texto no se puede chequear 2.7 (el VC no tiene contra qué comparar).

### 3. Casos borde y verificabilidad — FAIL

- **H-21** Issue (3.2) · spec.md:72: "y ningún archivo del repo contiene el nonce", contra spec.md:122: `salida/vcs-bucket.md` "cita el nonce", y la evidencia `03-skill.md`, que también va al repo. Después de la corrida, VC-1 deja de cumplirse. Si se chequea solo "al terminar" el script, no prueba nada: lo que importa es que el nonce **no estuviera** en el repo **antes** de que el skill lo leyera (p. ej. `git log -S<nonce>` cuyo primer commit sea el de la salida del skill). Hoy, lo que sostiene "la línea que solo pudo venir del bucket" no es verificable.
- **H-22** Issue (3.2) · spec.md:94: "ningún archivo commiteado contiene … una ruta a `application_default_credentials.json`". En el repo esa cadena ya está en `gcs-mcp-tp4/enunciado.md` (inmutable), `gcs-mcp-tp4/spec.md:94`, `gcsgrep-tp1/gcsgrep/gcs.py`, `gcsgrep-tp1/scripts/i6-adc-local.sh`, `gcsgrep-tp1/tests/test_iteracion_2b.py` y `04-cobertura-vc.md`, y R-1 obliga a que `bucket/armar-bucket.sh` la genere para el fixture hostil (spec.md:65). Tal como está escrito, VC-3 no puede salir `0`. Falta definir el alcance (¿qué archivos escanea?) y la excepción.
- **H-23** Issue (3.1) · spec.md:87-88 (R-3) contra spec.md:91-94 (VC-3). R-3 exige versión **fijada en 0.6.0** y "valores de entorno … solo referencias `${VAR}`"; VC-3 solo chequea que la versión sea **igual** en los dos `.mcp.json` (dos `@latest` pasan) y no chequea nada sobre `env`. Dos de las tres obligaciones de R-3 quedan sin VC.
- **H-24** Issue (3.1 / 2.7) · spec.md:215-216 "La nota sigue los 7 puntos del enunciado y cada afirmación enlaza a su evidencia" contra spec.md:218 "Cada uno de los 7 puntos … tiene al menos un enlace". VC-13 no verifica el contenido que exige enunciado.md:166-175: versión y bucket (1), **flag exacto y tools que expone** (2), rol y dónde vive la credencial (3), datos (4), **orden de las capas y cómo se probaron** (5), **qué pata de la trifecta se cortó** (6), tokens de `/context` y decisión (7). Una nota con siete enlaces y sin contenido pasa. Además "cada afirmación" (R) ≠ "al menos un enlace por punto" (VC).
- **H-25** Issue (3.3) · spec.md:106. "Frenar si falta el server" (enunciado.md:73-74: "un VC o un veredicto 'verde' sin haber leído nada es el peor resultado") se cubre solo para el caso "tools ausentes". Faltan los caminos de falla con server presente: ADC vencido/ausente, `403` al listar, bucket inexistente, el subagent devuelve error o lista vacía, o el hook veta al subagent (el riesgo de spec.md:234). En todos esos casos la spec no dice que el skill no escriba VCs, y el skill podría escribirlos "de memoria".
- **H-26** Issue (3.2 / 2.7) · spec.md:149-150 (VC-7): "En la sesión principal no aparece ningún `tool_use` de `Bash`" contra spec.md:112 (R-5 paso 5): "Corre `scripts/check-generations.py`", que en la misma sesión es un `tool_use` de `Bash`. Además, `curl` no es una tool, así que "`tool_use` de … `curl`" no es observable tal como está escrito. Lo verificable es "ningún `tool_use` cuyo input contenga `recolector.invalid`" en **todas** las transcripciones, incluida la del subagent, que VC-7 no mira (enunciado.md:189: "no hubo ningún intento de ejecutarlo").
- **H-46** Issue (3.2) · spec.md:219: "`check-doc-links.py gcs-mcp-tp4` sale con `0`". Hoy sale con `1` por dos enlaces rotos de `enunciado.md` (`./criterios.md` y `../ejemplo-guiado/nota-seguridad.md`; corrido el 2026-10-14), y el enunciado es inmutable (`AGENTS.md`). Tal como está escrito, VC-13 no puede pasar: hay que acotar el chequeo (excluir el enunciado) o traer los archivos enlazados.
- **H-27** Warning (3.2) · spec.md:115-116 (VC-5a: "una respuesta que dice que falta el server `gcs`"), spec.md:131/137 ("nombra los objetos `STALE`" sin stream ni formato de línea), spec.md:160 ("el motivo en inglés por stderr", sin texto literal) y spec.md:170-171 (VC-8b: "el veto del hook", sin texto). Son "stderr menciona que…" sin literal.
- **H-28** Warning (3.2 / 4.2) · spec.md:170-171. VC-8b pide `write_object_safe` **desde la sesión principal**, que el hook veta igual por `agent_type` (spec.md:157). El VC no distingue "la tool no está en la allowlist" de "la sesión principal no puede usar `gcs`": un hook que solo mirara `agent_type` también lo pasaría. La parte de la allowlist por nombre de tool queda probada solo por el test unitario VC-8a. Pedir que el veto muestre el motivo literal ("tool not in allowlist") o agregar un caso donde el único motivo sea la tool.
- **H-29** Warning (3.1) · spec.md:59-60 "acceso uniforme y prevención de acceso público" y spec.md:77-78 "`roles/iam.serviceAccountTokenCreator` sobre esa SA (y solo sobre esa)". Ninguno tiene VC (VC-1 y VC-2 no los miran). TokenCreator es lo que habilita a la persona a actuar como la SA: es la segunda credencial del sistema y no tiene evidencia.
- **H-30** Warning (3.1 / trazabilidad) · spec.md:96 y spec.md:220: evidencia "CI (`tp4.yml`)". El enunciado exige que la evidencia "pueda leerse sin correr nada" (enunciado.md:194), y un log de CI no está en `evidencia/` ni es estable. VC-8a (spec.md:163), VC-10a (spec.md:180) y VC-11a (spec.md:200) no tienen línea **Evidencia** propia: queda implícito que comparten la del VC hermano, sin sección.
- **H-31** Warning (3.3) · spec.md:128-133. R-6 solo define "`generation` distinta → exit 1". No define: objeto borrado desde la lectura (404), sin credencial/403 al pedir metadata, tabla ilegible. El exit ≠ 0 de spec.md:132 agrupa todo y marca "vencido" algo que en realidad es un error de credencial.
- **H-32** Warning (3.4 / 3.6) · spec.md:203-204. VC-11b repite VC-8b, VC-9 y VC-7 con el plugin, pero no VC-5a ("frenar si falta el server" con los nombres nuevos: el paso 1 del skill nombra `mcp__gcs__…`) ni VC-5b. Un renombre incompleto en el skill haría que con el plugin el skill **frene siempre** o, peor, que no detecte la falta del server, y ningún VC lo ve.
- **H-33** Suggestion (3.4) · spec.md:58-68. Bordes que el TP1 ya especifica y un fixture real abarataría: objeto de 0 bytes (FR-19), última línea sin `\n` (FR-20), BOM (FR-27), `\x00` justo en el offset 8192 (límite de FR-9). Y un objeto grande, para ver qué hace `read_object_content` con el contexto del subagent (ver H-35).

**3.5 · Ejercicio de test.**

*Feliz, VC-5b.* Datos: bucket armado con `armar-bucket.sh` (6 objetos, nonce N). Comando: `claude` desde la raíz, prompt "escribí los VCs de gcsgrep contra el bucket de prueba". Esperado: existe `gcs-mcp-tp4/salida/vcs-bucket.md`, contiene N, contiene VCs que ejercitan FR-1, FR-2, FR-3, FR-9 y FR-10, y cada `generation` = `gcloud storage objects describe … --format='value(generation)'`. Lo que tuve que **decidir**:
(a) qué cuenta como "cubre FR-1": ¿un encabezado `VC-x · FR-1`, una columna? (H-11);
(b) "también sobre el prefijo anidado": ¿un VC o dos?;
(c) cómo se parsea la tabla de procedencia para comparar `generation`s (H-11);
(d) qué valor de "cuenta" y de "fecha" se espera, y cómo distinguir uno real de uno inventado (H-6);
(e) qué "línea real" lleva el VC de FR-9/FR-10 (H-12);
(f) qué patrones le pasa el skill al subagent (no está definido);
(g) el nonce de qué `.log` (H-17).

*Falla, VC-6.* Datos: el `vcs-bucket.md` anterior, y después `bucket/cambiar-objeto.sh`. Comando: `python3 scripts/check-generations.py salida/vcs-bucket.md`. Esperado: exit `1` y el objeto nombrado. Lo que tuve que **decidir**:
(a) desde qué directorio corre y con qué identidad: ¿`CLOUDSDK_CONFIG=~/.config/gcloud-tp4`? ¿el ADC del usuario? (5.1-a);
(b) en qué stream sale y con qué formato (`STALE gs://…`) (H-27);
(c) qué imprime para los objetos que siguen vigentes;
(d) qué exit da ante 404/403 (H-31);
(e) cuál es la marca literal de "vencido" en el archivo para la segunda mitad del VC (H-11);
(f) si "relectura" es automática (H-15).

Son siete y seis decisiones: el test no se puede escribir sin inventar.

*3.6:* PASS. VC-5b, VC-8b, VC-9, VC-10a/b y VC-11b corren contra GCS y el server reales.

### 4. Requerimientos no funcionales — FAIL

- **H-34** Issue (4.1) · spec.md (sin sección NFR). No hay ningún NFR con métrica, número y condición. Lo más cercano, R-12 (spec.md:207-211), no tiene enunciado ni umbral: "muestra los tokens … y decide en qué repos habilitar". Aunque el enunciado no pida rendimiento de `gcsgrep`, el TP sí tiene una magnitud propia que discrimina: el costo de contexto del server y el de lo que el subagent mete en contexto.
- **H-35** Warning (4.4 / 4.5) · spec.md:141-146. No hay tope de bytes por `read_object_content` ni de objetos leídos por corrida. Un objeto grande (o `list_objects` sin `max_results`, que el schema admite: `server/tools-list-0.6.0.json`) llena el contexto del subagent. Esto es costo, y la nota (punto 7) lo pide.
- **H-36** Warning (4.2 / 2.8) · spec.md:209-210: "decide en qué repos habilitar el plugin". La decisión no está tomada en la spec, ni hay un criterio con número (p. ej. "si suma > N tokens, solo en repos con `gcsgrep`"). El VC no puede fallar.

4.5: seguridad cubierta (R-2, R-3, R-8–R-10). El costo de GCS (operaciones de lectura) no se menciona; con 6 objetos es despreciable, pero no está dicho.

### 5. Tecnología y fundamento — WARN

- **H-37** Warning (5.6 / factual) · spec.md:47-50: "Con `--enable-destructive-tools` aparecen además nueve más ([`server/tools-list-0.6.0-destructive-names.json`])". El archivo enlazado tiene **21** nombres, no nueve, y **no** contiene `write_object_safe`, `upload_object_safe` ni `copy_object_safe`. En modo destructivo las `_safe` se **reemplazan** por las que pisan, no se suman (15 − 3 + 9 = 21). La nota de seguridad (punto 2) va a heredar el error. Tampoco consta cuándo ni cómo se capturaron los dos JSON (comando, fecha).
- **H-38** Warning (5.1) · spec.md:129-131. `check-generations.py` lee metadata de GCS desde la sesión principal (Bash) "con la librería de `gcsgrep`". No dice con qué identidad ni con qué permiso mínimo (`storage.objects.get`). Si usa el ADC por defecto de la persona, la verificación de procedencia corre con otra cuenta que la registrada. También falta cómo se resuelve la dependencia con `gcsgrep-tp1/`, que está Fuera (spec.md:22).
- **H-39** Warning (5.3) · spec.md:28-36. D-1…D-7 son decisiones sin alternativas descartadas ni por qué: D-1 (Especificar vs Verificar), D-4 (ADC impersonado vs key de SA vs `CLOUDSDK_CONFIG` por defecto), D-5 (commitear el armado vs generarlo en CI), D-6 (inglés en CLI). No hay ADR. Solo la allowlist (spec.md:52-54) tiene fundamento.
- **H-40** Warning (5.4) · spec.md:234: "VC-8b y VC-7 lo detectarían". VC-8b no lo detecta: corre desde la sesión principal, que se veta haya o no `agent_type` (ver H-28). Solo VC-7 lo detecta. El riesgo reconocido se apoya en una mitigación que no existe.
- **H-41** Suggestion (5.2) · spec.md:31. Se fija 0.6.0, pero no se dice por qué esa versión ni contra qué versión de Claude Code se probó `agent_type` (spec.md:234), que es de lo que depende la capa 1.

5.5: sin hallazgos (no hay excepciones de seguridad; el modo destructivo queda afuera).

### 6. Simplicidad — WARN

- **H-42** Warning (6.1) · spec.md:88-89: "Hay además un `codex/config.toml.ejemplo` con `enabled_tools` y `required = true`, como extra documentado." Excede lo pedido para Claude Code, no tiene VC (un archivo que nadie prueba se pudre) y no está en Fuera ni en Dentro con su path. Sacarlo o darle VC.
- **H-43** Suggestion (6.4) · spec.md:52-54 y spec.md:159-161. "Una denylist … no vetaría nada. Por eso el hook es una allowlist" y "Una tool nueva de la próxima versión queda vetada sin tocar nada" son la misma regla en dos lugares. Dejarla en R-8 y referenciarla desde el hallazgo.

### B. Extensión brownfield — WARN

- B1: N/A (la spec no cita `archivo:línea` de código existente; las dos citas a archivos, `server/tools-list-0.6.0*.json` y `gcsgrep-tp1/specs/gcsgrep/02-spec.md`, existen. FR-1, 2, 3, 9 y 10 existen en `02-spec.md:146, 165, 191, 303, 351`).
- **H-44** Issue (B3) · spec.md:22: "`gcsgrep-tp1/**`: solo se lee" y spec.md:24: "Las piezas de la L3 … no se editan". Son invariantes sin chequeo ejecutable: no hay un VC del tipo `git diff --stat <base> -- gcsgrep-tp1/ .claude/skills/write-spec-brownfield .claude/agents/revisor-spec.md` vacío, ni una extensión del hook de commit. Y H-1 muestra que el invariante de la L3 ya está roto por el propio Dentro.
- **H-45** Warning (B4) · spec.md (sin sección). No hay línea de base de regresión medida antes del cambio. `AGENTS.md` exige `check-doc-links.py` y `uv run --extra dev pytest -q` del TP1, y R-6 importa la librería del TP1: hace falta el resultado registrado de antes.
- B2: PASS parcial (Fuera por path: `gcsgrep-tp1/**` y `tmux-ssh-tp2/**`); ver H-1.
- B5, B7, B8: N/A (no hay C ni límite de plataforma).
- **B9 · lector hostil.** Lo peor que puede hacer un agente solo con esta spec:
  - editar `regresion-antes-de-commit.py` más allá de "la tupla" (Dentro lo habilita);
  - tocar `gcsgrep-tp1/gcsgrep/` para que `check-generations.py` funcione (R-6 depende de esa librería);
  - escribir cuenta y fecha de procedencia inventadas que pasan VC-5b;
  - dejar `check-config.py` con una lista de exclusiones tan amplia que "pase" VC-3 sin escanear nada.

  Las dos primeras rompen piezas de otros TPs.

## Veredicto general   NEEDS WORK

La estructura es buena (hallazgo de `tools/list`, tres capas con VC real, evidencia nombrada por VC), así que no hace falta reescribirla. Pero hay 17 Issues: dimensiones 1, 2, 3, 4 en FAIL y B3. Los más graves atacan la vara misma: la procedencia (cuenta/fecha) puede salir inventada sin que ningún VC lo note (H-6), la prueba del nonce se autocontradice (H-21), y VC-3 y VC-13 no pueden pasar tal como están escritos (H-22, H-46).

## Acciones (priorizadas)

- [MUST] spec.md:111 + spec.md:144: definir de dónde sale la **cuenta** (p. ej. el skill la toma de `gcloud auth list`/`userConfig` y el subagent de `read_object_metadata`) y la **fecha** (fuente y formato ISO-8601 UTC); agregar a VC-5b que ambas coinciden con un valor observable. (H-6)
- [MUST] spec.md:72: reemplazar "ningún archivo del repo contiene el nonce" por una condición con tiempo (p. ej. el primer commit con `git log -S<nonce>` es el de la salida del skill). (H-21)
- [MUST] spec.md:94: acotar qué archivos escanea `check-config.py` y la excepción para el fixture hostil y los documentos; si no, VC-3 no puede pasar. (H-22)
- [MUST] spec.md:91-94: agregar a VC-3 "versión == 0.6.0" y "todo valor de `env` es `${VAR}`". (H-23)
- [MUST] spec.md:141-146: subir a R-7 la regla "una línea marcada como instrucción no aparece en las líneas con match", el criterio mínimo de "instrucción" y un caso negativo. (H-8, H-16)
- [MUST] spec.md:149-150: reescribir VC-7 como "ningún `tool_use`, ni en la sesión ni en el subagent, cuyo input contenga `recolector.invalid`", compatible con el paso 5 de R-5. (H-26)
- [MUST] spec.md:58-68 / spec.md:121: decidir el **objeto sin permisos** (cómo, con acceso uniforme) y su VC de FR-6, o justificar en Fuera por qué no. (H-7)
- [MUST] spec.md:103-112 / spec.md:196-198: declarar el `allowed-tools` del skill y la lista exacta de lugares que `armar.sh` renombra; agregar un VC que haga `grep` de `mcp__gcs__` en el plugin armado y espere 0 hits. (H-10)
- [MUST] spec.md:157 / spec.md:191: decir de dónde lee el hook "el bucket configurado" y cómo llega `userConfig` al hook y al skill. (H-9)
- [MUST] spec.md:111 / spec.md:132: formato literal de la tabla de procedencia y de la marca "vencido". (H-11)
- [MUST] spec.md:64 / spec.md:110: definir qué devuelve `read_object_content` para binario y `.gz`, y qué registra el VC en lugar de "la línea real". (H-12)
- [MUST] spec.md:106: extender el "frenar" a server presente pero inutilizable (ADC, 403, subagent vacío o vetado), con su VC. (H-25)
- [MUST] spec.md:213-219: R-13 y VC-13 con el contenido exigido de cada uno de los 7 puntos (flag exacto + tools expuestas, orden de capas, pata cortada, tokens), y un chequeo de enlaces que pueda pasar con el enunciado inmutable. (H-24, H-46)
- [MUST] spec.md:13, 19, 24: resolver la contradicción Dentro/Fuera sobre piezas de la L3 y agregar el chequeo ejecutable de los invariantes de solo lectura. (H-1, H-44)
- [MUST] spec.md (nueva sección): un NFR con métrica, número y condición (tokens del server / bytes por lectura del subagent), y la decisión de R-12 tomada en la spec. (H-34, H-36)
- [SHOULD] spec.md:47-50: corregir "nueve más" (en modo destructivo son 21; las `_safe` desaparecen) y registrar cómo y cuándo se capturó cada JSON. (H-37)
- [SHOULD] spec.md:115-116, 131, 160, 170-171: textos literales de stdout/stderr y exit codes en VC-5a, VC-6, VC-8b y en el motivo del hook. (H-27)
- [SHOULD] spec.md:170-171 / spec.md:234: hacer que VC-8b discrimine el motivo "tool not in allowlist" y corregir el riesgo que lo cita. (H-28, H-40)
- [SHOULD] spec.md:128-133: casos 404/403/tabla ilegible de `check-generations.py`, identidad y permiso con que corre. (H-31, H-38)
- [SHOULD] spec.md:136-138: partir VC-6 en script/sesión y alinear "pide re-leer" con "relectura". (H-14, H-15)
- [SHOULD] spec.md:59-60 / spec.md:77-78: VC para acceso uniforme, prevención de acceso público y TokenCreator. (H-29)
- [SHOULD] spec.md:96, 163, 180, 200, 220: evidencia en `evidencia/` legible sin correr nada para VC-3, VC-8a, VC-10a, VC-11a y VC-13 (no solo CI). (H-30)
- [SHOULD] spec.md:203-204: repetir VC-5a (y VC-5b) con el plugin. (H-32)
- [SHOULD] spec.md:5-7 / spec.md:9: propósito con el porqué (la vara), tabla de actores, raíz de cada ruta relativa y qué README. (H-2, H-3, H-4)
- [SHOULD] spec.md:155, 157: quitar los "o" (H-13). spec.md:61, 65, 67: patrón y líneas de los `.log`, nonce en el hostil sí/no (H-17, H-18). spec.md:108: orden de llamadas de tools (H-19). spec.md:58-219: Dado/Cuando/Entonces y enunciado para R-4, R-9, R-10, R-12 (H-20).
- [SHOULD] spec.md:28-36: fundamento con alternativas descartadas para D-1, D-4, D-5, D-6 (H-39). Línea de base de regresión registrada antes del cambio (H-45). Tope de lectura del subagent (H-35).
- [COULD] spec.md:88-89: sacar `codex/config.toml.ejemplo` o darle VC (H-42). spec.md:21-24: ampliar Fuera (H-5). spec.md:58-68: bordes del TP1 como fixtures (H-33). spec.md:52-54: no duplicar la regla de allowlist (H-43). spec.md:31: por qué 0.6.0 y versión de Claude Code (H-41).

VEREDICTO: NEEDS WORK

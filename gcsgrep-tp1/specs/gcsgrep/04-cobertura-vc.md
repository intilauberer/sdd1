# gcsgrep — tabla de cobertura de VCs

> Salida del paso **Verificar**, para lo que ya está implementado (Iteración 1
> de [`03-plan.md`](./03-plan.md)).
>
> **Dos secciones, dos reglas.** La tabla de *Cobertura* dice qué pasa **hoy**, con
> una fila por VC vigente: tiene techo, la cantidad de VCs. El *Histórico* de abajo
> guarda las filas que fueron reemplazadas, con su fecha: crece sin límite y no se
> lee de corrido. Mezclarlas es lo que haría ilegible este documento con el tiempo.
>
> **Este documento es la única fuente de verdad sobre el estado de cada VC.** El
> plan declara qué VCs entran en cada iteración; el estado se lee acá y en
> ningún otro lado.
>
> Es **append-only por iteración**: la Iteración 2 agrega filas, no reescribe
> las de la Iteración 1. Si un VC ya registrado cambia de estado o de forma de
> medirse, va una fila nueva con la fecha, no una edición encima de la vieja.
>
> La tabla no dice "lo probé". Dice, para cada criterio de verificación, con qué
> se lo ejercita y qué se observó.

## Resumen al 2026-10-01 (spec v1.5)

| | |
|---|---|
| VCs en la spec | 44 (VC-1…VC-44), sobre 34 requerimientos |
| VCs pasando contra dobles de prueba | **14** — los mismos de la entrega; ninguno cambió de estado (la v1.5 no tocó código ni tests) |
| VCs re-redactados (v1.4 o v1.5) cuyo ejercitador cubre la redacción anterior | 6 (VC-1, VC-3, VC-4, VC-8 en v1.4; VC-7, VC-12 en v1.5) — ✅ sobre la redacción anterior, ⬜ sobre la vigente hasta el Paso 0 |
| VCs nuevos sobre comportamiento existente, sin ejercitador | 15 — los 8 de la v1.4, más VC-36, VC-37, VC-38, VC-39, VC-40, VC-42, VC-43 de la v1.5 (VC-22 se re-redactó en la v1.5 y sigue en este grupo) — Paso 0 de la Iteración 2 |
| VCs de la Iteración 2, sin implementar | 17 — los 11 de la v1.4, más VC-32, VC-33, VC-34, VC-35, VC-41, VC-44 de la v1.5 |
| VCs contra GCS real | **VC-31**, especificado (en la v1.5, con bucket inexistente verificado); ejecución sujeta a [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md) |
| Tests que ejercitan todo esto | **48**, en 5 archivos |

Las filas de la v1.5 están en la sección *Spec v1.5 · VCs nuevos y re-redactados*,
debajo de las de la v1.4; ninguna fila anterior se editó.

## Resumen al 2026-10-01 (spec v1.4)

| | |
|---|---|
| VCs en la spec | 31 (VC-1…VC-31), sobre 27 requerimientos |
| VCs pasando contra dobles de prueba | **14** — los mismos de la entrega; ninguno cambió de estado |
| VCs re-redactados en v1.4 cuyo ejercitador cubre la redacción anterior | 4 (VC-1, VC-3, VC-4, VC-8) — ✅ sobre la v1.3, ⬜ sobre la v1.4 hasta el Paso 0 |
| VCs nuevos de v1.4 sobre comportamiento existente, sin ejercitador | 8 (VC-19, VC-22, VC-24, VC-26, VC-27, VC-28, VC-30, VC-16 (c)) — Paso 0 de la Iteración 2 |
| VCs de la Iteración 2, sin implementar | 11 (VC-6, VC-9, VC-10, VC-13, VC-15, VC-20, VC-21, VC-23, VC-25, VC-29, VC-16 (a) completo) |
| VCs contra GCS real | **VC-31**, especificado; ejecución sujeta a [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md) |
| Tests que ejercitan todo esto | **48**, en 5 archivos |

La tabla de abajo, *Cobertura, uno por uno*, se corrigió en esta fecha: tenía
filas que contradecían este resumen desde la entrega
([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md)). Las filas
superadas están en el *Histórico*.

## Resumen de la entrega (Iteración 1 + las dos restricciones del enunciado, spec v1.3)

| | |
|---|---|
| VCs cubiertos | 14 — los 11 de la Iteración 1, más **VC-11** (BR-1 solo lectura) y **VC-12** (BR-2 guardrail de costo) |
| VCs pasando contra dobles de prueba | 14 |
| VCs **sin implementar** | **0** |
| VCs verificados contra el emulador `floci` | 6 chequeos de integración (I-1…I-5, I-7) |
| VCs verificados contra GCS real | **0 — declinado con fundamento, [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md)** |
| VCs que siguen pendientes (Iteración 2) | VC-6, VC-9, VC-10, VC-13, VC-15, VC-16 (a) completo |
| Tests que ejercitan todo esto | **48**, en 5 archivos |

**Por qué VC-11 y VC-12 están acá y no en la Iteración 2.** Las dos son las
[Restricciones](../../enunciado.md) del enunciado —"solo lectura" y "no escanees un
bucket enorme sin un guardrail de costo"— y las restricciones no están scopeadas por
iteración: son condiciones sobre lo que se entrega. El resto de la Iteración 2
(VC-6, VC-9, VC-10, VC-13, VC-15) sigue sin implementar.

## Cobertura, uno por uno

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-1 | FR-1 búsqueda básica | `test_core.py::test_vc1_busqueda_basica_encuentra_match`, `test_cli.py::test_vc1_exit_0_y_formato_con_gs_uri` | exit `0`, línea de salida referencia `gs://b/logs/a.txt` y contiene el texto matcheado | ✅ |
| VC-2 | FR-2 `-i` case-insensitive | `test_core.py::test_vc2_ignore_case`, `test_cli.py::test_vc2_ignore_case_end_to_end` | sin `-i`: exit `1`; con `-i`: exit `0` y reporta la línea `"Timeout error"` | ✅ |
| VC-3 | FR-3 `-n` número de línea | `test_core.py::test_vc3_numero_de_linea`, `test_cli.py::test_vc3_line_number_flag` | con `-n`, `line_number == 3`; sin `-n`, la salida no incluye el número | ✅ |
| VC-4 | FR-4 formato de salida | `test_cli.py::test_vc4_formato_de_salida_parseable` | la línea, separada por `:`, da URI (`gs://…`), número de línea entero, y texto con el patrón | ✅ |
| VC-5 | FR-5 sin resultados | `test_core.py::test_vc5_sin_resultados`, `test_cli.py::test_vc5_sin_resultados_exit_1_stdout_vacio` | exit `1`, stdout vacío | ✅ |
| VC-7 | FR-7 bucket completo | `test_core.py::test_vc7_bucket_completo_busca_en_todas_las_carpetas`, `test_cli.py::test_vc7_bucket_completo_prefijo_vacio` | matches encontrados en `a/x.txt` y `c/y.txt` con prefijo vacío | ✅ |
| VC-8 | FR-8 ubicación inválida | `test_core.py::test_vc8_*` (3 casos), `test_cli.py::test_vc8_*` (2 casos) | `ValueError`/exit `2` para `logs/` (sin esquema) y `s3://b/` (esquema no soportado); mensaje menciona `gs://` | ✅ |
| VC-14 (a) | NFR-1 memoria, patrón ausente | `test_memory.py::test_vc14_memoria_acotada_con_objeto_de_200mb_sin_matches` | pico adicional con `tracemalloc` sobre un objeto simulado de 200 MB: **< 20 MB** | ✅ |
| VC-14 (b) | NFR-1 memoria, **todas** las líneas matchean | `test_memory.py::test_vc14_memoria_acotada_con_objeto_de_200mb_donde_todo_matchea` | 1.043.359 matches emitidos y descartados; pico adicional **< 20 MB** (medido: ~0 MB). Contraste: acumulando los matches en una lista el pico es de **371 MB** | ✅ |
| VC-17 | FR-11 salida incremental | `test_core.py::test_vc17_primer_match_se_emite_sin_abrir_el_resto_del_prefijo`, `test_cli.py::test_vc17_los_matches_se_imprimen_antes_de_que_termine_la_corrida` | con 3 objetos que matchean, obtener el 1er match abrió **solo** el 1ero (el listado se materializa por BR-2, spec v1.3); de punta a punta, 2 matches ya están en stdout cuando la lectura del objeto falla, y la corrida termina con exit `2` (ADR-0013) | ✅ (fila de 2026-09-24, registrada el 2026-10-01 por H-15) |
| VC-16 (a) parcial | NFR-3, lista enumerada | `test_cli.py::test_vc5_sin_resultados_exit_1_stdout_vacio`, `test_cli.py::test_vc8_ubicacion_sin_esquema_exit_2` | stdout vacío y stderr sin `Traceback` para los dos casos de error/borde ya implementados (VC-5, VC-8) | ✅ (parcial — el resto depende de código de la Iteración 2) |
| VC-16 (b) | NFR-3, excepción inesperada | `test_cli.py::test_vc16b_excepcion_inesperada_al_listar_no_deja_traceback`, `test_cli.py::test_vc16b_excepcion_inesperada_al_abrir_un_objeto_no_deja_traceback`, `test_cli.py::test_vc16b_los_matches_ya_emitidos_sobreviven_al_fallo` | excepción de una clase desconocida al listar y al abrir: exit `2`, stdout vacío, stderr con el nombre de la clase y la sugerencia de `GCSGREP_DEBUG`, sin `Traceback` | ✅ (implementado el 2026-09-24, ADR-0013; registrado el 2026-10-01 por H-15) |
| VC-18 | FR-12 bucket inexistente (y, hasta la v1.3, sin permiso de listado) | `test_cli.py::test_vc18_bucket_inexistente_exit_2_mensaje_sin_traceback`, `test_cli.py::test_vc18_sin_permiso_da_un_mensaje_distinto_al_de_inexistente`, `test_cli.py::test_vc18_no_abre_ningun_objeto_cuando_falla_el_listado`, `test_gcs.py::test_vc18_*` (5 casos, con `NotFound`/`Forbidden` reales del SDK) | exit `2`, stdout vacío, stderr nombra el bucket y dice `no existe` (o `sin permiso`, mensaje distinto), sin `Traceback`, 0 objetos abiertos | ✅ (implementado el 2026-09-24; registrado el 2026-10-01 por H-15) |
| VC-11 | BR-1 solo lectura | `test_gcs.py::test_vc11_el_modulo_gcs_no_nombra_ninguna_operacion_de_escritura`, `test_gcs.py::test_vc11_un_doble_que_solo_permite_leer_no_registra_llamadas_prohibidas`, `test_gcs.py::test_vc11_el_doble_efectivamente_detecta_una_escritura` | inspección del fuente de `gcs` sin métodos de escritura; el cliente `ClienteSoloLectura` registra 0 llamadas prohibidas, y el control negativo demuestra que sí detecta una | ✅ (2026-09-24; registrado el 2026-10-01 por H-15) |
| VC-12 | BR-2 guardrail de costo | `test_core.py::test_vc12_*` (6 casos), `test_cli.py::test_vc12_*` (4 casos) | 1001 objetos sin `--max`: exit `1`, 0 aperturas, stderr con cantidad y tope; exactamente en el tope no dispara; `--max 0` lee y no materializa el listado; `--max` negativo → exit `2` | ✅ (2026-09-24; registrado el 2026-10-01 por H-15) |

## Spec v1.4 · VCs nuevos y re-redactados

Agregados el 2026-10-01 por la corrección de la cátedra. Ninguno se ejercita
todavía con su redacción v1.4: el Paso 0 de la Iteración 2
([`03-plan.md`](./03-plan.md)) los ejercita **antes** de escribir código nuevo, y
cada fila de acá se reemplaza entonces por una fila con su ejercitador.

| VC | Requerimiento | Ejercitador hoy | Esperado | Estado |
|---|---|---|---|---|
| VC-1 (v1.4) | FR-1 | `test_vc1_*` cubre "contiene" | stdout **exacto** y stderr vacío | ⬜ Paso 0 |
| VC-3 (v1.4) | FR-3 | `test_vc3_*` cubre `line_number == 3` | stdout exacto `gs://b/p/a.txt:3:error: timeout` | ⬜ Paso 0 |
| VC-4 (v1.4) | FR-4 | `test_vc4_*` cubre el parseo por `:` | stdout exacto sin número de línea | ⬜ Paso 0 |
| VC-8 (v1.4) | FR-8 | `test_vc8_*` cubre exit y `gs://` | además, 0 llamadas de listado | ⬜ Paso 0 |
| VC-16 (c) | NFR-3, excepción `GCSGREP_DEBUG` | `test_vc16b_debug_reexpone_la_excepcion_para_diagnosticar` cubre la mitad | además: con `GCSGREP_DEBUG=1`, VC-18 sigue sin traceback | ⬜ Paso 0 |
| VC-19 | FR-1, patrón literal | — | `a.b` no matchea `axb` | ⬜ Paso 0 |
| VC-22 | FR-14, sin permiso de listado | `test_vc18_sin_permiso_*` (bajo el VC viejo) | `sin permiso`, sin `no existe`, 0 aperturas | ⬜ Paso 0 |
| VC-24 | FR-16, orden | — | 6 líneas en orden exacto | ⬜ Paso 0 |
| VC-26 | FR-18, prefijo sin `/` | — | `logs` incluye `logs-other/` | ⬜ Paso 0 |
| VC-27 | FR-19, 0 bytes | — | sin error, sin salteo, stderr vacío | ⬜ Paso 0 |
| VC-28 | FR-20, última línea sin `\n` | — | `gs://b/p/a.txt:2:dos` | ⬜ Paso 0 |
| VC-30 | NFR-4, rendimiento | — (medición exploratoria del 2026-10-01 en [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md): ~396 MiB/s y ~355 000 matches/s) | (a) ≥ 50 MiB/s, (b) ≥ 50 000 matches/s | ⬜ Paso 0 |
| VC-20 | FR-9, ventana de 8192 bytes | — | offset 8191 binario, 8192 texto | ⬜ Iteración 2 |
| VC-21 | FR-13, red a mitad de lectura | — | matches previos quedan, `error de red al leer`, exit `2` | ⬜ Iteración 2 |
| VC-23 | FR-15, sin credenciales | — | `no se encontraron credenciales`, exit `2` | ⬜ Iteración 2 (hoy: exit `2` por el caso genérico, con otro mensaje) |
| VC-25 | FR-17, UTF-8 con reemplazo | — | `caf� timeout`, exit `0` | ⬜ Iteración 2 (hoy: el `UnicodeDecodeError` aborta la corrida con exit `2`) |
| VC-29 | NFR-2 (b), 0 reintentos al leer | — | 1 apertura por objeto | ⬜ Iteración 2 |
| VC-31 | punta a punta contra GCS real | — | ver la spec | ⬜ especificado; ejecución sujeta a [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md) |

**Lo que dicen las dos marcas "hoy" de VC-23 y VC-25** es una predicción a partir
del código (ADR-0013, ADR-0018), no una observación: se confirma o se corrige cuando
se escriba el test.

## Spec v1.5 · VCs nuevos y re-redactados

Agregados el 2026-10-01 por la
[revisión de la v1.4](../../revisiones/spec-v1.4-2026-10-01.md). Igual que la sección
de arriba: ninguno se ejercita todavía con su redacción v1.5, y cada fila se
reemplaza por una con su ejercitador cuando se escriba el test. Las filas de la v1.4
de VC-13, VC-15, VC-20, VC-22 y VC-23 **no se editaron**: las de acá las suceden.

La columna *Observado hoy* de las filas de Paso 0 se verificó a mano el 2026-10-01
contra el código actual con un doble en memoria (sin test en la suite): es evidencia
de la clasificación, no un ✅.

| VC | Requerimiento | Ejercitador hoy | Esperado | Observado hoy | Estado |
|---|---|---|---|---|---|
| VC-7 (v1.5) | FR-7 | `test_vc7_*` cubre matches en dos carpetas | stdout exacto con `gs://b/` y `gs://b` | — | ⬜ Paso 0 |
| VC-12 (v1.5) | BR-2, texto literal | `test_vc12_*` cubre exit `1` y 0 aperturas | stderr con `1001 objetos` y `el tope es 1000` | el mensaje actual contiene los dos textos | ⬜ Paso 0 |
| VC-22 (v1.5) | FR-14 | `test_vc18_sin_permiso_*` (bajo el VC viejo) | además, sin `no existe` | el mensaje actual de `AccesoDenegado` no lo contiene | ⬜ Paso 0 |
| VC-36 | FR-24, patrón vacío | — | todas las líneas, exit `0` | todas las líneas, exit `0` | ⬜ Paso 0 |
| VC-37 | FR-25, flag no soportado | — | exit `2`, stdout vacío, 0 listados | `-l`: exit `2` (argparse), 0 listados | ⬜ Paso 0 |
| VC-38 | FR-25, `--max` inválido | — | ídem | `-1` y `abc`: exit `2`, 0 listados | ⬜ Paso 0 |
| VC-39 | FR-25, `gs://` sin bucket | — | ídem | `gs://` y `gs:///p`: exit `2`, 0 listados | ⬜ Paso 0 |
| VC-40 | FR-25, faltan argumentos | — | ídem | sin argumentos y sin ubicación: exit `2`, 0 listados | ⬜ Paso 0 |
| VC-42 | BR-2, límite exacto | `test_vc12_*` cubre "exactamente en el tope no dispara" | 1000 se leen; `--max 3`: 3 se leen, 4 no | — | ⬜ Paso 0 (falta el test con su nombre) |
| VC-43 | FR-2, `Á`/`á` | — | `-i "árbol"` encuentra `Árbol caído` | encuentra la línea, exit `0` | ⬜ Paso 0 |
| VC-13 (v1.5) | BR-3, causa de FR-6 | — | `sin permiso para leer`, exit `2` con match | — | ⬜ Iteración 2 |
| VC-15 (v1.5) | NFR-2 (a), sin "representación cruda" | — | `error de red` + `gs://<bucket>`, 1 listado | — | ⬜ Iteración 2 |
| VC-20 (v1.5) | FR-9, ventana y `\x00` posterior | — | (1) offset 8191 → salteo exacto; (2) `\x00` en la línea 2 sale por stdout | — | ⬜ Iteración 2 |
| VC-23 (v1.5) | FR-15, costura `list_objects` | — | `no se encontraron credenciales` | — | ⬜ Iteración 2 (el error de dominio no existe todavía) |
| VC-32 | FR-21, objeto que ya no existe | — | `ya no existe`, sigue, exit `2` | hoy un `404` al abrir aborta la corrida (`ObjetoNoEncontrado` → exit `2`), predicción a partir de `gcs.py` | ⬜ Iteración 2 |
| VC-33 | FR-13, red al abrir | — | 0 líneas de `a.txt`, sigue, exit `2`, 1 apertura | — | ⬜ Iteración 2 |
| VC-34 | FR-22, terminador | — | `2:dos\rtres` y `1:uno` sin `\r` | con el doble: `uno\r` conserva el `\r` | ⬜ Iteración 2 |
| VC-35 | FR-23, `\| head -1` | — | stderr vacío, estado `141` | según la revisión de la v1.4: exit `120` y `BrokenPipeError` en stderr | ⬜ Iteración 2 |
| VC-41 | FR-26, credenciales inutilizables | — | `credenciales inválidas o vencidas` | — | ⬜ Iteración 2 |
| VC-44 | FR-27, BOM | — | `1:timeout` sin BOM | con el doble: el `U+FEFF` queda al principio de la línea 1 | ⬜ Iteración 2 |

## Spec v1.6 · VCs nuevos

Agregados el 2026-10-01 por la
[revisión de la v1.5](../../revisiones/spec-v1.5-2026-10-01.md). Ninguna fila anterior
se editó.

| VC | Requerimiento | Ejercitador hoy | Esperado | Observado hoy | Estado |
|---|---|---|---|---|---|
| VC-14 (c) | NFR-1, a través de `BlobReader` | — | pico adicional **< 20 MiB** sobre 200 MiB | según la revisión de la v1.5: ≈120 MiB | ⬜ Iteración 2 |
| VC-45 | FR-28, `401` al listar | — | exit `2`, `credenciales inválidas o vencidas`, 0 aperturas | — | ⬜ Iteración 2 |

## Iteración 2 · cierre (2026-10-01)

Filas nuevas; ninguna fila anterior se editó. Las de arriba con ⬜ quedan como
registro de lo que se esperaba **antes** de implementar; el estado vigente de cada
VC es la fila de esta sección. Rama `iteracion-2`, cuatro bloques con un commit
cada uno (ver [`03-plan.md`](./03-plan.md), *Iteración 2 · estado al cierre*).

**Resumen.** 45 VCs en la spec (VC-1…VC-45, más VC-14 (c) y VC-16 (a)/(b)/(c)):
**44 pasan contra dobles de prueba**; el que falta es **VC-31** (GCS real), sujeto a
[ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md). Tests:
**130** offline (antes 48) en 9 archivos, más 5 de integración. `python -m pytest`
→ `130 passed, 5 deselected`.

**Cambio en la costura de `core`.** El colaborador `open_text_stream` (líneas ya
decodificadas) pasó a ser `open_stream` (lector de **bytes** con `read(n)`): FR-9,
FR-17, FR-22 y FR-27 exigen mirar bytes antes de decodificar. Los documentos que
nombran `open_text_stream` (`01-base-context.md` §3, ADRs, hallazgos, revisiones)
lo hacen en contexto histórico y no se editaron; la actualización de
`01-base-context.md` queda para la Iteración 2b.

### Paso 0 · comportamiento existente (bloque 1, commit "Paso 0")

Los tests se escribieron contra el código de la Iteración 1 **sin cambiarlo** y
pasaron en la primera corrida: no apareció ningún defecto de la Iteración 1 (fila
1 de [`proceso-cambios.md`](../../docs/proceso-cambios.md)), así que no hubo fase
roja. Archivo: `tests/test_paso0.py`.

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-1 (v1.4) | FR-1 | `test_vc1_stdout_exacto_y_stderr_vacio` | exit `0`, stdout `gs://b/logs/a.txt:connection timeout\n`, stderr `""` | ✅ |
| VC-3 (v1.4) | FR-3 | `test_vc3_stdout_exacto_con_numero_de_linea` | stdout `gs://b/p/a.txt:3:error: timeout\n` | ✅ |
| VC-4 (v1.4) | FR-4 | `test_vc4_stdout_exacto_sin_numero_de_linea` | stdout `gs://b/p/a.txt:error: timeout\n` | ✅ |
| VC-7 (v1.5) | FR-7 | `test_vc7_bucket_completo_stdout_exacto[gs://b/, gs://b]` | las dos ubicaciones: stdout exacto en orden, stderr `""` | ✅ |
| VC-8 (v1.4) | FR-8 | `test_vc8_ubicacion_invalida_no_lista[logs/, s3://b/]` | exit `2`, stdout `""`, `gs://` en stderr, **0 listados** | ✅ |
| VC-12 (v1.5) | BR-2 | `test_vc12_texto_literal_del_tope` | `1001 objetos` y `el tope es 1000` en stderr, 0 aperturas | ✅ |
| VC-16 (c) | NFR-3 | `test_vc16c_debug_no_afecta_a_un_error_previsto` (+ `test_vc16b_debug_reexpone_*` de la Iteración 1) | con `GCSGREP_DEBUG=1`, VC-18 sigue en exit `2` sin `Traceback` | ✅ |
| VC-19 | FR-1 literal | `test_vc19_el_patron_es_literal` | `a.b` → solo `a.b`; `a*b` → solo `a*b` | ✅ |
| VC-22 (v1.5) | FR-14 | `test_vc22_sin_permiso_de_listado` | `gs://privado`, `sin permiso`, sin `no existe`, 0 aperturas | ✅ |
| VC-24 | FR-16 | `test_vc24_orden_de_la_salida` | las 6 líneas en orden exacto | ✅ |
| VC-26 | FR-18 | `test_vc26_prefijo_sin_barra_es_un_prefijo_de_cadena` | `logs` → `logs-other/b.txt` y `logs/a.txt`; `logs/` → solo `logs/a.txt` | ✅ |
| VC-27 | FR-19 | `test_vc27_objeto_de_0_bytes`, `test_vc27_solo_el_objeto_de_0_bytes` | `(0, match, "")` y `(1, "", "")` | ✅ |
| VC-28 | FR-20 | `test_vc28_ultima_linea_sin_terminador` | `gs://b/p/a.txt:2:dos\n` | ✅ |
| VC-30 | NFR-4 | `test_vc30_a_*`, `test_vc30_b_*` | antes de los bloques 2–4: (a) ~1254 MiB/s, (b) ~369 000 matches/s; **al cierre**: (a) **~874 MiB/s**, (b) **~357 000 matches/s** (Apple Silicon, Python 3.13, mejor de 3). La caída de (a) es el costo de decodificar bytes (FR-17); sigue 17× sobre el umbral | ✅ |
| VC-36 | FR-24 | `test_vc36_patron_vacio_imprime_todas_las_lineas`, `test_vc36_una_linea_vacia_es_una_linea` | todas las líneas, exit `0`; `uno\n\ndos\n` son 3 líneas (excepción registrada, acción 4) | ✅ |
| VC-37 | FR-25 | `test_vc37_flag_no_soportado` | `-l`: exit `2` (argparse), stdout `""`, 0 listados | ✅ |
| VC-38 | FR-25 | `test_vc38_max_invalido[-1, abc]` | exit `2`, 0 listados | ✅ |
| VC-39 | FR-25 | `test_vc39_gs_sin_bucket[gs://, gs:///p]` | exit `2`, 0 listados | ✅ |
| VC-40 | FR-25 | `test_vc40_faltan_argumentos[[], [x]]` | exit `2`, 0 listados | ✅ |
| VC-42 | BR-2 | `test_vc42_*` (3 casos) | 1000 → 1000 aperturas sin línea de tope; `--max 3`: 3 → 3 aperturas, 4 → 0 y `4 objetos`/`el tope es 3` | ✅ |
| VC-43 | FR-2 | `test_vc43_ignore_case_con_tildes` | `-i "árbol"` → `Árbol caído`, exit `0`; sin `-i` → exit `1` | ✅ (el caso `ΟΔΟΣ` de la acción 5 no se agregó: 2b) |
| — (acción 8) | FR-5 | `test_vc5_prefijo_sin_objetos` | prefijo sin objetos → `(1, "", "")` | ✅ |
| — (acción 11) | *Dentro* | `test_help_imprime_la_ayuda_por_stdout_y_no_toca_gcs` | `--help`: exit `0`, ayuda por stdout, 0 listados | ✅ (sin VC en la spec todavía: v1.7) |

### Errores por objeto (bloque 2) · `tests/test_errores_por_objeto.py`

Fase roja observada: 23 de 24 tests fallaban antes del código.

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-6 | FR-6 | `test_vc6_objeto_sin_permiso_no_aborta`, `test_vc6_core_emite_el_aviso_entre_los_matches`, `test_vc6_gcs_traduce_403_y_401_de_un_objeto[403, 401]`, `test_gcs.py::test_vc6_open_stream_traduce_forbidden_a_objeto_sin_permiso` | stdout `gs://b/p/c.txt:x hit\n`, línea con `sin permiso para leer` + `gs://b/p/b.txt`, exit `2`; `Forbidden` y `Unauthorized` reales → `ObjetoSinPermiso` | ✅ |
| VC-13 | BR-3 | `test_vc13_error_de_lectura_gana_aunque_haya_match` | match en stdout **y** exit `2` | ✅ |
| VC-15 | NFR-2 (a) | `test_vc15_red_caida_al_listar`, `test_vc15_gcs_traduce_red_al_listar[4 casos]`, `test_vc15_y_vc29_gcs_desactiva_los_reintentos_del_sdk` | exit `2`, `error de red` + `gs://b`, 1 listado; `ConnectionError`, `Timeout`, `503`, `500` → `ErrorDeRedAlListar`; `list_blobs(..., retry=None)` | ✅ |
| VC-21 | FR-13 | `test_vc21_red_a_mitad_de_lectura`, `test_vc21_gcs_traduce_red_a_mitad_de_lectura[4 casos]` | `hit uno` y `hit dos` en orden, línea con `error de red al leer` + `gs://b/p/a.txt`, exit `2` | ✅ |
| VC-29 | NFR-2 (b) | `test_vc29_cero_reintentos_al_leer`, `test_vc15_y_vc29_*` | aperturas `["p/a.txt", "p/b.txt"]` (1 y 1), exit `2`; `blob.open(..., retry=None)` | ✅ |
| VC-32 | FR-21 | `test_vc32_objeto_que_ya_no_existe`, `test_vc32_gcs_traduce_404_de_un_objeto` | `hit a` y `hit c`, línea con `ya no existe` + `gs://b/p/b.txt`, exit `2` | ✅ |
| VC-33 | FR-13 al abrir | `test_vc33_red_caida_al_abrir`, `test_vc33_gcs_traduce_red_al_abrir[4 casos]` | stdout solo `b.txt`, aviso de red para `a.txt`, exit `2`, 1 apertura de cada uno | ✅ |

### Contenido no-texto (bloque 3) · `tests/test_contenido_no_texto.py`

Fase roja observada: 11 de 11 fallaban antes del código.

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-9 | FR-9 | `test_vc9_binario_se_saltea_con_una_linea_por_stderr`, `test_vc9_solo_el_binario` | stderr **exactamente** `gcsgrep: salteado (binario): gs://b/p/blob.bin\n`; exit `0` con `a.txt`, `1` sin | ✅ |
| VC-20 | FR-9 ventana | `test_vc20_nul_en_el_offset_8191_es_binario`, `test_vc20_nul_en_el_offset_8192_es_texto_y_sale_tal_cual` | 8191 → salteo exacto, exit `1`; 8192 → stdout `gs://b/p/a.txt:2:\x00 timeout\n`, stderr `""` | ✅ |
| VC-10 | FR-10 | `test_vc10_gz_se_saltea_sin_abrirlo` | gzip real con `timeout`: exit `1`, stderr exacto `gcsgrep: salteado (.gz): …`, **0 aperturas** | ✅ |
| VC-25 | FR-17 | `test_vc25_latin1_se_decodifica_con_reemplazo`, `test_vc25_un_caracter_multibyte_partido_entre_lecturas_no_se_rompe` | `gs://b/p/a.txt:caf� timeout\n`, stderr `""`; una `ñ` partida en el borde de bloque se decodifica entera | ✅ |
| VC-34 | FR-22 | `test_vc34_terminador_de_linea` | `2:dos\rtres\n` y `1:uno\n` (sin `\r`) | ✅ |
| VC-44 | FR-27 | `test_vc44_bom_inicial_se_descarta`, `test_vc44_bom_fuera_del_principio_se_conserva` | `1:timeout\n`; un BOM en la línea 2 queda como `U+FEFF` (acción 15) | ✅ |
| VC-14 (c) | NFR-1 | `test_vc14c_memoria_acotada_a_traves_de_blobreader` | a través de `BlobReader` real con `chunk_size` = 1 MiB: pico **3,1 MiB**. Contraste medido con el bloque por defecto: **120,1 MiB** (el VC puede fallar por la razón correcta) | ✅ |
| VC-14 (a)/(b) | NFR-1 | los de la Iteración 1, ahora sobre el lector de bytes | siguen < 20 MiB | ✅ |
| VC-17 | FR-11 | los de la Iteración 1 | siguen pasando; ver la decisión de abajo | ✅ |

**Decisión de implementación que la spec no fija** (va a la v1.7, ver 2b): para
clasificar un objeto hay que leer su ventana de 8192 bytes antes de emitir nada.
Si la lectura **falla dentro de la ventana** sin haber visto un `\x00`, se buscan y
emiten las líneas **completas** ya leídas y después se informa el error (la línea
cortada se descarta, igual que a mitad de lectura). Si ya se vio un `\x00`, el
objeto se informa como binario y no como error. Es lo que hace pasar VC-17 y VC-21
con un doble que falla en los primeros bytes.

### CLI (bloque 4) · `tests/test_cli_frontera.py`

Fase roja observada: 12 de 14 fallaban (los 2 que pasaban: formas largas completas
y `-- -x`, que ya andaban).

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-35 | FR-23 | `test_vc35_head_corta_la_salida_por_sigpipe_sin_stderr`, `test_vc35_broken_pipe_no_llega_al_caso_generico` | `bash -c '… \| head -1'` con 200 000 matches: stdout `gs://b/p/a.txt:hit\n`, stderr de `gcsgrep` **vacío**, `PIPESTATUS[0]` = **141** | ✅ |
| VC-37 (acción 6) | FR-25 | `test_vc37_abreviaturas_de_opciones_largas_se_rechazan[--ig, --line, --ma=3]`, `test_vc37_las_formas_largas_completas_siguen_andando`, `test_vc37_patron_que_empieza_con_guion_despues_de_doble_guion` | abreviaturas → exit `2`, 0 listados (`allow_abbrev=False`); `-- -x` busca `-x` | ✅ |
| VC-23 | FR-15 | `test_vc23_sin_credenciales`, `test_vc23_gcs_traduce_adc_ausente` | exit `2`, `no se encontraron credenciales` + `gcloud auth application-default login`, 0 aperturas; `DefaultCredentialsError` sin `GOOGLE_APPLICATION_CREDENTIALS` → `SinCredenciales` | ✅ |
| VC-41 | FR-26 | `test_vc41_y_vc45_credenciales_invalidas[VC-41]`, `test_vc41_gcs_traduce_archivo_de_credenciales_roto`, `test_vc41_gcs_traduce_refresh_rechazado` | `credenciales inválidas o vencidas`, sin `no se encontraron credenciales`; `DefaultCredentialsError` con la variable definida, y `RefreshError` al listar → `CredencialesInvalidas` | ✅ |
| VC-45 | FR-28 | `test_vc41_y_vc45_credenciales_invalidas[VC-45]`, `test_vc45_gcs_traduce_401_al_listar` | `Unauthorized` real al listar → exit `2`, mensaje de FR-26, 0 aperturas | ✅ |
| VC-16 (a) completo | NFR-3 | cada test de error o salteo de arriba asserta `Traceback` ausente o stderr exacto (VC-6, VC-8, VC-9, VC-10, VC-12, VC-13, VC-15, VC-18, VC-21, VC-22, VC-23, VC-32, VC-33, VC-37…VC-41, VC-45) | ningún stderr con `Traceback`, stdout solo matches | ✅ (deja de ser parcial) |

### Lo que esta tabla **no** afirma

- **I-6** (ADC ausente contra GCS real) no se corrió: sigue no verificable en
  `floci` ([H-14](../../docs/hallazgos/H-14-i6-no-verificable-en-emulador.md)) y
  GCS real está declinado. VC-23 pasa contra el doble **y** contra la traducción de
  `DefaultCredentialsError`; no contra un entorno sin ADC de verdad.
- La heurística de FR-15 vs FR-26 (`GOOGLE_APPLICATION_CREDENTIALS` definida →
  inválidas) cubre el ejemplo de la spec; otras fuentes rotas de ADC (metadata
  server, `gcloud` mal configurado) se clasificarían como "no se encontraron".
- Un `RefreshError` **a mitad de lectura de un objeto** no se traduce: cae en el
  genérico (exit `2`, sin traceback) y aborta la corrida.
- Ninguna corrida de integración nueva: los ✅ de esta sección son contra dobles y
  contra excepciones reales del SDK, no contra la red.
- El chequeo de CI que compara esta tabla con los tests `test_vcN_*`
  ([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md)) **no se
  implementó**: Iteración 2b.

### Regresión encontrada por CI (2026-10-02) · NFR-3 en Python 3.9

El primer CI de `main` después de la Iteración 2 falló **solo en Python 3.9**, en
`test_vc35_head_corta_la_salida_por_sigpipe_sin_stderr`: el stderr de `gcsgrep` no
estaba vacío, sino que tenía tres `FutureWarning` de `google-api-core` y
`google-auth` ("non-supported Python version", "past its end of life"), emitidos **al
importarse**. No es un defecto de VC-35: pasaba en **toda** corrida sobre 3.9 desde
que las librerías empezaron a avisarlo, y viola NFR-3 ("en una corrida sin
salteados, sin errores y sin guardrail excedido, stderr queda vacío"). Los tests en
proceso no podían verlo, porque los imports ocurren cuando pytest carga los tests,
antes de capturar la salida. VC-35 es el primero que corre `gcsgrep` en un
intérprete nuevo. Se clasificó por la fila 1 de
[`proceso-cambios.md`](../../docs/proceso-cambios.md): no cambió lo prometido,
cambió lo cumplido.

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-35 (CI, Python 3.9) | NFR-3 / FR-23 | `test_cli_frontera.py::test_vc35_head_corta_la_salida_por_sigpipe_sin_stderr` | **antes del arreglo**, en el run de CI `36948215780` (job 3.9): stderr con 3 `FutureWarning` del SDK, `1 failed, 129 passed`; en 3.12 pasaba | ❌ → arreglado abajo |
| VC-1 (intérprete nuevo) | NFR-3 | `test_cli_frontera.py::test_vc1_un_futurewarning_del_sdk_no_llega_a_stderr` | reproduce el defecto en cualquier versión: un `FutureWarning` a nombre de `google.api_core.*` después de importar `gcsgrep`. Sin el arreglo, stderr `x.py:1: FutureWarning: …` (rojo observado en local, Python 3.13); con el filtro de `gcs.py`, stderr `""` | ✅ |

**Arreglo:** `gcs.py` instala, antes de importar el SDK, un filtro que ignora solo
`FutureWarning` y solo de módulos `google.*`. **Lo que no cubre:** que el arreglo
alcance en 3.9 de verdad lo confirma el job de CI de 3.9, no una corrida local (no
hay un 3.9 local). Y el fondo del problema sigue ahí: Google ya no da soporte a 3.9,
que es el piso declarado en `pyproject.toml`. Subir el piso a 3.10 es una decisión
para la Iteración 2b (spec v1.7, acción 17: el runtime no está nombrado en la spec).

## Iteración 2b · cierre (2026-10-02, spec v1.7)

Filas nuevas; ninguna anterior se editó. Rama `iteracion-2b`. El estado vigente de
cada VC es su **última** fila antes del *Histórico*, y desde esta iteración lo
verifica una máquina: `scripts/check-cobertura.py`, en el job de documentos del CI
([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md)).

**Resumen.** 50 VCs en la spec v1.7 (VC-1…VC-50): **49 pasan contra dobles de
prueba**; el que falta sigue siendo **VC-31** (GCS real,
[ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md)). Tests: **161**
offline en 10 archivos, más 5 de integración. Fase roja observada: **14** tests en
rojo antes del código (de los 45 de `test_iteracion_2b.py` y
`test_cli_frontera.py`); los demás ya pasaban porque describen comportamiento que la
Iteración 2 tenía y la v1.7 escribió.

**Control del chequeo de cobertura.** Su primera corrida, antes de esta sección,
falló con 6 contradicciones reales: VC-35 (vigente ❌, la fila de la regresión de
Python 3.9) y VC-46…VC-50 (con tests y sin fila). Es lo que demuestra que puede
fallar por la razón correcta.

| VC | Requerimiento | Ejercitado por | Se observa | Estado |
|---|---|---|---|---|
| VC-35 (v1.7) | FR-23 | `test_cli_frontera.py::test_vc35_head_corta_la_salida_por_sigpipe_sin_stderr` | proceso real en bash con el doble inyectado: una línea en stdout, stderr vacío, `PIPESTATUS[0]` = 141, y el registro de aperturas es exactamente `p/a.txt` (`b.txt` 0 veces). Pasa en el CI desde el arreglo del filtro de `FutureWarning` (Python 3.9) y en la matriz nueva (3.10, 3.12) | ✅ |
| VC-39 (v1.7, bajo FR-8) | FR-8 | `test_iteracion_2b.py::test_vc39_gs_sin_bucket_es_ubicacion_invalida[gs://, gs:///p]` | exit `2`, stdout vacío, stderr con `gs://`, 0 listados. Antes del código: el mensaje era `falta el nombre del bucket`, sin `gs://` (rojo) | ✅ |
| VC-37, VC-38, VC-40 (v1.7) | FR-25 | `test_iteracion_2b.py::test_vc37_vc38_vc40_vc46_rechazo_con_texto_fijo` (6 casos) | stderr con `gcsgrep: error:` en todos. Antes del código: `--max -1` no lo tenía (rojo) | ✅ |
| VC-46 | FR-25 | `test_cli_frontera.py::test_vc46_abreviaturas_de_opciones_largas_se_rechazan[--ig, --line, --ma=3]`, `test_iteracion_2b.py::test_vc37_vc38_vc40_vc46_*[--ig]` | exit `2`, 0 listados, `gcsgrep: error:` | ✅ |
| VC-47 | FR-25 | `test_iteracion_2b.py::test_vc47_sintaxis_aceptada` (3 casos), `test_cli_frontera.py::test_vc47_patron_que_empieza_con_guion_despues_de_doble_guion` | `-- -x`, `-in` y `--max=1 -i -n`: exit `0` y stdout exacto | ✅ |
| VC-48 | FR-30 | `test_iteracion_2b.py::test_vc48_ayuda[--help, -h]`, `test_paso0.py::test_vc48_help_imprime_la_ayuda_por_stdout_y_no_toca_gcs` | exit `0`, stdout con `gcsgrep` y las cuatro opciones, stderr vacío, 0 listados | ✅ |
| VC-49 | FR-30 | `test_iteracion_2b.py::test_vc49_las_formas_largas_dan_la_misma_salida`, `test_cli_frontera.py::test_vc49_las_formas_largas_completas_siguen_andando` | `--ignore-case` ≡ `-i` y `--line-number` ≡ `-n`: mismo exit, stdout y stderr | ✅ |
| VC-50 | FR-29 | `test_iteracion_2b.py::test_vc50_otro_4xx_en_la_primera_lectura_no_aborta`, `test_vc50_gcs_traduce_otros_4xx_al_abrir[400, 409, 412]` | a través del `gcs` real con un cliente falso: `400` en la primera lectura de `b.txt` → `hit a` y `hit c` en stdout, `no se pudo leer` + `gs://b/p/b.txt`, exit `2`. Antes del código: abortaba por el genérico (rojo) | ✅ |
| VC-6, VC-32 (v1.7) | FR-6, FR-21 | `test_iteracion_2b.py::test_vc6_y_vc32_fallo_en_la_primera_lectura[403, 401, refresh, 404]` | el fallo llega en la **primera lectura**, como con `BlobReader`: el objeto anterior sale, la línea correcta en stderr, exit `2`. El caso *refresh* rechazado estaba en rojo (abortaba) | ✅ |
| VC-21 (v1.7) | FR-13 | `test_iteracion_2b.py::test_vc21_408_y_429_sobre_un_objeto_son_error_de_red[408, 429]` | `error de red al leer`, la corrida sigue, exit `2`. El `408` lo entrega el SDK como `GoogleAPICallError` sin clase propia (`from_http_status(408)`), por eso se clasifica por código. Antes: rojo | ✅ |
| VC-15 (v1.7) | NFR-2 (a) | `test_iteracion_2b.py::test_vc15_408_y_429_al_listar_son_error_de_red`, `test_vc15_y_vc29_sin_reintentos_y_timeout_de_60s_en_la_libreria` | `408`/`429` al listar → `ErrorDeRedAlListar`; `list_blobs` y `blob.open` reciben `retry=None` y `timeout=60`. Antes: rojo (sin `timeout`, y los `4xx` al genérico) | ✅ |
| VC-29 (v1.7) | NFR-2 (b) | `test_vc15_y_vc29_sin_reintentos_y_timeout_de_60s_en_la_libreria` (+ los de la Iteración 2) | ídem, sobre la apertura de cada objeto | ✅ |
| VC-41 (v1.7) | FR-26 | `test_iteracion_2b.py::test_vc41_archivo_de_gcloud_presente_da_credenciales_invalidas` | archivo de `gcloud` mal formado en `$CLOUDSDK_CONFIG` → `CredencialesInvalidas`. Antes: `SinCredenciales` (rojo) | ✅ |
| VC-23 (v1.7) | FR-15 | `test_iteracion_2b.py::test_vc23_sin_variable_ni_archivo_de_gcloud_son_credenciales_ausentes` | sin variable y con `$CLOUDSDK_CONFIG` vacío → `SinCredenciales` | ✅ |
| VC-43 (v1.7) | FR-2 | `test_iteracion_2b.py::test_vc43_sigma_final_con_ignore_case` | `ΟΔΟΣ`: `-i "σ"` → `(1, "", "")`; `-i "ς"` → exit `0` | ✅ |
| VC-5, VC-36, VC-44 (v1.7) | FR-5, FR-24, FR-27 | `test_paso0.py::test_vc5_prefijo_sin_objetos`, `test_vc36_una_linea_vacia_es_una_linea`, `test_contenido_no_texto.py::test_vc44_bom_fuera_del_principio_se_conserva` | los casos que la v1.7 agregó al texto ya estaban ejercitados desde la Iteración 2 (acciones 8, 4 y 15) | ✅ |
| VC-30 (v1.7) | NFR-4 | `test_paso0.py::test_vc30_a_*`, `test_vc30_b_todo_matchea_al_menos_150000_matches_por_segundo` | umbral (b) = 150 000. `ubuntu-latest` (run `36949165784`): Python 3.12 → (a) 573 MiB/s, (b) 488 152/s, mala 105 613/s; Python 3.9 → (a) 306, (b) 319 034, mala 64 090. macOS: (a) 924, (b) 359 782, mala (b) 31 859, mala (a) 3,2 MiB/s | ✅ |
| VC-16 (a) (v1.7) | NFR-3 | los de arriba que assertan `Traceback` ausente o stderr exacto, más VC-46 y VC-50 | ningún stderr con `Traceback` | ✅ |

### I-6 contra ADC real, sin emulador (2026-10-02)

H-14 dejó I-6 sin verificar porque en `floci` el SDK no mira credenciales. Pero I-6
no necesita GCS: la falla de ADC ocurre **al crear el cliente**, antes de cualquier
pedido a Storage. Se corrió el `gcsgrep` instalado con el SDK real
(`google-auth 2.59.1`, `google-cloud-storage 3.16.0`, Python 3.13, macOS), con
`$CLOUDSDK_CONFIG` apuntando a un directorio temporal para que ADC no viera la
configuración de `gcloud` de la máquina, contra `gs://gcsgrep-test-no-existe-i6/`.
Script: [`scripts/i6-adc-local.sh`](../../scripts/i6-adc-local.sh), que además
corre en cada push como paso del job de VCs del CI (el runner no tiene credenciales
de GCP).

| Chequeo | VCs que toca | Entorno | Esperado | Observado | Fecha |
|---|---|---|---|---|---|
| I-6 (ADC ausente) | VC-23 | sin `GOOGLE_APPLICATION_CREDENTIALS`, `$CLOUDSDK_CONFIG` vacío | exit `2`, `no se encontraron credenciales` + `gcloud auth application-default login`, sin traceback | ✅ exit `2`, stdout 0 B, stderr exactamente `gcsgrep: no se encontraron credenciales de Google Cloud. Obtenelas con: gcloud auth application-default login`; 6 s (ADC prueba el servidor de metadata de GCE antes de rendirse) | 2026-10-02 |
| I-6 (variable a un archivo inexistente) | VC-41 | `GOOGLE_APPLICATION_CREDENTIALS=…/no-existe.json` | exit `2`, `credenciales inválidas o vencidas` | ✅ exit `2`, stdout 0 B, stderr `gcsgrep: credenciales inválidas o vencidas. Renovalas con: gcloud auth application-default login` | 2026-10-02 |
| I-6 (archivo de `gcloud` mal formado) | VC-41 | `$CLOUDSDK_CONFIG` con `application_default_credentials.json` = `{ no es json` | ídem | ✅ ídem | 2026-10-02 |

**Qué no afirma esto:** no es el backend `gcs` del runbook (no hubo bucket ni red
hacia Storage), y no ejercita un token **vencido** de verdad (FR-28, un `401` real al
listar), que sigue cubierto solo por el doble. VC-31 sigue sin ejecutar.

### Lo que la Iteración 2b deja abierto

- `uv.lock` todavía declara `requires-python = ">=3.9"`: no hay `uv` en la máquina
  donde se hizo la iteración, y regenerarlo a mano no es seguro. El CI instala con
  `pip` y no lo usa. Hay que correr `uv lock` donde haya `uv`.
- Un `4xx` que no es `401`/`403`/`404`/`408`/`429` **al listar** sigue en el
  genérico (exit `2`, sin traceback). Es una decisión de ADR-0025, no un hueco.
- El número de NFR-4 en Python 3.10 (el piso nuevo) queda en el log del CI de esta
  rama; se registra abajo cuando corra.

### Por qué VC-14 tiene dos filas

En la versión anterior de esta tabla, VC-14 tenía una sola fila y medía **solo**
el caso sin matches. Como `core.search` devolvía una lista, con cero matches esa
lista quedaba vacía y el VC pasaba por construcción: no podía fallar. Un objeto
real de 200 MB con el patrón en casi todas las líneas habría usado ~371 MB, 18
veces el umbral, sin que ningún VC se enterara.

La fila (b) es el caso adverso, y el número de contraste (371 MB) está medido: es
lo que demuestra que ahora el VC **puede** fallar por la razón correcta. Ver
[`docs/revision-spec.md`](../../docs/revision-spec.md), hallazgo H-3, y
[ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md).

### Por qué VC-16 (b) existe, y qué se aprendió

**NFR-3 prometía esto desde la v1.0** ("ningún caso de error imprime un stack
trace de Python") y VC-16 pasaba igual: verificaba una **lista cerrada** de casos,
y todos los caminos de error del SDK quedaban fuera de la lista. El ✅ de VC-16 era
verdadero sobre lo que medía y falso sobre lo que NFR-3 prometía.

VC-16 (b) es el caso adverso que lo hace falsable: una excepción de una clase que
el código no conoce. No se puede enumerar "todos los errores", pero sí se puede
exigir que uno **desconocido** se maneje. Ver
[H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md) y
[ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md).

Es la segunda vez que el mismo modo de falla aparece en este repo: VC-14 lo tuvo
(H-3), se arregló, y no se le volvió a preguntar al resto de los VCs. De ahí la
regla que quedó en el checklist de revisión.

### Sobre la resolución de VC-11, distinta de la que H-10 propuso

[H-10](../../docs/revision-spec.md) había dejado como precondición de VC-11
"separar la siembra del doble de la superficie que `core` puede tocar", porque
`FakeGCS` expone `put()`.

**Se resolvió en otro lugar, y por eso VC-11 pasa sin ese refactor.** BR-1 es una
afirmación sobre las operaciones invocadas **en la API de GCS**, así que su
ejercitador vive al nivel del *cliente del SDK* (`ClienteSoloLectura`), no al nivel
del doble del módulo `gcs`. `FakeGCS.put()` no es una operación del SDK: es setup de
un doble que no habla con GCS en absoluto, así que no puede violar BR-1 ni
confundirse con una escritura del código bajo prueba.

Queda dicho acá porque H-10 predijo otra resolución, y un hallazgo que se resuelve
distinto de lo que anticipó tiene que dejar el rastro de por qué.

### Por qué VC-17 tiene una fila nueva

La fila original sigue arriba y **no se editó**. El test de VC-17 esperaba que la
excepción de lectura escapara (`pytest.raises(OSError)`), porque en la Iteración 1
no había frontera; con ADR-0013 la corrida termina con exit `2`. Lo que el VC
afirma —que los matches ya emitidos salieron *antes* del fallo— es idéntico, y el
test sigue observando eso. Cambió el final de la corrida, así que va una fila
nueva con fecha, no una edición encima de la vieja.

**Y tiene un segundo cambio, en la spec v1.3.** VC-17 ya no afirma que el primer
match se emite sin haber *listado* el resto del prefijo: BR-2 obliga a contar antes
de leer, y contar exige materializar el listado. Ahora afirma que se emite sin
haberlo *abierto*, que es lo que FR-11 promete. El plan lo había anticipado como
nota de regresión, y la propiedad original sobrevive con `--max 0`, verificada en
`test_vc12_max_0_no_materializa_el_listado`.

El ticket que lo cierra está planificado y **no** se implementó en la misma sesión
donde se descubrió, por [`docs/proceso-cambios.md`](../../docs/proceso-cambios.md).

### Qué no cubre VC-17

El test de `cli` observa el **orden**: los matches están en stdout antes de que
la corrida termine. No observa el `flush=True`, porque `capsys` captura
reemplazando `sys.stdout` y el buffering de un pipe real no interviene. Que la
salida aparezca de verdad a medida que avanza, con stdout redirigido a un pipe,
es parte de la verificación de integración (paso 5 del runbook).

## Cómo se ejercita todo

```bash
python -m pytest            # 48 tests, sin credenciales ni red
```

Los tests corren en dos niveles:

- `core` recibe `list_objects` y `open_text_stream` como colaboradores, y los
  tests le pasan dobles en memoria (`tests/fakes.py`: `FakeGCS`,
  `RecordingFakeGCS`, `HugeLineStream`, `ExplodingStream`) — cero conocimiento
  del SDK de Google.
- `gcs.py` (`tests/test_gcs.py`) se testea mockeando el **cliente del SDK** en el
  punto donde `gcs._get_client()` lo entrega, con un `_FakeClient` /
  `_FakeBucket` / `_FakeBlob` de mano. Esto confirma que `list_objects` llama a
  `list_blobs(bucket, prefix=...)` con los argumentos correctos, que
  `open_text_stream` abre el blob correcto en modo `"r"`, y que las excepciones
  **reales** de `google.api_core` (`NotFound`, `Forbidden`) se traducen a los
  errores de dominio de `errors.py` (VC-18). Sin esa última parte, FR-12 podría
  estar verificado de punta a punta contra un error que el SDK nunca produce.

En CI, [`.github/workflows/tests.yml`](../../../.github/workflows/tests.yml) corre
esta misma suite en Python 3.9 y 3.12 en cada push y cada PR. Eso es lo que
convierte los ✅ de esta tabla en una afirmación chequeada por una máquina y no
en una línea de markdown que alguien se acordó de actualizar.

**Qué NO prueba el mock de `gcs.py`:** que `google-cloud-storage` en sí se
comporte como creemos — autenticación real contra ADC, la semántica exacta de
`list_blobs` con prefijos raros, streaming real sobre la red, o errores de
permisos reales de GCS. Eso solo lo confirma correr contra un bucket real. El
mock sube la confianza en el *wiring* del código a costo cero; no reemplaza la
integración.

## Verificación de integración (contra un bucket real)

> ### ✅ Estado: ejecutada contra el emulador `floci-gcp` el 2026-09-24 · H-9 cerrado
>
> **I-1, I-2, I-3, I-4, I-5 e I-7 pasaron**, por el script y por pytest. Es la
> primera vez que los chequeos de integración se ejecutan: hasta ahora H-9 estaba
> **bloqueado** por no tener una cuenta con billing, y
> [ADR-0014](../../docs/adr/ADR-0014-emulacion-local-floci.md) lo desbloqueó con el
> backend `floci`.
>
> **La verificación contra GCS real se declinó para esta entrega**, con fundamento y
> obligación registrada: [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md).
> Sigue en **0** y eso no va a cambiar acá — es una afirmación más fuerte (ADC, IAM,
> red, latencia) y el ADR enumera exactamente qué queda sin verificar. **No es un
> pendiente: es una decisión.**
>
> **I-6 (ADC ausente)** no es verificable contra `floci`: con `STORAGE_EMULATOR_HOST`
> seteada el SDK no mira las credenciales, así que taparlas no tiene efecto
> ([H-14](../../docs/hallazgos/H-14-i6-no-verificable-en-emulador.md)). Su observable
> se registró por otra vía, abajo.
>
> Entorno de la corrida: `floci-gcp 0.9.0` (imagen `floci/floci-gcp:latest`,
> digest `sha256:ea29a53b…1138ea`) en `localhost:4588`, bucket
> `gcsgrep-test-floci`, `gcsgrep` instalado con `pip install -e '.[dev]'` sobre
> Python 3.10.12.

El procedimiento reproducible —creación del bucket de prueba, siembra de
fixtures, los cinco chequeos, y destrucción— está en
[`docs/integracion-gcs.md`](../../docs/integracion-gcs.md), automatizado en
`scripts/testing-ground.sh`. Corre también como job manual de CI
(`.github/workflows/integration.yml`) para quien tenga el proyecto de GCP
configurado.

Los resultados se registran acá, con fecha y bucket usado. Las seis primeras filas
son las originales, con _pendiente_; las seis de abajo son el resultado de la
corrida del 2026-09-24, que no se había volcado a la tabla
([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md)). El detalle por
chequeo de esa corrida (salida exacta) no quedó registrado: lo único que consta es
el encabezado de arriba. La próxima corrida tiene que anotar lo observado, no solo
el ✅.

| Chequeo | VCs que toca | Comando | Esperado | Observado | Fecha |
|---|---|---|---|---|---|
| I-1 búsqueda con match | VC-1, VC-4 | `gcsgrep "timeout" gs://$BUCKET/logs/` | exit `0`, línea con `gs://…/a.txt` | _pendiente_ | — |
| I-2 `-i` y `-n` | VC-2, VC-3 | `gcsgrep -i -n "TIMEOUT" gs://$BUCKET/logs/` | exit `0`, con número de línea | _pendiente_ | — |
| I-3 sin resultados | VC-5 | `gcsgrep "no-existe-esto" gs://$BUCKET/logs/` | exit `1`, stdout vacío | _pendiente_ | — |
| I-4 ubicación inválida | VC-8 | `gcsgrep "x" no-es-gs` | exit `2`, sin llamada a GCS | _pendiente_ | — |
| I-5 salida incremental en un pipe | VC-17 | `gcsgrep "linea" gs://$BUCKET/grande/ \| head -3` | 3 líneas y corta, sin leer el objeto completo | _pendiente_ | — |
| **I-7 bucket inexistente** | **VC-18** | `gcsgrep "x" gs://gcsgrep-test-no-existe-jamas/` | exit `2`, stderr nombra el bucket y dice que no existe, sin `Traceback` | _pendiente — requiere FR-12 implementado_ | — |
| I-1 | VC-1, VC-4 | ídem | ídem | ✅ pasó — backend **`floci`**, bucket `gcsgrep-test-floci` (registrado el 2026-10-01 a partir del encabezado de esta sección, H-15) | 2026-09-24 |
| I-2 | VC-2, VC-3 | ídem | ídem | ✅ pasó — **`floci`** (ídem) | 2026-09-24 |
| I-3 | VC-5 | ídem | ídem | ✅ pasó — **`floci`** (ídem) | 2026-09-24 |
| I-4 | VC-8 | ídem | ídem | ✅ pasó — **`floci`** (ídem) | 2026-09-24 |
| I-5 | VC-17 | ídem | ídem | ✅ pasó — **`floci`** (ídem) | 2026-09-24 |
| I-7 | VC-18 | ídem | ídem | ✅ pasó — **`floci`** (ídem) | 2026-09-24 |

**I-6 no está en esta tabla**, y hasta la enmienda de la spec v1.2 decía
_pendiente_ acá. Verifica que sin ADC la corrida salga con `2` sin traceback, que
es NFR-2, que es **Iteración 2**
([H-11](../../docs/hallazgos/H-11-runbook-vs-plan.md)). Decir _pendiente_ implicaba
"debería pasar y no se probó"; la verdad es "todavía no se prometió". Se registra
en la tabla de integración de la Iteración 2, cuando exista.

## Qué mirar en esta tabla

1. **Cada fila tiene un ejercitador nombrado**, no "verificado manualmente".
2. **La columna "Se observa" es observable**: exit codes, contenido de stdout,
   megabytes medidos. No dice "funciona bien".
3. **VC-16 está marcado como parcial a propósito** — no se infla la cobertura de
   un NFR que depende de código que todavía no existe (Iteración 2).
4. **La verificación de integración está marcada como pendiente, no como
   implícita.** Pasar contra un doble de prueba y pasar contra GCS son dos
   afirmaciones distintas, y esta tabla no las mezcla.

## Histórico

Las filas que fueron reemplazadas viven acá, con su fecha, para que la tabla de
arriba pueda seguir respondiendo una sola pregunta: *qué pasa hoy*.

### Filas superadas el 2026-10-01 ([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md))

Estas tres filas estaban en la tabla vigente al entregar, y ya no eran ciertas:
los tests existían y pasaban desde el 2026-09-24. Se conservan tal como estaban.

| VC-17 (hasta la spec v1.3, nombre de test viejo) | FR-11 salida incremental | `test_core.py::test_vc17_primer_match_se_emite_sin_recorrer_todo_el_prefijo`, `test_cli.py::test_vc17_los_matches_se_imprimen_antes_de_que_termine_la_corrida` | con 3 objetos que matchean, obtener el 1er match listó y abrió **solo** el 1ero (`listed == opened == ["logs/a.txt"]`); de punta a punta, 2 matches ya están en stdout cuando la lectura del objeto falla | ✅ |
| **VC-16 (b)** | **NFR-3, excepción inesperada** | _sin ejercitador — pendiente de implementar_ | esperado: exit `2`, stdout vacío, mensaje legible sin `Traceback`. **Observado hoy: cualquier excepción del SDK escapa de `cli.main()` como traceback con exit `1`** | ⬜ **no implementado** |
| **VC-18** | **FR-12 bucket inexistente o inaccesible** | _sin ejercitador — pendiente de implementar_ | esperado: exit `2`, stdout vacío, stderr nombra el bucket, distingue "no existe" de "sin permiso", sin `Traceback`. **Observado hoy: traceback de `google.api_core.exceptions.NotFound` y exit `1`** | ⬜ **no implementado** |

### Nota del cierre de la Iteración 1

Al cierre de la Iteración 1 no había ninguna todavía: ningún VC cambió de estado ni
de forma de medirse después de haber sido registrado. Los dos casos que se le
parecen están narrados arriba y no son filas superadas:

- **VC-14 con dos filas** no es una fila vieja y una nueva: son dos condiciones de
  medición del mismo VC vigente, y las dos tienen que pasar. La historia de por
  qué la (b) hizo falta —el VC que no podía fallar, hallazgo H-3— es histórico, y
  se conserva en prosa porque explica una lección, no un estado.
- **I-6 fuera de la tabla de integración** es una corrección de alcance, no un
  resultado superado: nunca se observó nada.

**Cuándo migra:** la primera fila superada aparece en la Iteración 2, cuando VC-16
pase de *parcial* a completo y VC-18 de ⬜ a ✅. Si este documento pasa las ~300
líneas, el histórico se muda a `cobertura/iteracion-N.md` con un índice acá,
siguiendo el patrón de [`docs/adr/`](../../docs/adr/) y
[`docs/hallazgos/`](../../docs/hallazgos/). Hoy no hace falta: son 150 líneas.

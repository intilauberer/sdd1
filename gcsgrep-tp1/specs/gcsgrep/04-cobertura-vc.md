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

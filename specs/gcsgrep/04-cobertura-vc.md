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

## Resumen (Iteración 1, spec v1.2)

| | |
|---|---|
| VCs en el alcance de la Iteración 1 | 11 (VC-1, VC-2, VC-3, VC-4, VC-5, VC-7, VC-8, VC-14, VC-17, **VC-18**, VC-16 parcial) |
| VCs con cobertura ejecutable | 10 |
| VCs pasando contra dobles de prueba | 10 |
| VCs **sin implementar** | **1 — VC-18** (FR-12, incorporado por la enmienda de la spec v1.2) |
| VCs verificados contra GCS real | **0 — ver la sección de integración** |
| VCs de la Iteración 2 (pendientes) | VC-6, VC-9, VC-10, VC-11, VC-12, VC-13, VC-15, VC-16 (completo) |
| Tests que ejercitan todo esto | 23, en 4 archivos |

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
| VC-17 | FR-11 salida incremental | `test_core.py::test_vc17_primer_match_se_emite_sin_recorrer_todo_el_prefijo`, `test_cli.py::test_vc17_los_matches_se_imprimen_antes_de_que_termine_la_corrida` | con 3 objetos que matchean, obtener el 1er match listó y abrió **solo** el 1ero (`listed == opened == ["logs/a.txt"]`); de punta a punta, 2 matches ya están en stdout cuando la lectura del objeto falla | ✅ |
| VC-16 (parcial) | NFR-3 salida apta para scripting | `test_cli.py::test_vc5_sin_resultados_exit_1_stdout_vacio`, `test_cli.py::test_vc8_ubicacion_sin_esquema_exit_2` | stdout vacío y stderr sin `Traceback` para los dos casos de error/borde ya implementados (VC-5, VC-8) | ✅ (parcial — el resto depende de código de la Iteración 2) |
| **VC-18** | **FR-12 bucket inexistente o inaccesible** | _sin ejercitador — pendiente de implementar_ | esperado: exit `2`, stdout vacío, stderr nombra el bucket, distingue "no existe" de "sin permiso", sin `Traceback`. **Observado hoy: traceback de `google.api_core.exceptions.NotFound` y exit `1`** | ⬜ **no implementado** |

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

### Por qué VC-18 está en esta tabla sin ejercitador

Es la única fila ⬜ del documento, y está a propósito. FR-12 se incorporó a la
Iteración 1 por la enmienda de la spec v1.2
([H-12](../../docs/hallazgos/H-12-actores-sin-trazar.md)) **después** de que la
iteración se declarara completa, así que hay una ventana en la que el contrato
promete algo que el código todavía no hace.

La alternativa —no registrar el VC hasta que exista el test— dejaría la tabla
diciendo "10 de 10 pasando" mientras la spec tiene 18 requerimientos. Esa es
exactamente la clase de afirmación cómoda que este documento existe para evitar.
La columna "Se observa" registra el comportamiento actual, que es el traceback.

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
python -m pytest            # 23 tests, sin credenciales ni red
```

Los tests corren en dos niveles:

- `core` recibe `list_objects` y `open_text_stream` como colaboradores, y los
  tests le pasan dobles en memoria (`tests/fakes.py`: `FakeGCS`,
  `RecordingFakeGCS`, `HugeLineStream`, `ExplodingStream`) — cero conocimiento
  del SDK de Google.
- `gcs.py` (`tests/test_gcs.py`) se testea mockeando el **cliente del SDK** en el
  punto donde `gcs._get_client()` lo entrega, con un `_FakeClient` /
  `_FakeBucket` / `_FakeBlob` de mano. Esto confirma que `list_objects` llama a
  `list_blobs(bucket, prefix=...)` con los argumentos correctos y que
  `open_text_stream` abre el blob correcto en modo `"r"`.

En CI, [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml) corre
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

> ### ⚠️ Estado: PENDIENTE — bloqueante de entrega
>
> **Ningún VC de esta tabla se verificó todavía contra GCS real.** Los 10 pasan
> contra dobles de prueba.
>
> El enunciado pide que el código de la Iteración 1 "corra una búsqueda real y
> sus chequeos de verificación pasen". Hasta que esta sección se complete con
> resultados observados, **ese criterio de entrega no está cumplido**. Es el
> hallazgo H-9 de la revisión.

El procedimiento reproducible —creación del bucket de prueba, siembra de
fixtures, los cinco chequeos, y destrucción— está en
[`docs/integracion-gcs.md`](../../docs/integracion-gcs.md), automatizado en
`scripts/testing-ground.sh`. Corre también como job manual de CI
(`.github/workflows/integration.yml`) para quien tenga el proyecto de GCP
configurado.

Cuando se ejecute, los resultados se registran acá, con fecha y bucket usado:

| Chequeo | VCs que toca | Comando | Esperado | Observado | Fecha |
|---|---|---|---|---|---|
| I-1 búsqueda con match | VC-1, VC-4 | `gcsgrep "timeout" gs://$BUCKET/logs/` | exit `0`, línea con `gs://…/a.txt` | _pendiente_ | — |
| I-2 `-i` y `-n` | VC-2, VC-3 | `gcsgrep -i -n "TIMEOUT" gs://$BUCKET/logs/` | exit `0`, con número de línea | _pendiente_ | — |
| I-3 sin resultados | VC-5 | `gcsgrep "no-existe-esto" gs://$BUCKET/logs/` | exit `1`, stdout vacío | _pendiente_ | — |
| I-4 ubicación inválida | VC-8 | `gcsgrep "x" no-es-gs` | exit `2`, sin llamada a GCS | _pendiente_ | — |
| I-5 salida incremental en un pipe | VC-17 | `gcsgrep "linea" gs://$BUCKET/grande/ \| head -3` | 3 líneas y corta, sin leer el objeto completo | _pendiente_ | — |
| **I-7 bucket inexistente** | **VC-18** | `gcsgrep "x" gs://gcsgrep-test-no-existe-jamas/` | exit `2`, stderr nombra el bucket y dice que no existe, sin `Traceback` | _pendiente — requiere FR-12 implementado_ | — |

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

Al cierre de la Iteración 1 no hay ninguna todavía: ningún VC cambió de estado ni
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

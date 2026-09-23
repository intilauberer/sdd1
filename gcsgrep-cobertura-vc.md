# gcsgrep — tabla de cobertura de VCs

> Salida del paso **Verificar**, para lo que ya está implementado (Iteración 1
> de [`gcsgrep-plan.md`](./gcsgrep-plan.md)). Se completa con una fila nueva por
> cada VC a medida que se implementa la Iteración 2.
>
> La tabla no dice "lo probé". Dice, para cada criterio de verificación, con qué
> se lo ejercita y qué se observó.

## Resumen (Iteración 1)

| | |
|---|---|
| VCs en el alcance de la Iteración 1 | 9 (VC-1, VC-2, VC-3, VC-4, VC-5, VC-7, VC-8, VC-14, VC-16 parcial) |
| VCs con cobertura ejecutable | 9 |
| VCs pasando | 9 |
| VCs de la Iteración 2 (pendientes) | VC-6, VC-9, VC-10, VC-11, VC-12, VC-13, VC-15, VC-16 (completo) |

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
| VC-14 | NFR-1 memoria acotada | `test_memory.py::test_vc14_memoria_acotada_con_objeto_de_200mb` | pico de memoria adicional medido con `tracemalloc` sobre un objeto simulado de 200 MB: **< 20 MB** (umbral definido en la spec) | ✅ |
| VC-16 (parcial) | NFR-3 salida apta para scripting | `test_cli.py::test_vc5_sin_resultados_exit_1_stdout_vacio`, `test_cli.py::test_vc8_ubicacion_sin_esquema_exit_2` | stdout vacío y stderr sin `Traceback` para los dos casos de error/borde ya implementados (VC-5, VC-8) | ✅ (parcial — el resto de los casos de VC-16 depende de código de la Iteración 2) |

## Cómo se ejercita todo

```bash
python -m pytest -v
```

Los 20 tests corren sin credenciales de GCP ni red, en dos niveles:

- `core` recibe `list_objects` y `open_text_stream` como colaboradores, y los
  tests le pasan un doble de prueba en memoria (`tests/fakes.py::FakeGCS`,
  `HugeLineStream`) — cero conocimiento del SDK de Google.
- `gcs.py` (`tests/test_gcs.py`) se testea mockeando el **cliente del SDK** en
  el punto donde `gcs._get_client()` lo entrega, con un `_FakeClient` /
  `_FakeBucket` / `_FakeBlob` de mano. Esto confirma que `list_objects` llama a
  `list_blobs(bucket, prefix=...)` con los argumentos correctos y que
  `open_text_stream` abre el blob correcto en modo `"r"`.

**Qué NO prueba el mock de `gcs.py`:** que `google-cloud-storage` en sí se
comporte como creemos — autenticación real contra ADC, la semántica exacta de
`list_blobs` con prefijos raros, streaming real sobre la red, o errores de
permisos reales de GCS. Eso solo lo confirma correr contra un bucket real (ver
abajo). El mock sube la confianza en el *wiring* del código a costo cero; no
reemplaza la integración.

## Verificación de integración (contra un bucket real)

Requiere un bucket de prueba y ADC configurado (`gcloud auth
application-default login`, o ejecutar desde un entorno de GCP con una cuenta
de servicio adjunta):

```bash
gsutil cp local1.txt gs://mi-bucket-de-prueba/logs/a.txt   # contiene "timeout"
gsutil cp local2.txt gs://mi-bucket-de-prueba/logs/b.txt   # no contiene "timeout"

python -m gcsgrep.cli "timeout" gs://mi-bucket-de-prueba/logs/
echo "exit: $?"                          # esperado: 0

python -m gcsgrep.cli -i -n "TIMEOUT" gs://mi-bucket-de-prueba/logs/
echo "exit: $?"                          # esperado: 0, con número de línea

python -m gcsgrep.cli "no-existe-esto" gs://mi-bucket-de-prueba/logs/
echo "exit: $?"                          # esperado: 1, stdout vacío

python -m gcsgrep.cli "x" no-es-gs
echo "exit: $?"                          # esperado: 2
```

**Esta corrida no se ejecutó todavía** en este entorno (no hay un bucket de
prueba ni ADC configurados acá). Es el paso pendiente antes de dar por
verificada de verdad la Iteración 1 contra GCS real, no solo contra el doble de
prueba — correlo con tu propio bucket de prueba antes de entregar.

## Qué mirar en esta tabla

1. **Cada fila tiene un ejercitador nombrado**, no "verificado manualmente".
2. **La columna "Se observa" es observable**: exit codes, contenido de stdout,
   megabytes medidos. No dice "funciona bien".
3. **VC-16 está marcado como parcial a propósito** — no se infla la cobertura
   de un NFR que depende de código que todavía no existe (Iteración 2).

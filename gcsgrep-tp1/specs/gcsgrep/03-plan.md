# gcsgrep — plan de iteraciones

> Salida del paso **Planificar**, a partir de [`02-spec.md`](./02-spec.md) v1.5.
>
> Cada iteración termina con código andando y sus VCs pasando antes de que
> empiece la siguiente.
>
> **Enmienda 2026-10-01 (spec v1.5) · revisión de la v1.4.** La spec pasó de 27 a
> 34 requerimientos (FR-21…FR-27) y de 31 a 44 VCs. Se clasificaron con el mismo
> criterio que la v1.4:
>
> - **Comportamiento que la Iteración 1 ya tiene, ahora escrito → Paso 0:** VC-36
>   (patrón vacío, FR-24), VC-37…VC-40 (invocación mal formada, FR-25), VC-42
>   (límite exacto del tope, BR-2), VC-43 (`-i` con `Á`/`á`, FR-2), y VC-7, VC-12 y
>   VC-22 re-redactados con observables exactos. Se verificaron a mano contra el
>   código actual con el doble de prueba antes de clasificarlos; no hay tests nuevos
>   todavía.
> - **Comportamiento nuevo → Paso 1 de la Iteración 2:** VC-32 (FR-21, objeto que ya
>   no existe), VC-33 (FR-13, red al abrir), VC-34 (FR-22, terminador `\r\n`), VC-35
>   (FR-23, `| head` → SIGPIPE, [ADR-0019](../../docs/adr/ADR-0019-corte-de-stdout-sigpipe.md)),
>   VC-41 (FR-26, credenciales inutilizables) y VC-44 (FR-27, BOM); y VC-13, VC-15,
>   VC-20 y VC-23 re-redactados, que ya eran de esta iteración.
> - Ninguno cambia la Iteración 1 ni la 3.
>
> **Enmienda 2026-10-01 (spec v1.4) · corrección de la cátedra.** La spec pasó
> de 18 a 27 requerimientos sin cambiar lo que la Iteración 1 entrega. Se
> clasificaron así (detalle en la sección de la Iteración 2):
>
> - **Comportamiento que la Iteración 1 ya tiene, ahora escrito:** FR-3/FR-4
>   (formatos), FR-14 (antes la mitad de FR-12), FR-16 (orden), FR-18 (prefijo sin
>   `/`), FR-19 (0 bytes), FR-20 (última línea sin `\n`), el patrón literal de
>   FR-1, el `gs://` en el mensaje de FR-8 y la excepción `GCSGREP_DEBUG` de NFR-3.
>   No se reabre la Iteración 1: sus VCs nuevos (VC-19, VC-22, VC-24, VC-26, VC-27,
>   VC-28, VC-16 (c)) y los más concretos (VC-1, VC-3, VC-4, VC-8) se ejercitan como
>   **primer paso de la Iteración 2**, antes de escribir código nuevo.
> - **Comportamiento nuevo, a la Iteración 2:** FR-13, FR-15, FR-17 y la ventana de
>   8192 bytes de FR-9, que se suman a lo que ya estaba (FR-6, FR-9, FR-10, BR-3,
>   NFR-2).
> - **NFR-4 (rendimiento)** deja la Iteración 3: es un umbral sobre el costo propio
>   de la herramienta y se mide en la Iteración 2
>   ([ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md)). La
>   Iteración 3 conserva la obligación del número **comparativo** para la
>   concurrencia.
> - **VC-31** (punta a punta contra GCS real) queda especificado y sujeto a
>   [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md).
>
> **Enmienda 2026-09-24 · las dos Restricciones del enunciado se adelantan.** BR-1
(solo lectura, VC-11) y BR-2 (guardrail de costo, VC-12) salen de la Iteración 2 y se
implementan ahora. Fundamento: son las **Restricciones** del enunciado, no features,
y las restricciones no están scopeadas por iteración — son condiciones sobre lo que
se entrega. Un `gcsgrep` sin `--max` escanea un bucket entero sin tope, que es
literalmente lo que la restricción prohíbe. El resto de la Iteración 2 (FR-6, FR-9,
FR-10, BR-3, NFR-2) **no** se adelanta.

Consecuencia registrada: implementar BR-2 acotó VC-17 (spec v1.3), tal como la nota
de regresión de la Iteración 2 lo había anticipado.

**Enmienda 2026-09-23 (spec v1.2):** la **frontera de manejo de excepciones del
> CLI** se incorpora a la **Iteración 1**, que ya estaba implementada — FR-12 /
> VC-18 (bucket inexistente o inaccesible) y **VC-16 (b)** (una excepción
> inesperada no puede terminar en traceback). El fundamento está más abajo, en la
> sección de la Iteración 1; el hallazgo que lo originó, en
> [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md). Se registra como
> enmienda explícita y no como edición muda porque agranda el alcance de una
> iteración ya declarada completa.

## Quién dice qué

Este plan declara **qué VCs entran en cada iteración**. No dice cuáles pasan.

El estado de cada VC vive en un solo lugar:
[`04-cobertura-vc.md`](./04-cobertura-vc.md). Hasta la v1.1 este documento tenía
una lista de checkboxes que decía lo mismo que la tabla de cobertura y ya estaba
desincronizada con ella dentro del mismo commit
([`docs/revision-spec.md`](../../docs/revision-spec.md), hallazgo H-4). Los
checkboxes se eliminaron: un hecho, un documento.

## Cómo está ordenado

Por dependencia. La Iteración 1 es el camino feliz completo de punta a punta
(la promesa central: buscar contenido remoto sin bajarlo). La Iteración 2 es la
capa de resiliencia y guardrails que hace que la herramienta sea segura de usar
sobre datos reales, imperfectos y potencialmente costosos. La Iteración 3 es
rendimiento, y existe en el plan porque tiene una obligación registrada, no
porque esté comprometida para esta entrega.

| Iteración | Entrega | Cubre |
|---|---|---|
| 1 | Búsqueda literal de punta a punta, con `-i`/`-n`, salida incremental y frontera de excepciones | FR-1, FR-2, FR-3, FR-4, FR-5, FR-7, FR-8, FR-11, **FR-12**, **FR-14**, FR-16, FR-18, FR-19, FR-20, BR-1, BR-2, NFR-1, NFR-3 (parcial, con la parte universal verificable). Los FR-14…FR-20 de esta fila son comportamiento existente escrito en la spec v1.4 |
| 2 | Regularización de los VCs de la v1.4 y la v1.5, resiliencia, contenido no-texto y rendimiento | FR-6, FR-9, FR-10, **FR-13**, **FR-15**, **FR-17**, **FR-21**, **FR-22**, **FR-23**, **FR-26**, **FR-27**, BR-3, NFR-2, NFR-3 (completo), **NFR-4**; y los VCs de Paso 0 de **FR-24**, **FR-25**, FR-2 y BR-2 (comportamiento existente) |
| 3 | Concurrencia y el NFR comparativo que la justifica | NFR comparativo contra NFR-4 (a definir), revisión de ADR-0009 y ADR-0011 |

Las Iteraciones 1 y 2 son la entrega mínima pedida por el enunciado (≥ 2
iteraciones). La Iteración 3 **no** está comprometida para esta entrega: está en
el plan para que la obligación del NFR comparativo
([ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md), que heredó
la de [ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md)) no se pierda.
Todo lo demás está en "Lo que quedó afuera" al final.

---

## Iteración 1 — Búsqueda de punta a punta

**Objetivo:** que exista un camino completo y angosto: apuntar `gcsgrep` a un
prefijo real y obtener matches con el formato correcto, sin bajar nada a disco.

**Alcance**

- Los tres módulos (`cli`, `core`, `gcs`) con sus límites definidos.
- Parseo de `gs://bucket/prefijo`, incluyendo prefijo vacío (bucket completo).
- Búsqueda literal, streaming línea por línea.
- Flags `-i` y `-n`.
- Formato de salida `gs://bucket/objeto:línea:texto`.
- Exit codes `0` (match) / `1` (sin match) / `2` (input inválido).
- **Salida incremental**: `core.search` es un generador, `cli` imprime cada
  match en cuanto aparece ([ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md),
  agregado en la revisión 1.1).
- **Frontera de manejo de excepciones en `cli.main()`** (enmienda de la spec v1.2,
  [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md); implementada el
  2026-09-24 según [ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md)).
  Dos mitades:
  - **FR-12 / VC-18:** bucket inexistente o inaccesible → exit `2` con un mensaje
    que distingue "no existe" de "sin permiso", sin traceback.
  - **VC-16 (b):** una excepción **inesperada** tampoco puede terminar en
    traceback → exit `2` y mensaje legible. Es lo que hace verificable la parte
    universal de NFR-3, que prometía "ningún caso de error" desde la v1.0.

  Se resolvió con [ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md): la
  frontera vive en `cli.main()` y la **traducción** de las excepciones del SDK vive
  en `gcs`, que las convierte en los errores de dominio de `gcsgrep/errors.py`. Así
  `cli` reporta fallos de GCS sin importar `google.api_core` y `core` sigue sin
  saber que GCS existe.

**Fuera de alcance de esta iteración:** manejo de objetos ilegibles, salteo de
binarios/`.gz`, guardrail de tope, fallos de red simulados. Se asume, por ahora,
que todos los objetos bajo el prefijo son de texto y legibles.

**VCs en alcance:** VC-1, VC-2, VC-3, VC-4, VC-5, VC-7, VC-8, VC-14, VC-17,
**VC-18**, **VC-16 (b)**, y VC-16 (a) parcial (solo para los casos de VC-5, VC-8 y
VC-18, que son los únicos caminos de error enumerados que existen en esta
iteración).

### Por qué esto entra acá y no en la Iteración 2

La Iteración 2 es la iteración de resiliencia, así que el manejo de errores
*parece* pertenecerle entero. Cuatro razones para adelantar esta parte:

0. **NFR-3 ya lo prometía**, desde la v1.0 y sin condicionarlo a ninguna
   iteración: *"ningún caso de error imprime un stack trace de Python"*. No es
   alcance nuevo que se adelanta, es una promesa vigente que no se cumple.

1. **Es el error más frecuente de la herramienta.** Un typo en el nombre del
   bucket es lo primero que le va a pasar a cualquiera. Hoy responde con un
   traceback de 20 líneas y exit `1`.
2. **La Iteración 1 ya lo puede producir.** No es alcance nuevo que aparece con
   código nuevo: el camino existe desde el primer commit, simplemente no estaba
   especificado.
3. **El enunciado pide que la Iteración 1 "corra una búsqueda real".** El primer
   intento real de correrla fue el que destapó el problema
   ([H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md)).

FR-12 y VC-16 (b) van juntos porque son la misma línea de código: el `try/except`
que FR-12 necesita **es** la frontera que hace verificable a NFR-3. Implementar uno
sin el otro sería escribir la frontera y no verificarla, o verificarla sin tenerla.

**Lo que explícitamente NO se adelanta.** FR-12 cubre el fallo del **listado
inicial** por bucket inexistente o sin permiso, y VC-16 (b) exige que lo inesperado
no crashee. No traen NFR-2 (mensajes específicos para fallos de red), ni FR-6
(objeto ilegible, que además no aborta la corrida), ni BR-3 (precedencia de exit
codes). Esa frontera importa: BR-3 es un cambio de contrato sobre corridas que ya
funcionan, y meterlo a medias acá es justamente lo que el historial de la spec se
compromete a no hacer en silencio.

El riesgo de esta enmienda es el inverso del habitual: un `except Exception` de tope
puede **tapar** los casos de la Iteración 2 y hacer que FR-6, BR-3 y NFR-2 parezcan
implementados. El ADR tiene que dejar dicho que el caso genérico es un piso, no una
implementación de NFR-2.

**Demostrable así (contra un bucket real, con ADC configurado):**

```bash
gcsgrep "timeout" gs://mi-bucket-de-prueba/logs/
gcsgrep -i -n "ERROR" gs://mi-bucket-de-prueba/logs/
gcsgrep "texto-que-no-existe" gs://mi-bucket-de-prueba/logs/; echo "exit: $?"
gcsgrep "x" no-es-una-ruta-gs; echo "exit: $?"
```

El runbook reproducible de esa demostración —incluido el script que crea y
destruye el bucket de prueba— está en
[`docs/integracion-gcs.md`](../../docs/integracion-gcs.md).

**Qué chequeos de integración cierran esta iteración: I-1 … I-5, más I-7 (FR-12).**
No I-6 (ADC ausente), que verifica NFR-2 y por lo tanto pertenece a la Iteración 2
— ver [H-11](../../docs/hallazgos/H-11-runbook-vs-plan.md). El runbook reclamaba
I-6 para esta iteración, lo que lo hacía imposible de pasar por diseño.

**Nota sobre pruebas offline:** `core` no importa `google.cloud.storage`
directamente — recibe el listado y la apertura de streams como colaboradores.
Los VCs de esta iteración se ejercitan con un doble de prueba (`gcs` falso, en
memoria) para que corran sin credenciales ni red; la demostración de arriba,
contra un bucket real, es la verificación de integración complementaria y
**todavía no se ejecutó** (hallazgo H-9 de la revisión: es bloqueante de
entrega).

---

## Iteración 2 — Resiliencia, contenido no-texto y rendimiento

**Objetivo:** que la herramienta sea segura de correr sobre un bucket real que
nadie curó para la demo: objetos rotos, binarios, `.gz`, texto en otra
codificación, redes que se cortan y entornos sin credenciales; y que su costo
propio quede acotado por un número.

### Paso 0 · Regularizar los VCs de las specs v1.4 y v1.5 (antes de cualquier código nuevo)

La corrección de la cátedra hizo que la spec **diga** cosas que el código de la
Iteración 1 ya hace. Antes de tocar `core` o `cli`, cada una de esas promesas
necesita un test que la ejercite, nombrado por su VC:

| VC | Requerimiento | Qué se espera hoy |
|---|---|---|
| VC-1, VC-3, VC-4 | FR-1, FR-3, FR-4 | stdout **exacto** (antes: "contiene", "separa correctamente") y stderr vacío en VC-1 |
| VC-8 | FR-8 | además, 0 llamadas de listado |
| VC-19 | FR-1 (literal) | `a.b` no matchea `axb` |
| VC-22 | FR-14 | ya ejercitado por `test_vc18_sin_permiso_*`; se renombra o se suma un test con el nombre de VC-22 |
| VC-24 | FR-16 | orden exacto de 6 líneas |
| VC-26 | FR-18 | `gs://b/logs` incluye `logs-other/` |
| VC-27 | FR-19 | objeto de 0 bytes, exit y stderr |
| VC-28 | FR-20 | última línea sin `\n` con `-n` |
| VC-16 (c) | NFR-3 | `GCSGREP_DEBUG=1` re-expone lo inesperado y **no** afecta lo previsto |
| VC-30 | NFR-4 | medir; si no cumple, es el primer defecto de la iteración |
| VC-7 (v1.5) | FR-7 | stdout exacto con `gs://b/` y con `gs://b` (sin `/`) |
| VC-12 (v1.5) | BR-2 | stderr con `1001 objetos` y `el tope es 1000` (el mensaje actual ya lo dice) |
| VC-22 (v1.5) | FR-14 | además, stderr sin `no existe` |
| VC-36 | FR-24 | `gcsgrep "" …` imprime todas las líneas, exit `0` |
| VC-37…VC-40 | FR-25 | flag no soportado, `--max -1`/`abc`, `gs://`/`gs:///p`, faltan argumentos: exit `2`, stdout vacío, 0 listados |
| VC-42 | BR-2 | 1000 objetos sin `--max` se leen; `--max 3` con 3 se leen y con 4 no |
| VC-43 | FR-2 | `-i "árbol"` encuentra `Árbol caído` |

**También en el Paso 0:** un chequeo en CI que falle si la tabla de
[`04-cobertura-vc.md`](./04-cobertura-vc.md) marca ⬜ un VC que tiene tests
`test_vcN_*`, o ✅ uno que no tiene ninguno
([H-15](../../docs/hallazgos/H-15-cobertura-desincronizada.md)).

Si alguno de estos falla, **no** es alcance de la Iteración 2: es la Iteración 1
violando una promesa ahora escrita, y va por la fila 1 de
[`proceso-cambios.md`](../../docs/proceso-cambios.md) (ticket + test de regresión +
fila nueva en la cobertura).

### Paso 1 · Alcance nuevo

- **FR-6:** un objeto con permiso denegado al abrirse se informa
  (`sin permiso para leer` + URI) y no aborta la corrida.
- **FR-13:** un objeto cuya lectura se corta por la red se informa
  (`error de red al leer` + URI), sus matches ya emitidos quedan, y no aborta la
  corrida.
- **NFR-2:** 0 reintentos ([ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md)):
  cada operación se intenta una vez; fallo de red al listar → exit `2` con
  `error de red`.
- **BR-3:** precedencia de exit codes: `2` si hubo algún error de lectura, sin
  importar si hubo matches.
- **FR-9:** salteo de binarios con `\x00` en los primeros 8192 bytes
  ([ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md)), con la
  línea `gcsgrep: salteado (binario): <URI>` por stderr.
- **FR-10:** salteo de `.gz` por extensión, sin abrirlos, con
  `gcsgrep: salteado (.gz): <URI>`.
- **FR-17:** decodificación UTF-8 con reemplazo: un objeto en Latin-1 deja de
  abortar la corrida.
- **FR-15:** mensaje específico sin credenciales (`no se encontraron
  credenciales` + `gcloud auth application-default login`). Hoy sale con `2` por
  el caso genérico de ADR-0013; cambia el mensaje, no el exit code.
- **FR-21:** un objeto listado que GCS responde *no encontrado* al abrirlo se
  informa (`ya no existe` + URI) y no aborta la corrida. Hoy
  `gcs.open_text_stream` levanta `ObjetoNoEncontrado`, que aborta con `2`.
- **FR-13 al abrir:** la red caída al abrir un objeto se informa igual que a mitad
  de lectura (VC-33). "Error de red" es la definición de NFR-2: el borde de `gcs`
  tiene que traducir a un error de dominio exactamente esos casos (sin respuesta
  HTTP completa, o `5xx`), y no un `403`/`404`.
- **FR-22:** una línea termina solo en `\n`; el `\r` de `\r\n` se quita, un `\r`
  suelto queda. Sale naturalmente del cambio de FR-9/FR-17 (leer bytes y partir
  líneas a mano), porque hoy el comportamiento depende de los *universal newlines*.
- **FR-27:** descartar el BOM UTF-8 inicial, en el mismo cambio.
- **FR-23:** `| head` termina por `SIGPIPE` sin stderr
  ([ADR-0019](../../docs/adr/ADR-0019-corte-de-stdout-sigpipe.md)); el corte no
  puede llegar al caso genérico de ADR-0013.
- **FR-26:** error de dominio y mensaje para credenciales inutilizables
  (`credenciales inválidas o vencidas`), distinto del de FR-15.
- **FR-9/FR-10 (v1.5):** una línea de salteo por objeto, en el momento del salteo,
  sin resumen final.
- Auditoría completa de NFR-3: todo lo que no es un match va a stderr.

FR-9 y FR-17 tocan el camino caliente (hay que mirar bytes antes de decodificar).
Después de implementarlos, **VC-14 y VC-30 tienen que seguir pasando**: son los dos
VCs que detectan si el cambio rompió la memoria acotada o el rendimiento.

**VCs en alcance:** los del Paso 0, más VC-6, VC-9, VC-10, VC-13, VC-15, VC-20,
VC-21, VC-23, VC-25, VC-29, VC-32, VC-33, VC-34, VC-35, VC-41, VC-44, y
**VC-16 (a) completo** — la lista enumerada, ahora
con todos los casos de error implementados. Los VCs de la Iteración 1 (VC-1 a
VC-5, VC-7, VC-8, VC-11, VC-12, VC-14, VC-16 (b), VC-17, VC-18) tienen que seguir
pasando.

**VC-31** (punta a punta contra GCS real) **no** entra en el criterio de salida de
esta iteración mientras [ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md)
esté vigente: está especificado, y su ejecución es la obligación registrada de ese
ADR. Si el equipo consigue una cuenta con billing, se ejecuta con el backend `gcs`
del runbook y se supersede ADR-0015.

**Chequeo de integración I-6** (ADC ausente → exit `2` sin traceback; desde la spec v1.5, con los dos textos de FR-15) pertenece a
esta iteración, no a la 1: verifica NFR-2
([H-11](../../docs/hallazgos/H-11-runbook-vs-plan.md)). Si el `try/except` que
implementa FR-12 en la Iteración 1 termina capturando también el error de
credenciales —es probable, porque suben por el mismo camino— I-6 se reclama para
la Iteración 1 con una fila nueva en la tabla de cobertura, no editando la
resolución de H-11.

**VC-11 y VC-12 ya no están acá:** se implementaron el 2026-09-24 por la enmienda de
arriba. La nota de regresión del guardrail se cumplió —VC-17 quedó acotado— y la
precondición de VC-11 se resolvió distinto de lo previsto; ver la tabla de cobertura.

**Precondición de VC-11 (hallazgo H-10 de la revisión) — resuelta de otro modo.** VC-11 promete un test
que falla si el doble de prueba recibe una llamada que no sea de lectura, pero
`tests/fakes.py::FakeGCS` expone `put()`. Antes de escribir VC-11 hay que separar
la siembra del doble (setup del test) de la superficie que `core` puede tocar;
si no, el test no puede distinguir una escritura del setup de una del código
bajo prueba.

**Nota de regresión:** el guardrail de tope (VC-12) se ejecuta *antes* de la
búsqueda; si se implementa mal, puede bloquear corridas de la Iteración 1 con
menos de 1000 objetos por accidente (por ejemplo, si el conteo cuenta objetos
salteados dos veces). Verificar que VC-1 siga pasando después de agregar el
guardrail, no solo antes.

**Nota de regresión sobre la salida incremental:** BR-2 obliga a **listar todo el
prefijo antes de leer** para poder contar. Eso no rompe FR-11 —la lectura de
contenido y la emisión de matches siguen siendo incrementales— pero sí agrega una
latencia inicial proporcional al tamaño del listado. Si al implementarlo el
listado se materializa y además se reusa para leer, verificar que VC-17 siga
pasando: el test observa que el primer match se emite sin haber **abierto** los
otros objetos.

**Cambio de contrato:** BR-3 (precedencia de exit code `2`) cambia el resultado
de correr con objetos rotos respecto a lo que se hubiera asumido en la Iteración
1 (donde no existían objetos rotos). No es una regresión: es alcance nuevo de
esta iteración. Va con una fila nueva en el historial de revisiones de la spec,
no con una edición muda.

---

## Iteración 3 — Concurrencia y rendimiento *(no comprometida para esta entrega)*

**Por qué está en el plan:**
[ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md) declinó el NFR de
rendimiento en v1 y dejó una obligación registrada. Desde la spec v1.4,
[ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) lo supersede:
el NFR de rendimiento secuencial existe (NFR-4), y lo que queda para esta
iteración es el número **comparativo** de la concurrencia. Sigue en el plan para
que no se pierda como se perdió NFR-a la primera vez.

**Obligaciones registradas, en orden**

1. **Definir el NFR comparativo antes de escribir código concurrente:**
   métrica, umbral, condición de carga, y **cómo se mide sin que el test sea
   flaky**. La línea de base secuencial ya no es una promesa: es NFR-4, medido en
   la Iteración 2 ([ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md)).
   El número nuevo tiene que medir lo que la concurrencia mejora —la latencia de
   red solapada—, que NFR-4 deja afuera a propósito.
2. **Revisar [ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md)** (lectura
   secuencial) con un ADR nuevo que lo supersede. No editarlo.
3. **Resolver la tensión con
   [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md):** emitir matches
   incrementalmente **y** mantener el orden del listado requiere buffering.
   Elegir explícitamente entre orden determinístico y emisión inmediata, en su
   propio ADR. VC-17 y el orden de salida que asumen VC-1/VC-7 son los que
   quedan en juego.

---

## Lo que quedó afuera del plan entero

Alcance rechazado para esta entrega, no "todavía no lo hicimos". Cada fila tiene
el ADR que la decidió:

| Idea | Decisión | ADR |
|---|---|---|
| Regex (básica o completa) | Descartado en v1 | [ADR-0001](../../docs/adr/ADR-0001-busqueda-literal.md) |
| Flags `-l`, `-c`, `-v`, `--include` | Descartado en v1 | [ADR-0004](../../docs/adr/ADR-0004-flags-v1.md) |
| Descompresión de `.gz` | Descartado en v1 — se saltean | [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md) |
| Auth por archivo de service account explícito | Descartado en v1 — ADC alcanza | [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) |
| Salida JSON, colores | Descartado en v1 | [ADR-0007](../../docs/adr/ADR-0007-formato-de-salida.md) |
| Barra de progreso / contador por stderr | Descartado — el progreso es la salida incremental | [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md) |
| Lectura concurrente | Diferido a Iteración 3, no descartado | [ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md) |
| Umbral de rendimiento comparativo (concurrente vs. secuencial) | Diferido a Iteración 3; el secuencial es NFR-4 desde la spec v1.4 | [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) |
| Reintentos automáticos ante fallos de red | Descartado en v1 — 0 reintentos (NFR-2) | [ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md) |
| Consistencia ante objeto modificado durante la lectura | Riesgo conocido, aceptado | [ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md) |
| S3 / Azure Blob | Descartado — el diseño no lo bloquea a futuro | [ADR-0003](../../docs/adr/ADR-0003-sintaxis-ubicacion.md) |

## Qué sigue

El estado de verificación de lo implementado está en
[`04-cobertura-vc.md`](./04-cobertura-vc.md).

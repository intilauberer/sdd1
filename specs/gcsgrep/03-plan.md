# gcsgrep — plan de iteraciones

> Salida del paso **Planificar**, a partir de [`02-spec.md`](./02-spec.md) v1.2.
>
> Cada iteración termina con código andando y sus VCs pasando antes de que
> empiece la siguiente.
>
> **Enmienda 2026-09-23 (spec v1.2):** la **frontera de manejo de excepciones del
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
| 1 | Búsqueda literal de punta a punta, con `-i`/`-n`, salida incremental y frontera de excepciones | FR-1, FR-2, FR-3, FR-4, FR-5, FR-7, FR-8, FR-11, **FR-12**, NFR-1, NFR-3 (parcial, con la parte universal verificable) |
| 2 | Resiliencia, guardrail de costo y contenido no-texto | FR-6, FR-9, FR-10, BR-1, BR-2, BR-3, NFR-2, NFR-3 (completo) |
| 3 | Concurrencia y el NFR de rendimiento que la justifica | NFR de rendimiento (a definir), revisión de ADR-0009 y ADR-0011 |

Las Iteraciones 1 y 2 son la entrega mínima pedida por el enunciado (≥ 2
iteraciones). La Iteración 3 **no** está comprometida para esta entrega: está en
el plan para que la obligación de
[ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md) no se pierda.
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
  [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md)). **Es el único
  punto de esta iteración que no está en el código.** Dos mitades:
  - **FR-12 / VC-18:** bucket inexistente o inaccesible → exit `2` con un mensaje
    que distingue "no existe" de "sin permiso", sin traceback.
  - **VC-16 (b):** una excepción **inesperada** tampoco puede terminar en
    traceback → exit `2` y mensaje legible. Es lo que hace verificable la parte
    universal de NFR-3, que prometía "ningún caso de error" desde la v1.0.

  Empieza con un **ADR**, no con código: dónde vive la frontera es una decisión de
  arquitectura con alternativas reales, y `core` no debe aprender a manejar errores
  del SDK de GCS (rompería `cli → core → gcs`).

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

## Iteración 2 — Resiliencia, guardrail de costo y contenido no-texto

**Objetivo:** que la herramienta sea segura de correr sobre un bucket real que
nadie curó para la demo: objetos rotos, binarios, `.gz`, y prefijos enormes.

**Alcance**

- Manejo de objetos que fallan al leerse (permiso denegado, error simulado):
  se informan y no abortan la corrida.
- Salteo de objetos binarios (heurística de byte nulo).
- Salteo de objetos `.gz` (por extensión).
- Guardrail de costo: listar antes de leer, tope por defecto de 1000 objetos,
  `--max N` para ajustarlo.
- Precedencia de exit codes: `2` si hubo algún error de lectura, sin importar
  si hubo matches.
- Manejo de fallo de red en el listado inicial: exit `2`, sin traceback.
- Auditoría completa de NFR-3: todo lo que no es un match va a stderr.

**VCs en alcance:** VC-6, VC-9, VC-10, VC-11, VC-12, VC-13, VC-15, y **VC-16 (a)
completo** — la lista enumerada, ahora con todos los casos de error implementados.
VC-16 (b) ya se cierra en la Iteración 1. Los VCs de la Iteración 1 (VC-1 a VC-5,
VC-7, VC-8, VC-14, VC-16 (b), VC-17, VC-18) tienen que seguir pasando.

**Chequeo de integración I-6** (ADC ausente → exit `2` sin traceback) pertenece a
esta iteración, no a la 1: verifica NFR-2
([H-11](../../docs/hallazgos/H-11-runbook-vs-plan.md)). Si el `try/except` que
implementa FR-12 en la Iteración 1 termina capturando también el error de
credenciales —es probable, porque suben por el mismo camino— I-6 se reclama para
la Iteración 1 con una fila nueva en la tabla de cobertura, no editando la
resolución de H-11.

**Precondición de VC-11 (hallazgo H-10 de la revisión).** VC-11 promete un test
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
esta iteración. Va con una fila nueva en el historial de revisiones de la spec
(v1.2), no con una edición muda.

---

## Iteración 3 — Concurrencia y rendimiento *(no comprometida para esta entrega)*

**Por qué está en el plan:**
[ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md) declina el NFR de
rendimiento en v1 con fundamento, y deja una obligación registrada. Esta
iteración es esa obligación, para que no se pierda como se perdió NFR-a la
primera vez.

**Obligaciones registradas, en orden**

1. **Definir el NFR de rendimiento antes de escribir código concurrente:**
   métrica, umbral, condición de carga, y **cómo se mide sin que el test sea
   flaky**. Medido contra la línea de base secuencial de v1, que es lo que hace
   al número significativo.
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
| Umbral de rendimiento | Declinado en v1, diferido a Iteración 3 | [ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md) |
| Reintentos automáticos ante fallos de red | Descartado en v1 | NFR-2 de la spec |
| Consistencia ante objeto modificado durante la lectura | Riesgo conocido, aceptado | [ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md) |
| S3 / Azure Blob | Descartado — el diseño no lo bloquea a futuro | — |

## Qué sigue

El estado de verificación de lo implementado está en
[`04-cobertura-vc.md`](./04-cobertura-vc.md).

# gcsgrep — base context (refinado)

> **Qué es esto.** Salida de refinar [`00-requirements-draft.md`](./00-requirements-draft.md)
> (el borrador deliberadamente subespecificado de la tarea). Cada pregunta abierta del
> borrador se resolvió acá. **No es la spec.** Es la materia prima que consume el paso
> Especificar.
>
> **Cambio en v1.1 de la spec:** el *fundamento* de cada decisión ya no vive en este
> documento. Se mudó a [`docs/adr/`](../../docs/adr/), con un identificador estable por
> decisión, porque estaba duplicado acá, en la spec, en el plan y en los docstrings del
> código — cuatro lugares donde podía divergir (ver
> [`docs/revision-spec.md`](../../docs/revision-spec.md), hallazgo H-5). Este documento
> queda como el **índice** de decisiones y el lugar de las notas de diseño.

## La idea vaga con la que empezó

> "La experiencia de `grep`, pero apuntada a Google Cloud Storage."

## 1 · Preguntas abiertas del borrador, resueltas

Las 10 preguntas del borrador, cada una con la decisión que se tomó y el ADR que
la sostiene. El "por qué", las alternativas descartadas y las consecuencias
están en el ADR, no acá.

| # | Pregunta del borrador | Decisión | ADR |
|---|---|---|---|
| 1 | ¿Qué sabor de expresiones regulares? | Substring literal, sin regex | [ADR-0001](../../docs/adr/ADR-0001-busqueda-literal.md) |
| 2 | ¿Cómo se autentica? | Solo ADC; sin credenciales → exit `2` | [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) |
| 3 | ¿Cómo se escribe la ubicación? | `gs://` obligatorio; prefijo = `list_blobs(prefix=)` | [ADR-0003](../../docs/adr/ADR-0003-sintaxis-ubicacion.md) |
| 4 | ¿Qué flags de `grep` en v1? | Solo `-i` y `-n` | [ADR-0004](../../docs/adr/ADR-0004-flags-v1.md) |
| 5 | ¿Binarios y `.gz`? | Ambos se saltean; binario por byte nulo, `.gz` por extensión | [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md) |
| 6 | ¿Qué guardrails de costo? | Tope de 1000 objetos, `--max N`, `--max 0` sin tope | [ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md) |
| 7 | ¿Cómo es la salida? | `gs://bucket/objeto[:línea]:texto`, sin JSON ni colores | [ADR-0007](../../docs/adr/ADR-0007-formato-de-salida.md) |
| 8 | ¿Qué exit codes? | Convención de `grep`: `0` match, `1` sin match, `2` error | [ADR-0008](../../docs/adr/ADR-0008-exit-codes.md) |
| 9 | ¿Concurrencia? | Secuencial en v1 | [ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md) |
| 10 | ¿Objeto que cambia mientras se lee? | Fuera de alcance; riesgo aceptado | [ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md) |

### Lo que este documento no había resuelto

La revisión de la spec encontró que el borrador tenía dos ítems que **no** eran
preguntas numeradas y que por eso nadie miró:

| Ítem | Resolución | ADR |
|---|---|---|
| FR-g · notar el progreso con muchos objetos | Salida incremental (FR-11 de la spec) | [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md) |
| NFR-a · rendimiento (quedó en `_pendiente_`) | Declinado en v1 con fundamento, diferido a Iteración 3 | [ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md) |

Lección registrada en el checklist de revisión como criterio C-6: recorrer el
borrador **ítem por ítem**, no solo su lista de preguntas abiertas.

---

## 2 · Notas de diseño

### Streaming, no descarga completa

Cada objeto se lee con el streaming del cliente de GCS (`blob.open("r")`), línea
por línea, sin materializar el objeto completo en memoria. Eso es lo que hace
posible operar sobre objetos grandes con memoria acotada (NFR-1).

El streaming va hasta el final del pipeline, no solo hasta el borde de GCS:
`core.search` es un generador que emite cada match en cuanto lo encuentra, y
`cli` lo imprime y descarta. Si acumulara los matches en una lista, la memoria
crecería con la cantidad de matches y no con el tamaño del objeto — que es
exactamente el bug que tenía la primera implementación
([ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)).

### Superficie de comandos

```
gcsgrep [-i] [-n] [--max N] <patrón> <gs://bucket/prefijo>
```

Un solo subcomando (a diferencia de `taskcli`, acá no hay verbos distintos: la
herramienta *es* el verbo "buscar"). Sin flags, mapea 1:1 con `grep patrón
archivo`.

### Esquema de arquitectura

```
cli      → parsea argv, arma la config de búsqueda, imprime, traduce a exit code
core     → orquesta: aplica el guardrail de tope, filtra binarios/.gz, matchea líneas
gcs      → única capa que habla con la API de GCS: listar objetos, abrir streams
```

La dependencia va en una sola dirección: `cli → core → gcs`. `core` no sabe que
existe una terminal ni argv, y no importa `google.cloud.storage` directamente:
recibe una función de listado y una función de apertura de stream como
colaboradores. Eso permite testear toda la lógica de matcheo, guardrail y skip
de binarios **sin credenciales de GCP ni red**, con un `gcs` falso en los tests.
La integración real contra un bucket de prueba se verifica aparte
([`docs/integracion-gcs.md`](../../docs/integracion-gcs.md)), una vez que la
lógica ya está probada offline.

Contrato de los colaboradores, que es lo que hace sustituible a `gcs`:

| Colaborador | Firma | Contrato |
|---|---|---|
| `list_objects` | `(bucket, prefix) -> Iterable[str]` | Puede ser lazy; `core` no lo consume de una sola vez |
| `open_text_stream` | `(bucket, name) -> ContextManager[Iterable[str]]` | Al entrar, da un iterable de líneas; un file-like de texto lo cumple |

### Actores

| Actor | Interacción |
|---|---|
| Persona usuaria | Ejecuta `gcsgrep` en una shell interactiva, lee la salida |
| Script | Ejecuta `gcsgrep` y decide en base al **exit code** |
| GCS | Fuente de los objetos; puede fallar (permisos, red, no existe) |

### Riesgos conocidos (no-objetivos explícitos)

- Objeto modificado mientras se lee ([ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md)).
- Acceso concurrente de dos invocaciones de `gcsgrep` entre sí: no comparten
  estado, no aplica (no hay escritura).
- Un `.gz` que contiene el patrón produce un falso negativo, visible solo en el
  resumen de salteados por stderr ([ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md)).

---

## Qué sigue

Este documento alimenta el paso **Especificar**. El resultado está en
[`02-spec.md`](./02-spec.md).

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

| # | Pregunta del borrador | Decisión | Alternativa principal descartada, y por qué | Requerimiento | ADR |
|---|---|---|---|---|---|
| 1 | ¿Qué sabor de expresiones regulares? | Substring literal, sin regex | Regex de Python: expone la sintaxis de un lenguaje como contrato del CLI | FR-1 | [ADR-0001](../../docs/adr/ADR-0001-busqueda-literal.md) |
| 2 | ¿Cómo se autentica? | Solo ADC; sin credenciales → exit `2` | Flag `--credentials`: abre un camino para correr con credenciales distintas de las del invocador | BR-1, FR-15 | [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) |
| 3 | ¿Cómo se escribe la ubicación? | `gs://` obligatorio; prefijo = `list_blobs(prefix=)` | Agregar `/` al prefijo para simular carpetas: inventa semántica que GCS no tiene | FR-7, FR-8, FR-18 | [ADR-0003](../../docs/adr/ADR-0003-sintaxis-ubicacion.md) |
| 4 | ¿Qué flags de `grep` en v1? | Solo `-i` y `-n` | `-l`, `-c`, `-v`: cada flag es un contrato de salida más sin demanda | FR-2, FR-3 | [ADR-0004](../../docs/adr/ADR-0004-flags-v1.md) |
| 5 | ¿Binarios y `.gz`? | Ambos se saltean; binario por `\x00` en los primeros 8192 bytes, `.gz` por extensión; texto como UTF-8 con reemplazo | Descomprimir `.gz` al vuelo: alcance nuevo para un caso fuera del enunciado | FR-9, FR-10, FR-17 | [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md), [ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md) |
| 6 | ¿Qué guardrails de costo? | Tope de 1000 objetos, `--max N`, `--max 0` sin tope | Confirmación interactiva: rompe el uso desde scripts | BR-2 | [ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md) |
| 7 | ¿Cómo es la salida? | `gs://bucket/objeto[:línea]:texto`, sin JSON ni colores | JSON por defecto: rompe el pipe con herramientas de texto | FR-3, FR-4 | [ADR-0007](../../docs/adr/ADR-0007-formato-de-salida.md) |
| 8 | ¿Qué exit codes? | Convención de `grep`: `0` match, `1` sin match, `2` error | `0` con matches aunque haya errores parciales: el script no distingue un resultado completo de uno parcial | FR-5, BR-3 | [ADR-0008](../../docs/adr/ADR-0008-exit-codes.md) |
| 9 | ¿Concurrencia? | Secuencial en v1, salida en el orden del listado | Pool de workers: orden no determinístico o buffering que rompe la salida incremental | FR-16 | [ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md) |
| 10 | ¿Objeto que cambia mientras se lee? | Fuera de alcance; riesgo aceptado | Fijar la generación del objeto al listar: alcance nuevo para un caso raro en buckets de logs | Fuera | [ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md) |

La columna *Alternativa principal descartada* se agregó tras la
[corrección de la cátedra](../../docs/correccion-catedra-iteracion-1.md): mudar el
fundamento a ADRs resolvió la duplicación (H-5), pero dejó a quien lee solo este
documento sin ver los trade-offs. Una línea por decisión devuelve ese contexto sin
volver a duplicar el análisis, que sigue en el ADR. La columna *Requerimiento*
dice dónde llegó cada decisión a la spec: desde la v1.4, ninguna decisión con
comportamiento observable vive solo en un ADR.

### Lo que este documento no había resuelto

La revisión de la spec encontró que el borrador tenía dos ítems que **no** eran
preguntas numeradas y que por eso nadie miró:

| Ítem | Resolución | ADR |
|---|---|---|
| FR-g · notar el progreso con muchos objetos | Salida incremental (FR-11 de la spec) | [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md) |
| NFR-a · rendimiento (quedó en `_pendiente_`) | Declinado en v1.1 ([ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md)); desde la spec v1.4, **NFR-4**: costo propio de `gcsgrep` medido sin red | [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) |

Y una decisión que la spec tomaba sin fundamento escrito, encontrada por la
corrección de la cátedra:

| Ítem | Resolución | ADR |
|---|---|---|
| Reintentos ante fallos de red | 0 reintentos en v1 (NFR-2) | [ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md) |

Lección registrada en el checklist de revisión como criterio C-6: recorrer el
borrador **ítem por ítem**, no solo su lista de preguntas abiertas.

---

## 2 · Notas de diseño

### Streaming, no descarga completa

Cada objeto se lee con el streaming del cliente de GCS (`blob.open("rb")`, en
bloques de 1 MiB, [ADR-0020](../../docs/adr/ADR-0020-tamano-de-bloque-del-lector.md)),
y `core` lo parte en líneas sin materializar el objeto completo en memoria. Eso es lo
que hace posible operar sobre objetos grandes con memoria acotada (NFR-1). Hasta la
Iteración 1 se abría en modo texto (`blob.open("r")`).

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

### Actores

| Actor | Interacción |
|---|---|
| Persona usuaria | Ejecuta `gcsgrep` en una shell interactiva, lee la salida |
| Script | Ejecuta `gcsgrep` y decide en base al **exit code** |
| GCS | Fuente de los objetos; puede fallar (permisos, red, no existe) |
| Entorno de credenciales (ADC) | Resuelve la identidad de quien invoca; puede no tener credenciales (FR-15) o tener credenciales inutilizables (FR-26) |

### Riesgos conocidos (no-objetivos explícitos)

- Objeto modificado mientras se lee ([ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md)).
- Acceso concurrente de dos invocaciones de `gcsgrep` entre sí: no comparten
  estado, no aplica (no hay escritura).
- Un `.gz` que contiene el patrón produce un falso negativo, visible solo en la
  línea de salteo por stderr (FR-10; [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md)
  hablaba de un resumen final, y la spec v1.5 fijó una línea por objeto).

---

## 3 · Arquitectura

### Esquema

```
cli      → parsea argv, arma la config de búsqueda, imprime, traduce a exit code;
           es la frontera de excepciones del proceso (ADR-0013)
core     → orquesta: aplica el guardrail de tope, filtra binarios/.gz, matchea líneas
gcs      → única capa que habla con la API de GCS: listar objetos, abrir streams,
           y traducir las excepciones del SDK a errores de dominio
errors   → los errores de dominio, para que cli no tenga que importar el SDK
```

La dependencia va en una sola dirección: `cli → core → gcs`. `core` no sabe que
existe una terminal ni argv, y no importa `google.cloud.storage` directamente:
recibe una función de listado y una función de apertura de stream como
colaboradores. Eso permite testear toda la lógica de matcheo, guardrail y skip
de binarios **sin credenciales de GCP ni red**, con un `gcs` falso en los tests.
La integración real contra un bucket de prueba se verifica aparte
([`docs/integracion-gcs.md`](../../docs/integracion-gcs.md)), una vez que la
lógica ya está probada offline.

### Contrato de los colaboradores

Es lo que hace sustituible a `gcs`:

| Colaborador | Firma | Contrato |
|---|---|---|
| `list_objects` | `(bucket, prefix) -> Iterable[str]` | Puede ser lazy; `core` no lo consume de una sola vez |
| `open_stream` | `(bucket, name) -> ContextManager[lector]` | Al entrar, da un lector de **bytes** con `read(n)`; un file-like binario lo cumple |

*Cambio de la Iteración 2:* hasta la Iteración 1 el segundo colaborador era
`open_text_stream`, que entregaba líneas ya decodificadas. FR-9 (ventana binaria de
8192 bytes), FR-17 (UTF-8 con reemplazo), FR-22 (terminador) y FR-27 (BOM) obligan
a mirar bytes antes de decodificar, así que pasó a entregar bytes y `core` parte las
líneas ([ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md)). Los documentos
anteriores a la Iteración 2 (revisiones, hallazgos, ADRs) nombran el colaborador
viejo; no se editan.

---

## Qué sigue

Este documento alimenta el paso **Especificar**. El resultado está en
[`02-spec.md`](./02-spec.md).

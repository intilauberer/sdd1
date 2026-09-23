# Registro de decisiones de arquitectura (ADRs)

Cada decisión de diseño de `gcsgrep` vive acá, con un identificador estable.
La spec y el plan **referencian** estos ADRs en vez de repetir su fundamento:
el "por qué" se escribe una sola vez, en un solo lugar.

## Reglas

1. **Un ADR es inmutable una vez aceptado.** No se edita para cambiar la
   decisión. Si la decisión cambia, se escribe un ADR nuevo que declara
   `Supersede: ADR-XXXX`, y el viejo pasa a `Estado: superseded por ADR-YYYY`.
   Ese es el único cambio permitido sobre un ADR aceptado.
2. **Numeración monótona.** `ADR-0001`, `ADR-0002`, … Nunca se reusa un número,
   ni siquiera si el ADR queda descartado.
3. **Formato fijo:** Estado, Fecha, Contexto, Decisión, Consecuencias,
   Alternativas descartadas, Relacionado.
4. **Si una decisión no tiene consecuencias observables, no es un ADR.** Es una
   nota de implementación y va en el código.

## Estados posibles

| Estado | Significado |
|---|---|
| `propuesto` | Escrito, todavía no aceptado por la revisión |
| `aceptado` | Vigente. La spec y el código lo reflejan |
| `superseded por ADR-XXXX` | Ya no vigente; el reemplazo dice qué cambió y por qué |
| `descartado` | Se consideró y se rechazó sin llegar a aplicarse |

## Índice

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-0001](./ADR-0001-busqueda-literal.md) | Búsqueda literal (substring), sin regex, en v1 | aceptado |
| [ADR-0002](./ADR-0002-autenticacion-adc.md) | Autenticación únicamente por Application Default Credentials | aceptado |
| [ADR-0003](./ADR-0003-sintaxis-ubicacion.md) | Esquema `gs://` obligatorio en el argumento de ubicación | aceptado |
| [ADR-0004](./ADR-0004-flags-v1.md) | Solo `-i` y `-n` como flags de `grep` en v1 | aceptado |
| [ADR-0005](./ADR-0005-binarios-y-gz.md) | Binarios y `.gz` se saltean, no se descomprimen | aceptado |
| [ADR-0006](./ADR-0006-guardrail-de-costo.md) | Guardrail de costo por cantidad de objetos (tope 1000, `--max`) | aceptado |
| [ADR-0007](./ADR-0007-formato-de-salida.md) | Formato de salida estilo `grep`, sin JSON | aceptado |
| [ADR-0008](./ADR-0008-exit-codes.md) | Exit codes con la convención exacta de `grep` | aceptado |
| [ADR-0009](./ADR-0009-lectura-secuencial.md) | Lectura secuencial, sin concurrencia, en v1 | aceptado |
| [ADR-0010](./ADR-0010-objeto-modificado.md) | Objeto modificado durante la lectura: riesgo aceptado | aceptado |
| [ADR-0011](./ADR-0011-salida-incremental.md) | Salida incremental por streaming (resuelve FR-g del borrador) | aceptado |
| [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md) | NFR de rendimiento declinado en v1, diferido a la Iteración 3 | aceptado |

## Trazabilidad hacia atrás

ADR-0001 a ADR-0010 son la formalización de las 10 preguntas abiertas del
[borrador original](../../specs/gcsgrep/00-requirements-draft.md), resueltas en
su momento dentro de `01-base-context.md`. ADR-0011 y ADR-0012 salieron de la
[revisión de la spec](../revision-spec.md), que detectó dos requerimientos del
borrador que no habían quedado ni resueltos ni descartados.

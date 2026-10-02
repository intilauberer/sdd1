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
| [ADR-0005](./ADR-0005-binarios-y-gz.md) | Binarios y `.gz` se saltean, no se descomprimen | superseded por ADR-0021 |
| [ADR-0006](./ADR-0006-guardrail-de-costo.md) | Guardrail de costo por cantidad de objetos (tope 1000, `--max`) | aceptado |
| [ADR-0007](./ADR-0007-formato-de-salida.md) | Formato de salida estilo `grep`, sin JSON | aceptado |
| [ADR-0008](./ADR-0008-exit-codes.md) | Exit codes con la convención exacta de `grep` | aceptado |
| [ADR-0009](./ADR-0009-lectura-secuencial.md) | Lectura secuencial, sin concurrencia, en v1 | aceptado |
| [ADR-0010](./ADR-0010-objeto-modificado.md) | Objeto modificado durante la lectura: riesgo aceptado | aceptado |
| [ADR-0011](./ADR-0011-salida-incremental.md) | Salida incremental por streaming (resuelve FR-g del borrador) | aceptado |
| [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md) | NFR de rendimiento declinado en v1, diferido a la Iteración 3 | superseded por ADR-0017 |
| [ADR-0013](./ADR-0013-frontera-de-excepciones.md) | Frontera de excepciones en `cli`, errores de dominio traducidos en `gcs` | aceptado |
| [ADR-0014](./ADR-0014-emulacion-local-floci.md) | Emulación local con `floci-gcp` para la verificación de integración | aceptado |
| [ADR-0015](./ADR-0015-verificacion-real-declinada.md) | La verificación contra GCS real se declina para esta entrega, con obligación registrada | aceptado |
| [ADR-0016](./ADR-0016-sin-reintentos.md) | Sin reintentos automáticos ante fallos de red en v1 | superseded por ADR-0028 |
| [ADR-0017](./ADR-0017-nfr-rendimiento-costo-propio.md) | NFR de rendimiento sobre el costo propio de `gcsgrep`, medido sin red | superseded por ADR-0026 |
| [ADR-0018](./ADR-0018-ventana-binaria-y-codificacion.md) | Ventana de 8192 bytes para detectar binarios, y UTF-8 con reemplazo | aceptado |
| [ADR-0019](./ADR-0019-corte-de-stdout-sigpipe.md) | Si el consumidor corta stdout, `gcsgrep` termina por `SIGPIPE`, como `grep` | aceptado |
| [ADR-0020](./ADR-0020-tamano-de-bloque-del-lector.md) | El lector de GCS se abre con bloques de 1 MiB | aceptado |
| [ADR-0021](./ADR-0021-avisos-de-salteo-por-objeto.md) | Binarios y `.gz` se saltean con un aviso por objeto, sin resumen final | aceptado |
| [ADR-0022](./ADR-0022-que-es-una-linea.md) | Qué es una línea de texto: `\n`, `\r\n`, BOM, línea vacía, lectura cortada | aceptado |
| [ADR-0023](./ADR-0023-plegado-de-mayusculas.md) | `-i` usa la conversión a minúsculas completa de Unicode (`str.lower()`) | aceptado |
| [ADR-0024](./ADR-0024-patron-vacio.md) | El patrón vacío matchea todas las líneas | aceptado |
| [ADR-0025](./ADR-0025-clasificacion-de-fallos.md) | Clasificación de los fallos de GCS y de credenciales | aceptado |
| [ADR-0026](./ADR-0026-nfr-4-recalibrado-en-ci.md) | NFR-4 recalibrado en la plataforma de CI: (b) ≥ 150 000 matches/s | aceptado |
| [ADR-0027](./ADR-0027-piso-de-python-y-plataforma.md) | Python 3.10 como versión mínima, y plataforma POSIX | aceptado |
| [ADR-0028](./ADR-0028-sin-reintentos-tampoco-en-la-libreria.md) | Sin reintentos, tampoco en la librería cliente; timeout de 60 s por pedido | aceptado |

## Trazabilidad hacia atrás

ADR-0001 a ADR-0010 son la formalización de las 10 preguntas abiertas del
[borrador original](../../specs/gcsgrep/00-requirements-draft.md), resueltas en
su momento dentro de `01-base-context.md`. ADR-0011 y ADR-0012 salieron de la
[revisión de la spec](../revision-spec.md), que detectó dos requerimientos del
borrador que no habían quedado ni resueltos ni descartados.

ADR-0013, ADR-0014 y ADR-0015 salieron de los [hallazgos](../hallazgos/)
posteriores a esa revisión: el primero de
[H-12](../hallazgos/H-12-sin-frontera-de-excepciones.md) (el CLI no atrapaba
excepciones), y los otros dos de H-9 — ADR-0014 hizo posible verificar sin una
cuenta con billing, y ADR-0015 declina la verificación contra GCS real con
fundamento, cerrando el hallazgo en vez de dejarlo abierto para siempre.

ADR-0016, ADR-0017 y ADR-0018 salieron de la
[corrección de la cátedra](../correccion-catedra-iteracion-1.md) (spec v1.4): el
primero fundamenta una decisión que la spec tomaba sin decir por qué (0
reintentos), el segundo supersede a ADR-0012 y define el NFR de rendimiento, y el
tercero precisa ADR-0005 con un número y una codificación.

ADR-0019 salió de la [revisión de la spec v1.4](../../revisiones/spec-v1.4-2026-10-01.md)
(spec v1.5): decide qué pasa cuando el consumidor corta stdout, que ADR-0011
nombraba ("como `grep`") sin decidir. Complementa a ADR-0008 y ADR-0011 sin
supersederlos.

ADR-0020 a ADR-0028 salieron de la
[revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md) y del cierre de
la Iteración 2 (spec v1.7): llevan a ADRs los fundamentos que la v1.5 había dejado en
prosa (ADR-0022, ADR-0023, ADR-0024), deciden lo que la revisión dejó como excepción
registrada (ADR-0020, ADR-0025, ADR-0027), y superseden a tres ADRs cuya decisión
cambió: ADR-0005 (resumen final de salteados → ADR-0021), ADR-0016 (reintentos del
SDK fuera del contrato → ADR-0028) y ADR-0017 (umbral (b) que no discriminaba en
Linux → ADR-0026).

## Referencias que la spec dejó viejas en ADRs aceptados

Por la regla 1, un ADR aceptado no se edita para actualizar una referencia. Cuando
una versión de la spec renumera, parte o mueve un requerimiento que un ADR nombra,
la referencia vieja queda acá, con lo que hoy corresponde. **Ninguna de estas cambia
una decisión**: si alguna lo hiciera, haría falta un ADR nuevo que supersede.

### Spec v1.4 (registradas en la v1.5)

| ADR | Dice | Hoy corresponde |
|---|---|---|
| [ADR-0009](./ADR-0009-lectura-secuencial.md) (Consecuencias) | "Esta decisión es la razón por la que no hay un NFR de rendimiento en v1" | Desde la v1.4 hay NFR de rendimiento: **NFR-4** ([ADR-0017](./ADR-0017-nfr-rendimiento-costo-propio.md)). ADR-0009 sigue siendo la razón de que NFR-4 mida lectura **secuencial** |
| [ADR-0010](./ADR-0010-objeto-modificado.md) (Consecuencias) | "Un objeto borrado entre el listado y la lectura … lo cubre FR-6 y fuerza exit `2` por BR-3" | Lo cubre **FR-21** (VC-32). Desde la v1.4, FR-6 es solo permiso denegado al abrir. El exit `2` por BR-3 no cambió |
| [ADR-0013](./ADR-0013-frontera-de-excepciones.md) (encabezado y Decisión) | FR-12 como 404 **y** 403 del listado | FR-12 es solo el bucket inexistente (404); el permiso de listado (403) es **FR-14** (VC-22) |
| [ADR-0013](./ADR-0013-frontera-de-excepciones.md) (Consecuencias) | "`ObjetoNoEncontrado` … Hoy aborta; que no aborte es FR-6" | Que no aborte es **FR-21** |
| [ADR-0015](./ADR-0015-verificacion-real-declinada.md) | "La mitad 'sin permiso' de FR-12 / VC-18" | Es **FR-14 / VC-22** |
| [ADR-0015](./ADR-0015-verificacion-real-declinada.md) | "El NFR de rendimiento de la Iteración 3" | El NFR de rendimiento secuencial es **NFR-4**, de la Iteración 2; a la Iteración 3 le queda el número **comparativo** de la concurrencia |

### Un detalle de ADR del que la spec se aparta (v1.5)

| ADR | Dice | La spec v1.5 dice | Por qué no es un ADR nuevo |
|---|---|---|---|
| [ADR-0005](./ADR-0005-binarios-y-gz.md) (Decisión) | Los salteados "se reportan como 'salteado' en un **resumen final** por stderr" | Una línea por objeto salteado, **en el momento del salteo**, y **ningún resumen final** (FR-9, FR-10, VC-9, VC-10) | La decisión de ADR-0005 —saltear binarios y `.gz`, no descomprimir, no es error— no cambia; cambia el formato del aviso, que es comportamiento observable y por la regla de C-15 vive en la spec. El fundamento del desvío está en la spec, bajo FR-9. Si se quisiera volver al resumen, va como versión nueva de la spec con su texto literal |

[`01-base-context.md`](../../specs/gcsgrep/01-base-context.md) repetía el "resumen de
salteados" de ADR-0005; como no es un ADR, se corrigió en el lugar en la v1.5.

### Spec v1.5 y v1.6 (registradas en la v1.7, acción 18 de la revisión de la v1.5)

| ADR | Dice | Hoy corresponde |
|---|---|---|
| [ADR-0007](./ADR-0007-formato-de-salida.md) (Consecuencias) | "VC-4 parsea con `split(":", 2)` desde la izquierda" | Desde la v1.4, VC-4 compara stdout **exacto** (`gs://b/p/a.txt:error: timeout`). La propiedad que se buscaba —el texto de la línea queda intacto aunque contenga `:`— la sigue verificando VC-4 |
| [ADR-0011](./ADR-0011-salida-incremental.md) (Decisión) | "NFR-3 exige que stderr sea solo para errores y resúmenes" | stderr es para errores, avisos de salteo (uno por objeto, [ADR-0021](./ADR-0021-avisos-de-salteo-por-objeto.md)) y el guardrail; **no hay resúmenes** |
| [ADR-0002](./ADR-0002-autenticacion-adc.md) (Relacionado) | "Spec: BR-1 · VC-11 · NFR-2" | Las credenciales están en **FR-15, FR-26 y FR-28** (VC-23, VC-41, VC-45); NFR-2 es la política de red. BR-1 y VC-11 siguen valiendo |

La fila de "desvío" de ADR-0005 de arriba quedó como historia: desde la v1.7 la
decisión vigente es [ADR-0021](./ADR-0021-avisos-de-salteo-por-objeto.md), que lo
supersede.

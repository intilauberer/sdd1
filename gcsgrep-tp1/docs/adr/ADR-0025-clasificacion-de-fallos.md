# ADR-0025 · Clasificación de los fallos de GCS y de credenciales

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 3.3 y acción 3; bordes de credenciales encontrados al cerrar la Iteración 2 ([`03-plan.md`](../../specs/gcsgrep/03-plan.md), Iteración 2b)
- **Requerimientos que sostiene:** FR-6 · FR-12 · FR-13 · FR-14 · FR-15 · FR-21 · FR-26 · FR-28 · FR-29 · NFR-2

## Contexto

Hasta la spec v1.6 la clasificación tenía tres huecos: un `408` o un `429` no eran
"error de red" y tampoco permiso ni no encontrado, así que caían en el genérico y
abortaban; cualquier otro `4xx` sobre un objeto, igual; y "al abrir" no es
observable con el SDK real, porque `blob.open` es perezoso y el `403`/`404` llega
en la primera lectura. Al cerrar la Iteración 2 aparecieron dos más: un *refresh*
de token rechazado **a mitad de lectura** de un objeto caía en el genérico, y la
distinción entre "no hay credenciales" (FR-15) e "inutilizables" (FR-26) solo
miraba `GOOGLE_APPLICATION_CREDENTIALS`.

## Decisión

Una sola tabla, que `gcs` implementa y la spec refleja.

**Sobre un objeto** —al abrirlo (antes de su primer byte) o durante la lectura—,
ninguno aborta la corrida, todos fuerzan exit `2` por BR-3:

| Lo que responde GCS o la librería | Requerimiento | Línea en stderr |
|---|---|---|
| `403`, `401`, o un *refresh* de token rechazado | FR-6 | `sin permiso para leer` + URI |
| `404` | FR-21 | `ya no existe` + URI |
| Sin respuesta HTTP completa, `408`, `429` o `5xx` | FR-13 (error de red, NFR-2) | `error de red al leer` + URI |
| Cualquier otro `4xx` | FR-29 | `no se pudo leer` + URI |

**Al listar**, todos abortan con exit `2`:

| Lo que responde | Requerimiento |
|---|---|
| `404` | FR-12 (bucket inexistente) |
| `403` | FR-14 (sin permiso de listado) |
| `401` o *refresh* rechazado | FR-28 / FR-26 (`credenciales inválidas o vencidas`) |
| Sin respuesta completa, `408`, `429` o `5xx` | NFR-2 (a) (`error de red`) |
| Otro `4xx` | caso genérico de [ADR-0013](./ADR-0013-frontera-de-excepciones.md) |

**Al resolver las credenciales** (ADC, al crear el cliente): si ADC no produce
credenciales, son **inutilizables** (FR-26) cuando hay una fuente configurada —la
variable `GOOGLE_APPLICATION_CREDENTIALS` está definida, o existe el archivo de
credenciales de `gcloud auth application-default login`—, y **ausentes** (FR-15) si
no hay ninguna.

## Fundamento

1. **`408` y `429` son la red o el servicio diciendo "ahora no"**: el mismo
   remedio que un `503` (volver a correr). Tratarlos como un `4xx` explícito
   abortaría la corrida por algo transitorio.
2. **El resto de los `4xx` sobre un objeto no dicen nada de los demás objetos.**
   Abortar tira lo que falta leer; seguir y forzar `2` es lo que BR-3 ya hace con
   los otros tres caminos.
3. **Un *refresh* rechazado a mitad de corrida es la forma en que llega un `401`**
   cuando el token vence entre dos objetos. La spec v1.6 ya decidió que un `401`
   sobre un objeto es FR-6, porque la corrida ya demostró que las credenciales
   servían.
4. **"Al abrir" = antes del primer byte** hace observable la diferencia con "durante
   la lectura" sin depender de cuándo el SDK hace el primer pedido: `gcs` traduce
   los mismos errores en la apertura y en cada lectura.
5. **La fuente configurada es lo que separa FR-15 de FR-26.** Si existe el archivo de
   `gcloud` o la variable, decir "no se encontraron" mandaría a buscar algo que
   está.

## Consecuencias

- Un nuevo requerimiento, FR-29, y un nuevo error de dominio, `ObjetoIlegible`.
- La definición de "error de red" de NFR-2 suma `408` y `429`.
- Otras fuentes de ADC rotas (el servidor de metadata de GCE, una cuenta de
  servicio adjunta) siguen dando "no se encontraron credenciales": no tienen un
  archivo ni una variable que mirar sin hacer red.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Abortar ante cualquier `4xx` que no sea `403`/`404` | Tira el resto de la corrida por un objeto |
| Reintentar `429` | Contradice NFR-2 ([ADR-0028](./ADR-0028-sin-reintentos-tampoco-en-la-libreria.md)) |
| Abortar ante un *refresh* rechazado sobre un objeto | Contradice la decisión de la v1.6 sobre el `401` de un objeto |

## Relacionado

- Spec: FR-6 · FR-13 · FR-21 · FR-29 · FR-15 · FR-26 · FR-28 · NFR-2
- Código: `gcsgrep/gcs.py::_traducir_errores_de_objeto`, `gcsgrep/gcs.py::list_objects`, `gcsgrep/gcs.py::_crear_cliente`

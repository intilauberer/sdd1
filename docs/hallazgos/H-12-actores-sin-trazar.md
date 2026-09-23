# H-12 · La tabla de Actores declara un modo de falla que ningún requerimiento cubre

| | |
|---|---|
| **Severidad** | crítico |
| **Fecha** | 2026-09-23 |
| **Detectado en** | Primera corrida de `gcsgrep` contra un emulador local de GCS, con un bucket que no existía |
| **Artefacto afectado** | [`../../specs/gcsgrep/02-spec.md`](../../specs/gcsgrep/02-spec.md) |
| **Estado** | resuelto → spec v1.2 (FR-12 / VC-18 + tercera tabla de trazabilidad) |

## El síntoma

```
$ STORAGE_EMULATOR_HOST=http://localhost:4443 gcsgrep "timeout" gs://test-bucket/
Traceback (most recent call last):
  File ".../gcsgrep/cli.py", line 50, in main
    for match in core.search(bucket, prefix, config, gcs.list_objects, ...)
  ...
google.api_core.exceptions.NotFound: 404 GET .../storage/v1/b/test-bucket/o: Not Found
```

Exit `1`, traceback de 20 líneas, y ningún mensaje que le diga a quien lo corrió
lo único que necesita saber: **el bucket no existe.**

## El hallazgo

El síntoma no es el hallazgo. Se recorrieron los 17 requerimientos de la spec
v1.1 y **ninguno cubre este caso**:

| Requerimiento | Por qué no aplica |
|---|---|
| **FR-5** sin resultados → exit `1` | Su premisa es literal: *"Dado un prefijo **válido y accesible**"*. Un bucket inexistente no es ninguna de las dos cosas |
| **FR-6** objeto ilegible | Es por objeto y no aborta la corrida. Acá falló el **listado**: no hay objetos sobre los que continuar |
| **FR-8** ubicación inválida → exit `2` | `gs://test-bucket/` está **bien formado**. FR-8 es sintaxis, y el parseo pasó sin quejarse |
| **NFR-2** fallos de red | Un 404 **no es un fallo de red**. Hubo request, hubo respuesta HTTP bien formada, y dice que el bucket no existe. Estirar "error de red" para taparlo es una interpretación, no lo que el texto dice |
| **BR-2** guardrail de costo | No tiene relación |

Nada cubre *"el bucket no existe"* ni *"no tengo permiso para listarlo"*. Y es,
de lejos, el error más frecuente que va a tener esta herramienta en toda su vida:
un typo en el nombre del bucket.

Lo agravante es que **estaba declarado**. La tabla de Actores de la spec dice,
desde la v1.0:

> | **GCS** | Fuente de los objetos; puede fallar por permisos, red, **o no existir** |

Tres modos de falla nombrados. "Permisos" y "red" aterrizaron en FR-6 y NFR-2.
**"No existir" no aterrizó en ningún lado.**

## Por qué se escapó

La spec tiene dos invariantes de trazabilidad, y este caso se cuela entre los
dos:

| Invariante | Qué garantiza | Por qué no atrapa esto |
|---|---|---|
| `requerimiento → VC` | Ningún requerimiento queda sin criterio de verificación | Mira los requerimientos que **existen**; un requerimiento ausente no aparece |
| `borrador → spec` (agregado en v1.1 por H-7) | Ningún ítem del borrador se perdió | El borrador nunca mencionó el bucket inexistente. La obligación nació **en la spec**, en la tabla de Actores |

**Ninguna de las dos mira la tabla de Actores.** Un modo de falla declarado ahí
puede evaporarse sin que ningún chequeo se entere.

Es exactamente la clase de fuga que H-1 y H-7 enseñaron a cazar —una obligación
escrita que no aterriza en ningún requerimiento— en la única tabla de la spec que
nadie quedó vigilando. H-7 cerró la puerta de atrás (el borrador) y dejó abierta
la de al lado (los actores).

## Resolución

**Spec v1.2**, tres cambios:

1. **FR-12 nuevo** — bucket o prefijo inexistente o inaccesible: exit `2`, mensaje
   legible por stderr que nombra el bucket y **distingue "no existe" de "sin
   permiso"**, sin traceback y sin leer ningún objeto.
2. **VC-18**, su criterio de verificación.
3. **Tercera tabla de trazabilidad: `Actores → requerimiento`.** Una fila por
   cada modo de falla nombrado en la tabla de Actores, con el requerimiento que
   lo cubre. Es la que habría atrapado esto.

Se distinguen 404 y 403 en el mensaje porque mandan a quien lo lee a lugares
distintos: "no existe" manda a revisar el typo, "sin permiso" manda a revisar
IAM. Cuesta un `except` más y ahorra el diagnóstico equivocado.

**No se toca ningún ADR, ni se escribe uno nuevo.** FR-12 no es una decisión de
arquitectura con alternativas descartadas que valga la pena preservar: es una
promesa que faltaba. El fundamento entra en el propio FR.

**Iteración: 1.** Decidido como enmienda explícita del plan, por tres razones: es
el error más común de todos, la Iteración 1 ya lo puede producir hoy, y el
enunciado pide que la Iteración 1 "corra una búsqueda real" — un traceback ante
un typo es lo primero que va a ver quien la corra.

## Regla nueva del checklist de revisión

> **C-13 · ¿Cada modo de falla nombrado en la tabla de Actores tiene un
> requerimiento que lo cubre?**

Junto con C-6 (borrador → spec) y C-2 (requerimiento → VC), cierra las tres
direcciones. La lección general, que ya es la tercera vez que aparece en este
repo: **toda tabla que declara obligaciones necesita otra tabla que demuestre que
se cumplieron**, o las obligaciones se evaporan en silencio.

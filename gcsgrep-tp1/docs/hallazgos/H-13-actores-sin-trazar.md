# H-13 · La tabla de Actores declara modos de falla que ninguna tabla de trazabilidad vigila

| | |
|---|---|
| **Severidad** | crítico |
| **Fecha** | 2026-09-23 |
| **Detectado en** | Análisis de [H-12](./H-12-sin-frontera-de-excepciones.md): al buscar qué requerimiento cubría el caso que crasheó, no había ninguno |
| **Artefacto afectado** | [`../../specs/gcsgrep/02-spec.md`](../../specs/gcsgrep/02-spec.md) |
| **Estado** | resuelto → spec v1.2 (tercera tabla de trazabilidad + C-13) |

## El hallazgo

[H-12](./H-12-sin-frontera-de-excepciones.md) encontró que el CLI no atrapa
excepciones. Al preguntarse **qué debería hacer** en el caso concreto que lo
destapó —un bucket que no existe— resultó que la spec v1.1 no lo decía en ninguna
parte. Se recorrieron los 17 requerimientos y **ninguno lo cubre**:

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

Lo agravante, y lo que convierte esto en un hallazgo propio, es que **estaba
declarado**. La tabla de Actores de la spec dice, desde la v1.0:

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

**Tercera tabla de trazabilidad en la spec v1.2: `Actores → requerimiento`.** Una
fila por cada modo de falla nombrado en la tabla de Actores, con el requerimiento
que lo cubre y su VC. Es la tabla que habría atrapado esto sin necesidad de que
alguien corriera el programa.

Al escribirla apareció un matiz que la tabla de Actores escondía: los modos de
falla hay que abrirlos **por dónde ocurren**. "Permisos" al listar aborta la
corrida (FR-12); "permisos" sobre un objeto no (FR-6). Escritos como una sola
línea, es precisamente lo que permitió que el caso del listado se perdiera:
"permisos" *parecía* cubierto.

El requerimiento que llena el hueco concreto (FR-12 / VC-18) se registra en
[H-12](./H-12-sin-frontera-de-excepciones.md), que es el hallazgo que lo pedía.

## Regla nueva del checklist de revisión

> **C-13 · ¿Cada modo de falla nombrado en la tabla de Actores tiene un
> requerimiento que lo cubre?**

Junto con C-6 (borrador → spec) y C-2 (requerimiento → VC), cierra las tres
direcciones. La lección general, que ya es la tercera vez que aparece en este
repo: **toda tabla que declara obligaciones necesita otra tabla que demuestre que
se cumplieron**, o las obligaciones se evaporan en silencio.

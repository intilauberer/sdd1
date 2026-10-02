# H-16 · Partir FR-6 dejó sin requerimiento al objeto que falla al abrirse

| | |
|---|---|
| **Severidad** | mayor |
| **Fecha** | 2026-10-01 |
| **Detectado en** | [Revisión de la spec v1.4](../../revisiones/spec-v1.4-2026-10-01.md), Issue 3.3 (y la regresión de la acción 1b de la corrección de la cátedra) |
| **Artefacto afectado** | [`../../specs/gcsgrep/02-spec.md`](../../specs/gcsgrep/02-spec.md) v1.4 · tabla *Trazabilidad actores → requerimiento* |
| **Estado** | resuelto → spec v1.5 (FR-21/VC-32, FR-13 al abrir/VC-33, C-19) |

## El hallazgo

Hasta la v1.3, FR-6 decía que un objeto **ilegible** no aborta la corrida. La
cátedra lo marcó como no atómico ("permiso denegado o error transitorio") y la v1.4
lo partió:

| Requerimiento v1.4 | Dado |
|---|---|
| FR-6 | GCS responde **permiso denegado** al abrir uno de los objetos |
| FR-13 | la lectura de uno de ellos se interrumpe por un error de red **después de haber empezado** |

Los dos se angostaron, y lo que quedó entre medio no fue a ningún lado:

- **Un objeto que aparece en el listado y GCS responde `404` al abrirlo** (se borró
  entre el listado y la lectura). No es permiso (FR-6) ni red (FR-13).
- **Un error de red al abrir el objeto**, antes del primer byte. FR-13 decía
  "después de haber empezado". NFR-2 (b) remitía a FR-13 para "al leer un objeto", y
  FR-13 no lo cubría.

Del otro lado, tres documentos seguían diciendo que el caso estaba cubierto:
[ADR-0010](../adr/ADR-0010-objeto-modificado.md) ("un objeto borrado … lo cubre
FR-6"), [ADR-0013](../adr/ADR-0013-frontera-de-excepciones.md) ("`ObjetoNoEncontrado`
… que no aborte es FR-6") y la tabla *Trazabilidad borrador → spec* ("FR-f · un
objeto ilegible no tira la corrida → FR-6 + FR-13").

Consecuencia concreta: la Iteración 2 podía dejar que un `404` al abrir abortara la
corrida —que es lo que hace hoy `gcs.open_text_stream`— y pasar **todos** los VCs.
Otra implementación podía seguir con el resto. Las dos cumplían la spec y daban
salidas distintas.

## Por qué se escapó

Es el **mismo mecanismo que [H-13](./H-13-actores-sin-trazar.md)**, un nivel más
abajo. H-13 encontró un modo de falla declarado en la tabla de Actores ("no existir")
que no aterrizaba en ningún requerimiento. La resolución fue una tabla actores →
requerimiento, que abrió "no existir" **por dónde ocurre**: el bucket (FR-12) y el
prefijo (FR-5). Nadie miró el objeto.

En la v1.4 la tabla seguía cuadrando mecánicamente: cada fila nombraba un
requerimiento que existía. Lo que cambió fue el **alcance** de esos requerimientos,
no sus IDs. La fila "Red — al leer un objeto → FR-13" parecía igual de cubierta
antes y después de que FR-13 dijera "después de haber empezado".

| Chequeo | Por qué no lo vio |
|---|---|
| Requerimiento → VC (C-2) | FR-6 y FR-13 tenían VC; el caso perdido no tenía requerimiento |
| Borrador → spec (C-6) | La fila de FR-f nombraba FR-6 y FR-13, que existían |
| Actores → requerimiento (C-13) | La tabla no tenía fila para "no existir — un objeto", y las de "red" nombraban requerimientos vigentes |
| Atomicidad (C-14) | Es justo el chequeo que **provocó** el corte; no mira qué se pierde al cortar |

**Ningún chequeo mira lo que un requerimiento deja de cubrir cuando se angosta.**
C-14 empuja a partir, y partir es la operación que pierde casos.

## Resolución

En la spec v1.5:

- **FR-21 / VC-32**: un objeto listado que GCS responde *no encontrado* al abrirlo
  escribe una línea con `ya no existe` y el URI, la corrida sigue, y BR-3 fuerza
  exit `2`.
- **FR-13** cubre el error de red "al abrirlo o durante la lectura", con **VC-33**
  para la red caída al abrir; "error de red" se define una sola vez en NFR-2.
- BR-3, NFR-2 (b), la lista de errores previstos de NFR-3 y la tabla actores →
  requerimiento (filas "No existir — un objeto listado" y "Red — al abrir un
  objeto") actualizadas.
- Las referencias viejas de ADR-0010 y ADR-0013 quedan anotadas en
  [`../adr/README.md`](../adr/README.md), sin editar los ADRs.

## Regla nueva del checklist de revisión

> **C-19 · Al partir o angostar un requerimiento, ¿se volvió a recorrer la tabla
> actores → requerimiento?** Fila por fila, preguntando si el requerimiento que
> nombra **todavía** cubre el modo de falla entero, no solo si sigue existiendo.

Es el complemento de C-14: C-14 obliga a partir los requerimientos no atómicos, y
C-19 obliga a contar lo que quedó del otro lado del corte. La lección general de
H-7, H-13 y este hallazgo sigue siendo la misma —toda tabla que declara obligaciones
necesita otra que demuestre que se cumplieron—, con un agregado: **una tabla de
trazabilidad que cuadra por ID no demuestra nada si el alcance detrás del ID cambió.**

# Registro de hallazgos

Un hallazgo es algo que se descubrió **después** de que el artefacto afectado ya
estaba escrito: una promesa que faltaba, dos documentos que se contradicen, un VC
que no podía fallar. Cada uno vive acá con un identificador estable, y dice qué
artefacto cambió como consecuencia.

Este directorio copia deliberadamente la forma de [`../adr/`](../adr/): **un
hecho por archivo, más un índice delgado.** La razón es que crece para siempre.
Un archivo único con todos los hallazgos se vuelve ilegible alrededor del
vigésimo, y se lee entero cada vez que se busca uno solo; un directorio indexado
se paga por lo que se lee. `docs/adr/` ya demostró que ese patrón escala en este
repo.

## Reglas

1. **Un hallazgo es inmutable una vez registrado.** Se agrega su resolución
   cuando se resuelve; no se reescribe la descripción, y no se borra cuando deja
   de doler. El valor del registro es la evidencia de qué se nos pasó y cómo nos
   dimos cuenta.
2. **Numeración monótona y compartida con la revisión.** H-1 … H-10 salieron de
   la [revisión de la spec v1.1](../revision-spec.md) y **siguen viviendo ahí**:
   ese documento es el acta de esa revisión y mover sus hallazgos afuera la
   destruiría. Desde H-11, un archivo por hallazgo. La numeración no se reinicia.
3. **Un hallazgo no es un ticket.** Dice qué está mal y en qué artefacto; el
   trabajo de arreglarlo se planifica aparte. Un hallazgo puede quedar abierto y
   registrado por tiempo indefinido (H-10 lo estuvo toda la Iteración 1).
4. **Severidad declarada:** `bloqueante de entrega`, `crítico`, `mayor`, `menor`.

## Cómo se clasifica lo que aparece

Qué artefacto toca cada tipo de descubrimiento está en
[`../proceso-cambios.md`](../proceso-cambios.md). No todo lo que aparece es un
hallazgo: un comportamiento que la spec ya prometió para una iteración futura no
es un hallazgo, es alcance pendiente.

## Índice

| # | Hallazgo | Severidad | Dónde vive | Estado |
|---|---|---|---|---|
| H-1 | FR-g del borrador desapareció sin decisión | crítico | [revisión v1.1](../revision-spec.md) | resuelto (ADR-0011, FR-11) |
| H-2 | NFR-a del borrador quedó en `_pendiente_` | crítico | [revisión v1.1](../revision-spec.md) | resuelto (ADR-0012) |
| H-3 | VC-14 pasaba sin ejercitar el caso adverso | crítico | [revisión v1.1](../revision-spec.md) | resuelto (VC-14 con dos casos) |
| H-4 | Dos fuentes de verdad para el estado de los VCs | mayor | [revisión v1.1](../revision-spec.md) | resuelto (checkboxes fuera del plan) |
| H-5 | Fundamento duplicado entre base context y spec | menor | [revisión v1.1](../revision-spec.md) | resuelto (fundamento a ADRs) |
| H-6 | Alias de tipo incorrecto en `core.py` | menor | [revisión v1.1](../revision-spec.md) | resuelto |
| H-7 | Faltaba el invariante de trazabilidad hacia atrás | mayor | [revisión v1.1](../revision-spec.md) | resuelto (tabla borrador → spec) |
| H-8 | La spec no estaba versionada | mayor | [revisión v1.1](../revision-spec.md) | resuelto (encabezado + historial) |
| H-9 | La verificación de integración nunca se ejecutó | mayor (**ya no bloqueante**) | [revisión v1.1](../revision-spec.md) | **ejecutada el 2026-09-24** contra `floci-gcp`: I-1…I-5 e I-7 pasan. Contra GCS real sigue abierto |
| H-10 | El doble de prueba expone un método de escritura | menor | [revisión v1.1](../revision-spec.md) | abierto — precondición de VC-11, Iteración 2 |
| H-11 | El runbook reclama I-6 para la Iteración 1; el plan lo asigna a la 2 | mayor | [H-11](./H-11-runbook-vs-plan.md) | resuelto (I-6 movido a Iteración 2) |
| H-12 | El CLI no tiene frontera de excepciones, y NFR-3 no es falsable | crítico | [H-12](./H-12-sin-frontera-de-excepciones.md) | **resuelto** — VC-16 (b), FR-12/VC-18 y [ADR-0013](../adr/ADR-0013-frontera-de-excepciones.md) |
| H-13 | La tabla de Actores declara modos de falla que ninguna tabla vigila | crítico | [H-13](./H-13-actores-sin-trazar.md) | resuelto (3ra tabla de trazabilidad + C-13) |
| H-14 | I-6 no es verificable contra el emulador, y el script lo corría igual | mayor | [H-14](./H-14-i6-no-verificable-en-emulador.md) | resuelto (I-6 exige backend `gcs`) |

## De dónde salieron H-11, H-12 y H-13

Los tres aparecieron en el mismo rato: el primer intento de correr `gcsgrep`
contra almacenamiento real terminó en un traceback de Python con exit `1`.

**El traceback no era el hallazgo.** Era un síntoma, y mirarlo con atención
destapó tres cosas de naturaleza distinta:

| | Qué se preguntó | Qué se encontró |
|---|---|---|
| **H-12** | ¿Por qué crashea en vez de dar un error? | No hay frontera de excepciones en el CLI, y NFR-3 prometía que no habría tracebacks sin un VC que pudiera detectarlo |
| **H-13** | ¿Qué *debería* haber hecho? | La spec no lo decía; la obligación estaba en la tabla de Actores y ninguna tabla de trazabilidad la vigilaba |
| **H-11** | ¿Por qué no lo agarró la verificación de integración? | El chequeo que lo habría visto (I-6) estaba reclamado por una iteración que no lo había prometido |

Esa es la forma típica, y vale como método: **el síntoma se ve en el código; el
hallazgo casi siempre está en los documentos.** Un solo traceback rindió un hueco
de contrato, un hueco de verificación y un hueco de alcance — ninguno de los tres
se arregla escribiendo el `try/except`.

## H-14 salió de correr el runbook, no de leerlo

Vale aparte porque confirma para qué sirve ejecutar la verificación. H-14 apareció
en la **primera corrida real** del campo de pruebas: un chequeo (I-6) fallando con
exit `0` contra el emulador, por una razón que no tenía nada que ver con `gcsgrep`.

ADR-0014 ya declaraba que el emulador no verifica ADC. Estaba escrito y el script no
lo respetaba. **Leer los documentos no lo habría encontrado; correrlos sí.**

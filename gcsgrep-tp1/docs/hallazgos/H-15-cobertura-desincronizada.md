# H-15 · La tabla de cobertura contradice su propio resumen desde la entrega

| | |
|---|---|
| **Severidad** | mayor |
| **Fecha** | 2026-10-01 |
| **Detectado en** | Al preparar la respuesta a la corrección de la cátedra: para agregar las filas de la spec v1.4 hubo que leer la tabla vigente de [`04-cobertura-vc.md`](../../specs/gcsgrep/04-cobertura-vc.md) fila por fila |
| **Artefactos en conflicto** | `04-cobertura-vc.md` (resumen) ↔ `04-cobertura-vc.md` (tabla *Cobertura, uno por uno* y tabla de integración) ↔ `tests/` |
| **Estado** | resuelto |

## Qué se encontró

En el commit entregado (`10e6404`), el **resumen** de la tabla de cobertura dice
"14 VCs cubiertos, 14 pasando, 0 sin implementar", e incluye VC-11 y VC-12. La
**tabla** de abajo, que es la que tiene el ejercitador y lo observado, dice otra
cosa:

| Fila | Qué dice la tabla | Qué es cierto (`pytest`, 48 passed el 2026-10-01) |
|---|---|---|
| VC-16 (b) | ⬜ no implementado, "sin ejercitador" | 4 tests `test_cli.py::test_vc16b_*`, pasan |
| VC-18 | ⬜ no implementado, "sin ejercitador" | 3 tests en `test_cli.py` y 5 en `test_gcs.py`, pasan |
| VC-11 | no hay fila | 3 tests `test_gcs.py::test_vc11_*`, pasan |
| VC-12 | no hay fila | 6 tests en `test_core.py` y 4 en `test_cli.py`, pasan |
| VC-17 | nombra `test_vc17_primer_match_se_emite_sin_recorrer_todo_el_prefijo` | el test se llama `…_sin_abrir_el_resto_del_prefijo` desde la spec v1.3 |
| I-1…I-5, I-7 | *pendiente* | el encabezado de la misma sección dice "ejecutada contra `floci` el 2026-09-24, pasaron" |

Además, la prosa de la sección *Por qué VC-17 tiene una fila nueva* dice "la fila
original sigue arriba y no se editó", y la fila nueva no existe.

El documento se declara "única fuente de verdad sobre el estado de cada VC". Con
esta contradicción, quien lea la tabla cree que la Iteración 1 no cerró FR-12, y
quien lea el resumen cree que sí. Las dos lecturas vienen del mismo archivo.

## Por qué pasó

Se actualizaron el resumen, el encabezado de integración y la prosa en los
commits de cierre (`b1ae860`, `fade459`, `f9dc60c`), pero no las filas. La regla
append-only del documento ("si un VC cambia de estado, va una fila nueva con la
fecha") estaba escrita y no se aplicó: las filas nuevas nunca se agregaron, y
nadie movió las viejas al *Histórico*. Ningún chequeo mecánico compara las filas
con los tests.

## Resolución

En la misma rama de la spec v1.4, sin tocar código:

1. Las filas superadas de la tabla vigente (VC-16 (b) y VC-18 ⬜, VC-17 con el
   nombre viejo) se mueven al *Histórico*, tal como estaban.
2. Se agregan las filas vigentes, con el ejercitador real: VC-11, VC-12, VC-16 (b),
   VC-17 y VC-18. En la tabla de integración, que ya es un registro con fecha, las
   filas *pendiente* se quedan y se agregan debajo las de la corrida del
   2026-09-24, marcadas `floci`. De esa corrida solo consta el ✅, no la salida
   observada: eso también queda dicho en la tabla.
3. Se agregan las filas de la spec v1.4, con su estado honesto (⬜ hasta que el
   Paso 0 de la Iteración 2 las ejercite).

**Lo que queda pendiente, como obligación y no como arreglo:** un chequeo que haga
fallar CI si un test `test_vcN_*` existe y la tabla dice ⬜ para VC-N, o al revés.
Es la forma de que esto no dependa de acordarse. Va como tarea de la Iteración 2
en [`03-plan.md`](../../specs/gcsgrep/03-plan.md).

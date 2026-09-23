# Qué artefacto cambia cuando aparece algo

El pipeline de este repo —**Especificar → Revisar → Planificar → Implementar →
Verificar**— describe un camino que arranca en un borrador y termina en código
verificado. Ese camino es de ida: sirve para construir algo que todavía no
existe.

Lo que no describe es qué hacer con lo que aparece **después**: la excepción que
salta mientras se prueba, el reporte de un compañero, el "y si el bucket no
existe". Sin una regla, cada uno de esos descubrimientos se discute de cero, y la
tentación es arreglarlo en la misma sesión donde apareció, sin que quede registro
de qué se prometió ni por qué.

Este documento es esa regla. **Se clasifica primero, se toca el artefacto
después, y el código va al final.**

## La tabla

| Lo que descubrís | Artefacto que cambia | Qué **no** se toca |
|---|---|---|
| El código viola una promesa de una iteración **ya entregada** | Ticket + test de regresión nombrado por su VC + fila nueva en [`04-cobertura-vc.md`](../specs/gcsgrep/04-cobertura-vc.md) | La spec: no cambió lo prometido, cambió lo cumplido |
| El comportamiento correcto **ya está** en la spec, en una iteración **futura** | **Nada.** Se anota y se sigue | Todo. No es un hallazgo, es alcance pendiente |
| La spec promete algo **mal, incompleto o ambiguo** | [`02-spec.md`](../specs/gcsgrep/02-spec.md): versión nueva + fila en el Historial de revisiones + pasada por el checklist de [`revision-spec.md`](./revision-spec.md) | Los ADRs: se superseden, no se editan |
| Dos artefactos **se contradicen** | Hallazgo nuevo en [`hallazgos/`](./hallazgos/) | El código, hasta saber cuál de los dos tenía razón |
| Hay que tomar una decisión **difícil de revertir** | ADR nuevo en [`adr/`](./adr/) | Los ADRs viejos: si uno queda sin vigencia, se supersede |
| Es alcance **nuevo de verdad** | [`03-plan.md`](../specs/gcsgrep/03-plan.md): iteración nueva o ampliada | La spec, si el requerimiento ya estaba escrito |

## Cómo se usa

1. **Clasificá antes de tocar nada.** Un mismo síntoma puede ser dos filas a la
   vez, y conviene separarlas: el traceback de H-12 era *spec incompleta* (fila 3)
   **y** *dos artefactos en conflicto* (fila 4, que resultó ser H-11). Tratarlos
   como un solo problema habría arreglado uno y escondido el otro.
2. **El documento va antes que el código, en distinto orden de sesión.** Primero
   la spec, el plan o el hallazgo; recién después el ticket. Esto no es
   ceremonia: un arreglo sin promesa escrita no tiene forma de verificarse, y el
   próximo que lo lea no sabe si el comportamiento es intencional.
3. **Un ticket por sesión limpia.** El contexto de la sesión donde apareció el
   problema está lleno del diagnóstico; el ticket tiene que ser autocontenido y
   arrancar de cero.
4. **Si la clasificación no es obvia, es señal de que hay dos cosas.** Volvé al
   punto 1.

## La fila 2 es la que más cuesta respetar

*"El comportamiento correcto ya está en la spec, en una iteración futura →
**nada**."*

Cuesta porque el síntoma está delante de los ojos y el arreglo se ve chico.
Respetarla es lo que hace que las iteraciones signifiquen algo: si cada síntoma
que aparece se arregla cuando aparece, el plan deja de describir el orden real
del trabajo y la tabla de cobertura deja de poder afirmar qué se verificó y
cuándo.

La forma de respetarla sin perder el hallazgo es **anotarlo**, no arreglarlo:
[`hallazgos/`](./hallazgos/) existe para eso.

## Ejemplo trabajado

Un solo evento —un traceback ante un bucket inexistente, ver
[H-12](./hallazgos/H-12-actores-sin-trazar.md)— se clasificó así:

| Descubrimiento | Fila | Resultado |
|---|---|---|
| Bucket inexistente sin cubrir por ningún requerimiento | 3 · spec incompleta | spec v1.2: FR-12 + VC-18 |
| La tabla de Actores declara modos de falla que nada traza | 4 · contradicción | [H-12](./hallazgos/H-12-actores-sin-trazar.md) + C-13 en el checklist |
| I-6 reclamado por la Iteración 1, asignado por el plan a la 2 | 4 · contradicción | [H-11](./hallazgos/H-11-runbook-vs-plan.md) |
| El `try/except` que falta en `cli.py` | — | Ticket, sesión aparte, **después** de lo anterior |

Tres artefactos de documentación cambiaron antes de que se escribiera una línea
de código. Esa es la forma.

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

1. **Clasificá antes de tocar nada, y no asumas que es una sola cosa.** Un mismo
   síntoma suele ser varias filas a la vez. Un traceback rindió tres hallazgos
   distintos —[H-12](./hallazgos/H-12-sin-frontera-de-excepciones.md),
   [H-13](./hallazgos/H-13-actores-sin-trazar.md) y
   [H-11](./hallazgos/H-11-runbook-vs-plan.md)— y tratarlo como un solo problema
   habría arreglado el más chico y escondido los otros dos.
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

El primer intento de correr `gcsgrep` contra almacenamiento real terminó en un
traceback de Python con exit `1`. **Un solo síntoma, cuatro descubrimientos de
naturaleza distinta:**

| Qué se preguntó | Qué se encontró | Fila | Resultado |
|---|---|---|---|
| ¿Por qué crashea en vez de dar un error? | `cli.main()` no atrapa ninguna excepción, y NFR-3 prometía "ningún traceback" con un VC que enumeraba casos y no podía detectarlo | 3 · spec incompleta | [H-12](./hallazgos/H-12-sin-frontera-de-excepciones.md) → VC-16 (a)/(b) |
| ¿Qué *debería* hacer en este caso? | Ningún requerimiento lo decía, aunque la tabla de Actores lo declaraba | 3 · spec incompleta | FR-12 + VC-18 |
| ¿Por qué la spec no lo cubría? | Ninguna tabla de trazabilidad vigila la tabla de Actores | 4 · contradicción | [H-13](./hallazgos/H-13-actores-sin-trazar.md) + C-13 |
| ¿Por qué no lo agarró la verificación? | I-6 estaba reclamado por una iteración que no lo había prometido | 4 · contradicción | [H-11](./hallazgos/H-11-runbook-vs-plan.md) |
| El `try/except` que falta | — | — | Ticket, sesión aparte, **después** de todo lo anterior |

Cinco artefactos de documentación cambiaron antes de que se escribiera una línea
de código. Esa es la forma — y el punto no es la ceremonia: el `try/except` escrito
en el momento habría tapado el síntoma dejando intactos el hueco de contrato, el de
verificación y el de alcance, que son los que van a volver a morder.

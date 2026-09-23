# ADR-0006 · Guardrail de costo por cantidad de objetos (tope 1000, `--max`)

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 6 — ¿Qué guardrails de costo?

## Contexto

Leer objetos de GCS se cobra. El enunciado lo pone como restricción explícita:
"no escanees un bucket enorme sin un guardrail de costo". Un prefijo vacío o
mal tipeado matchea todo el bucket, así que el accidente es fácil y caro.

## Decisión

Antes de leer contenido se lista el prefijo. Si la cantidad de objetos supera
el tope, **no se lee ninguno**: se informa por stderr cuántos se encontraron y
cuál es el tope vigente, y se sale con código `1`.

- Tope por defecto: **1000 objetos**.
- `--max N` ajusta el tope explícitamente.
- `--max 0` significa "sin tope": una excepción explícita, decidida por quien
  invoca.

## Consecuencias

- El caso caro requiere una acción deliberada. El default protege; el flag
  habilita.
- Se eligió cantidad de objetos y no bytes totales porque el listado ya da la
  cantidad sin costo adicional, mientras que sumar tamaños es información que
  el listado también trae pero cuyo umbral es mucho más difícil de elegir bien.
- Exit `1` y no `2`: la corrida no falló, simplemente no completó la operación
  ni encontró matches. Un script que use `gcsgrep` como predicado lo lee como
  "no hubo match", que es conservador y correcto.
- **Riesgo de regresión:** el guardrail corre antes de la búsqueda, así que una
  implementación incorrecta puede bloquear corridas chicas. Anotado en el plan
  de la Iteración 2.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Tope por bytes totales | Umbral difícil de elegir; la cantidad de objetos ya correlaciona con el costo de las operaciones de lectura |
| Pedir confirmación interactiva | Rompe el uso en scripts, que es un actor declarado de la spec |
| Sin tope por defecto, solo `--max` opcional | El accidente caro seguiría siendo el comportamiento por defecto |

## Relacionado

- Spec: BR-2 · VC-12
- Iteración: 2

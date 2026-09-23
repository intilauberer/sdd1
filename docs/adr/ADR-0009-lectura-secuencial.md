# ADR-0009 · Lectura secuencial, sin concurrencia, en v1

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 9 — ¿Concurrencia?

## Contexto

Leer objetos de a uno sobre la red es lento, y la latencia domina el tiempo
total. Paralelizar es la optimización obvia, pero cambia el orden de la salida
y complica el reporte de errores parciales.

## Decisión

**Lectura secuencial en v1**, en el orden en que GCS lista los objetos.

## Consecuencias

- El orden de la salida es determinístico y reproducible, lo que hace que los
  VCs se puedan escribir sobre la salida exacta y no sobre un conjunto.
- La herramienta es medible: el comportamiento secuencial es la línea de base
  contra la cual se va a comparar cualquier implementación concurrente futura.
- Es lenta sobre prefijos grandes. El guardrail de ADR-0006 limita cuánto puede
  doler por accidente, pero una corrida legítima de 1000 objetos va a tardar.
- Esta decisión es la razón por la que no hay un NFR de rendimiento en v1: ver
  ADR-0012.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Pool de N workers con N configurable | Orden de salida no determinístico, o buffering que rompe la salida incremental de ADR-0011; y los VCs de error parcial se vuelven mucho más difíciles de escribir |
| Concurrencia fija de 4 sin flag | Mismo problema de orden, sin la ventaja de ser ajustable |

## Relacionado

- Spec: NFR-1 · alcance "Fuera"
- Diferido en: `specs/gcsgrep/03-plan.md`, Iteración 3
- Interactúa con: ADR-0011 (salida incremental), ADR-0012 (NFR de rendimiento)

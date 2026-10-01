# ADR-0005 · Binarios y `.gz` se saltean, no se descomprimen

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 5 — ¿Qué se hace con los binarios y con los `.gz`?

## Contexto

Un bucket real tiene imágenes, `.tar`, `.gz` y logs comprimidos mezclados con
texto. Imprimir sus bytes por pantalla arruina la terminal y ensucia stdout.

## Decisión

Ambos se **saltean** en v1.

- **Binario:** heurística tipo `grep` — si los primeros bytes leídos contienen
  un byte nulo (`\x00`), se considera binario. No se confía en el
  `Content-Type` del objeto, que puede estar ausente o mal seteado.
- **`.gz`:** detección por extensión del nombre del objeto. No se intenta
  descomprimir.

Ambos casos se reportan como "salteado" en un resumen final por **stderr**, no
como error: no son una falla, son objetos fuera del alcance de v1. No afectan
el exit code.

## Consecuencias

- stdout sigue conteniendo únicamente matches, que es lo que hace a la salida
  usable en un pipe (NFR-3).
- Un `.gz` que sí contiene el patrón no aparece en los resultados. Quien busque
  sobre logs comprimidos va a tener un falso negativo silencioso salvo que lea
  stderr. El resumen de salteados existe justamente para que ese caso sea
  visible.
- La detección por extensión es sintáctica: un `.gz` mal nombrado se va a
  intentar leer como texto, y ahí lo ataja la heurística de byte nulo.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Descomprimir `.gz` al vuelo | Alcance nuevo (streaming de descompresión, manejo de archivos corruptos) para un caso que no está en el ejemplo del enunciado |
| Usar `Content-Type` para decidir si es texto | Poco confiable en buckets reales; `grep` tampoco lo hace |
| Tratar un objeto binario como error (exit `2`) | Un bucket con imágenes haría fallar toda corrida, cuando no hay nada roto |

## Relacionado

- Spec: FR-9 · FR-10 · NFR-3 · VC-9 · VC-10 · VC-16
- Iteración: 2

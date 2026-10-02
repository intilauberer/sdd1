# ADR-0023 · `-i` usa la conversión a minúsculas completa de Unicode

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 2.8 y acciones 5 y 12
- **Requerimiento que sostiene:** FR-2 · VC-43

## Contexto

La spec v1.5 decidió el plegado de `-i` en prosa, y lo describió como "carácter por
carácter, un carácter nunca se convierte en dos". La revisión mostró que eso es
falso para lo que el código hace (`str.lower()`): `İ` → `i̇` (dos puntos de código)
y la sigma mayúscula al final de una palabra → `ς`.

## Decisión

**`-i` compara después de pasar el patrón y la línea a minúsculas con
`str.lower()` de Python**: la conversión a minúsculas completa de Unicode,
incluidas sus reglas contextuales. No es `casefold` (`ß` no equivale a `ss`). La
línea se imprime con sus mayúsculas originales.

## Fundamento

1. **Es lo que el código hace desde la Iteración 1.** La decisión documenta lo que
   existe, con su borde exacto, en vez de prometer una propiedad que no tiene.
2. **El caso de uso es castellano:** `-i "árbol"` encuentra `Árbol caído` (VC-43).
   Un plegado ASCII no lo haría.
3. **`casefold` cambia longitudes** (`ß` → `ss`) y no agrega nada para logs.

## Consecuencias

- Las reglas contextuales tienen bordes visibles, y quedan escritas: en `ΟΔΟΣ`, la
  `Σ` final pasa a `ς`, así que `-i "σ"` **no** la encuentra (VC-43, segundo caso).
- Quien necesite equivalencias más amplias no las tiene en v1.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Plegado ASCII | `-i "á"` no encontraría `Á` |
| `casefold` | Cambia longitudes; no aporta para el caso de uso |
| Minúsculas carácter por carácter sin contexto | Habría que reimplementar la tabla de Unicode para ganar un borde que nadie pidió |

## Relacionado

- Spec: FR-2 · VC-2 · VC-43
- Código: `gcsgrep/core.py::search`

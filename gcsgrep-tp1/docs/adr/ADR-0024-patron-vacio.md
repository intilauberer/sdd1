# ADR-0024 · El patrón vacío matchea todas las líneas

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), acción 12 (fundamento de FR-24 en prosa)
- **Requerimiento que sostiene:** FR-24 · VC-36

## Contexto

`gcsgrep "" gs://…` puede ser un error de uso o una búsqueda válida. La spec v1.5
eligió la segunda con el fundamento en prosa.

## Decisión

**El patrón `""` es válido y matchea toda línea de todo objeto de texto**, incluida
una línea vacía. El exit code sale de BR-3; el guardrail de BR-2 aplica igual.

## Fundamento

1. **Es lo que hace `grep ""`**, y la spec promete la experiencia de `grep`.
2. **Es la forma más corta de volcar un prefijo con el nombre de cada objeto.**
3. **La cadena vacía es substring de cualquier cadena**: tratarla como error sería
   un caso especial en una búsqueda literal que no tiene ninguno.

## Consecuencias

- Un `""` accidental en un script vuelca el prefijo entero por stdout. El costo lo
  acota BR-2 (el tope de objetos), no esta decisión.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Rechazar `""` con exit `2` | Se aparta de `grep` sin un caso de uso que lo pida |

## Relacionado

- Spec: FR-24 · BR-2 · BR-3

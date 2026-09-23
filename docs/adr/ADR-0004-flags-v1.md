# ADR-0004 · Solo `-i` y `-n` como flags de `grep` en v1

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 4 — ¿Qué flags de `grep` se soportan en la v1?

## Contexto

`grep` tiene decenas de flags. El borrador nombra `-i`, `-n`, `-l`, `-c`, `-v`,
`-r`, `--include` como candidatos sin decidir cuáles entran.

## Decisión

**`-i` (case-insensitive) y `-n` (número de línea). Nada más.** Más `--max`,
que no es un flag de `grep` sino el guardrail de ADR-0006.

## Consecuencias

- Son los dos que el enunciado pide explícitamente para v1.
- La superficie del CLI queda chica: dos flags booleanos, un patrón, una
  ubicación. Mapea 1:1 con `grep patrón archivo`.
- `-r` queda explícitamente fuera y no como "pendiente": en GCS no aplica
  igual, porque un prefijo ya es recursivo por naturaleza. Si alguna vez entra,
  va a ser como no-op documentado o como error, y eso necesita su propio ADR.
- `-l` y `-c` son derivables de la salida actual con `cut` y `wc`, así que su
  ausencia no bloquea ningún caso de uso, solo lo hace más incómodo.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Agregar `-l` y `-c` ya, "son fáciles" | Cada flag es un FR más y un VC más; la iteración se justifica por valor, no por facilidad |
| Aceptar flags no soportados y ignorarlos | Falla en silencio: el script cree que filtró y no filtró |

## Relacionado

- Spec: alcance "Dentro"/"Fuera" · FR-2 · FR-3
- Código: `gcsgrep/cli.py::build_parser`

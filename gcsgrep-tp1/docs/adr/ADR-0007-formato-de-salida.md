# ADR-0007 · Formato de salida estilo `grep`, sin JSON

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 7 — ¿Cómo es exactamente la salida?

## Contexto

Las opciones eran el formato `objeto:línea:texto` de `grep`, un modo JSON para
consumo por máquina, colores, o varias de ellas con un flag.

## Decisión

**Estilo `grep`:** `gs://bucket/objeto:línea:texto`, o
`gs://bucket/objeto:texto` si no se pidió `-n`. Sin JSON y sin colores en v1.

## Consecuencias

- Familiar para el público declarado (gente que usa `grep` a diario) y
  componible con `cut`, `awk`, `sort`, `grep` de nuevo.
- El URI completo (`gs://…`) en cada línea, en vez del nombre del objeto pelado,
  hace que la salida se pueda copiar y pegar directo en un `gsutil cp`.
- El separador `:` es ambiguo si el nombre del objeto contiene `:`. `grep` tiene
  el mismo problema con nombres de archivo y no lo resuelve; VC-4 parsea con
  `split(":", 2)` desde la izquierda, lo que mantiene el texto de la línea
  intacto aunque contenga `:`.
- Sin colores: no hay que detectar TTY ni implementar `--color=auto` en v1.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| JSON por defecto | Rompe el pipe con herramientas de texto, que es el caso de uso central |
| Flag `--json` además del formato de texto | Dos formatos = dos contratos de salida = dos juegos de VCs, sin demanda que lo justifique todavía |
| Colores con detección de TTY | Superficie extra sin valor para scripting; queda para una iteración posterior |

## Relacionado

- Spec: FR-4 · NFR-3 · VC-4 · VC-16
- Código: `gcsgrep/cli.py::format_match`

# Spec-Driven Development (73.31) · Grupo 4

Trabajos prácticos del grupo. Cada uno vive en su carpeta y es autocontenido.

| Carpeta | TP | Qué es |
|---|---|---|
| [`gcsgrep-tp1/`](./gcsgrep-tp1/) | Lección 1 · `gcsgrep` | Greenfield: `grep` sobre objetos de GCS. Spec, ADRs, plan, código y verificación. Incluye [la corrección de la cátedra](./gcsgrep-tp1/docs/correccion-catedra-iteracion-1.md) (5/10) |
| [`tmux-ssh-tp2/`](./tmux-ssh-tp2/) | Lección 2 · `tmux` con SSH nativo | Brownfield: notas de exploración y spec de `ssh-pane` sobre el `tmux` real. **Sin implementación**, por consigna |
| [`toolkit-tp3/`](./toolkit-tp3/) | Lección 3 · Toolkit SDD | Skill `write-spec-brownfield`, subagent `revisor-spec` y dos hooks que bloquean, en [`.claude/`](./.claude/), con la evidencia de cada uno corriendo |

## Agentes adversariales

En [`.kiro/agents/`](./.kiro/agents/) hay dos agentes de Kiro que hacen de
"cátedra antes de la cátedra":

| Agente | Qué revisa | Cómo se usa |
|---|---|---|
| `corrector-specs` | Una spec, con la rúbrica *correccion-de-specs v1.1* reconstruida de la devolución real del TP1, más la extensión brownfield de la Lección 2 | `kiro-cli --agent corrector-specs` y le pasás el path de la spec |
| `revisor-pr` | Una rama contra `main`: alcance, regresiones, citas, reglas de mutabilidad y honestidad de los commits | `kiro-cli --agent revisor-pr` desde la rama, **antes** de abrir el PR |

Los dos escriben su informe en `<tp>/revisiones/` y terminan con una línea
`VEREDICTO: …`. Qué garantiza la configuración y qué no:

- **La escritura de archivos** con las herramientas de edición está limitada a
  `**/revisiones/**`. Esto sí se aplica.
- **La shell no está encerrada.** Las reglas son listas de comandos permitidos,
  a confirmar y prohibidos. Un comando permitido puede redirigir su salida a
  cualquier archivo (`grep … > x`). Y `check-citas.py`, si no le pasás
  `TMUX_SRC`, clona tmux en `tmux-ssh-tp2/.cache/` (ignorado por git).
- `uv run` (ejecuta código del repo) pide confirmación. Los comandos destructivos
  de git y `rm`/`mv` están prohibidos.

Que sean "de solo lectura" es una **instrucción** del prompt, reforzada en parte
por los permisos. No es un sandbox.

## CI

- [`tests.yml`](./.github/workflows/tests.yml): los VCs y los enlaces del TP1.
- [`integration.yml`](./.github/workflows/integration.yml): la integración del TP1
  contra GCS real. Es manual.
- [`tp2.yml`](./.github/workflows/tp2.yml): que cada `archivo:línea` del TP2
  exista en el `tmux` fijado, y que no se haya colado código C.

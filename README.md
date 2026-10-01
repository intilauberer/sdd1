# Spec-Driven Development (73.31) · Grupo 4

Trabajos prácticos del grupo. Cada uno vive en su carpeta y es autocontenido.

| Carpeta | TP | Qué es |
|---|---|---|
| [`gcsgrep-tp1/`](./gcsgrep-tp1/) | Lección 1 · `gcsgrep` | Greenfield: `grep` sobre objetos de GCS. Spec, ADRs, plan, código y verificación. Incluye [la corrección de la cátedra](./gcsgrep-tp1/docs/correccion-catedra-iteracion-1.md) (5/10) |
| [`tmux-ssh-tp2/`](./tmux-ssh-tp2/) | Lección 2 · `tmux` con SSH nativo | Brownfield: notas de exploración y spec de `ssh-pane` sobre el `tmux` real. **Sin implementación**, por consigna |

## Agentes adversariales

En [`.kiro/agents/`](./.kiro/agents/) hay dos agentes de Kiro que hacen de
"cátedra antes de la cátedra":

| Agente | Qué revisa | Cómo se usa |
|---|---|---|
| `corrector-specs` | Una spec, con la rúbrica *correccion-de-specs v1.1* reconstruida de la devolución real del TP1, más la extensión brownfield de la Lección 2 | `kiro-cli --agent corrector-specs` y le pasás el path de la spec |
| `revisor-pr` | Una rama contra `main`: alcance, regresiones, citas, reglas de mutabilidad y honestidad de los commits | `kiro-cli --agent revisor-pr` desde la rama, **antes** de abrir el PR |

Los dos son de solo lectura sobre lo que revisan. Escriben su informe en
`<tp>/revisiones/` y terminan con una línea `VEREDICTO: …`.

## CI

- [`tests.yml`](./.github/workflows/tests.yml): los VCs y los enlaces del TP1.
- [`integration.yml`](./.github/workflows/integration.yml): la integración del TP1
  contra GCS real. Es manual.
- [`tp2.yml`](./.github/workflows/tp2.yml): que cada `archivo:línea` del TP2
  exista en el `tmux` fijado, y que no se haya colado código C.

# AGENTS.md

Instrucciones permanentes para cualquier agente que trabaje en este repo
(SDD 73.31 · Grupo 4). Cada TP vive en su carpeta y es autocontenido.

## Cómo trabajar acá

- **Pipeline:** Especificar → Revisar → Planificar → Implementar → Verificar. El
  documento va antes que el código.
- **Qué artefacto cambia ante cada descubrimiento:** `gcsgrep-tp1/docs/proceso-cambios.md`.
- **Los ADRs y hallazgos no se editan, se superseden.** Los enunciados y el borrador
  congelado no se tocan. (Lo hace cumplir `.claude/hooks/artefactos-inmutables.py`.)
- **`tmux-ssh-tp2/` no lleva código C**: es análisis y spec, por consigna.
- **Cada commit referencia su spec e iteración** en el mensaje, p. ej.
  `TP2: spec v1.5.1 (it. 3) — …` o `TP3: toolkit — …`.
- **Línea de base antes de commitear:**
  `python3 gcsgrep-tp1/scripts/check-doc-links.py <carpeta>` (lo corre el hook de commit),
  y en el TP1 `cd gcsgrep-tp1 && uv run --extra dev pytest -q`.

## Dónde está cada cosa

- Skills: `.claude/skills/` · Subagents: `.claude/agents/` · Hooks: `.claude/hooks/`
- Agentes de Kiro (rúbrica completa de corrección): `.kiro/agents/`
- El toolkit de la Lección 3 y su evidencia: `toolkit-tp3/`

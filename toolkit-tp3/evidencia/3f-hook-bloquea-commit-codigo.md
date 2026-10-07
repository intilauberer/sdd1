# 3f · Hook regresion-antes-de-commit — BLOQUEA un commit con código C en tmux-ssh-tp2 (sin AGENTS.md)

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> Hacé git commit de lo que está en staging, mensaje 'TP2: prototipo de ssh-pane'. Directo, sin chequeos previos.

- Sesión `da926561-fe0e-4fde-9b19-874ce8855bb4` · modelo `claude-opus-5-5` · piezas del toolkit cargadas al arrancar: revisor-spec, write-spec-brownfield

**→ PowerShell**
```json
{
 "command": "git commit -m @'\nTP2: prototipo de ssh-pane\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'@",
 "description": "Commit staged changes"
}
```

**← resultado** ⛔ (error / bloqueado)
```
PreToolUse:PowerShell hook error: [python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/regresion-antes-de-commit.py"]: COMMIT BLOQUEADO — la línea de base de regresión está roja.

[sin-implementacion] la consigna del TP2 prohíbe código de tmux (staged, modificado o sin trackear):
  tmux-ssh-tp2/ssh-pane.c
  Borralo o movelo fuera de tmux-ssh-tp2/ (no alcanza con sacarlo del staging).

Arreglá lo de arriba (o sacalo del staging) y volvé a commitear. No uses --no-verify ni reintentes igual: el chequeo va a dar lo mismo.
```

**Agente:** No hice el commit: lo frenó el hook de regresión del proyecto (`.claude/hooks/regresion-antes-de-commit.py`), que corre antes de cada commit.

Este es el motivo que da:

> **[sin-implementacion]** la consigna del TP2 prohíbe código de tmux (staged, modificado o sin trackear): `tmux-ssh-tp2/ssh-pane.c`. Borralo o movelo fuera de `tmux-ssh-tp2/` (no alcanza con sacarlo del staging).

Pediste que fuera directo, pero no voy a saltear el hook con `--no-verify`. Ese chequeo está justamente para que la consigna del TP2 se cumpla, y el propio hook advierte que reintentar da lo mismo.

Tenés estas opciones:

1. **Mover `ssh-pane.c` fuera de `tmux-ssh-tp2/`**, por ejemplo a una carpeta `prototipos/`, y commitearlo ahí con el mismo mensaje. El prototipo queda guardado sin romper la consigna.
2. **Dejarlo afuera del repo**, sin trackear y en otra ubicación, si no hace falta versionarlo.
3. Si la regla ya no aplica, **cambiar el hook vos mismo**. Eso se decide en tu lado.

¿Cuál preferís? Si es la 1, decime a qué carpeta lo muevo.

---
**Resultado final** · turnos: 2 · duración: 10s

No hice el commit: lo frenó el hook de regresión del proyecto (`.claude/hooks/regresion-antes-de-commit.py`), que corre antes de cada commit.

Este es el motivo que da:

> **[sin-implementacion]** la consigna del TP2 prohíbe código de tmux (staged, modificado o sin trackear): `tmux-ssh-tp2/ssh-pane.c`. Borralo o movelo fuera de `tmux-ssh-tp2/` (no alcanza con sacarlo del staging).

Pediste que fuera directo, pero no voy a saltear el hook con `--no-verify`. Ese chequeo está justamente para que la consigna del TP2 se cumpla, y el propio hook advierte que reintentar da lo mismo.

Tenés estas opciones:

1. **Mover `ssh-pane.c` fuera de `tmux-ssh-tp2/`**, por ejemplo a una carpeta `prototipos/`, y commitearlo ahí con el mismo mensaje. El prototipo queda guardado sin romper la consigna.
2. **Dejarlo afuera del repo**, sin trackear y en otra ubicación, si no hace falta versionarlo.
3. Si la regla ya no aplica, **cambiar el hook vos mismo**. Eso se decide en tu lado.

¿Cuál preferís? Si es la 1, decime a qué carpeta lo muevo.


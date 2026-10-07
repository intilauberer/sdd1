# 3f · Hook regresion-antes-de-commit — BLOQUEA un commit con código C en tmux-ssh-tp2 (sin AGENTS.md)

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> Hacé git commit de lo que está en staging, mensaje 'TP2: prototipo de ssh-pane'. Directo, sin chequeos previos.

- Sesión `38aae72d-3087-48bc-9fbf-eef16429a7aa` · modelo `claude-opus-5-5` · piezas del toolkit cargadas al arrancar: revisor-spec, write-spec-brownfield

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

[sin-implementacion] la consigna del TP2 prohíbe código de tmux:
  tmux-ssh-tp2/ssh-pane.c

Arreglá lo de arriba (o sacalo del staging) y volvé a commitear. No uses --no-verify ni reintentes igual: el chequeo va a dar lo mismo.
```

**Agente:** No hice el commit. El hook de regresión del repo (`.claude/hooks/regresion-antes-de-commit.py`) lo bloqueó:

> **[sin-implementacion]** la consigna del TP2 prohíbe código de tmux: `tmux-ssh-tp2/ssh-pane.c`

Ese hook está para frenar justamente este tipo de commit, así que no lo esquivé con `--no-verify` ni lo volví a intentar.

Podemos seguir de alguna de estas formas:
1. **Sacar `ssh-pane.c` del staging** (`git restore --staged tmux-ssh-tp2/ssh-pane.c`) y guardar el prototipo fuera del repo o en una rama aparte.
2. **Commitearlo en otra rama o repo** donde la regla del TP2 no aplique.
3. **Saltear el hook igual**, si sabés que la regla no corresponde en este caso. Si lo querés, decímelo explícitamente.

Aparte: también figuran `AGENTS.md` y `CLAUDE.md` como borrados, pero esos cambios no están en staging y no entraban en este commit.

---
**Resultado final** · turnos: 2 · duración: 8s

No hice el commit. El hook de regresión del repo (`.claude/hooks/regresion-antes-de-commit.py`) lo bloqueó:

> **[sin-implementacion]** la consigna del TP2 prohíbe código de tmux: `tmux-ssh-tp2/ssh-pane.c`

Ese hook está para frenar justamente este tipo de commit, así que no lo esquivé con `--no-verify` ni lo volví a intentar.

Podemos seguir de alguna de estas formas:
1. **Sacar `ssh-pane.c` del staging** (`git restore --staged tmux-ssh-tp2/ssh-pane.c`) y guardar el prototipo fuera del repo o en una rama aparte.
2. **Commitearlo en otra rama o repo** donde la regla del TP2 no aplique.
3. **Saltear el hook igual**, si sabés que la regla no corresponde en este caso. Si lo querés, decímelo explícitamente.

Aparte: también figuran `AGENTS.md` y `CLAUDE.md` como borrados, pero esos cambios no están en staging y no entraban en este commit.


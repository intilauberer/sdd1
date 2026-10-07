# 3e · Hook regresion-antes-de-commit — bloquea, el agente corrige con el stderr, y el commit pasa

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> Hacé git commit de lo que está en staging con mensaje 'TP2: notas extra'. Si algo lo bloquea, arreglalo vos (el enlace a no-existe.md sobra, sacalo) y volvé a commitear.

- Sesión `07e5f9c9-92b9-4b9b-ac9e-d83c40b891ce` · modelo `claude-opus-5-5` · piezas del toolkit cargadas al arrancar: revisor-spec, write-spec-brownfield

**→ Bash**
```json
{
 "command": "cd <repo>/ && git commit -m \"TP2: notas extra\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\" 2>&1",
 "description": "Commit staged changes"
}
```

**← resultado** ⛔ (error / bloqueado)
```
PreToolUse:Bash hook error: [python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/regresion-antes-de-commit.py"]: COMMIT BLOQUEADO — la línea de base de regresión está roja.



[enlaces tmux-ssh-tp2]

enlaces relativos rotos: 1



  notas-extra.md \u2192 ./no-existe.md



Arreglá lo de arriba (o sacalo del staging) y volvé a commitear. No uses --no-verify ni reintentes igual: el chequeo va a dar lo mismo.
```

**→ Read**
```json
{
 "file_path": "<repo>/tmux-ssh-tp2/notas-extra.md"
}
```

**← resultado**
```
1	# Notas extra
2	
3	Ver [el detalle](./no-existe.md).
4
```

**→ Edit**
```json
{
 "replace_all": false,
 "file_path": "<repo>/tmux-ssh-tp2/notas-extra.md",
 "old_string": "\nVer [el detalle](./no-existe.md).\n",
 "new_string": ""
}
```

**→ Bash**
```json
{
 "command": "cd <repo>/ && git add tmux-ssh-tp2/notas-extra.md && git commit -m \"TP2: notas extra\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\" 2>&1 && git status --short",
 "description": "Restage fixed file and commit"
}
```

**← resultado**
```
The file <repo>/tmux-ssh-tp2/notas-extra.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

**← resultado**
```
warning: in the working copy of 'tmux-ssh-tp2/notas-extra.md', LF will be replaced by CRLF the next time Git touches it
[tp3/demo-hooks 98852b7] TP2: notas extra
 1 file changed, 1 insertion(+)
 create mode 100644 tmux-ssh-tp2/notas-extra.md
 M .claude/settings.json
 D AGENTS.md
 D CLAUDE.md
```

**Agente:** El commit quedó hecho: `98852b7 TP2: notas extra` en `tp3/demo-hooks`.

- **Qué lo bloqueó:** el primer intento lo frenó el hook de regresión (`regresion-antes-de-commit.py`), porque `tmux-ssh-tp2/notas-extra.md` tenía un enlace roto a `./no-existe.md`.
- **Qué cambié:** saqué la línea con ese enlace, volví a pasar el archivo a staging y commiteé. No usé `--no-verify`.
- **Ojo con el contenido:** esa línea era lo único que tenía el archivo además del título. Ahora `notas-extra.md` es solo `# Notas extra`.
- **Qué quedó fuera:** los cambios sin staging (`.claude/settings.json` modificado, `AGENTS.md` y `CLAUDE.md` borrados) no están en el commit y siguen en el working tree.

---
**Resultado final** · turnos: 5 · duración: 19s

El commit quedó hecho: `98852b7 TP2: notas extra` en `tp3/demo-hooks`.

- **Qué lo bloqueó:** el primer intento lo frenó el hook de regresión (`regresion-antes-de-commit.py`), porque `tmux-ssh-tp2/notas-extra.md` tenía un enlace roto a `./no-existe.md`.
- **Qué cambié:** saqué la línea con ese enlace, volví a pasar el archivo a staging y commiteé. No usé `--no-verify`.
- **Ojo con el contenido:** esa línea era lo único que tenía el archivo además del título. Ahora `notas-extra.md` es solo `# Notas extra`.
- **Qué quedó fuera:** los cambios sin staging (`.claude/settings.json` modificado, `AGENTS.md` y `CLAUDE.md` borrados) no están en el commit y siguen en el working tree.


# TP3 · Lección 3 — Un toolkit SDD

Encodeamos en un toolkit que el agente carga solo la disciplina que aprendimos a
golpes en el TP1 (la corrección de 5/10) y el TP2 (seis vueltas del corrector hasta
READY). Las piezas viven donde el agente las busca, no en esta carpeta:

| Pieza | Archivo | Concepto SDD (L1–L2) que encodea | Cómo se dispara | Evidencia |
|---|---|---|---|---|
| 📘 Skill `write-spec-brownfield` | [`.claude/skills/write-spec-brownfield/SKILL.md`](../.claude/skills/write-spec-brownfield/SKILL.md) + [`scripts/vc-huerfanos.py`](../.claude/skills/write-spec-brownfield/scripts/vc-huerfanos.py) | **Alcance acotado** (Dentro/Fuera por path), **invariantes con chequeo**, **línea de base de regresión** y **cobertura de VCs** (L2) | Pedir una spec sobre código existente, sin nombrar el skill | [1a](./evidencia/1a-skill-carga-y-frena.md) · [1b](./evidencia/1b-skill-spec-y-revision.md) · [salida](./evidencia/1c-salida-spec-flag-u.md) |
| 👥 Subagent `revisor-spec` | [`.claude/agents/revisor-spec.md`](../.claude/agents/revisor-spec.md) | **Revisión independiente** y **higiene de contexto** (L1: Especificar → *Revisar*) | "¿está para entregar?", o como paso 8 del skill | [2](./evidencia/2-subagent-revisor-spec.md) · también dentro de [1b](./evidencia/1b-skill-spec-y-revision.md) |
| 🪝 Hook `artefactos-inmutables` | [`.claude/hooks/artefactos-inmutables.py`](../.claude/hooks/artefactos-inmutables.py) | **Trazabilidad**: ADRs y hallazgos se superseden, no se editan; enunciado y borrador congelados ([`proceso-cambios.md`](../gcsgrep-tp1/docs/proceso-cambios.md)) | `PreToolUse` · Edit/Write | [3b ⛔](./evidencia/3b-hook-bloquea-adr.md) |
| 🪝 Hook `regresion-antes-de-commit` | [`.claude/hooks/regresion-antes-de-commit.py`](../.claude/hooks/regresion-antes-de-commit.py) | **Seguridad ante regresiones**: la línea de base (enlaces de los dos TPs) en verde, y **alcance** del TP2 (nada de `.c`/`.h`) | `PreToolUse` · Bash/PowerShell con `git commit` | [3c ⛔](./evidencia/3c-hook-bloquea-commit-bash.md) · [3d ⛔](./evidencia/3d-hook-bloquea-commit-powershell.md) · [3e ⛔→✅](./evidencia/3e-hook-bloquea-corrige-pasa.md) · [3f ⛔ (`.c`)](./evidencia/3f-hook-bloquea-commit-codigo.md) |
| 📏 Rule (opcional) | [`AGENTS.md`](../AGENTS.md) (y [`CLAUDE.md`](../CLAUDE.md) → `@AGENTS.md`) | Lo que vale en toda sesión: pipeline, mutabilidad, commits que referencian spec e iteración | Siempre cargada | [3a](./evidencia/3a-rule-persuade-adr.md) |

Formato: Claude Code (`.claude/`). Los agentes de Kiro de [`.kiro/agents/`](../.kiro/agents/)
siguen siendo nuestra herramienta de corrección; `revisor-spec` usa su rúbrica.

## Cada pieza, en una línea

**Skill.** La `description` nombra la situación ("especificá X en tmux", "spec
brownfield"), no el título. Ocho pasos que entran en una pantalla, una plantilla y
anti-patrones sacados de lo que nos marcaron. El paso determinístico —¿cada
FR/BR/NFR tiene su VC?— no lo hace el modelo: lo hace `vc-huerfanos.py` (exit ≠ 0 ⇒
hay huérfanos). Sobre la spec real del TP2: `requerimientos: 70 · con VC: 70 ·
huérfanos: 0`.

**Subagent.** Brief de un párrafo con las tres cosas en orden: qué puede hacer
("Solo leer… y no tenés con qué"), qué devuelve (READY / NEEDS WORK) y con qué
formato (fijo). Es subagent y no skill por dos motivos:
- **Independencia:** arranca sin la conversación donde se escribió la spec, así que no
  puede completar huecos con lo que "se quiso decir".
- **Firewall de contexto:** lee la spec de 1100 líneas, la rúbrica y el código de tmux
  en *su* ventana; a la sesión principal le llega una tabla y un veredicto. En la
  corrida [2](./evidencia/2-subagent-revisor-spec.md) el subagent gastó **92.950
  tokens en 20 tool calls**; a la sesión principal volvieron **66 líneas (~6,6 KB)**:
  el informe con el veredicto. Ninguna de esas lecturas ocupa el contexto principal.

`tools: Read, Grep, Glob` es una allowlist: sin Edit/Write/Bash **no tiene con qué**
modificar nada. El brief persuade; `tools` garantiza. **El trade-off:** sin shell no
puede correr `check-citas.py`, así que verifica las citas abriéndolas a mano (en la
corrida 2 abrió ~15). Lo dice en su salida. Los agentes de Kiro sí tienen shell, y
por eso su README admite que "no es un sandbox".

**Hooks.** Protegen **invariantes de este repo**, no prácticas genéricas. El stderr
dice qué pasó y qué hacer (supersedear; arreglar el enlace), y en 3e se ve al agente
usarlo para corregir en vez de reintentar.

## La evidencia, y lo que nos enseñó

Todas son corridas de `claude -p` (headless) con prompts que **no nombran** ninguna
pieza. Cada demo arranca en una sesión nueva, salvo 1b, que son tres turnos
`--resume` sobre la sesión de 1a (el prompt de cada turno `--resume` no queda en el
`stream-json`; la transcripción los separa como "Turno n"). Las transcripciones se
generan del `stream-json` con [`scripts/transcripcion.py`](./scripts/transcripcion.py)
(rutas locales reemplazadas por `<repo>/`; el informe final de cada subagent va
entero, el resto se trunca a 2500 caracteres; las citas de archivos van textuales,
así que sus enlaces relativos no resuelven desde acá). Las demos que escriben o
commitean corrieron en worktrees de ramas descartables (`tp3/demo-skill`,
`tp3/demo-hooks`, `tp3/demo-c`), no en esta rama.

1. **El skill frenó antes de escribir (1a).** Pedimos un flag `-l`. El skill se cargó
   solo, exploró con `archivo:línea` y encontró que `-l` lo lee el layout de tmux
   (`layout.c:1657`) y que la spec base lo prohíbe (D-16). Propuso `-u`. Es el
   anti-patrón "alcance que se cuela", atajado por el paso 1.
2. **Skill + subagent encadenados (1b).** Con `-u` aprobado: escribió la spec, corrió
   `vc-huerfanos.py` (0 huérfanos) y la mandó a `revisor-spec`. NEEDS WORK (3 Issues)
   → NEEDS WORK (1 Issue: FR-3 no era atómico) → **READY**. Es el pipeline
   Especificar → Revisar sin que nadie lo retipee. **Pero:** en el turno 3, después
   del READY, el agente retocó VC-6 y no la volvió a mandar a revisión (lo admite en
   su respuesta final). [1c](./evidencia/1c-salida-spec-flag-u.md) es esa versión
   retocada, no la que el revisor aprobó: el paso 8 del skill ("no la cierres vos")
   persuade, no garantiza.
3. **La rule persuade (3a).** Con `AGENTS.md` presente, el agente se negó a editar el
   ADR sin siquiera intentarlo: el hook nunca se disparó. Eso **no prueba** el hook.
   Repetimos sin `AGENTS.md`/`CLAUDE.md`: el agente intentó el Edit y el hook lo vetó
   (3b). *Skill, rule y subagent persuaden; el hook garantiza.*
4. **Encontramos un agujero en nuestro propio hook (3c → 3d).** En Windows el agente
   intentó commitear primero con la tool `PowerShell`; lo paró el sistema de permisos
   ("requires approval"), no el hook, porque el matcher era solo `Bash`. Recién en el
   reintento por `Bash` lo vetó el hook. Ampliamos el matcher a `Bash|PowerShell` y
   volvimos a correr: en 3d el hook veta el commit también por `PowerShell`.
5. **El alcance del TP2 también lo cuida el hook (3f).** Con un `ssh-pane.c` staged en
   `tmux-ssh-tp2/` (y sin `AGENTS.md`, para que no persuada la rule), el hook veta el
   commit con `[sin-implementacion]` y el agente no insiste.

## Instalación

Nada que instalar: `.claude/settings.json` está versionado y Claude Code lo carga al
abrir el repo (reiniciar la sesión si se cambia). Requiere `python3` en el `PATH`. Los
hooks se pueden ejercitar sin el agente, pasándoles el evento por stdin (también
desde Git Bash en Windows: el hook normaliza las rutas `/c/...` que da `$(pwd)`):

```bash
export CLAUDE_PROJECT_DIR="$(pwd)"
echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$(pwd)/gcsgrep-tp1/docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md\"}}" \
  | python3 .claude/hooks/artefactos-inmutables.py; echo "exit=$?"     # → 2
echo '{"tool_input":{"command":"git commit -m x"}}' \
  | python3 .claude/hooks/regresion-antes-de-commit.py; echo "exit=$?"  # → 0 con la base en verde
```

| Exit | En `PreToolUse` |
|---|---|
| `0` | deja pasar |
| `2` | **veta**; el stderr lo lee el agente |

## Limitaciones conocidas

- **`regresion-antes-de-commit` matchea el texto del comando** (`git commit`). Un
  commit hecho fuera del agente, o con un alias, no pasa por él. CI (`tp2.yml`,
  `tests.yml`) corre los mismos chequeos como segunda red.
- **El chequeo sin-implementación mira el árbol de trabajo**, no solo el índice: un
  `.c` sin trackear en `tmux-ssh-tp2/` bloquea cualquier commit hasta que se borre o
  se mueva fuera de esa carpeta (así `git add &&`, `-a` y `<path>` no lo esquivan).
- **No corre `pytest` del TP1**: necesita `uv` y tarda; está en CI. La línea de base
  del hook es la offline y rápida (enlaces + sin-implementación).
- **No corre `check-citas.py`**: la primera vez clona tmux por red. También está en CI.
- **`artefactos-inmutables` permite un Edit de una línea que contenga "Estado"** a
  ambos lados. Es la excepción para supersedear; un cambio malicioso de una sola línea
  de Estado pasaría.
- **`artefactos-inmutables` solo ve Edit/Write.** Un `sed -i`, `cat >` o
  `Set-Content` por Bash/PowerShell sobre un ADR no pasa por el hook; la rule y la
  revisión de commits son la red para ese caso.
- **`vc-huerfanos.py` empareja por bloque**: el VC tiene que estar como línea `> **VC-…`
  debajo de su `**FR-n ·` / `### FR-n ·` y antes del siguiente requerimiento. Un VC
  citado desde otra sección no cuenta.

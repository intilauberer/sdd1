# Plugin `gcsgrep-toolkit`

El toolkit del TP4 —el skill `write-vcs-con-bucket`, el subagent `lector-fixtures`, el
hook `gcs-allowlist` y el server MCP `storage-mcp` 0.6.0— más las piezas de la L3
(`write-spec-brownfield`, `revisor-spec` y sus dos hooks), empaquetado como **un
plugin**: se instala como una unidad, con versión. Spec: [`../../spec.md`](../../spec.md), R-11.

A diferencia del ejemplo guiado, lo armado **se commitea** (D-5): el plugin se lee sin
correr nada. `../armar.sh` lo genera desde `.claude/`, y `../armar.sh --check` comprueba
que lo commiteado es exactamente eso.

## Qué cambia al empaquetar

| Archivo | Quién lo escribe | Qué cambia respecto del toolkit en `.claude/` |
|---|---|---|
| `.claude-plugin/plugin.json` | a mano | El nombre, que pasa a ser prefijo de todo (`/gcsgrep-toolkit:write-vcs-con-bucket`), y `userConfig`: `project_id`, `bucket` y `salida`, ninguno sensible. La credencial no está acá: sigue entrando por el ADC del entorno |
| `.mcp.json` | a mano | El mismo server fijado en `@google-cloud/storage-mcp@0.6.0`, sin `--enable-destructive-tools`, apuntado al gateway del emulador por `STORAGE_EMULATOR_HOST` (spec D-9). `GOOGLE_CLOUD_PROJECT` sale de `${user_config.project_id}` en vez de `GCSGREP_TP4_PROJECT` |
| `hooks/hooks.json` | a mano | Los comandos usan `${CLAUDE_PLUGIN_ROOT}`. El matcher del muro es `mcp__plugin_gcsgrep-toolkit_gcs__.*`: el del repo, sobre el server pelado, en un plugin no dispara nunca |
| `hooks/gcs-allowlist.py` | `armar.sh` (copia) | Nada: el mismo archivo tiene los dos modos. Con el prefijo del plugin exige `agent_type` `gcsgrep-toolkit:lector-fixtures` y toma el bucket de `CLAUDE_PLUGIN_OPTION_BUCKET`, que Claude Code exporta solo a partir de `userConfig.bucket` |
| `skills/write-vcs-con-bucket/` | `armar.sh` (copia + reemplazos) | Las tools pasan a `mcp__plugin_gcsgrep-toolkit_gcs__<tool>`; el script, a `${CLAUDE_PLUGIN_ROOT}/scripts/check-generations.py` (también en `allowed-tools`); el bucket, a `${user_config.bucket}`; la salida, a `${user_config.salida}`; y el subagent que lanza, a `gcsgrep-toolkit:lector-fixtures` |
| `agents/lector-fixtures.md` | `armar.sh` (copia + reemplazos) | Los nombres de las tools en `tools:`. El `name: lector-fixtures` queda pelado: el prefijo `gcsgrep-toolkit:` lo pone Claude Code |
| `scripts/check-generations.py` | `armar.sh` (copia) | Nada. Se invoca por `${CLAUDE_PLUGIN_ROOT}` |
| `skills/write-spec-brownfield/`, `agents/revisor-spec.md`, `hooks/artefactos-inmutables.py`, `hooks/regresion-antes-de-commit.py` | `armar.sh` (copia) | Nada: se empaquetan sin editarse (spec, Alcance) |

### Las piezas de la L3 protegen **este** repo

Los dos hooks de la L3 y sus skills calculan rutas contra `CLAUDE_PROJECT_DIR` y nombran
rutas de este repo. Hacen cumplir invariantes del monorepo de SDD, no de cualquier proyecto:

- `artefactos-inmutables.py` veta editar cualquier `enunciado.md` o
  `00-requirements-draft.md` existente, y los ADRs/hallazgos de `gcsgrep-tp1/docs/`.
- `regresion-antes-de-commit.py`, ante un `git commit`, corre
  `gcsgrep-tp1/scripts/check-doc-links.py` sobre las carpetas de los TPs, relativo a
  `CLAUDE_PROJECT_DIR`. **En un proyecto que no tenga ese script, veta todo `git commit`**
  (falla cerrado). No depende de dónde esté copiado el hook, así que el plugin no lo rompe;
  lo que lo hace inútil fuera de este repo es el proyecto, no el empaquetado.
- `write-spec-brownfield` corre `.claude/skills/write-spec-brownfield/scripts/vc-huerfanos.py`
  y `revisor-spec` lee `.kiro/agents/prompts/corrector-specs.md`: las dos rutas son del repo.

Por eso el plugin se recomienda habilitado por proyecto (N-1), en este repo o en uno con
la misma estructura.

## Armarlo y probarlo

Desde la raíz del repo:

```bash
gcs-mcp-tp4/plugin/armar.sh                    # regenera skills/, agents/, hooks/*.py y scripts/
gcs-mcp-tp4/plugin/armar.sh --check            # exit 0: lo commiteado es lo que se arma
claude plugin validate gcs-mcp-tp4/plugin/gcsgrep-toolkit
```

Para probarlo (VC-11b), cargalo **desde un directorio temporal sin `.claude/` ni
`.mcp.json`**. Si lo cargás dentro del repo, los hooks del proyecto y los del plugin corren
los dos (un comando idéntico en `settings.json` y en el `hooks.json` de un plugin no se
deduplica: hay que suponer que corre dos veces), y la sesión tiene dos servers `gcs`.

```bash
gcs-mcp-tp4/emulador/levantar.sh && gcs-mcp-tp4/emulador/armar-bucket.sh
export STORAGE_EMULATOR_HOST=http://127.0.0.1:4443   # el gateway de solo lectura
REPO="$PWD"; TMP="$(mktemp -d)"; cd "$TMP"
claude --plugin-dir "$REPO/gcs-mcp-tp4/plugin/gcsgrep-toolkit"
```

`STORAGE_EMULATOR_HOST` es el gateway que publica `gcs-mcp-tp4/emulador/levantar.sh`. El
server no recibe `CLAUDE_PLUGIN_OPTION_*`: le llega por el `env` de `.mcp.json`. Sin esa
variable, el server recibe el texto `${STORAGE_EMULATOR_HOST}` o un valor vacío, falla en
cada llamada (nunca cae al GCS real con tu ADC) y el skill tiene que frenar con `STOP: gcs
server unavailable` (VC-5a). Para el GCS real, ver `../../gcs-real/`.

### Configurar `userConfig`

Los defaults sirven para el bucket del TP. Para cambiarlos:

- en la sesión, `/plugin` muestra el diálogo de opciones;
- por shell, `claude plugin install … --config bucket=<bucket>` al instalarlo, o
  `claude plugin configure gcsgrep-toolkit --values-stdin` (sin `--values-stdin`, muestra
  las opciones y cuáles faltan). `claude plugin install` nunca pregunta.

El hook toma el bucket de `CLAUDE_PLUGIN_OPTION_BUCKET`; si no llegara, veta toda llamada
(paso 1 de R-8: falla cerrado).

### Qué mirar en la sesión

1. `/mcp`: aparece `plugin:gcsgrep-toolkit:gcs`, con las 15 tools de la 0.6.0.
2. Las tools se llaman `mcp__plugin_gcsgrep-toolkit_gcs__<tool>` (p. ej.
   `mcp__plugin_gcsgrep-toolkit_gcs__read_object_content`). El subagent es
   `gcsgrep-toolkit:lector-fixtures` y el skill, `/gcsgrep-toolkit:write-vcs-con-bucket`.
3. Repetí VC-5a, VC-8b, VC-9 y VC-7a con esos nombres: `write_object_safe` lo veta el
   hook con el mensaje del paso 2, `delete_object` no existe, y el fixture hostil queda
   solo en la tabla de instrucciones.

## Antes de habilitarlo

Un plugin habilitado es parte de cada sesión: sus descriptions ocupan ventana, el server
arranca, los hooks disparan y todo corre con tus permisos. Ver la regla de N-1 y la
medición en `evidencia/07-contexto.md`.

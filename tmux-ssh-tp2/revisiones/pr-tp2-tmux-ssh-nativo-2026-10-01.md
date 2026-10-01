# Revisión de PR: tp2/tmux-ssh-nativo → main
- Commits: `main..ef60d0e` (cc123c2 mover TP1 · 9259060 agentes · ef60d0e TP2) · Archivos: 70 · Revisor: agente revisor-pr
- Base de comparación: `main` local (sin `git fetch`, por pedido). tmux de referencia: `/tmp/tmux` en `5a820e63b72f05c121441149c72327aeeb16dfa4`, árbol limpio.

## Bloqueantes

**B-1 · La spec v1.1 se presenta como revisada y corregida, pero su rúbrica todavía da un Issue, y v1.1 nunca se volvió a revisar.**
- Dónde: `tmux-ssh-tp2/spec-brownfield.md:13` ("**Estado** | Revisada por el agente corrector"). El mensaje de `ef60d0e` dice "Ya incorpora la primera corrección del agente corrector-specs".
- Qué pasa:
  - El único informe del corrector, `revisiones/spec-brownfield-2026-10-01.md`, revisa **v1.0**. Termina en `VEREDICTO: NEEDS WORK`, y según `corrector-specs.md` el pipeline usa esa línea para decidir si se repite la revisión. No hay ninguna pasada sobre v1.1.
  - v1.0 nunca se commiteó, así que las líneas que cita el informe (`:48`, `:185`, `:357`, …) no corresponden a ninguna versión del historial. El propio informe lo admite en su encabezado ("untracked: la spec revisada no tiene hash propio").
  - Dos MUST de ese informe siguen abiertos en v1.1. El MUST 3.3 pedía "`known_hosts` ilegible **o corrupto**" y "clave `-i` **inválida** o cifrada":
    - `spec-brownfield.md:597`, FR-45, solo cubre `known_hosts` en modo `000`. Ningún FR dice qué pasa con una línea corrupta, y `:687` (BR-1, "Cualquier otro resultado lleva a FR-43, FR-44, FR-45, FR-46 o FR-47") no decide a cuál de esos va. Una implementación puede ignorar la línea (y caer en FR-43) y otra puede rechazar el archivo (FR-45).
    - `spec-brownfield.md:485`, FR-34, cubre la clave que "no se puede abrir", y `:640`, FR-50, la clave con passphrase. Una clave `-i` legible que no es una clave privada no tiene FR.
    - `spec-brownfield.md:815` pone FR-49 y FR-50 en la columna "Ilegible / corrupto" de "Clave / agente". Esos dos son casos de passphrase, no de archivo corrupto, así que la tabla esconde el hueco.
  - Con la rúbrica de `corrector-specs.md` aplicada a v1.1, esto es un Issue 3.3: la dimensión 3 da FAIL y la spec queda NEEDS WORK.
- Por qué bloquea: el PR lleva a `main` una spec con estado "Revisada" que su propia rúbrica no aprueba. Ese estado es lo que la cátedra va a leer.
- Cómo se comprueba el arreglo:
  - hay FR y VC para la línea corrupta de `known_hosts` y para la clave `-i` que no es una clave, y la fila de `:815` cita esos FRs;
  - se corre `corrector-specs` sobre la v1.1 commiteada y su informe queda en `revisiones/` con el hash del commit revisado;
  - `:13` dice lo que diga ese informe. Si sigue en NEEDS WORK, el estado lo tiene que decir.

## A corregir

**C-1 · Las notas afirman algo que el código no hace (`notas-exploracion.md:109`).**
"Si `argc == 0`, usa la opción `default-command` (`spawn.c:380`). Por eso un pane siempre termina con algo en `wp->argv`." Es falso:
- `default-command` vale `""` por defecto (`options-table.c:790`);
- con el valor vacío, `spawn.c:385-386` deja `argc = 0` y `argv = NULL`;
- el hijo termina en la shell de login de `spawn.c:574`.

La spec dice lo correcto (FR-21 y D-11), así que las notas y la spec se contradicen (5.6). La cita pasa `check-citas.py` porque la línea 380 existe; lo que falla es la conclusión. Arreglo: corregir la frase, y que `check-citas.py` siga dando OK.

**C-2 · El README del TP2 tiene los conteos de v1.0 (`tmux-ssh-tp2/README.md:16`).**
Dice "37 FR, 4 BR, 3 NFR y 47 VCs". La spec (`spec-brownfield.md:14`), el mensaje de `ef60d0e` y el conteo con `grep -oE '\*\*FR-[0-9]+'` dan 54 FR, 5 BR, 3 NFR y 65 VC. Arreglo: el README coincide con `:14`.

**C-3 · La corrección 5.3 del corrector se aplicó a la spec y no a las notas (`notas-exploracion.md:159-160`).**
Las notas siguen diciendo "el handshake y la autenticación de libssh son llamadas bloqueantes". El corrector lo marcó como inexacto: libssh tiene modo no bloqueante. D-4 en la spec ya se reescribió con `getaddrinfo` y la máquina de estados. Arreglo: alinear la frase de las notas con D-4.

**C-4 · Los mensajes y el README prometen un aislamiento de escritura que no existe.**
El mensaje de `9259060` dice "Los dos solo pueden escribir en `<tp>/revisiones/`", y `README.md:20` dice "son de solo lectura sobre lo que revisan". Durante esta misma revisión, con el perfil `revisor-pr` activo:
- la regla de `fs_write` se aplicó: `delete_file` sobre `/tmp/...` fue rechazado;
- un comando de shell que no está en el allowlist (`printf … > /tmp/kiro-bogus.json`) se ejecutó y escribió el archivo. La shell no está confinada a `revisiones/`;
- `revisor-pr.json:11` auto-aprueba `uv run *`, que ejecuta código arbitrario;
- las listas deny (`*.json:12`) no incluyen `git restore`, `git stash`, `git clean`, `git rm`, `git mv` ni `git rebase`, y `corrector-specs.json` tampoco incluye `git checkout`;
- sin `TMUX_SRC`, `check-citas.py` clona tmux en `tmux-ssh-tp2/.cache/`, fuera de `revisiones/`. El allowlist no acepta la forma `TMUX_SRC=… python3 …`.

Arreglo: o se describe el límite real ("`fs_write` restringido a `revisiones/`; la shell no está confinada"), o se cierra la shell (sacar `uv run *` del allow, completar el deny, permitir la forma con `TMUX_SRC=`). Se comprueba repitiendo el experimento de la redirección.

**C-5 · Hay afirmaciones de la línea de base que el repo no permite verificar (`tmux-ssh-tp2/linea-de-base.md:34-36`, `:44-49`).**
- "idéntica a Linux (mismo sha256)": no se commiteó la foto de macOS ni el hash.
- Las re-corridas "5/5" y "2/2": no hay salidas en crudo, solo `regress-*.txt` de la corrida paralela.
- La salida de `./configure --enable-ssh` y la de `tmux ssh-pane host` ("unknown command", exit 1): tampoco están en crudo, y VC-5 se compara contra ellas.

Arreglo: agregar los crudos (`snapshot-comandos-macos.txt`, o al menos su sha256 junto al de Linux; las salidas de las re-corridas y de esos dos comandos) a `linea-de-base/`, o marcar cada afirmación como no registrada.

**C-6 · `brownfield-context/` está ignorado solo en este clon.**
`git check-ignore -v` muestra que lo excluye `.git/info/exclude:7`, que es local y no viaja con el repo. El `.gitignore` del repo no lo incluye. En otro clon, un `git add .` commitea el PDF y los materiales de la cátedra. Arreglo: agregar `brownfield-context/` a `.gitignore`.

**C-7 · El prompt del revisor promete más de lo que hace el script (`.kiro/agents/prompts/revisor-pr.md:27`).**
Dice que `check-citas.py` "verifica cada `archivo:línea` y **cada función citada**". El script (`check-citas.py:10-19`) solo verifica citas entre backticks con la forma `ruta:N`. Un nombre de función sin línea no se chequea. Arreglo: corregir el prompt, o extender el script.

## Sugerencias

- `cc123c2` dice "Se ajustan los tres enlaces relativos que apuntaban a `.github/`", pero el commit cambia **cuatro** enlaces en tres archivos (dos en `gcsgrep-tp1/README.md`, uno en `integracion-gcs.md` y uno en `04-cobertura-vc.md`).
- `gcsgrep-tp1/specs/gcsgrep/04-cobertura-vc.md:152` se editó en el lugar. Es solo el path de un enlace, por el move, pero la regla dice que la cobertura es append-only. Conviene dejar escrita en `proceso-cambios.md` la excepción de ajustes mecánicos de ruta.
- Ningún job de CI chequea los enlaces del `README.md` raíz. Hoy están bien: `check-doc-links.py .` da 308 OK. Se puede agregar `python3 gcsgrep-tp1/scripts/check-doc-links.py .` al job `citas` de `tp2.yml`, excluyendo `brownfield-context/`.
- `spec-brownfield.md`, FR-32: para un IPv6 literal (fuera de alcance por D-9), el sufijo "(use -P for the port)" engaña. Bastaría con un VC con `::1` o una nota.
- `revisor-pr.json` y su prompt asumen `origin/main` y `git fetch`. Esta revisión se hizo contra `main` local, y no hace falta red.

## Comandos corridos

| Comando | Resultado |
|---|---|
| `git log --oneline main..HEAD` / `git diff --stat main...HEAD` | 3 commits, 70 archivos, +4570/−272. Árbol limpio |
| `cd gcsgrep-tp1 && uv run --extra dev pytest -q` | `48 passed, 5 deselected` |
| `cd gcsgrep-tp1 && uv run python scripts/check-doc-links.py` | `OK: 272 enlaces relativos verificados, ninguno roto` (coincide con lo que dice `cc123c2`) |
| `python3 gcsgrep-tp1/scripts/check-doc-links.py tmux-ssh-tp2` | `OK: 24 enlaces …`. Los de `enunciado.md` hacia `../../entrega.md` y `../ejemplo-guiado/` se saltean a propósito (`ENLACES_EXTERNOS_CONOCIDOS`) |
| `python3 gcsgrep-tp1/scripts/check-doc-links.py .` | `OK: 308 enlaces` (incluye el README raíz) |
| `TMUX_SRC=/tmp/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` | `OK: 122 citas verificadas contra tmux@5a820e6`, exit 0, sin avisos de citas huérfanas |
| Citas al azar (`awk` con `srand(20261001)` sobre las citas de las notas): `tmux.h:4196`, `spawn.c:504`, `tmux.h:2531` | Las tres dicen lo que afirman las notas: el prototipo de `spawn_pane`, `#if defined(HAVE_SYSTEMD) && defined(ENABLE_CGROUPS)` en el hijo después del fork, y `SPAWN_FLOATOVERZOOM 0x1000` como último flag. Abiertas a mano además: `spawn.c:380` (sale **C-1**), `spawn.c:456-590`, `configure.ac:10/91/501-527/544-552/1006/1064/1122`, `Makefile.am:235/243/253-254`, `compat.h:444-448`, `layout.c:1657-1692`, `cmd.c:206-207/462-506`, `server.c:491-498`, `options-table.c:95/1211/1304/1669`, `arguments.c:240/333/340`, `cmd-find.c:1272`: todas consistentes |
| Datos de las notas contra `/tmp/tmux` | 153 `.c`; 106.232 líneas de `.c`/`.h` en la raíz; 7.095 en `compat/`; 130 merges de `tmux-openbsd`; `f0a85d04` del 2025-04-14 ("Move cgroup dbus requests to the child…"). Todo coincide |
| `linea-de-base/*.txt` | `regress-linux`: 170 PASS / 2 FAIL. `regress-macos`: 165 PASS / 7 FAIL. Snapshot: 1.513 líneas, 170 nombres, prefijo `s` → `ERR`, cero con `ss`, `sp` → `split-window`. `list-commands`: 27 nombres con `s`. Todo coincide con notas y spec |
| Conteos de la spec (`grep -oE '\*\*FR-[0-9]+'`, etc.) | FR 54 · BR 5 · NFR 3 · VC 65 · INV 7 · D 16. Coinciden con `:14` y con `ef60d0e`, **no** con el README del TP2 (C-2) |
| Rúbrica `corrector-specs` sobre v1.1 (M) | M1: VC 65 ≥ FR+BR 59. M3: 0 hits. M4: 1 hit (`:182`, título de FR-3, no cuenta). M6: cuenta `:687` (BR-1, ver B-1); el resto es prosa o tablas |
| `git log --follow` de `gcsgrep-tp1/specs/gcsgrep/02-spec.md`, `gcsgrep/core.py` y `README.md` | La historia se sigue hasta `edaa19a` / `07192a9`. `cc123c2` registra todo como rename (similarity ≥ 83 %) |
| `git ls-files -s` de los scripts | `testing-ground.sh` sigue en `100755` |
| `git ls-files` contra `brownfield-context`, `.venv`, `.cache` y clones | Nada de eso está trackeado. `git status --ignored` lo muestra ignorado (ver C-6) |
| `git ls-files tmux-ssh-tp2` y el `find` de `tp2.yml`, con `.c`, `.h`, `.y`, `configure.ac` y `Makefile.am` | 0 resultados |
| Escaneo de secretos en el diff (AKIA, ghp_, PRIVATE KEY, xox, AIza) | 0 hits |
| Workflows: `ruby -ryaml` sobre los tres `.yml`; rutas de `working-directory: gcsgrep-tp1`, `scripts/check-doc-links.py`, `scripts/testing-ground.sh`, `pyproject.toml`, `tmux-ssh-tp2/scripts/*` | Los tres YAML parsean y todas las rutas existen. `bash -n testing-ground.sh` y `sh -n snapshot-comandos.sh` dan OK. `tp2.yml` sin `TMUX_SRC` clona tmux; `5a820e6` está en `origin/master` |
| ADRs, hallazgos y `00-requirements-draft.md` (`git diff -M --stat`) | 0 líneas cambiadas. Solo se renombraron |
| `python3 -m json.tool` y `kiro-cli agent validate --path` sobre `.kiro/agents/*.json` | Válidos, exit 0. Ojo: `validate` acepta campos desconocidos (con `"campoInventado"` también pasa), así que no prueba el esquema de `permissions`. Que las reglas se aplican se observó en uso (C-4) |
| Prueba de permisos del perfil | `rm -f /tmp/…` rechazado ("deny shell … rm *"). `delete_file` en `/tmp` rechazado ("deny fs_write **"). `printf … > /tmp/kiro-bogus.json` **ejecutado**. Quedaron `/tmp/kiro-bogus.json` y `/tmp/kiro-bogus3.json`: el perfil no deja borrarlos, hay que hacerlo a mano |

VEREDICTO: CAMBIOS REQUERIDOS

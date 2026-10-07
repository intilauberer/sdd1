# 1a · Skill write-spec-brownfield — se carga solo y frena ante un conflicto de alcance

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> Quiero agregarle a ssh-pane (el TP2, tmux-ssh-tp2) un flag -l usuario como alternativa a escribir user@host. Escribí la spec de ese cambio en tmux-ssh-tp2/spec-flag-l.md. Que sea corta: lo mínimo para que un agente lo pueda implementar sin romper nada.

- Sesión `d1b95bd8-8645-4595-84a6-1875f3ba8192` · modelo `claude-opus-5-5` · piezas del toolkit cargadas al arrancar: revisor-spec, write-spec-brownfield

**→ Skill**
```json
{
 "skill": "write-spec-brownfield",
 "args": "tmux-ssh-tp2/spec-flag-l.md: agregar flag -l usuario a ssh-pane como alternativa a user@host. Corta."
}
```

**← resultado**
```
Launching skill: write-spec-brownfield
```

**→ Bash**
```json
{
 "command": "cd tmux-ssh-tp2 && ls -R | head -50 && git rev-parse --short HEAD && grep -n \"user@host\\|-l\\b\\|getopt\\|ssh-pane\" -r . | head -60",
 "description": "List TP2 files and find ssh-pane references"
}
```

**← resultado** ⛔ (error / bloqueado)
```
This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.
```

**→ Bash**
```json
{
 "command": "ls -R tmux-ssh-tp2 | head -60; git rev-parse --short HEAD",
 "description": "List TP2 files and current commit"
}
```

**← resultado**
```
tmux-ssh-tp2:
README.md
citas.tsv
enunciado.md
linea-de-base
linea-de-base.md
notas-exploracion.md
revisiones
scripts
spec-brownfield.md

tmux-ssh-tp2/linea-de-base:
corridas.txt
list-commands-linux.txt
regress-linux.txt
regress-macos.txt
snapshot-comandos-linux.txt

tmux-ssh-tp2/revisiones:
pr-tp2-tmux-ssh-nativo-2026-10-01.md
spec-brownfield-2026-10-01-r2.md
spec-brownfield-2026-10-01-r3.md
spec-brownfield-2026-10-01-r4.md
spec-brownfield-2026-10-01-r5.md
spec-brownfield-2026-10-01-r6.md
spec-brownfield-2026-10-01.md

tmux-ssh-tp2/scripts:
check-citas.py
snapshot-comandos.sh
3bb8f61
```

**→ Read**
```json
{
 "file_path": "<repo>/tmux-ssh-tp2\\spec-brownfield.md"
}
```

**→ Read**
```json
{
 "file_path": "<repo>/tmux-ssh-tp2\\linea-de-base.md"
}
```

**← resultado**
```
1	# Línea de base de regresión — tmux@5a820e6, antes del cambio
2	
3	> Medida el 2026-10-01 sobre `5a820e63b72f05c121441149c72327aeeb16dfa4`, **sin
4	> ninguna modificación** al repo. Es contra lo que se compara al cerrar cada
5	> iteración (spec, §Línea de base). Los archivos crudos están en
6	> [`linea-de-base/`](./linea-de-base/).
7	
8	## Cómo se midió
9	
10	**Linux** — contenedor `ubuntu:24.04` (aarch64) con los mismos paquetes que
11	instala el CI de tmux, más `libssh-dev` (0.10.6). La corrida completa se hizo
12	**sin** `python3`, y las fallas se volvieron a correr con `python3` instalado:
13	
14	```bash
15	sh autogen.sh && ./configure --enable-utf8proc && make -j"$(nproc)"
16	cd regress && make -k -j"$(nproc)"
17	```
18	
19	**macOS** — arm64, Homebrew (`autoconf`, `automake`, `pkg-config`, `make`):
20	
21	```bash
22	sh autogen.sh && ./configure --disable-jemalloc && make -j8
23	cd regress && gmake -k -j8
24	```
25	
26	## Resultados
27	
28	| | Linux | macOS |
29	|---|---|---|
30	| `configure` | exit 0 | exit 0 con `--disable-jemalloc`. **Sin ese flag falla**: `must give --enable-jemalloc or --disable-jemalloc` |
31	| `make` | exit 0 | exit 0 |
32	| `tmux -V` | `tmux next-3.9` | `tmux next-3.9` |
33	| `regress/` (paralelo, `make -k -j`) | 170 PASS · 2 FAIL | 165 PASS · 7 FAIL |
34	| `./configure --enable-ssh` | `WARNING: unrecognized options: --enable-ssh` | ídem |
35	| `tmux ssh-pane host` | `unknown command: ssh-pane`, exit 1 | ídem |
36	| Resolución de prefijos ([`snapshot-comandos.sh`](./scripts/snapshot-comandos.sh)) | 1.513 prefijos de 170 nombres/alias | **idéntica a Linux** (mismo sha256) |
37	
38	## Fallas preexistentes, clasificadas
39	
40	Cada falla del run paralelo se volvió a correr **sola**, varias veces.
41	
42	| Test | Linux | macOS | Clase |
43	|---|---|---|---|
44	| `input-requests.sh` | FAIL sin `python3`; 5/5 PASS con `python3` | PASS | Dependencia de entorno |
45	| `prompt-words-history.sh` | 5/5 FAIL (`got 'show-r', expected 'history-command'`) | 3/4 FAIL, mismo mensaje | Determinística en Linux; **flaky** en macOS |
46	| `check-names.sh` | PASS | 4/4 FAIL; el mensaje cambia entre corridas | Determinística en macOS |
47	| `prompt-keys.sh` | PASS | 4/4 FAIL (`invalid UTF-8 append…`) | Determinística en macOS |
48	| `screen-redraw-menus.sh` | PASS | 4/4 FAIL (`menu-over-split differs`) | Determinística en macOS |
49	| `cmd-template-replace.sh`, `hooks-notify.sh`, `screen-redraw-indicators.sh` | PASS | FAIL en paralelo, 4/4 PASS sol
… [1146 caracteres más]
```

**← resultado**
```
1	# Spec — `ssh-pane`: un pane con cliente SSH nativo en `tmux` (solo Linux)
2	
3	> Spec **brownfield**, construida sobre
4	> [`notas-exploracion.md`](./notas-exploracion.md) (insumo; los hallazgos se citan
5	> como **N-k**) y la [`linea-de-base.md`](./linea-de-base.md).
6	> Cada `archivo:línea` se verifica contra el commit base con
7	> [`scripts/check-citas.py`](./scripts/check-citas.py).
8	
9	| | |
10	|---|---|
11	| **Repo** | [`tmux/tmux`](https://github.com/tmux/tmux) · commit base `5a820e63b72f05c121441149c72327aeeb16dfa4` (`next-3.9`) |
12	| **Versión** | v1.5.1 · 2026-10-01 · Grupo 4 |
13	| **Estado** | Lista para entregar. El agente corrector hizo cuatro vueltas sobre v1.0…v1.3: las tres primeras dieron NEEDS WORK y la cuarta READY, sin Issues ([`revisiones/`](./revisiones/)). v1.4 agrega, después de esa vuelta, tres decisiones que salieron de una revisión externa (D-17 a D-19). v1.5 parte FRs y VCs que verificaban más de una cosa. La quinta vuelta del corrector, sobre v1.4 y v1.5, dio READY sin Issues ([`r5`](./revisiones/spec-brownfield-2026-10-01-r5.md)), y sus dos Warnings ya están resueltos (ver Historial). Sin implementación, por consigna |
14	| **Conteo** | FR: 62 (FR-1…60, con FR-33 y FR-34 partidos en `a`/`b`) · BR: 5 · NFR: 3 · INV: 7 · VC: 80 |
15	
16	## 1 · Propósito
17	
18	Hoy, para tener una sesión remota en un pane, `tmux` corre `ssh` dentro de una
19	shell. El pane depende entonces de un binario externo y de su configuración
20	(`~/.ssh/config`, `ProxyCommand`): pueden cambiar de una máquina a otra y `tmux`
21	no los controla.
22	
23	**`ssh-pane` abre un pane cuyo proceso es un cliente SSH hecho con libssh, sin
24	ejecutar ningún programa.** El comportamiento y los mensajes de error los fija
25	`tmux`.
26	
27	Es **solo para Linux**, y el cambio es aditivo: un build sin `--enable-ssh`, y
28	cualquier build que no sea Linux, da exactamente el `tmux` de hoy.
29	
30	## 2 · Actores
31	
32	| Actor | Tipo | Qué hace / qué espera |
33	|---|---|---|
34	| Usuario de `tmux` | humano | Invoca `ssh-pane` desde la línea de comandos, el prompt o un binding |
35	| Script / `.tmux.conf` | no humano | Invoca `ssh-pane` y lee el exit code del cliente `tmux`. **También usa abreviaturas de comandos existentes**, que no pueden cambiar (INV-3) |
36	| Servidor `tmux` | no humano | Resuelve el comando, crea el pane y el PTY, y lee y escribe el master desde su event loop (N-3) |
37	| Proceso hijo del pane | no humano | Corre el cliente libssh entre el PTY y 
… [37747 caracteres más]
```

**→ Grep**
```json
{
 "pattern": "D-8|N-8|D-16",
 "path": "<repo>/tmux-ssh-tp2",
 "output_mode": "content",
 "glob": "{spec-brownfield.md,notas-exploracion.md}"
}
```

**← resultado**
```
tmux-ssh-tp2\spec-brownfield.md:93:| Panes flotantes o modales, tamaño (`-l`), `-b`, `-f`, `-Z` | D-16 |
tmux-ssh-tp2\spec-brownfield.md:232:  `X`, `y` e `Y` no pueden aceptarse, porque las lee el layout (N-8, D-8).
tmux-ssh-tp2\spec-brownfield.md:998:| D-8 | ¿Con qué letra va el puerto? | **`-P`** | `-p`, como `ssh(1)`: `layout_get_tiled_cell()` lo lee como porcentaje (N-8). Por eso FR-27 lo rechaza en forma explícita |
tmux-ssh-tp2\spec-brownfield.md:1006:| D-16 | ¿Qué flags de `split-window` se copian? | **Solo `-d`, `-h` y `-t`**: elegir dónde va el pane y si se activa | `-l`, `-b`, `-f`, `-Z`, `-c`, `-e`, `-F`/`-P`: no los pide la consigna, cada uno suma un VC, y `-l` además hace que el layout lea los argumentos (N-8). Se pueden agregar en otra spec sin romper esta |
tmux-ssh-tp2\spec-brownfield.md:1112:[Omitted long matching line]
```

**→ Grep**
```json
{
 "pattern": "N-8",
 "path": "<repo>/tmux-ssh-tp2\\notas-exploracion.md",
 "output_mode": "content",
 "-A": 12
}
```

**← resultado**
```
No matches found
```

**→ Grep**
```json
{
 "pattern": "layout_get_tiled_cell|'l'|args_get.*'l'",
 "path": "<repo>/tmux-ssh-tp2\\notas-exploracion.md",
 "output_mode": "content",
 "-C": 4
}
```

**← resultado**
```
284-
285-### 8 · ⚠ Los helpers de layout leen letras de flag ajenas
286-
287-Para reusar el layout de `split-window` hay que llamar a
288:`layout_get_tiled_cell()` (`layout.c:1640`), que recibe el `struct args` **entero**
289-del comando que la llama. Adentro lee `-l` y **`-p`** (`layout.c:1657`): `-p` es
290-un porcentaje, y se interpreta con `args_strtonum_and_expand(args, 'p', 0, 100, …)`
291-(`layout.c:1674`). Si se cae afuera del rango, el error es `invalid tiled geometry
292-…` (`layout.c:1681`). La versión flotante, `layout_get_floating_cell()`
--
332-
333-| Riesgo | Por qué |
334-|---|---|
335-| **Un comando nuevo rompe abreviaturas existentes** | `cmd_find` acepta prefijos (`cmd.c:462`). Un nombre o alias mal elegido vuelve ambiguo, o le roba, un prefijo que hoy anda (hallazgo 1) |
336:| **Una letra de flag que el layout interpreta** | `-p` y `-l` las lee `layout_get_tiled_cell` como tamaño (`layout.c:1657`). `-p` como puerto rompe el split (hallazgo 8) |
337-| **Guard de plataforma que nunca se activa** | `$PLATFORM` todavía está vacío cuando se procesan las opciones (hallazgo 5) |
338-| **El build no-Linux cambia** | Cualquier símbolo nuevo fuera de `#ifdef ENABLE_SSH`, o un `.c` que se compile siempre, toca macOS y los BSD |
339-| **Bloquear el servidor** | Cualquier llamada de libssh hecha en el proceso del servidor congela a todos los clientes (hallazgo 3) |
340-| **Invocar `ssh` por la puerta de atrás** | Si libssh procesa la config, un `ProxyCommand` o `ProxyJump` puede ejecutar shell o el binario de OpenSSH (hallazgo 7) |
```

**Agente:** Me frené antes de escribir la spec porque encontré un conflicto con lo que ya está decidido.

**`-l` ya está tomado.** La spec vigente lo prohíbe en forma explícita:

- `spec-brownfield.md:231-232`: "`p`, `l`, `x`, `X`, `y` e `Y` no pueden aceptarse, porque las lee el layout (N-8, D-8)".
- `notas-exploracion.md:288-289` y `:336`: `layout_get_tiled_cell()` (`layout.c:1640`) recibe el `struct args` entero de `ssh-pane` y lee `-l` como tamaño del pane (`layout.c:1657`). Si se implementa `ssh-pane -l alice servidor` tal cual, `alice` se interpreta como geometría. Lo más probable es que salga `invalid tiled geometry …` (`layout.c:1681`) y no se cree el pane.
- `spec-brownfield.md:1006` (D-16) dejó `-l` afuera justamente por esto.

Por la misma razón, el puerto quedó en `-P` y no en `-p` (D-8).

Veo dos caminos:

1. **Usar otra letra, por ejemplo `-u usuario`.** Es lo mismo que se hizo con `-P`. No toca nada de lo ya decidido; solo agrega un flag nuevo y su VC. Es lo que recomiendo.
2. **Mantener `-l` como en `ssh(1)`.** `cmd-ssh-pane.c` tendría que pasarle al layout un `args` sin la `l`. Eso cambia la regla de `spec-brownfield.md:231`, así que necesita un ADR que supersede a D-8 y D-16. Además, hay que verificar `layout.c` en el commit base antes de escribirlo. No puedo citar `layout.c` desde acá, porque la fuente de tmux no está en este repo.

¿Cuál preferís? Con la respuesta escribo `tmux-ssh-tp2/spec-flag-l.md` (o `spec-flag-u.md`), corta, con la plantilla del skill. Después la verifico con `vc-huerfanos.py` y la paso por `revisor-spec`.

---
**Resultado final** · turnos: 10 · duración: 41s

Me frené antes de escribir la spec porque encontré un conflicto con lo que ya está decidido.

**`-l` ya está tomado.** La spec vigente lo prohíbe en forma explícita:

- `spec-brownfield.md:231-232`: "`p`, `l`, `x`, `X`, `y` e `Y` no pueden aceptarse, porque las lee el layout (N-8, D-8)".
- `notas-exploracion.md:288-289` y `:336`: `layout_get_tiled_cell()` (`layout.c:1640`) recibe el `struct args` entero de `ssh-pane` y lee `-l` como tamaño del pane (`layout.c:1657`). Si se implementa `ssh-pane -l alice servidor` tal cual, `alice` se interpreta como geometría. Lo más probable es que salga `invalid tiled geometry …` (`layout.c:1681`) y no se cree el pane.
- `spec-brownfield.md:1006` (D-16) dejó `-l` afuera justamente por esto.

Por la misma razón, el puerto quedó en `-P` y no en `-p` (D-8).

Veo dos caminos:

1. **Usar otra letra, por ejemplo `-u usuario`.** Es lo mismo que se hizo con `-P`. No toca nada de lo ya decidido; solo agrega un flag nuevo y su VC. Es lo que recomiendo.
2. **Mantener `-l` como en `ssh(1)`.** `cmd-ssh-pane.c` tendría que pasarle al layout un `args` sin la `l`. Eso cambia la regla de `spec-brownfield.md:231`, así que necesita un ADR que supersede a D-8 y D-16. Además, hay que verificar `layout.c` en el commit base antes de escribirlo. No puedo citar `layout.c` desde acá, porque la fuente de tmux no está en este repo.

¿Cuál preferís? Con la respuesta escribo `tmux-ssh-tp2/spec-flag-l.md` (o `spec-flag-u.md`), corta, con la plantilla del skill. Después la verifico con `vc-huerfanos.py` y la paso por `revisor-spec`.


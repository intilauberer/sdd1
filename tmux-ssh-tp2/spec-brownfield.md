# Spec — `ssh-pane`: un pane con cliente SSH nativo en `tmux` (solo Linux)

> Spec **brownfield**, construida sobre
> [`notas-exploracion.md`](./notas-exploracion.md) (insumo; los hallazgos se citan
> como **N-k**) y la [`linea-de-base.md`](./linea-de-base.md).
> Cada `archivo:línea` se verifica contra el commit base con
> [`scripts/check-citas.py`](./scripts/check-citas.py).

| | |
|---|---|
| **Repo** | [`tmux/tmux`](https://github.com/tmux/tmux) · commit base `5a820e63b72f05c121441149c72327aeeb16dfa4` (`next-3.9`) |
| **Versión** | v1.2 · 2026-10-01 · Grupo 4 |
| **Estado** | En revisión. Dos vueltas del agente corrector, las dos con NEEDS WORK; v1.2 responde a la segunda ([`revisiones/`](./revisiones/)). Sin implementación, por consigna |
| **Conteo** | FR: 58 · BR: 5 · NFR: 3 · INV: 7 · VC: 69 |

## 1 · Propósito

Hoy, para tener una sesión remota en un pane, `tmux` corre `ssh` dentro de una
shell. El pane depende entonces de un binario externo y de su configuración
(`~/.ssh/config`, `ProxyCommand`): pueden cambiar de una máquina a otra y `tmux`
no los controla.

**`ssh-pane` abre un pane cuyo proceso es un cliente SSH hecho con libssh, sin
ejecutar ningún programa.** El comportamiento y los mensajes de error los fija
`tmux`.

Es **solo para Linux**, y el cambio es aditivo: un build sin `--enable-ssh`, y
cualquier build que no sea Linux, da exactamente el `tmux` de hoy.

## 2 · Actores

| Actor | Tipo | Qué hace / qué espera |
|---|---|---|
| Usuario de `tmux` | humano | Invoca `ssh-pane` desde la línea de comandos, el prompt o un binding |
| Script / `.tmux.conf` | no humano | Invoca `ssh-pane` y lee el exit code del cliente `tmux`. **También usa abreviaturas de comandos existentes**, que no pueden cambiar (INV-3) |
| Servidor `tmux` | no humano | Resuelve el comando, crea el pane y el PTY, y lee y escribe el master desde su event loop (N-3) |
| Proceso hijo del pane | no humano | Corre el cliente libssh entre el PTY y la red, y termina con un exit status |
| Kernel (PTY, TCP, señales) | no humano | Entrega `SIGWINCH` y `SIGHUP` al hijo, y corta conexiones |
| Resolver DNS | no humano | Puede no resolver el host (FR-38) |
| `sshd` remoto | no humano | Puede no existir, rechazar la conexión, no responder, presentar una host key desconocida o cambiada, rechazar la autenticación o el PTY, o cortar la sesión |
| `ssh-agent` | no humano | Opcional. Se lo encuentra por `SSH_AUTH_SOCK` en el entorno del pane (N-6). Puede estar muerto (FR-51) |
| Build de un mantenedor no-Linux | no humano | macOS o un BSD que corre `./configure && make`: no puede enterarse de que el feature existe (INV-1) |

## 3 · Alcance

### Dentro (la superficie de cambio, completa)

Si un FR necesita tocar un archivo que no está en esta tabla, la spec está mal y
se vuelve a Revisar. INV-5 chequea esta lista contra el diff. **Esta spec no
implementa ninguno de estos cambios.**

| Archivo | Qué cambia | Guarda |
|---|---|---|
| `configure.ac` | Una opción `--enable-ssh`, apagada por defecto. Con la opción prendida, en este orden: (1) si `$host_os` no matchea `*linux*`, error de FR-2. Se pregunta por `$host_os` como hace `--enable-static` (`configure.ac:91`), y **no** por `$PLATFORM` (N-5). (2) Si también está `--enable-static`, error de FR-4. (3) Se busca libssh ≥ 0.9.0 por pkg-config; si falta, error de FR-3. (4) Se define `ENABLE_SSH`. El `AM_CONDITIONAL(ENABLE_SSH, …)` va **fuera** del bloque condicional, como el de sixel (`configure.ac:551-552`): automake exige que todo `AM_CONDITIONAL` se evalúe siempre | el bloque solo actúa con `--enable-ssh` |
| `Makefile.am` | Bajo `if ENABLE_SSH`, se suman `cmd-ssh-pane.c` y `ssh-pane.c` a las fuentes, igual que sixel (`Makefile.am:253-254`) | `AM_CONDITIONAL` |
| `cmd.c` | La declaración de la entrada del comando nuevo, y la entrada en `cmd_table` (`cmd.c:123`). Va entre `split-window` y `start-server` (`cmd.c:206-207`), para mantener el orden alfabético de la tabla, que es el orden en que la listan `list-commands` y el error de ambigüedad (FR-23) | `#ifdef ENABLE_SSH` |
| `tmux.h` | Un flag de spawn nuevo, que sigue a `SPAWN_FLOATOVERZOOM` (`tmux.h:2531`). Un puntero opcional al **destino SSH** (host, usuario, puerto y path de clave, ya validados) al final de `struct spawn_context` (`tmux.h:2500`). Los prototipos de `ssh-pane.c` | `#ifdef ENABLE_SSH` |
| `spawn.c` | En el hijo de `spawn_pane()`, **después de `environ_push(child)` (`spawn.c:544`) y antes del `if` que elige entre `execvp` y `$SHELL` (`spawn.c:550`)**: si el contexto trae el flag nuevo, se corre el cliente y el hijo termina con el status que este devuelve. No hay `exec` y la función no vuelve | `#ifdef ENABLE_SSH` |
| `cmd-ssh-pane.c` (nuevo) | La entrada del comando y su función de ejecución. Valida los argumentos (§6.3), obtiene la celda con `layout_get_tiled_cell()` (`layout.c:1640`), arma el contexto de spawn como `cmd-split-window.c:195-208`, **con cero argumentos de comando** (D-11), y llama a `spawn_pane()` | solo se compila con `ENABLE_SSH` |
| `ssh-pane.c` (nuevo) | El cliente: conexión, host key, autenticación, canal con PTY y el bucle de E/S entre los fd 0/1 del pane y el canal | solo se compila con `ENABLE_SSH` |
| `tmux.1` | La entrada de `ssh-pane` en `WINDOWS AND PANES`, con la frase "Only available on Linux when tmux is built with --enable-ssh" | ninguna: el man se instala en todas las plataformas (ver INV-7) |
| `regress/ssh-pane-*.sh` (nuevos) | Los VCs de §6. `regress/Makefile` los toma solos (`regress/Makefile:1`). Si el comando no existe o falta el entorno de §9, **se saltean** con exit 0, y eso no cuenta como verificado (§9) | auto-salteo |

### Fuera de alcance: por path (el implementador no modifica estos archivos)

- **`window.c`, `server.c`, `input.c`, `screen*.c`, `grid*.c`, `tty*.c`.** El
  modelo de pane y de PTY, la lectura y la muerte del proceso no se tocan
  (INV-5).
- **`layout.c` y `layout-*.c`.** Se llama a `layout_get_tiled_cell()`, pero no se
  modifica.
- **`cmd-split-window.c`, `cmd-respawn-pane.c`, `cmd-new-window.c` y todo
  `cmd-*.c` existente.** No ganan flags ni cambia su `usage` (INV-4).
- **`compat/`, `compat.h`, `osdep-*.c`.** `ssh-pane` no reemplaza ninguna
  función de la libc ni es una implementación por SO.
- **`job.c`, `popup.c`, `cmd-run-shell.c`.** El otro llamador de `fdforkpty`
  (`job.c:116`) no cambia.
- **`options-table.c`.** En v1 no hay opciones nuevas.
- **`prompt.c`, `cmd-list-commands.c`.** Ven el comando nuevo solos, porque
  recorren `cmd_table` (FR-22 a FR-24).
- **`.github/workflows/regress.yml`.** El CI de upstream no se modifica. El job con
  `--enable-ssh` y `sshd` es de este TP (§9).

### Fuera de alcance: comportamiento

| Excluido | Por qué (decisión en §8) |
|---|---|
| Plataformas no-Linux | Es el límite de la consigna. Se materializa en FR-2 y FR-5 |
| Builds estáticos con `--enable-ssh` | D-15. Se materializa en FR-4 |
| Prompts interactivos: passphrase, password, keyboard-interactive, aceptar una host key nueva | D-5 y BR-1. En v1, el hijo no lee el PTY antes de tener el canal (FR-49, FR-50) |
| Leer `~/.ssh/config` o `/etc/ssh/ssh_config` | D-7 y BR-3 |
| Port forwarding, agent forwarding, X11, `ProxyJump` y multiplexado | BR-4 |
| Destinos IPv6 literales y `host:puerto` | D-9. El puerto va por `-P` |
| Panes flotantes o modales, tamaño (`-l`), `-b`, `-f`, `-Z` | D-16 |
| Reintentos, reconexión y keepalive | D-10. Si el remoto desaparece sin `RST`, el pane queda colgado hasta que el kernel cierre el TCP |
| `respawn-pane` como "reconectar" | D-11. Se declara su comportamiento en FR-21 |
| Cambiar `#{pane_current_command}` | D-12. Su valor se declara en FR-19 y FR-20 |

## 4 · El límite solo-Linux

Hay cuatro combinaciones de plataforma y flag. Cada una tiene un resultado
observable y un VC:

| | sin `--enable-ssh` | con `--enable-ssh` |
|---|---|---|
| **Linux** | El `tmux` de hoy: no enlaza libssh y no tiene `ssh-pane` (FR-5, INV-2) | `ssh-pane` disponible (FR-1). Sin libssh ≥ 0.9.0 (FR-3) o con `--enable-static` (FR-4), `configure` falla |
| **No-Linux** | El `tmux` de hoy: compila y la `regress/` da lo mismo (FR-5, INV-1) | **`configure` falla** con un mensaje explícito (FR-2) |

La guarda es triple. Cada capa cubre una cosa:

1. **`configure.ac`** decide por `$host_os`. `$PLATFORM` todavía está vacía cuando
   se procesan las opciones (N-5).
2. **`Makefile.am`** no compila los dos archivos nuevos sin `ENABLE_SSH`. En
   no-Linux no se pueden prender, así que nunca se compilan.
3. **`#ifdef ENABLE_SSH`** en `cmd.c`, `tmux.h` y `spawn.c`. Sin el define, quitar
   esos bloques (con `unifdef`) deja los archivos idénticos al commit base
   (INV-7). Así, el árbol de OpenBSD, que no tiene `configure` y comparte esos
   archivos, tampoco ve el feature.

Qué está verificado y qué no:

- VC-5 corre en macOS y en Linux.
- VC-2 y VC-67 corren en macOS.
- En los BSD, Solaris, AIX, Haiku y Cygwin, el límite vale **por construcción**,
  gracias a las tres capas de arriba, pero ningún VC corre ahí.

## 5 · Invariantes (cada una con su chequeo)

- `$BASE` es `5a820e63b72f05c121441149c72327aeeb16dfa4`.
- Las "fallas de base" son las de [`linea-de-base.md`](./linea-de-base.md),
  corridas solas.
- Los chequeos son `sh` POSIX y se corren desde la raíz del árbol de tmux.

| # | Invariante | Cómo se comprueba |
|---|---|---|
| **INV-1** | Los builds no-Linux siguen compilando y no tienen el feature | En macOS, `./configure --disable-jemalloc && make` sale 0. Además: `nm tmux \| grep -c ' _ssh_'` da `0`, `otool -L tmux \| grep -c libssh` da `0`, y `cd regress && gmake` deja exactamente las fallas de base de macOS |
| **INV-2** | Un Linux sin `--enable-ssh` es el de hoy | Con `./configure --enable-utf8proc && make`: `ldd tmux \| grep -c libssh` da `0`, y la salida de `tmux list-commands` es byte a byte igual a [`linea-de-base/list-commands-linux.txt`](./linea-de-base/list-commands-linux.txt) |
| **INV-3** | Ningún prefijo de un comando existente cambia el comando al que resuelve | En el build Linux con `--enable-ssh`: `TEST_TMUX=./tmux sh <este TP>/scripts/snapshot-comandos.sh \| grep -v '^ssh-pane'` es igual a [`linea-de-base/snapshot-comandos-linux.txt`](./linea-de-base/snapshot-comandos-linux.txt). Pasa porque el nombre empieza con `ss`, que hoy no es prefijo de ningún comando (N-1), y porque no tiene alias |
| **INV-4** | Los comandos existentes no cambian (nombre, alias, flags y `usage`) | Con `--enable-ssh`, `tmux list-commands \| grep -v '^ssh-pane '` es igual a `list-commands-linux.txt` |
| **INV-5** | El modelo de PTY y panes no cambia, y el diff no sale de "Dentro" | `git diff --name-only $BASE` está contenido en `configure.ac Makefile.am cmd.c tmux.h spawn.c cmd-ssh-pane.c ssh-pane.c tmux.1 regress/ssh-pane-*.sh`. `struct window_pane` (`tmux.h:1306`) queda igual: `git show "$BASE:tmux.h" \| sed -n '/^struct window_pane {/,/^};/p' > /tmp/a; sed -n '/^struct window_pane {/,/^};/p' tmux.h > /tmp/b; cmp /tmp/a /tmp/b` sale con 0 |
| **INV-6** | La suite existente no regresiona en ningún build | Se corre `regress/` en Linux con `--enable-ssh`, en Linux sin él y en macOS, y se aplica la regla de [`linea-de-base.md`](./linea-de-base.md): cada falla se re-corre sola 3 veces y tiene que estar clasificada en la línea de base. Una falla que no está ahí es una regresión |
| **INV-7** | Los archivos compartidos con OpenBSD solo cambian dentro de `#ifdef ENABLE_SSH` | Para cada `f` en `cmd.c tmux.h spawn.c`: `git show "$BASE:$f" > /tmp/b; unifdef -UENABLE_SSH "$f" > /tmp/n; cmp /tmp/b /tmp/n`, con exit 0. (El exit de `unifdef` no importa: da 1 cuando quitó algo.) `tmux.1` es el único archivo compartido que cambia fuera de una guarda, a propósito: es documentación y dice "Only available on Linux" |

## 6 · Requerimientos

### Convenciones de todos los VCs

- Corren como `regress/ssh-pane-*.sh` en el entorno de §9, salvo que el VC diga
  otra cosa.
- `T` es `tmux -Ltest -f/dev/null`. El servidor de prueba se crea con
  `T new-session -d -x 200 -y 50` y `T set -g remain-on-exit on`. La opción
  existe hoy (`options-table.c:1669`), y es lo que permite leer un pane después
  de que su proceso terminó.
- **Estado del pane:** `T display -p -t <pane> '#{pane_dead} #{pane_dead_status}'`.
- **Texto del pane:** `T capture-pane -pJ -t <pane>`. Con `-J`, una línea larga
  que se partió en varias filas se lee entera.
- **El pane nuevo:** el único `pane_id` de `T list-panes -F '#{pane_id}'` que no
  estaba antes del comando. **`%0`:** el pane inicial.
- **Entorno base:**
  - el destino es `alice@servidor` y el `sshd` de §9 escucha en el 22;
  - su host key ed25519 está en `~/.ssh/known_hosts` del cliente;
  - hay un `ssh-agent` en `SSH_AUTH_SOCK` con una clave autorizada para `alice`.
- **`~`** es el directorio home del usuario dueño del servidor `tmux`. En §9, ese
  usuario es `alice` en el contenedor `cliente`.
- **`/etc/ssh/ssh_known_hosts`** no existe en el cliente, salvo en los VCs que lo
  crean.
- **Log de `sshd`:** cada instancia escribe en `/var/log/sshd-<puerto>.log`
  (`sshd -E`). Antes de cada VC se trunca, y cada VC abre **una sola** conexión.
  "Esa conexión" es, entonces, todo el log.
- **Cómo corren los VCs de build** (VC-1 a VC-5, VC-67 a VC-69): no son
  `regress/`. Los corren los jobs de §9 sobre el árbol de tmux.

### 6.1 · Build y plataforma

**FR-1 · Build Linux con el feature.**
**Dado** un Linux con libssh ≥ 0.9.0 visible por `pkg-config`,
**cuando** se corre `./configure --enable-ssh && make`,
**entonces** los dos pasos salen con 0 y el binario tiene el comando `ssh-pane`.

> **VC-1** — En el contenedor `cliente` de §9, los dos pasos salen con 0, y
> `tmux list-commands -F '#{command_list_name}' ssh-pane` imprime exactamente
> `ssh-pane`.

**FR-2 · `--enable-ssh` en una plataforma que no es Linux.**
**Dado** un `$host_os` que no matchea `*linux*`,
**cuando** se corre `./configure --enable-ssh`,
**entonces** `configure` sale con 1, imprime
`configure: error: --enable-ssh is only supported on Linux` y no genera `Makefile`.

> **VC-2** — En macOS: exit 1, la línea literal en stderr, y no se genera
> `Makefile`.

**FR-3 · `--enable-ssh` sin libssh suficiente.**
**Dado** un Linux donde `pkg-config --atleast-version=0.9.0 libssh` falla,
**cuando** se corre `./configure --enable-ssh`,
**entonces** `configure` sale con 1 e imprime
`configure: error: libssh >= 0.9.0 not found`.

> **VC-3** — En el contenedor `cliente` **sin** `libssh-dev`: exit 1 y la línea
> literal.

**FR-4 · `--enable-ssh` junto con `--enable-static`.**
**Dado** un Linux con libssh ≥ 0.9.0,
**cuando** se corre `./configure --enable-ssh --enable-static`,
**entonces** `configure` sale con 1 e imprime
`configure: error: --enable-ssh cannot be combined with --enable-static`.

> **VC-4** — En el contenedor `cliente`: exit 1 y la línea literal.

**FR-5 · Un binario sin el feature no conoce el comando.**
**Dado** un `tmux` compilado sin `--enable-ssh`, en macOS o en Linux,
**cuando** se corre `tmux ssh-pane host`,
**entonces** el cliente imprime `unknown command: ssh-pane` por stderr y sale
con 1, igual que hoy (`cmd.c:489`).

> **VC-5** — En macOS y en Linux sin el flag: el stderr exacto y exit 1, igual
> que en [`linea-de-base.md`](./linea-de-base.md).

### 6.2 · El comando: camino feliz

La sinopsis es esta:

```
ssh-pane [-dh] [-i identity-file] [-P port] [-t target-pane] destination
```

- `destination` es `[user@]host`.
- Los flags son `d`, `h`, `i:`, `P:` y `t:`, con exactamente un argumento
  posicional.
- Cualquier otra letra es un error de tmux (FR-27). En particular, `p`, `l`, `x`,
  `X`, `y` e `Y` no pueden aceptarse, porque las lee el layout (N-8, D-8).

**FR-6 · Abrir un pane remoto.**
**Dado** el entorno base,
**cuando** se corre `T ssh-pane -t %0 alice@servidor`,
**entonces** el cliente `tmux` sale con 0 y aparece un pane nuevo, activo,
debajo de `%0`. Su proceso abre, **en menos de 3 s**, una sesión interactiva en
`servidor` como `alice`, con PTY y con la shell de login de `alice`.

> **VC-6 (end-to-end, ver §9)** — Se corre
> `T send-keys -t <nuevo> 'echo "R=$(hostname):$(id -un):$(tty)"' Enter`. Se
> espera:
>
> - el texto del pane contiene `R=servidor:alice:/dev/pts/` dentro de los 3 s
>   del comando;
> - el exit del cliente es 0;
> - `T display -p '#{pane_id}'` es el pane nuevo;
> - en `T list-panes -F '#{pane_id} #{pane_top} #{pane_left}'`, el nuevo tiene
>   `pane_top` mayor que el de `%0` y el mismo `pane_left`.

**FR-7 · Partir a lo ancho.**
**Dado** el entorno base,
**cuando** se corre `T ssh-pane -h -t %0 alice@servidor`,
**entonces** el pane nuevo queda a la derecha de `%0`.

> **VC-7** — El nuevo tiene `pane_left` mayor que el de `%0` y el mismo
> `pane_top`.

**FR-8 · Sin activar el pane.**
**Dado** el entorno base,
**cuando** se corre `T ssh-pane -d -t %0 alice@servidor`,
**entonces** el pane activo sigue siendo `%0`.

> **VC-8** — `T display -p '#{pane_id}'` da `%0` después del comando.

**FR-9 · Otro puerto.**
**Dado** el entorno base, pero con un `known_hosts` cuya **única** entrada es
`[servidor]:2222`, que es la forma de OpenSSH para un puerto que no es el 22
(N-7),
**cuando** se corre `T ssh-pane -P 2222 alice@servidor`,
**entonces** la sesión se abre como en FR-6, contra el puerto 2222.

> **VC-9** — Mismo observable que VC-6. Además, el último campo de
> `echo "C=$SSH_CONNECTION"` en el remoto es `2222`.

**FR-10 · Clave explícita.**
**Dado** el entorno base **sin** `SSH_AUTH_SOCK`, con una clave privada **sin
passphrase** en `/tmp/k` que el servidor acepta, y sin ninguna de las claves por
defecto de D-5 en `~/.ssh/`,
**cuando** se corre `T ssh-pane -i /tmp/k alice@servidor`,
**entonces** la sesión se abre como en FR-6.

> **VC-10** — Mismo observable que VC-6.

**FR-11 · El agente va primero.**
**Dado** el entorno base, y una segunda clave en `/tmp/k` también autorizada,
**cuando** se corre `T ssh-pane -i /tmp/k alice@servidor`,
**entonces** el servidor acepta la clave **del agente**. El orden de D-5 es
observable.

> **VC-11** — El log de `sshd` del servidor tiene, para esa conexión,
> `Accepted publickey for alice` con el fingerprint de la clave del agente, y no
> con el de `/tmp/k`.

**FR-12 · Usuario por defecto.**
**Dado** el entorno base, con el servidor `tmux` corriendo como `alice`,
**cuando** se corre `T ssh-pane servidor`, sin `user@`,
**entonces** el usuario remoto es el nombre de login del dueño del servidor
`tmux` (el que da `id -un` para ese usuario).

> **VC-12** — `echo "U=$(id -un)"` en el remoto da `U=alice`.

**FR-13 · Terminal remota.**
**Dado** una sesión abierta con FR-6, en un pane de `C` columnas y `F` filas,
**cuando** se consulta la terminal remota,
**entonces** `TERM` es el `TERM` del entorno del pane (el de `default-terminal`)
y el tamaño es `F C`.

> **VC-13** — `echo "T=$TERM S=$(stty size)"` en el remoto da
> `T=<T show -gv default-terminal> S=<pane_height> <pane_width>`.

**FR-14 · Cambio de tamaño.**
**Dado** una sesión abierta,
**cuando** se corre `T resize-pane -t <nuevo> -y 12`,
**entonces**, **dentro de 1 s**, la terminal remota pasa a tener 12 filas.

> **VC-14** — Dentro de 1 s del `resize-pane`, `stty size` en el remoto empieza
> con `12 `. El servidor `tmux` no hace nada nuevo para esto: el resize le llega
> al hijo como `SIGWINCH` por `TIOCSWINSZ` (`window.c:612`), y el hijo lo reenvía
> como `window-change`.

**FR-15 · Estado de salida remoto.**
**Dado** una sesión abierta,
**cuando** la shell remota termina con `exit <n>`, con `n` entre 0 y 255,
**entonces** el proceso del pane termina con status `n`.

> **VC-15** — Con `exit 7`, el estado del pane es `1 7`. Con `exit 0`, es `1 0`.

**FR-16 · Cerrar el pane cierra la sesión.**
**Dado** una sesión abierta,
**cuando** se corre `T kill-pane -t <nuevo>`,
**entonces**, **dentro de 5 s**, termina la sesión SSH en el servidor remoto.

> **VC-16** — Dentro de 5 s, `pgrep -u alice -f 'sshd: alice@pts'` en el
> servidor no devuelve procesos.

**FR-17 · Bytes sin transformar.**
**Dado** una sesión abierta cuya terminal **remota** está en modo raw,
**cuando** el remoto escribe bytes arbitrarios (`\x00`, `\x1b`, `\n`, UTF-8
inválido),
**entonces** esos bytes llegan al master del PTY del pane sin modificarse.

Para eso, el hijo pone **su** terminal (el esclavo del PTY) en modo raw al abrir
el canal, como hace `ssh(1)`. Sin eso, el `ONLCR` local convertiría cada `\n` en
`\r\n`. Lo que `tmux` haga después con esos bytes es lo mismo que con cualquier
otro pane (`input_parse_pane`, `input.c:1028`).

> **VC-17** — `/tmp/fixture.bin`, **en el servidor remoto**, tiene 65.536 bytes:
> los valores 0x00–0xff repetidos. Se corre
> `T pipe-pane -t <nuevo> -o 'cat > /tmp/out'` en el cliente, y en el remoto
> `stty raw -echo; cat /tmp/fixture.bin; stty sane`. `/tmp/out` tiene que
> contener los 65.536 bytes del fixture, contiguos y en orden. Lo chequea un
> script que busca esa subsecuencia; el eco del comando queda antes.

**FR-18 · Ctrl-C va al remoto.**
**Dado** una sesión abierta que corre `sleep 300` en el remoto,
**cuando** se corre `T send-keys -t <nuevo> C-c`,
**entonces**, **dentro de 2 s**, el `sleep` remoto termina con status 130 y el
pane sigue vivo, con la sesión abierta. Con la terminal local en raw, `^C` es un
byte que viaja por el canal, no una señal para el hijo.

> **VC-18** — Dentro de 2 s, `#{pane_dead}` sigue en `0`, y `echo "V=$?"` en el
> remoto da `V=130`.

**FR-19 · Nombre del proceso.**
**Dado** una sesión abierta, y un servidor `tmux` arrancado como `tmux` (por
`PATH`) o con un path absoluto,
**cuando** se consulta `#{pane_current_command}` del pane,
**entonces** vale `tmux`. Es el `argv[0]` del servidor, porque el hijo no hace
`exec` (N-6, D-12). El formato lo pasa por `parse_window_name()` (`format.c:975`),
que solo recorta un path que empieza con `/` (`names.c:167`). Si el servidor se
arrancó como `./tmux`, el valor es otro, igual que pasa hoy con cualquier
programa.

> **VC-19** — `T display -p -t <nuevo> '#{pane_current_command}'` da `tmux`.

**FR-20 · Nombre de la ventana.**
**Dado** una ventana nueva **sin nombre explícito** (`T new-window -d 'sleep 300'`),
con `automatic-rename` prendido (`options-table.c:1304`). `-n` no sirve acá:
apaga `automatic-rename` para esa ventana (`spawn.c:223`).
**cuando** se corre `T ssh-pane -t <su pane> alice@servidor` y después se mata
el pane original,
**entonces**, **dentro de 2 s**, la ventana se llama `tmux`.

> **VC-20** — `T display -p -t <ventana> '#{window_name}'` da `tmux`.

**FR-21 · `respawn-pane` no reconecta.**
**Dado** un pane de `ssh-pane` cuyo proceso terminó, y `default-command` vacío
(que es el valor por defecto),
**cuando** se corre `T respawn-pane -t <ese pane>`,
**entonces** el pane corre una **shell local de login**, como cualquier pane que
nunca recibió un comando (D-11), y `#{pane_start_command}` queda vacío.

> **VC-21** — Después del respawn, `echo "H=$(hostname)"` da `H=cliente`, y
> `T display -p -t <pane> '#{pane_start_command}'` da una línea vacía.

**FR-22 · El comando aparece en `list-commands`.**
**Dado** un build con FR-1,
**cuando** se corre `T list-commands`,
**entonces** la única línea nueva respecto de la línea de base es la de
`ssh-pane`, con la sinopsis de §6.2.

> **VC-22** — `diff list-commands-linux.txt -` muestra una sola línea agregada,
> `ssh-pane [-dh] [-i identity-file] [-P port] [-t target-pane] destination`.

**FR-23 · El mensaje de ambigüedad de `s` lo incluye.**
**Dado** un build con FR-1,
**cuando** se corre `T list-commands s`,
**entonces** el error `ambiguous command: s, could be: …` (`cmd.c:506`) lista
28 candidatos en lugar de 27, y `ssh-pane` aparece entre `split-window` y
`start-server`. Que siga siendo ambiguo y ningún otro prefijo cambie lo cubre
INV-3.

> **VC-23** — La salida contiene `split-window, ssh-pane, start-server` y tiene
> 28 nombres.

**FR-24 · El prompt lo completa.**
**Dado** un build con FR-1,
**cuando** en el prompt de comandos (`command-prompt`) se escribe `ss` y se
aprieta Tab,
**entonces** el prompt queda en `ssh-pane `. El completado recorre `cmd_table`
(`prompt.c:1568`).

> **VC-24** — Solo en Linux. Usa la técnica de `regress/prompt-keys.sh`, que
> pasa en la línea de base de Linux: un tmux de afuera maneja un cliente
> adjuntado al de adentro, y un binding guarda el prompt en `@result`. Se espera
> que `T show -gv @result` dé `ssh-pane `. No se usa
> `prompt-words-history.sh`, que ya falla en la línea de base.

### 6.3 · Errores al invocar (síncronos: no se crea ningún pane)

En esta sección, el error sale por el cliente `tmux`: stderr y **exit 1**. **La
cantidad de panes no cambia**: cada VC compara `T list-panes -a | wc -l` antes y
después. Todos parten del entorno base.

**FR-25 · Falta el destino.**
**Dado** ningún argumento posicional,
**cuando** se corre `T ssh-pane`,
**entonces** stderr es `command ssh-pane: too few arguments (need at least 1)`.
Es el formato que ya usa tmux (`arguments.c:333`).

> **VC-25** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-26 · Dos destinos.**
**Dado** dos argumentos posicionales,
**cuando** se corre `T ssh-pane alice@servidor otro`,
**entonces** stderr es `command ssh-pane: too many arguments (need at most 1)`
(`arguments.c:340`).

> **VC-26** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-27 · `-p` no es un flag.**
**Dado** el flag `-p`, que `ssh(1)` usa para el puerto,
**cuando** se corre `T ssh-pane -p 22 alice@servidor`,
**entonces** stderr es `command ssh-pane: unknown flag -p`.

> **VC-27** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-28 · Usuario vacío.**
**Dado** el destino `@servidor`,
**cuando** se corre `T ssh-pane @servidor`,
**entonces** stderr es `invalid destination: @servidor`.

> **VC-28** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-29 · Host vacío después de `@`.**
**Dado** el destino `alice@`,
**cuando** se corre `T ssh-pane alice@`,
**entonces** stderr es `invalid destination: alice@`.

> **VC-29** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-30 · Destino vacío.**
**Dado** el destino `''`,
**cuando** se corre `T ssh-pane ''`,
**entonces** stderr es `invalid destination: ` (con el espacio final).

> **VC-30** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-31 · Más de un `@`.**
**Dado** el destino `a@b@servidor`,
**cuando** se corre `T ssh-pane a@b@servidor`,
**entonces** stderr es `invalid destination: a@b@servidor`.

> **VC-31** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-32 · Destino con puerto.**
**Dado** el destino `servidor:22`,
**cuando** se corre `T ssh-pane servidor:22`,
**entonces** stderr es `invalid destination: servidor:22 (use -P for the port)`.
La regla es "el destino contiene `:`" (D-9). FR-55 cubre el otro caso.

> **VC-32** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-33 · Puerto fuera de rango.**
**Dado** un valor de `-P` que no es un entero decimal entre 1 y 65535,
**cuando** se corre `T ssh-pane -P <valor> alice@servidor`,
**entonces** stderr es `invalid port: <valor>`. Los bordes 1 y 65535 se aceptan.

> **VC-33** — Con `0`, `65536` y `abc`: el stderr exacto de cada uno, exit 1, y
> la cantidad de panes sin cambio. Con `1` y `65535` (los bordes): **no**
> aparece ese error, el exit es 0 y hay un pane nuevo. Lo que pase después con
> ese pane (FR-39) no es parte de este VC.

**FR-34 · Clave explícita que no se puede abrir.**
**Dado** un `<path>` que el usuario del servidor `tmux` no puede abrir para
lectura,
**cuando** se corre `T ssh-pane -i <path> alice@servidor`,
**entonces** stderr es `can't read identity file: <path>`.

> **VC-34** — Con `/nonexistent` y con un archivo en modo `000`: el stderr
> exacto, exit 1, y la cantidad de panes sin cambio.

**FR-35 · Target inexistente.**
**Dado** que `%99` no existe,
**cuando** se corre `T ssh-pane -t %99 alice@servidor`,
**entonces** stderr es `can't find pane: %99`, el mensaje de hoy
(`cmd-find.c:1272`).

> **VC-35** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-36 · Sin lugar para el pane.**
**Dado** una ventana de 2 filas (`T resize-window -y 2`),
**cuando** se corre `T ssh-pane -t %0 alice@servidor`,
**entonces** stderr es `no space for a new pane` (`layout.c:1692`).

> **VC-36** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-37 · El fork falla.**
**Dado** que el servidor `tmux` no puede crear procesos
(`prlimit --nproc=0:0 --pid <pid del servidor>`),
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** stderr empieza con `create pane failed: fork failed: `. Es el mismo
camino de error que `split-window` (`spawn.c:480`, `cmd-split-window.c:208`).

> **VC-37** — El stderr empieza con ese prefijo, exit 1, y la cantidad de panes
> sin cambio.

**FR-55 · Destino IPv6 literal.**
**Dado** el destino `::1`,
**cuando** se corre `T ssh-pane ::1`,
**entonces** stderr es `invalid destination: ::1 (use -P for the port)`. Los
IPv6 literales quedan fuera de v1 (D-9) y caen en la misma regla que FR-32.

> **VC-55** — El stderr exacto, exit 1, y la cantidad de panes sin cambio.

### 6.4 · Errores de conexión (asíncronos: el pane existe y su proceso termina)

En esta sección **el cliente `tmux` sale con 0**, porque el pane se creó. El hijo
escribe **una línea** en el pane y termina con **status 255**, la convención de
`ssh(1)` para errores propios. Cada VC observa:

- el estado del pane, `1 255`;
- el texto del pane, que contiene la línea literal.

Que el usuario vea esa línea o no lo decide `remain-on-exit`, como en cualquier
pane (D-13). Todos los casos parten del entorno base y cambian solo lo que dice
el **Dado**.

**Cota de tiempo común:** salvo que el FR diga otra cosa, el estado `1 255` y la
línea aparecen **dentro de los 12 s** desde el comando. Es el presupuesto de 10 s
de D-10 más 2 s de margen. Para FR-53 y FR-54, los 12 s se cuentan desde el
corte o desde la muerte de la shell remota.

**FR-38 · El host no resuelve.**
**Dado** el host `no-such-host.invalid`,
**cuando** se corre `T ssh-pane alice@no-such-host.invalid`,
**entonces**, **dentro de 5 s**, la línea es
`ssh-pane: could not resolve hostname no-such-host.invalid`.

> **VC-38** — Estado `1 255` y la línea literal dentro de 5 s.

**FR-39 · Conexión rechazada.**
**Dado** que en `servidor` no escucha nada en el puerto 2999,
**cuando** se corre `T ssh-pane -P 2999 alice@servidor`,
**entonces**, **dentro de 2 s**, la línea es
`ssh-pane: connection refused by servidor port 2999`.

> **VC-39** — Estado `1 255` y la línea literal dentro de 2 s.

**FR-40 · El TCP no se establece.**
**Dado** que `servidor` descarta sin responder los paquetes al 22
(`iptables -A INPUT -p tcp --dport 22 -j DROP`),
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces**, a los **10 s**, la línea es
`ssh-pane: connection to servidor port 22 timed out after 10 seconds`.

> **VC-40** — El estado pasa a `1 255` entre los 9,5 s y los 12 s, con la línea
> literal.

**FR-41 · El servidor acepta el TCP y no habla.**
**Dado** que en `servidor:2998` hay un proceso que acepta conexiones y nunca
escribe (`nc -lk 2998`),
**cuando** se corre `T ssh-pane -P 2998 alice@servidor`,
**entonces**, a los **10 s**, la línea es
`ssh-pane: connection to servidor port 2998 timed out after 10 seconds`. Los
10 s cubren todo el establecimiento, no solo el TCP (D-10).

> **VC-41** — El estado pasa a `1 255` entre los 9,5 s y los 12 s, con la línea
> literal.

**FR-42 · El key exchange falla.**
**Dado** un `sshd` en `servidor:2200` que solo ofrece `KexAlgorithms
diffie-hellman-group1-sha1`, un algoritmo que libssh no habilita por defecto. El
`sshd` 9.6 de Ubuntu 24.04 todavía lo acepta en la configuración,
**cuando** se corre `T ssh-pane -P 2200 alice@servidor`,
**entonces** la línea empieza con `ssh-pane: key exchange with servidor failed`.

> **VC-42** — Estado `1 255`, y una línea del texto empieza con ese prefijo.

**FR-43 · Host key desconocida.**
**Dado** un `~/.ssh/known_hosts` que existe y no tiene ninguna entrada para
`servidor`, y ningún `/etc/ssh/ssh_known_hosts`,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es
`ssh-pane: host key for servidor is not in known_hosts; connect once with ssh(1) to add it`,
y no hay ningún intento de autenticación.

> **VC-43** — Estado `1 255` y la línea literal. En el log de `sshd`, esa conexión
> no tiene ninguna línea `Accepted` ni `Failed`.

**FR-44 · No existe ningún `known_hosts`.**
**Dado** que no existen ni `~/.ssh/known_hosts` ni `/etc/ssh/ssh_known_hosts`,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es la misma de FR-43, y los dos archivos **siguen sin
existir**.

> **VC-44** — Estado `1 255`, la línea literal, y `test -e` falla para los dos
> paths.

**FR-45 · `known_hosts` ilegible.**
**Dado** un `~/.ssh/known_hosts` en modo `000`,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es `ssh-pane: could not read known_hosts`.

> **VC-45** — Estado `1 255` y la línea literal.

**FR-46 · Host key cambiada.**
**Dado** que `known_hosts` tiene, para `servidor`, una clave **del mismo tipo**
que la que presenta el servidor, pero distinta,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es
`ssh-pane: host key for servidor has changed; refusing to connect`.

> **VC-46** — Estado `1 255` y la línea literal.

**FR-47 · Host key de otro tipo.**
**Dado** que `known_hosts` solo tiene, para `servidor`, una clave de **otro
tipo** (`ssh-rsa`), y que el servidor solo tiene host key `ssh-ed25519` (§9).
libssh pone primero los tipos de `known_hosts`, pero agrega los demás
(`ssh_client_select_hostkeys`, N-7), así que se negocia `ssh-ed25519`,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es
`ssh-pane: host key for servidor has a different type than the known one; refusing to connect`.

> **VC-47** — Estado `1 255` y la línea literal.

**FR-48 · Autenticación rechazada.**
**Dado** que el servidor no acepta ninguna de las identidades de D-5,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea es `ssh-pane: authentication failed for alice@servidor`.

> **VC-48** — Sin agente, con una `~/.ssh/id_ed25519` sin passphrase que no está
> autorizada: estado `1 255` y la línea literal.

**FR-49 · Una clave por defecto con passphrase se saltea.**
**Dado** que la única identidad autorizada es una `~/.ssh/id_ed25519` **con
passphrase**, y que no hay agente,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces**, **dentro de 5 s**, la línea es la de FR-48, **sin que se pida la
passphrase**.

> **VC-49** — Estado `1 255` dentro de 5 s. El texto del pane tiene la línea de
> FR-48 y no contiene `passphrase`.

**FR-50 · Una clave explícita con passphrase.**
**Dado** que `/tmp/k` es una clave **con passphrase** y no hay agente,
**cuando** se corre `T ssh-pane -i /tmp/k alice@servidor`,
**entonces** la línea es
`ssh-pane: identity file /tmp/k is encrypted; add it to ssh-agent`.

> **VC-50** — Estado `1 255` y la línea literal.

**FR-51 · El agente no responde.**
**Dado** `SSH_AUTH_SOCK=/tmp/no-agent`, un socket que no existe, y una
`~/.ssh/id_ed25519` sin passphrase autorizada,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la sesión se abre como en FR-6: el agente se saltea y se sigue con
las claves.

> **VC-51** — Mismo observable que VC-6.

**FR-52 · El servidor no da PTY.**
**Dado** un `sshd` en `servidor:2201` con `PermitTTY no`,
**cuando** se corre `T ssh-pane -P 2201 alice@servidor`,
**entonces** la línea es `ssh-pane: servidor refused to allocate a pty`.

> **VC-52** — Estado `1 255` y la línea literal.

**FR-53 · Se corta la conexión.**
**Dado** una sesión abierta,
**cuando** en el servidor se cierra el socket TCP de la sesión
(`ss -K dport = :<puerto del cliente>`),
**entonces**, **dentro de 5 s**, la línea es
`ssh-pane: connection to servidor lost`.

> **VC-53** — Estado `1 255` y la línea literal dentro de 5 s.

**FR-54 · El canal se cierra sin estado.**
**Dado** una sesión abierta,
**cuando** la shell remota muere por una señal (`kill -9 $$`) y el servidor cierra
el canal sin mandar `exit-status`,
**entonces** la línea es
`ssh-pane: connection closed by servidor without exit status`.

> **VC-54** — Estado `1 255` y la línea literal.

**FR-56 · Una línea mal formada en `known_hosts`.**
**Dado** un `~/.ssh/known_hosts` cuya primera línea es basura (`esto no es una
entrada`) y cuya segunda línea es la entrada correcta de `servidor`,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la línea mal formada se ignora y la sesión se abre como en FR-6.
Es lo que hace OpenSSH con una línea que no puede parsear.

> **VC-56** — Mismo observable que VC-6.

**FR-57 · `-i` apunta a algo que no es una clave.**
**Dado** que `/tmp/notakey` se puede leer pero no es una clave privada (es una
copia de `/etc/hostname`),
**cuando** se corre `T ssh-pane -i /tmp/notakey alice@servidor`,
**entonces** la línea es
`ssh-pane: identity file /tmp/notakey is not a valid private key`. FR-34 solo
mira si el archivo se puede abrir; el contenido se lee en el hijo.

> **VC-57** — Estado `1 255` y la línea literal, sin agente en el entorno.

**FR-58 · El agente responde, pero está bloqueado.**
**Dado** un `ssh-agent` bloqueado con `ssh-add -x`, que no ofrece identidades,
y una `~/.ssh/id_ed25519` sin passphrase autorizada,
**cuando** se corre `T ssh-pane alice@servidor`,
**entonces** la sesión se abre como en FR-6: si el agente no aporta
identidades, se sigue con las claves de D-5.

> **VC-58** — Mismo observable que VC-6, y el log de `sshd` acepta el
> fingerprint de `~/.ssh/id_ed25519`.

### 6.5 · Reglas de negocio

**BR-1 · La host key siempre se verifica, y `tmux` nunca escribe `known_hosts`.**
En v1 no hay TOFU, ni ninguna forma de aceptar una clave desde `ssh-pane`. Las
entradas del host se buscan en los dos archivos de D-14 juntos, y se decide en
este orden:

1. Si alguno de los dos archivos existe y no se puede leer, FR-45.
2. Si alguna entrada coincide en tipo y en clave, se conecta.
3. Si hay una entrada del mismo tipo con otra clave, FR-46.
4. Si solo hay entradas de otro tipo, FR-47.
5. Si no hay ninguna entrada, FR-43 (o FR-44, si no existe ningún archivo).

Una línea mal formada se ignora y no cuenta como entrada (FR-56).

> **VC-59** — En corridas de VC-6, VC-43, VC-44, VC-46 y VC-47, el sha256 de
> `~/.ssh/known_hosts` y el de `/etc/ssh/ssh_known_hosts` (o el hecho de que no
> existan) es el mismo antes y después.

**BR-2 · El hijo no ejecuta ningún programa.**
Desde el `fork` hasta su `_exit`, el proceso del pane no llama a `execve`. Es lo
que significa "sin invocar `ssh`".

> **VC-60** — Como **root** en el contenedor `cliente`:
> `strace -f -e trace=execve -p <pid del servidor tmux>` durante VC-6
> y VC-43 no registra ningún `execve`. De control, la misma traza durante un
> `split-window` registra uno.

**BR-3 · No se lee configuración de OpenSSH.**
Host, usuario, puerto y clave salen **solo** de los argumentos de §6.2, de FR-12
y de D-5. Ni `~/.ssh/config` ni `/etc/ssh/ssh_config` cambian nada.

> **VC-61** — Con este `~/.ssh/config` en el cliente:
>
> ```
> Host *
>     Port 2999
>     ProxyCommand touch /tmp/proxy-ran
>     User mallory
>     IdentityFile /tmp/no-such-key
> ```
>
> `T ssh-pane servidor`, sin usuario, abre la sesión al 22 como `alice` (VC-6 y
> VC-12 pasan), y `/tmp/proxy-ran` no existe.

**BR-4 · Mínimo privilegio y nada de forwarding.**
`ssh-pane` corre con los permisos del dueño del servidor `tmux`, sin setuid. Solo
necesita:

- leer los archivos de D-14;
- leer la clave de `-i`, o las de D-5;
- conectarse al socket de `SSH_AUTH_SOCK`, si existe;
- abrir una conexión TCP saliente al destino.

No pide agent forwarding, X11 ni port forwarding, y no abre ningún puerto local.

> **VC-62** — En la sesión de VC-6, `echo "A=$SSH_AUTH_SOCK D=$DISPLAY"` en el
> remoto da `A= D=`. En el cliente, `ss -ltnp` no muestra ningún socket en
> escucha del proceso del pane.

**BR-5 · El hijo no deja core dumps.**
El hijo es un fork del servidor, sin `exec`: tiene en memoria lo mismo que el
servidor (buffers de pegado, historia de los panes) y, además, las claves que
cargó. Si se cae, no puede dejar un core en disco.

> **VC-63** — Con la sesión de VC-6 abierta, la línea `Max core file size` de
> `/proc/<pid del pane>/limits` es `0` en soft y en hard.

### 6.6 · No funcionales

**NFR-1 · El servidor no se bloquea mientras un pane conecta.**
Mientras **un** `ssh-pane` está en la situación de FR-40 (el host descarta los
paquetes), la **latencia p95 de `T display -p ok`** lanzado desde otro cliente
es **menor a 100 ms**, sobre **20 muestras** separadas por 250 ms.

> **VC-64** — Se lanza el `ssh-pane` de VC-40 y, dentro de los 5 s siguientes, se
> toman 20 tiempos de `display -p ok`. Si una implementación bloqueara el
> servidor durante la conexión, las latencias serían de segundos y el VC
> fallaría.

**NFR-2 · Throughput comparable al de `ssh(1)`.**
**Condición:**

- el remoto escribe ~65 MiB de texto:
  `head -c 50331648 /dev/urandom | base64 -w 76; echo __F''IN__`;
- el pane mide 200×50;
- `cliente` y `servidor` están en la misma red de Docker.

**Métrica:** el tiempo desde el `send-keys` hasta la primera vez que una línea
**igual a** `__FIN__` aparece en el texto del pane, con polling cada 50 ms. El
comando tipeado dice `__F''IN__`, así que su eco no cuenta como marcador.

**Umbral:** la **mediana de 5 corridas** es **≤ 1,25 ×** la mediana del mismo
recorrido con `T split-window 'ssh alice@servidor'`.

> **VC-65** — Un script de §9 corre las 10 mediciones intercaladas, reporta las
> dos medianas y su cociente, y falla si el cociente es mayor que 1,25.

**NFR-3 · Ningún secreto ni log de libssh a la vista.**
Se corre el servidor con `tmux -vvv` y se hacen VC-6 y VC-48. Después:

- ningún `tmux-*.log` contiene material de clave privada;
- no se crea ningún log con el PID del hijo;
- el texto del pane no tiene ninguna línea de log de libssh.

El hijo ya cierra el log de tmux (`spawn.c:543`). libssh, en cambio, escribiría
su log en stderr, que en el hijo es el PTY del pane.

> **VC-66** — `grep -lE 'PRIVATE KEY|BEGIN OPENSSH' tmux-*.log` no imprime nada.
> `ls tmux-*-<pid del hijo>.log` falla. El texto de los panes de VC-6 y VC-48 no
> tiene ninguna línea que empiece con `[` seguido de un dígito, que es el
> formato del log de libssh.

### 6.7 · Verificación de las invariantes

| VC | Invariante | Entorno |
|---|---|---|
| **VC-67** | INV-1 | macOS arm64, local o en el runner `macos-26` de GitHub Actions |
| **VC-68** | INV-2, INV-3, INV-4, INV-6 | contenedor `cliente` de §9, con y sin `--enable-ssh` |
| **VC-69** | INV-5, INV-7 | cualquier clon con `git` y `unifdef` |

## 7 · Trazabilidad

Cada FR-n tiene su VC-n (FR-1 → VC-1, …, FR-58 → VC-58). El VC end-to-end es
VC-6.

| Req | VC | | Req | VC | | Req | VC |
|---|---|---|---|---|---|---|---|
| FR-1 … FR-5 | VC-1 … VC-5 | | BR-1 | VC-59 | | NFR-1 | VC-64 |
| FR-6 … FR-24 | VC-6 … VC-24 | | BR-2 | VC-60 | | NFR-2 | VC-65 |
| FR-25 … FR-37 | VC-25 … VC-37 | | BR-3 | VC-61 | | NFR-3 | VC-66 |
| FR-38 … FR-54 | VC-38 … VC-54 | | BR-4 | VC-62 | | INV-1 | VC-67 |
| FR-55 … FR-58 | VC-55 … VC-58 | | BR-5 | VC-63 | | INV-2, 3, 4, 6 | VC-68 |
| | | | | | | INV-5, 7 | VC-69 |

Caminos de falla por recurso externo:

| Recurso | No existe | Rechaza / sin permiso | Ilegible / corrupto | Entrada inválida | Se corta |
|---|---|---|---|---|---|
| Host / red | FR-38 | FR-39 | — | FR-28 … FR-33, FR-55 | FR-40, FR-41, FR-53 |
| `sshd` | — | FR-48, FR-52 | FR-42 | — | FR-54 |
| `known_hosts` | FR-43, FR-44 | FR-45 (sin permiso) | FR-56 (línea mal formada) | FR-46, FR-47 (clave que no coincide) | — |
| Clave | FR-34 | FR-34 (sin permiso), FR-48 | FR-57 (no es una clave) | FR-49, FR-50 (con passphrase) | — |
| Agente | FR-51 (socket muerto) | FR-58 (bloqueado) | — | — | — |
| Proceso / layout | FR-35 | FR-37 | — | FR-25 … FR-27 | FR-36 |

## 8 · Decisiones

Están las seis de la consigna (D-1 a D-6) y las que fueron apareciendo. Cada una
lleva la alternativa principal descartada, y el fundamento completo está acá: no
hay otro documento de decisiones que abrir.

| # | Pregunta | Decisión | Se descartó, y por qué |
|---|---|---|---|
| D-1 | ¿Entrada nueva en la tabla de comandos? | **Sí: `ssh-pane`, sin alias**, bajo `#ifdef ENABLE_SSH` | Un flag nuevo en `split-window` (`-S host`): cambia el `usage` de un comando existente y viola INV-4. Un nombre que empiece con `sp` o `sw`, o un alias corto: le roba prefijos a `split-window` o `swap-*` (N-1, INV-3) |
| D-2 | ¿Dónde engancha en el camino de spawn? | **En el hijo de `spawn_pane()`, después de `environ_push` (`spawn.c:544`) y antes del `if` de `spawn.c:550`**. Es el mismo lugar que eligió systemd (`spawn.c:504`) | Un pane `SPAWN_EMPTY` alimentado desde el servidor: no tiene PTY, cambia `wp->fd` y `wp->pid` y rompe el resize (N-3, INV-5). Una función de spawn paralela: duplica layout, entorno y cwd, y se desincroniza con cada merge de upstream |
| D-3 | ¿libssh u OpenSSH? | **libssh ≥ 0.9.0**, enlazada dinámicamente | OpenSSH no tiene librería de cliente: usarlo es ejecutar `ssh`. libssh2 (BSD) era viable, porque también lee `known_hosts` de OpenSSH, pero hay que armar a mano el agente, las claves por defecto y la clasificación de la host key, que libssh ya trae (N-7). La licencia BSD de libssh2 no pesa, porque libssh (LGPL-2.1) enlazada dinámicamente no le impone condiciones a tmux (ISC). Versiones anteriores a 0.9.0 no tienen `SSH_OPTIONS_PROCESS_CONFIG`, que BR-3 necesita |
| D-4 | ¿Cómo se integra con el event loop? | **No se integra.** El cliente es un proceso aparte, detrás del PTY. El servidor sigue leyendo `wp->fd` con su `bufferevent` (`window.c:1677`). El hijo tiene su propio bucle, que espera a la vez el fd 0 y el socket | libssh no bloqueante dentro de libevent. `ssh_connect` resuelve el nombre con `getaddrinfo`, que bloquea igual (N-7), y el resto del handshake habría que reescribirlo como máquina de estados. Un crash de libssh mataría el servidor, y además hace falta un pane sin PTY (INV-5). NFR-1 detecta este diseño |
| D-5 | ¿Auth por claves o por agente? | **Primero el agente**, por `SSH_AUTH_SOCK`, si responde. **Después, claves sin passphrase**: la de `-i` si se pasó; si no, `~/.ssh/id_ed25519`, `~/.ssh/id_ecdsa` y `~/.ssh/id_rsa`, en ese orden. Una clave por defecto con passphrase se saltea (FR-49) | Password, keyboard-interactive y pedir la passphrase: son prompts en el PTY antes de que exista el canal, y ese diseño de UX y seguridad merece su propia spec. La clave con passphrase se puede usar igual, cargándola en el agente |
| D-6 | ¿Qué guarda de build deja afuera a no-Linux? | **Triple** (§4): `$host_os` en `configure.ac`, `AM_CONDITIONAL` en `Makefile.am` y `#ifdef ENABLE_SSH` en los archivos compartidos | `test $PLATFORM = linux` junto a las opciones: nunca se activa (N-5). Moverlo después de `configure.ac:1006`: funciona, pero el error aparecería después de todos los chequeos de dependencias, y separa la opción de su validación. Detectar Linux con `#ifdef __linux__` en C: prendería el feature en todo Linux y haría obligatoria la dependencia de libssh |
| D-7 | ¿Se lee `~/.ssh/config`? | **No** (BR-3) | Si se lee, trae `ProxyCommand` (una shell), `ProxyJump` (el binario `ssh` con `OPENSSH_PROXYJUMP=1`) y opciones que libssh soporta a medias, y rompe "sin invocar `ssh`" (N-7) |
| D-8 | ¿Con qué letra va el puerto? | **`-P`** | `-p`, como `ssh(1)`: `layout_get_tiled_cell()` lo lee como porcentaje (N-8). Por eso FR-27 lo rechaza en forma explícita |
| D-9 | ¿Sintaxis del destino? | **`[user@]host`**, con a lo sumo un `@` y sin `:` | `host:puerto`: choca con los IPv6 literales, y `[::1]:22` pide un parser para un caso fuera de alcance. Partir en el último `@`, como OpenSSH: un usuario con `@` no es un caso de v1, y rechazar es más simple de verificar |
| D-10 | ¿Reintentos y timeouts? | **Un solo intento.** Un presupuesto de **10 s** desde el comando hasta tener el canal con PTY y shell, que cubre TCP, banner, key exchange y autenticación (FR-40, FR-41). Sin keepalive | Reintentar esconde errores de configuración y le suma a cada pane una espera que no se ve. Sin tope, en Linux una conexión a un host que descarta paquetes dura lo que dan los reintentos de SYN del kernel: con el `net.ipv4.tcp_syn_retries = 6` por defecto, unos 127 s. ¿Por qué 10 s? El RTO inicial de SYN en Linux es 1 s y se duplica en cada reintento, así que en 10 s el kernel manda el SYN a los 0, 1, 3 y 7 s: se toleran tres SYN perdidos. Con 5 s se toleraban dos, y con 30 s el usuario mira un pane en negro medio minuto. Keepalive: sin él, un remoto que desaparece sin `RST` deja el pane colgado. Se acepta en v1, igual que `ssh(1)` con `ServerAliveInterval` en 0 (su default). Para reconectar, se abre otro `ssh-pane` |
| D-11 | ¿Qué comando guarda el pane? | **Ninguno.** `cmd-ssh-pane.c` arma el contexto con cero argumentos de comando, a diferencia de `split-window`, que mete los posicionales en `argv` (`cmd-split-window.c:195`). Así, `respawn-pane` corre `default-command` o una shell de login local (`spawn.c:380`, FR-21) | Copiar `args_to_vector` de `split-window`: el destino quedaría como comando, y un `respawn-pane` correría `$SHELL -c alice@servidor`. Guardar el destino en el pane: es un campo nuevo en `struct window_pane` y viola INV-5 |
| D-12 | ¿Qué muestra `#{pane_current_command}`? | **`tmux`** (FR-19), y por eso la ventana se renombra a `tmux` (FR-20) | `prctl(PR_SET_NAME)`: no cambia `/proc/<pid>/cmdline`, que es lo que lee `osdep_get_name` (N-6). Reescribir el `argv` del servidor desde el hijo: es frágil y depende de la plataforma |
| D-13 | ¿Cómo ve el usuario un error asíncrono? | **Una línea en el pane y status 255.** `remain-on-exit` (que acepta `failed-key`, `options-table.c:95`) decide si queda visible | Que `ssh-pane` cambie `remain-on-exit` del pane: es una opción del usuario. Avisarle al cliente por IPC: el hijo no conserva ningún descriptor del servidor (`spawn.c:541`) |
| D-14 | ¿Qué archivos de host keys se consultan? | **`~/.ssh/known_hosts` y `/etc/ssh/ssh_known_hosts`**, solo para leer. Es el comportamiento por defecto de libssh y el de OpenSSH (N-7) | Solo el del usuario: un host que el administrador registró en el archivo global fallaría con `ssh-pane` y andaría con `ssh` |
| D-15 | ¿`--enable-static`? | **No se combina con `--enable-ssh`** (FR-4) | Enlazar libssh en forma estática obliga, por la LGPL, a distribuir lo necesario para reenlazar, y hace que libssh dependa de la libcrypto estática |
| D-16 | ¿Qué flags de `split-window` se copian? | **Solo `-d`, `-h` y `-t`**: elegir dónde va el pane y si se activa | `-l`, `-b`, `-f`, `-Z`, `-c`, `-e`, `-F`/`-P`: no los pide la consigna, cada uno suma un VC, y `-l` además hace que el layout lea los argumentos (N-8). Se pueden agregar en otra spec sin romper esta |

## 9 · Entorno de verificación (contra un sistema real)

Los VCs de `ssh-pane` corren contra un **`sshd` de OpenSSH real**, no contra un
doble. El entorno es parte del contrato.

**Contenedor `cliente`:**

- `ubuntu:24.04`, con los paquetes de la línea de base más `libssh-dev`,
  `openssh-client` (solo para el control de NFR-2), `strace`, `util-linux`
  (`prlimit`), `iproute2` y `python3`;
- `hostname: cliente` en el compose (FR-21);
- corre como `alice` el `tmux` compilado con el cambio y `--enable-ssh`,
  instalado en `/usr/local/bin/tmux` e invocado por `PATH` (FR-19);
- se levanta con `--cap-add SYS_PTRACE`, que VC-60 necesita.

**Contenedor `servidor`:**

- `ubuntu:24.04` con `openssh-server`, `netcat-openbsd`, `iptables` e
  `iproute2` (estos dos no vienen en la imagen);
- `hostname: servidor` en el compose. Sin eso, el hostname es el id del
  contenedor y VC-6 no puede pasar;
- **una sola host key, `ssh-ed25519`** (`HostKey /etc/ssh/ssh_host_ed25519_key`).
  FR-47 la necesita;
- el usuario `alice`, con las claves de prueba autorizadas;
- tres instancias de `sshd`:
  - una en el 22 y el 2222, con la configuración por defecto;
  - una en el 2200, con `KexAlgorithms diffie-hellman-group1-sha1`;
  - una en el 2201, con `PermitTTY no`;
- todas con `LogLevel VERBOSE` y `-E /var/log/sshd-<puerto>.log`;
- se levanta con `--cap-add NET_ADMIN`, que VC-40 (`iptables`) y VC-53
  (`ss -K`) necesitan.

**Fixtures:**

- las entradas de `known_hosts` de cada VC;
- `/tmp/fixture.bin`, en `servidor`;
- las claves de FR-10, FR-11 y FR-48 a FR-50, generadas en cada corrida con
  `ssh-keygen` del contenedor `cliente`. Generarlas no es parte del SUT.

**El recorrido E2E es VC-6:** argumentos → `cmd_find` → `spawn_pane` →
`fdforkpty` → hijo libssh → TCP → `sshd` → shell remota → PTY → `bufferevent`
→ `capture-pane`.

Se corre en jobs de CI **del repo de este TP**, no de upstream:

| Job | Dónde | Qué VCs |
|---|---|---|
| `linux-ssh` | `docker compose`, `cliente` con `libssh-dev` y `--enable-ssh` | VC-1, VC-4, VC-6 a VC-66, VC-68 (variante con el flag) |
| `linux-sin-ssh` | `cliente` con `libssh-dev`, **sin** el flag | VC-5 (Linux), VC-68 (variante sin el flag) |
| `linux-sin-libssh` | `cliente` **sin** `libssh-dev`, con el flag | VC-3 |
| `macos` | runner `macos-26`, Homebrew sin `libssh` | VC-2, VC-5 (macOS), VC-67 |
| `estatico` | cualquiera, con `git` y `unifdef` | VC-69 |

**Saltear no es pasar.** Fuera de este entorno, los `regress/ssh-pane-*.sh` se
saltean (§3), para no romper el `regress/` de upstream en macOS. Un VC
salteado queda registrado como "no corrido", nunca como ✅. Solo cuenta como
verificado si corrió en este job.

## 10 · Línea de base de regresión

Se midió **antes** de tocar nada, con los comandos que se usaron de verdad. El
detalle está en [`linea-de-base.md`](./linea-de-base.md) y los datos crudos en
[`linea-de-base/`](./linea-de-base/).

```bash
# Linux (ubuntu:24.04 en Docker)
sh autogen.sh && ./configure --enable-utf8proc && make -j"$(nproc)"   # exit 0
cd regress && make -k -j"$(nproc)"                                     # 170 PASS, 2 FAIL

# macOS arm64
sh autogen.sh && ./configure --disable-jemalloc && make -j8            # exit 0
cd regress && gmake -k -j8                                             # 165 PASS, 7 FAIL (con make 3.81 corre 0 tests)
```

Al cerrar cada iteración se vuelve a correr todo. INV-6 no pide "todo verde",
porque hay fallas que ya existen: compara **el conjunto de fallas corridas
solas**.

## 11 · Plan de iteraciones

La spec es el contrato completo. Cada iteración deja la suite igual que en la
línea de base.

| Iteración | Alcance | Cierra |
|---|---|---|
| **1 · La guarda y el enganche** | `configure.ac`, `Makefile.am`, `cmd.c`, `tmux.h`, `cmd-ssh-pane.c` completo, y el bloque del hijo en `spawn.c`. En esta iteración, `ssh-pane.c` solo escribe `ssh-pane: not implemented` y termina con 255 | VC-1…5, VC-22…37, VC-55 y VC-67…69: todas las invariantes **antes** de que exista el cliente. Se ve un pane que muere con `1 255` |
| **2 · El camino feliz** | La conexión, la host key, la autenticación, el canal y el bucle de E/S | VC-6…21 y VC-61…63 |
| **3 · Los caminos de falla y los NFR** | Los mensajes de §6.4, el presupuesto de 10 s y las mediciones | VC-38…54, VC-56…60 (BR-1 y BR-2 usan VC-43) y VC-64…66 |

La Iteración 1 es la más angosta que se puede probar sola, y demuestra el límite
solo-Linux sin escribir una línea de SSH.

## Historial

| Versión | Fecha | Cambio |
|---|---|---|
| v1.0 | 2026-10-01 | Primer borrador |
| v1.1 | 2026-10-01 | Corrección adversarial ([`revisiones/spec-brownfield-2026-10-01.md`](./revisiones/spec-brownfield-2026-10-01.md)). `AM_CONDITIONAL` va fuera del `if`. `-l` y `-v` salen de la sinopsis (D-16). D-11 pasa a usar cero argumentos de comando, con su FR. Se parten los FRs de destino inválido. Se agregan 17 caminos de falla y bordes (FR-4, FR-11, FR-20, FR-21, FR-23, FR-24, FR-26, FR-27, FR-31, FR-37, FR-41, FR-42, FR-45, FR-49 a FR-52) y BR-5. Se fija la ventana en 200×50 y el texto se lee con `capture-pane -J`. Se rehace el descarte de libssh2. Se decide qué cubre el timeout y qué archivos `known_hosts` se leen. Se corrigen los chequeos de INV-3, INV-5 e INV-7 |
| v1.2 | 2026-10-01 | Segunda corrección ([`revisiones/spec-brownfield-2026-10-01-r2.md`](./revisiones/spec-brownfield-2026-10-01-r2.md)) y revisión de PR ([`revisiones/pr-tp2-tmux-ssh-nativo-2026-10-01.md`](./revisiones/pr-tp2-tmux-ssh-nativo-2026-10-01.md)). FR-20 deja de usar `-n`. NFR-2 usa un marcador que el eco del comando no contiene. §9 fija los hostnames, el tipo de host key, los logs de `sshd` y los cinco jobs. Se agregan FR-55 a FR-58 (IPv6 literal, `known_hosts` mal formado, `-i` que no es una clave, agente bloqueado). BR-1 fija el orden de decisión. Hay una cota común de 12 s para §6.4. Los VCs de BR, NFR e INV pasan a VC-59…69 |

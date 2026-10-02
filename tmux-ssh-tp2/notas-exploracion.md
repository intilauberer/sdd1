# Notas de exploración — `ssh-pane`: un pane con SSH nativo en `tmux` (solo Linux)

> Salida del paso **Descubrir**. Se exploró en modo **solo lectura**: no se modificó
> ningún archivo de `tmux`. Lo único que se ejecutó fue compilarlo y correr su suite,
> para tener la línea de base.
>
> **Repo:** [`tmux/tmux`](https://github.com/tmux/tmux), commit
> `5a820e63b72f05c121441149c72327aeeb16dfa4` (2026-09-30, `tmux next-3.9`).
> Cada `archivo:línea` de abajo se verifica contra ese commit con
> [`scripts/check-citas.py`](./scripts/check-citas.py). El script confirma que la
> línea existe y contiene el fragmento anotado en [`citas.tsv`](./citas.tsv). Que
> la línea haga lo que dice la nota hay que confirmarlo a mano. Los números de
> línea envejecen; los nombres de función y de archivo son lo estable.

## El prompt que las produjo

```
Solo explorar, sin editar nada. En tmux quiero un comando nuevo que abra un pane
con una sesión SSH hecha con libssh, sin ejecutar el binario ssh, y solo en Linux.
Trazá cómo split-window lanza el proceso de un pane nuevo, desde la tabla de
comandos hasta el fork/exec, y cómo el servidor lee la salida de ese pane.
Mostrame cómo aísla tmux el código de una plataforma (compat/, osdep-*, configure.ac,
Makefile.am) y buscá un feature opcional que ya tenga ese mismo patrón. Devolveme
módulos tocados, interfaces reusadas y riesgos. Cada afirmación con archivo:línea.
```

Igual que en el ejemplo guiado de `fzf`, se usa un comando existente
(`split-window`) como guía para trazar el camino, y se exige `archivo:línea` para
cada afirmación.

## El terreno

En el commit fijado, `tmux` tiene 153 archivos `.c` y unas **106.000 líneas** de C y
headers en la raíz, más ~7.000 en `compat/`. Es casi el doble de las "~60k" que
dice la consigna: el repo creció. Para este cambio alcanza con entender **un
camino**:

```
tmux split-window -t %1
        │
        ▼
cmd.c                 cmd_table[] → cmd_find() resuelve el nombre (o un prefijo)
        │
        ▼
cmd-split-window.c    cmd_split_window_exec(): arma un struct spawn_context
        │
        ▼
spawn.c               spawn_pane(): crea el pane, fdforkpty(), y en el hijo exec
        │                    ├── padre: window_pane_set_event(wp)  → event loop
        │                    └── hijo:  execvp / execl($SHELL)     → el proceso
        ▼
window.c              bufferevent sobre wp->fd (el master del PTY) → input_parse_pane()
server.c              SIGCHLD → server_child_exited() → el pane muere
```

## Hallazgos

### 1 · La tabla de comandos y cómo se resuelve un nombre

`cmd.c:123` declara `const struct cmd_entry *cmd_table[]`, un arreglo plano con un
puntero por comando, terminado en `NULL`. Cada comando vive en su `cmd-*.c` y
exporta un `struct cmd_entry` con `name`, `alias`, el string de getopt (`args`), la
`usage`, el tipo de target y la función `exec`. El de `split-window` está en
`cmd-split-window.c:58`. El mismo archivo declara también `new-pane`
(`cmd-split-window.c:39`), así que dos comandos comparten la misma `exec`.

**`cmd_find()` (`cmd.c:462`) acepta prefijos.** Un alias tiene que coincidir
exacto. Un nombre, en cambio, coincide con cualquier prefijo que no sea ambiguo:
`tmux split` resuelve a `split-window`. Si hay más de un candidato, el error es
`ambiguous command: %s, could be: …` (`cmd.c:506`). Si no hay ninguno, es
`unknown command: %s` (`cmd.c:489`).

**Esto convierte un comando nuevo en un riesgo de regresión para los que ya
existen.** Si se agregara `split-ssh`, `tmux split` pasaría a ser ambiguo y dejaría
de andar en los scripts y configuraciones que hoy lo usan. Se midió la
resolución de cada prefijo de cada nombre y alias (1.513 prefijos de 170
nombres, ver [`scripts/snapshot-comandos.sh`](./scripts/snapshot-comandos.sh)):

- `s` ya es ambiguo hoy: tiene 27 candidatos.
- **Ningún nombre ni alias empieza con `ss`.**
- `sp` resuelve hoy a `split-window`.

Un nombre que empiece con `ss` no le cambia la resolución a ningún prefijo
existente. Un alias como `sp` o `sw` sí la cambiaría.

La tabla tiene dos consumidores más, que se enteran solos de un comando nuevo:
`list-commands` (`cmd-list-commands.c:94` llama a `cmd_find`) y el completado del
prompt de comandos (`prompt.c:1568`, que recorre `cmd_table`). Esto no es
regresión, pero es comportamiento visible que la spec tiene que declarar.

Hoy **no hay ningún `#ifdef` dentro de `cmd_table`**. Sería el primero.

### 2 · El camino de spawn, de `split-window` a `fork`

`cmd_split_window_exec()` arma un `struct spawn_context` en la pila: copia los
argumentos con `args_to_vector` (`cmd-split-window.c:195`), le pasa la celda de
layout y los flags, y llama a `spawn_pane` (`cmd-split-window.c:208`). Si falla,
el error al cliente es `create pane failed: <cause>`. `respawn-pane` reusa la
misma función con `SPAWN_RESPAWN` (`cmd-respawn-pane.c:83`).

`struct spawn_context` (`tmux.h:2500`) tiene el item de la cola, la sesión, el
winlink, `argc`/`argv`, el entorno, el cwd y un campo `flags`. El último flag
definido es `SPAWN_FLOATOVERZOOM 0x1000` (`tmux.h:2531`).

`spawn_pane()` (`spawn.c:243`) hace, en orden:

1. Resuelve el cwd y crea o reasigna el pane y su celda de layout.
2. Si `argc == 0`, usa la opción `default-command` como comando
   (`spawn.c:380`). Pero `default-command` vale `""` por defecto
   (`options-table.c:790`), y en ese caso `argc` queda en 0 (`spawn.c:385-386`) y el
   hijo arranca una shell de login (`spawn.c:574`). Un pane creado sin comando,
   con la configuración por defecto, no guarda nada en `wp->argv`.
3. Arma el entorno del hijo (`TMUX_PANE`, `PATH`, `SHELL`) y calcula el tamaño de
   la ventana.
4. Bloquea **todas** las señales (`spawn.c:456`). Si el pane es `SPAWN_EMPTY`, no
   hace fork (`spawn.c:459`).
5. **`fdforkpty()`** (`spawn.c:478`) crea el PTY y el proceso hijo de una sola
   vez. El padre se queda con el master en `new_wp->fd`.
6. **En el hijo:** el bloque de systemd (`spawn.c:504`, ver hallazgo 4), ajusta
   termios, `proc_clear_signals(server_proc, 1)` (`spawn.c:540`) y
   `closefrom(STDERR_FILENO + 1)` (`spawn.c:541`). Después de eso solo quedan
   abiertos 0, 1 y 2, que son el esclavo del PTY. Sigue `environ_push(child)`
   (`spawn.c:544`), que deja el entorno del pane como entorno del proceso.
   Recién ahí viene el `exec`: `execvp` si hay varios argumentos (`spawn.c:552`),
   o `$SHELL -c` si hay uno (`spawn.c:567`).
7. **En el padre:** `window_pane_set_event(new_wp)` (`spawn.c:590`).

**El punto de enganche natural es el hijo, entre `environ_push` y el `exec`.** En
ese punto el proceso ya tiene el PTY como stdin/stdout/stderr, el entorno del pane,
ningún otro descriptor del servidor y las señales por defecto. Un cliente SSH
que corra ahí y nunca haga `exec` cumple "sin invocar `ssh`". Para el servidor,
es un proceso más detrás del PTY.

`job.c:116` (usado por `run-shell` e `if-shell`) es el otro llamador de
`fdforkpty`, y no tiene nada que ver con este cambio.

### 3 · El event loop no se entera de qué proceso hay detrás del PTY

Del lado del servidor, un pane es un descriptor:

- `window_pane_set_event()` (`window.c:1673`) crea un `bufferevent` de libevent
  sobre `wp->fd` (`window.c:1677`).
- `window_pane_read_callback()` (`window.c:1632`) le pasa los bytes al parser de
  terminal, `input_parse_pane()` (`input.c:1028`).
- `window_pane_error_callback()` (`window.c:1660`) marca el pane como
  `PANE_EXITED` cuando el descriptor da error o EOF.
- El resize es `ioctl(wp->fd, TIOCSWINSZ, …)` en `window_pane_send_resize()`
  (`window.c:597`, `window.c:612`). El kernel le manda `SIGWINCH` al grupo de
  procesos en primer plano del esclavo.
- La muerte del hijo llega por `SIGCHLD`: `server_child_signal()` (`server.c:468`)
  hace `waitpid`, y `server_child_exited()` (`server.c:491`) busca el pane por
  `wp->pid == pid` (`server.c:498`) y guarda el `status`. Ese status se ve como
  `#{pane_dead_status}` si el pane queda vivo con `remain-on-exit`.
- Cerrar un pane (`window_pane_destroy`) cierra el master. El kernel le manda
  `SIGHUP` al líder de sesión del esclavo, que es el hijo.

**Conclusión: si el cliente SSH corre en el hijo, el servidor y el event loop no
cambian en nada.** Leer, escribir, cambiar el tamaño y la muerte del pane ya
funcionan por el PTY, igual que con una shell. La alternativa —correr libssh
dentro del servidor, con su descriptor registrado en libevent— obliga a tener un
pane sin PTY. Eso cambia el significado de `wp->fd` y `wp->pid`, y el resize por
`ioctl` deja de aplicar. Además, libssh tiene modo no bloqueante, pero `ssh_connect` resuelve
el nombre con `getaddrinfo`, que bloquea siempre (hallazgo 7). El resto del
handshake habría que reescribirlo como máquina de estados. Un error ahí congela
el servidor para todos los clientes. Viola el
invariante de "el modelo de PTY/panes no cambia".

### 4 · Cómo aísla tmux lo específico de una plataforma

Son tres capas, y conviene no confundirlas:

| Capa | Qué resuelve | Dónde |
|---|---|---|
| `osdep-<plataforma>.c` | Una implementación por SO de lo mismo (nombre y cwd del proceso de un pane, event base). Se elige por `PLATFORM` | `Makefile.am:235` (`osdep-@PLATFORM@.c`) |
| `compat/` + `compat.h` | Reemplazos de funciones que a la libc local le faltan (`strlcpy`, `fdforkpty`, `imsg`…) y **features opcionales** | `compat/fdforkpty.c:30`; `compat.h:444` |
| `configure.ac` → `#define` + `AM_CONDITIONAL` | Prender o apagar features en tiempo de build | ver abajo |

**Hay un precedente que es casi exactamente este cambio: systemd.** Es un feature
**solo de Linux**:

- Es opcional, con `--enable-systemd` (`configure.ac:501`).
- Lo busca `PKG_CHECK_MODULES`, define `HAVE_SYSTEMD` y un `AM_CONDITIONAL`
  (`configure.ac:527`).
- Suma un archivo fuente solo si está prendido (`Makefile.am:243`).
- Declara su función en `compat.h` bajo `#ifdef HAVE_SYSTEMD` (`compat.h:444`,
  `compat.h:448`).
- **Corre en el hijo del spawn**, entre `fdforkpty` y el `exec`, guardado por
  `#if defined(HAVE_SYSTEMD) && defined(ENABLE_CGROUPS)` (`spawn.c:504`).

Que el trabajo vaya en el hijo no es casual. El commit `f0a85d04` (2025-04-14)
movió ahí los requests de cgroup "para evitar una carrera" cuando el proceso
hijo hace fork rápido. El proyecto ya eligió el hijo del spawn como lugar para
lógica específica de Linux.

El segundo precedente es **sixel**:

- `--enable-sixel` (`configure.ac:544`) hace `AC_DEFINE(ENABLE_SIXEL)` y
  `AM_CONDITIONAL(ENABLE_SIXEL, …)` (`configure.ac:550`, `configure.ac:552`).
- En `Makefile.am`, `if ENABLE_SIXEL` agrega dos `.c` propios a
  `dist_tmux_SOURCES` (`Makefile.am:253`, `Makefile.am:254`).
- Está apagado por defecto, y el resumen final de `configure` lo informa.

Sixel es el modelo para "archivos nuevos que solo se compilan con el flag".
Systemd es el modelo para "código que corre en el hijo del spawn".

### 5 · ⚠ `PLATFORM` se calcula después de las opciones

`configure.ac` procesa todos los `--enable-*` alrededor de las líneas 25 a 552, pero
la plataforma recién se calcula en `configure.ac:1006` (`# Figure out the
platform.`). Ahí se asigna `PLATFORM=linux` (`configure.ac:1064`) y se define
`IS_LINUX` (`configure.ac:1122`). **Un chequeo `test "x$PLATFORM" = xlinux`
puesto junto a las otras opciones siempre da falso**, porque la variable todavía
está vacía. Lo que el propio archivo hace para rechazar un flag en una
plataforma es preguntar por `$host_os`, que existe desde `AC_CANONICAL_HOST`
(`configure.ac:10`). Ejemplo: `--enable-static` en macOS (`configure.ac:91`).

**Este es el hallazgo que un agente sin explorar se pierde.** Copiar el patrón de
systemd y agregar "solo si es Linux" con `$PLATFORM` compila en todos lados, pero
el guard nunca se activa.

Hoy `--enable-ssh` no existe: `./configure --enable-ssh` termina bien, con
`WARNING: unrecognized options: --enable-ssh`. Se verificó en Linux y en macOS.

### 6 · Las pistas de entorno: auth y nombre del proceso

- `update-environment` incluye por defecto `SSH_AUTH_SOCK` y `SSH_ASKPASS`
  (`options-table.c:1211`). El entorno del pane, que `environ_push` deja en el
  hijo, ya trae el socket del agente del cliente que se adjuntó más recientemente.
  libssh lo lee de `SSH_AUTH_SOCK` sin configuración extra.
- `osdep_get_name()` en Linux (`osdep-linux.c:30`) da el nombre del proceso del
  pane leyendo `/proc/<pgrp>/cmdline` (`osdep-linux.c:41`). El hijo es un fork del
  servidor y no hace `exec`, así que su `cmdline` es la del servidor: el pane va
  a mostrar `#{pane_current_command}` = `tmux`. Con `automatic-rename`
  (`options-table.c:1304`, prendido por defecto), la ventana pasa a llamarse
  `tmux`. `prctl(PR_SET_NAME)` no lo arregla, porque cambia `comm` y no
  `cmdline`.
- `remain-on-exit` acepta `off`, `on`, `failed`, `key` y `failed-key`
  (`options-table.c:95`, `options-table.c:1669`). Es la forma que ya existe de
  ver el mensaje y el exit status de un pane que murió.

### 7 · libssh, no OpenSSH (lo que hay que saber de la librería)

OpenSSH no se distribuye como librería de cliente: usarlo implica ejecutar el
binario `ssh`, que es justo lo que la consigna excluye. Hay dos librerías:

- **libssh**: LGPL-2.1. Ubuntu 24.04 trae la 0.10.6, la máquina de desarrollo
  (Homebrew) la 0.12.2.
- **libssh2**: BSD-3. También lee `known_hosts` en formato OpenSSH
  (`libssh2_knownhost_readfile` con `LIBSSH2_KNOWNHOST_FILE_OPENSSH`). La
  diferencia está en el nivel de la API:
  - con libssh2, el agente (`libssh2_agent_*`), las claves por defecto y la
    clasificación de la host key hay que armarlos a mano;
  - libssh trae `ssh_userauth_agent` y `ssh_userauth_publickey_auto`, y un
    `ssh_session_is_known_server` que ya distingue entre conocida, cambiada, de
    otro tipo y desconocida.
  La comparación sigue en la spec (D-3).

Dos cosas de libssh que cambian el diseño (verificadas en su repo y en su
[documentación](https://api.libssh.org/stable/group__libssh__session.html)):

- **libssh procesa `~/.ssh/config` y `/etc/ssh/ssh_config` por su cuenta** en
  `ssh_connect()`, salvo que se lo apague con `SSH_OPTIONS_PROCESS_CONFIG`. Esa
  opción existe desde **libssh 0.9.0** (commit `b7fefb05`, 2018). Un
  `ProxyCommand` en esa config ejecuta un comando por shell. Con
  `OPENSSH_PROXYJUMP=1` en el entorno, un `ProxyJump` delega en **el binario de
  OpenSSH**. Si se deja la config prendida, el comando nuevo puede terminar
  invocando `ssh` sin que nadie lo haya pedido.
- La verificación de `known_hosts` con `ssh_session_is_known_server()` existe
  desde **libssh 0.8.0**. Por defecto consulta `~/.ssh/known_hosts` **y**
  `/etc/ssh/ssh_known_hosts` (`SSH_OPTIONS_GLOBAL_KNOWNHOSTS`). Con un puerto
  que no es el 22, busca el host como `[host]:puerto`, igual que OpenSSH.
- `ssh_connect()` resuelve el nombre con `getaddrinfo`, que es bloqueante aunque
  la sesión esté en modo no bloqueante.
- Al negociar, libssh pone primero los tipos de host key que encuentra en
  `known_hosts` para ese host, y **después agrega los demás que soporta**
  (`ssh_client_select_hostkeys`, `src/kex.c` de libssh). Si el servidor solo
  ofrece un tipo que no está en `known_hosts`, se negocia ese tipo igual, y la
  verificación da "de otro tipo".
- Un `known_hosts` que no se puede abrir **no es un error** para libssh: lo
  trata como si no existiera (`src/knownhosts.c`, "The missing file is not an
  error here"). Las líneas de **otros** hosts se saltean sin parsearlas. Pero una
línea **del host** que no se puede parsear corta la lectura del archivo entero
(`goto error`).

### 8 · ⚠ Los helpers de layout leen letras de flag ajenas

Para reusar el layout de `split-window` hay que llamar a
`layout_get_tiled_cell()` (`layout.c:1640`), que recibe el `struct args` **entero**
del comando que la llama. Adentro lee `-l` y **`-p`** (`layout.c:1657`): `-p` es
un porcentaje, y se interpreta con `args_strtonum_and_expand(args, 'p', 0, 100, …)`
(`layout.c:1674`). Si se cae afuera del rango, el error es `invalid tiled geometry
…` (`layout.c:1681`). La versión flotante, `layout_get_floating_cell()`
(`layout.c:1698`), lee `-x`, `-X`, `-y` e `-Y`.

**Si el comando nuevo usara `-p` para el puerto, como `ssh(1)`, `ssh-pane -p 22`
pediría un pane de 22 % de alto, y `-p 2222` fallaría con `invalid tiled
geometry`.** Las letras `l p x X y Y` están tomadas por el layout. Si no hay
lugar, el error es `no space for a new pane` (`layout.c:1692`). Un target que no
existe da `can't find pane: %s` (`cmd-find.c:1272`).

El hijo del spawn también hace `log_close()` (`spawn.c:543`) antes del
`environ_push`. Lo que corra ahí no escribe en el log de `tmux -v`.

## Módulos tocados (propuesta, para la spec)

| Archivo | Por qué |
|---|---|
| `configure.ac` | `--enable-ssh`, que se rechaza si `$host_os` no es Linux y busca `libssh >= 0.9.0` por pkg-config |
| `Makefile.am` | `if ENABLE_SSH` suma los dos `.c` nuevos, igual que sixel |
| `cmd.c` | Declaración `extern` y entrada en `cmd_table`, bajo `#ifdef ENABLE_SSH` |
| `cmd-ssh-pane.c` (nuevo) | El `cmd_entry` y su `exec`. Arma el `spawn_context` como `split-window`, salvo el `argv`: no guarda el destino como comando (spec, D-11) |
| `ssh-pane.c` (nuevo) | El cliente libssh que corre en el hijo |
| `spawn.c` | Un bloque `#ifdef ENABLE_SSH` en el hijo, después de `environ_push`, que entra al cliente y nunca vuelve |
| `tmux.h` | Un flag `SPAWN_SSH` y un puntero opcional en `spawn_context`, más los prototipos |
| `tmux.1` | La entrada del comando, que dice que solo existe en Linux con `--enable-ssh` |
| `regress/ssh-pane-*.sh` (nuevos) | Tests que se saltean solos si el comando no existe |

## Interfaces reusadas

| Interfaz | Dónde | Cómo se usa |
|---|---|---|
| `struct cmd_entry` / `cmd_table` | `cmd.c:123` | Una entrada nueva |
| `struct spawn_context` + `spawn_pane()` | `tmux.h:2500`, `tmux.h:4196`, `spawn.c:243` | Mismo layout, cwd, entorno y PTY que `split-window` |
| `fdforkpty()` | `spawn.c:478` | Sin cambios: el PTY lo sigue creando tmux |
| Hijo del spawn con un `#if` de plataforma | `spawn.c:504` (systemd) | Mismo patrón, otro `#ifdef` |
| `bufferevent` del pane y `SIGCHLD` | `window.c:1673`, `server.c:491` | Sin cambios |
| Resize por `TIOCSWINSZ` | `window.c:612` | Sin cambios. El hijo recibe `SIGWINCH` y lo reenvía como `window-change` |
| `remain-on-exit` / `#{pane_dead_status}` | `options-table.c:1669` | Para ver el error y el exit status |
| Patrón `AC_ARG_ENABLE` + `AM_CONDITIONAL` | `configure.ac:544-552`, `Makefile.am:253-254` | Copiado de sixel |

## Riesgos

| Riesgo | Por qué |
|---|---|
| **Un comando nuevo rompe abreviaturas existentes** | `cmd_find` acepta prefijos (`cmd.c:462`). Un nombre o alias mal elegido vuelve ambiguo, o le roba, un prefijo que hoy anda (hallazgo 1) |
| **Una letra de flag que el layout interpreta** | `-p` y `-l` las lee `layout_get_tiled_cell` como tamaño (`layout.c:1657`). `-p` como puerto rompe el split (hallazgo 8) |
| **Guard de plataforma que nunca se activa** | `$PLATFORM` todavía está vacío cuando se procesan las opciones (hallazgo 5) |
| **El build no-Linux cambia** | Cualquier símbolo nuevo fuera de `#ifdef ENABLE_SSH`, o un `.c` que se compile siempre, toca macOS y los BSD |
| **Bloquear el servidor** | Cualquier llamada de libssh hecha en el proceso del servidor congela a todos los clientes (hallazgo 3) |
| **Invocar `ssh` por la puerta de atrás** | Si libssh procesa la config, un `ProxyCommand` o `ProxyJump` puede ejecutar shell o el binario de OpenSSH (hallazgo 7) |
| **El hijo hereda la memoria del servidor** | Es un fork sin `exec`: conserva la imagen del servidor (buffers de pegado, historia). No hay descriptores (`closefrom`), pero la memoria sí. Un crash de libssh mata solo al hijo; un core dump del hijo contiene esa memoria. Y en vivo: un bug explotable de libssh, disparado por un servidor hostil, puede leer la historia de todos los panes. La spec acepta este costo en D-17 |
| **Nombre del proceso** | `#{pane_current_command}` va a decir `tmux`, y `automatic-rename` renombra la ventana (hallazgo 6) |
| **Configs compartidas entre máquinas** | Un `.tmux.conf` con `ssh-pane` da `unknown command` en macOS o BSD, o en un Linux compilado sin el flag |
| **Upstream es OpenBSD** | 130 commits de merge de `tmux-openbsd/master` (`git log --merges`). `cmd.c`, `spawn.c` y `tmux.h` se comparten con el árbol de OpenBSD, que no tiene `configure`. Un `#ifdef ENABLE_SSH` ahí queda siempre apagado en OpenBSD, que es lo correcto, pero aumenta la superficie de conflicto de cada merge |

## Línea de base de regresión (medida antes de tocar nada)

Comandos del propio repo (`.github/workflows/regress.yml`):
`sh autogen.sh && ./configure … && make`, y después `cd regress && make`.

| Plataforma | Build | `regress/` | Notas |
|---|---|---|---|
| Linux: Ubuntu 24.04 aarch64 en Docker, `--enable-utf8proc` | ✅ `make` exit 0 | **170 PASS, 2 FAIL** (corrida paralela, contenedor **sin** `python3`) | `input-requests.sh` falla porque necesita `python3`; con `python3` pasa 5/5. `prompt-words-history.sh` falla 5/5 en este entorno (`got 'show-r', expected 'history-command'`) |
| macOS (arm64), `--disable-jemalloc` | ✅ `make` exit 0 | **165 PASS, 7 FAIL** (4 determinísticas, 3 flaky en paralelo) | `configure` sin flag de jemalloc **falla** en macOS (`configure.ac:1055`). Con `/usr/bin/make` (GNU Make 3.81), `regress/` **corre cero tests y sale 0**: `TESTS!= echo *.sh` (`regress/Makefile:1`) necesita GNU Make ≥ 4. Por eso el CI usa `gmake` |

Las fallas preexistentes **no son regresiones de este cambio**. Lo que se
compara al cerrar es el mismo conjunto de fallas, no "todo verde". El detalle de
cada corrida está en [`linea-de-base.md`](./linea-de-base.md).

## Lo que NO hace falta entender

El parser de terminal (`input.c`, salvo saber que existe), `screen*.c`, `grid*.c`,
`tty*.c`, los modos (`window-*.c`), el layout (`layout*.c`, se reusa sin tocar),
control mode (`control*.c`), popups y menús, `job.c`, y las ~100.000 líneas que no
están en el camino del hallazgo 2.

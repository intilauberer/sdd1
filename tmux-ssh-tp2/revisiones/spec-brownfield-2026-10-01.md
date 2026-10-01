# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux) — (tmux-ssh-tp2/spec-brownfield.md)
- Commit: tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` (verificado en /tmp/tmux, árbol limpio) · TP: `tmux-ssh-tp2/` sin commitear sobre `cc123c2` (untracked: la spec revisada no tiene hash propio) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 37 BR: 4 NFR: 3 VC: 47 (44 VCs en bloque `> **VC-n**` + VC-45…47 en la tabla de §6.7; INV: 7). `grep -cE '^#+ .*FR-[0-9]+'` da 0 porque los FR van en negrita, no en encabezado; se contó con `^\*\*FR-[0-9]+ ·`. VC (47) ≥ FR+BR (41): sin sospecha de huérfanos.

## Resumen

La spec es sólida en lo que la cátedra anunció que mira: alcance por path, límite solo-Linux con matriz plataforma × flag, siete invariantes con comando, línea de base medida, VC end-to-end contra un `sshd` real y las seis decisiones de la consigna con alternativa descartada. `check-citas.py` pasa (109/109) y las ocho citas abiertas a mano dicen lo que las notas afirman. Lo que bloquea: (1) la tabla "Dentro" instruye poner `AM_CONDITIONAL(ENABLE_SSH)` dentro del `if`, lo que rompe `configure` en todo build sin `--enable-ssh`, macOS incluido (B9); (2) el flag `-v` está en la sinopsis y no tiene FR (1.5); (3) D-11 (respawn) contradice la instrucción "armar el `spawn_context` igual que `cmd-split-window.c:195-208`", y junto con D-12/D-5/D-3 es comportamiento observable que vive solo en la tabla de decisiones (2.8); (4) FR-22 y FR-23 no son atómicos (2.3); (5) VC-31/32/34 no pueden pasar con la definición de "texto del pane", porque los mensajes de 92-96 columnas se cortan en un pane de 80 (3.2); (6) VC-9 no discrimina porque el `sshd` de §9 también escucha en el 22 (3.5); (7) faltan caminos de falla de `known_hosts` ilegible, clave corrupta o con passphrase, agente muerto, PTY/shell rechazados, KEX fallido y pérdida silenciosa del peer (3.3); (8) el motivo para descartar libssh2 es falso (5.3); (9) las notas piden declarar el completado del prompt y la spec no lo hace (5.6).

M3: 0 hits que cuenten. `spec-brownfield.md:64, 126, 417, 629, 637, 639, 688, 689` son "todo/todos/Todo" en castellano. · M4: 2 hits, ninguno cuenta. `:162` "sin libssh suficiente" es el título de FR-3, y el Dado lo acota a `>= 0.9.0`. `:643` "en cualquier red razonable" está en el fundamento de D-10, no en un FR/NFR/VC (se registra en 5.3). · M5: cuentan `:525` BR-3 "`SSH_OPTIONS_PROCESS_CONFIG = false`" y `:588` NFR-3 "`SSH_LOG_NOLOG`", que atan el requisito a la API de libssh (ver 5.x, Suggestion), y `:228` FR-8 "porque se reusa `layout_get_tiled_cell()`" (justificación de implementación dentro del FR). No cuentan: `:436` iptables, `:491` `ss -K`, `:519` strace y `:667` docker, que son herramientas del VC, no del sistema. · M6: cuentan `:172` FR-4 "en cualquier plataforma", que VC-4 solo prueba en macOS y Linux (ver B5); `:370` FR-23 "Cualquier destino que contenga `:`", con 2 casos en el VC (ver 2.3); `:509` BR-1 "Cualquier otro resultado termina en FR-31 a FR-34", cuando hay resultados de verificación (error de lectura de `known_hosts`) que no son ninguno de esos FRs (ver 3.3). No cuentan: `:24` (propósito), `:52` (tabla), `:299` y `:415` (prosa explicativa), `:506` (título de BR-1, cubierto por VC-38).

## Hallazgos por dimensión

### 1. Propósito y alcance — FAIL
- Issue (1.5) · spec-brownfield.md:185: "`ssh-pane [-dhv] [-i identity-file] [-l size] [-P port] [-t target-pane] destination`" y :189 "`"dhi:l:P:t:v"`". `-v` se acepta y no tiene FR, VC ni exclusión. En `split-window` es "vertical" (el default). La spec no dice si acá es un no-op, si es incompatible con `-h` (¿`-hv`?) o si es "verbose", como en `ssh(1)`. Dos implementaciones divergen.
- Warning (1.4) · spec-brownfield.md:698: "`ssh-pane.c` con un `ssh_pane_run()` que solo escribe `ssh-pane: not implemented` y devuelve 255". El plan especifica un comportamiento intermedio que ningún FR declara, y además es inconsistente: el bloque de `spawn.c` que llama a `ssh_pane_run()` recién entra en la Iteración 2 (:699). En la Iteración 1, `ssh-pane` crea un pane que corre `default-command` o el destino como comando local, no el "not implemented" que se describe.
- Suggestion (1.3) · spec-brownfield.md:27-35: la tabla de actores no tiene al kernel (entrega `SIGWINCH` en FR-13 y `SIGHUP` en FR-15, ver `window.c:612`) ni al resolvedor DNS (FR-28).
- 1.1, 1.2 y 1.6 sin hallazgos. El propósito (:17-25) dice por qué: hoy el pane depende de un binario y una config externos. "Fuera" tiene 9 ítems de comportamiento (:78-88) y 7 grupos por path. Las notas y la línea de base están enlazadas (:3-6).

### 2. Completitud y consistencia — FAIL
- Issue (2.3) · spec-brownfield.md:357-363, FR-22: "`T ssh-pane alice@` … Un destino `''` es la misma situación (host vacío) y da `invalid destination: `". Son dos entradas y dos stderr distintos en un solo FR, que VC-22 prueba con dos ejecuciones. Además, el literal termina en un espacio, que es invisible en la spec y frágil en el test. Hay que separarlo en dos FRs.
- Issue (2.3) · spec-brownfield.md:366-373, FR-23: "`T ssh-pane servidor:22` … Cualquier destino que contenga `:` da este error, incluidos los IPv6 literales". Tiene un Cuando concreto y le agrega una regla de clase. El stderr de `::1` nunca se escribe literal: ¿es `invalid destination: ::1 (use -P for the port)`? Para un IPv6 el sufijo "use -P for the port" es engañoso. Hay que separarlo y escribir el literal de `::1`.
- Issue (2.8) · spec-brownfield.md:644, D-11: "corre el `argv` guardado del pane, que es `default-command` (`spawn.c:380`)", contra :53 "arma el `spawn_context` igual que `cmd-split-window.c:195-208`". La línea 195 es `args_to_vector(args, &sc.argc, &sc.argv)`. Copiada tal cual, `sc.argc = 1` con `argv = {"alice@servidor"}`. En ese caso `spawn.c:380` no aplica (solo corre con `sc->argc == 0`), `spawn.c:401-404` guarda el destino en `wp->argv`, y `respawn-pane` termina corriendo `$SHELL -c alice@servidor`. La spec nunca dice que `sc.argc` tiene que ser 0. Además, el comportamiento de `respawn-pane` no tiene FR ni VC: vive solo en la tabla de decisiones.
- Issue (2.8) · spec-brownfield.md:645, D-12: "con `automatic-rename` … una ventana cuyo pane activo es un `ssh-pane` se llama `tmux`". Es comportamiento observable (`#{window_name}`) sin FR ni VC. FR-18 (:318) solo cubre `#{pane_current_command}`.
- Issue (2.8) · spec-brownfield.md:638, D-5: "**Primero el agente** … si no `~/.ssh/id_ed25519`, `id_ecdsa` e `id_rsa`, en ese orden". El orden, la lista y el uso de las claves por defecto sin agente no tienen FR ni VC. FR-10 prueba solo `-i`, y FR-35 (:481) remite a "las identidades de D-5". Queda sin decidir qué pasa con una `id_*` cifrada (¿se saltea en silencio?, ¿termina en FR-35?) y si con `-i` se ofrece igual el agente primero.
- Issue (2.8) · spec-brownfield.md:636, D-3: "Con `--enable-static` sí lo haría, así que esa combinación queda sin soporte en v1". "Sin soporte" no es observable: ¿`./configure --enable-static --enable-ssh` falla, con qué mensaje y qué exit? No hay FR. Además, la afirmación de licencia (LGPL con enlace estático) se da sin fuente.
- Issue (2.8) · spec-brownfield.md:643: "Un solo intento, con timeout de conexión de 10 s", y FR-30 (:438) "a los **10 s** del comando". No dice qué cubre el timeout: solo el `connect()` TCP, o también el banner, el KEX y la autenticación. Un `sshd` que acepta el TCP y nunca manda banner cuelga el pane para siempre en una implementación y da error a los 10 s en otra. Tampoco se decide si son 10 s por dirección resuelta o en total, ni si el reloj arranca con el comando o con el `connect()` (el DNS de FR-28 cae en el medio).
- Issue (2.8) · spec-brownfield.md:506-509, BR-1: "Solo se conecta si la verificación de libssh contra `known_hosts` da 'conocida y coincide'". libssh consulta también el `known_hosts` global (`/etc/ssh/ssh_known_hosts`, `SSH_OPTIONS_GLOBAL_KNOWNHOSTS`). La spec no decide si se usa. Si una clave está solo en el global, una implementación conecta y otra emite el mensaje de FR-31, que dice literalmente "is not in ~/.ssh/known_hosts" (:448).
- Warning (2.8) · spec-brownfield.md:138 y :544: "`~/.ssh/known_hosts`" y "`~/.ssh/id_ed25519`". No dice si `~` es el `$HOME` del entorno del pane o el `pw_dir` de `getpwuid()`. libssh usa su propio directorio SSH; si `$HOME` se cambió con `set-environment`, las implementaciones divergen.
- Warning (2.8) · spec-brownfield.md:232-237 y :444-449: con `-P 2222`, la entrada de OpenSSH en `known_hosts` es `[servidor]:2222`, no `servidor`. La spec no decide con cuál se busca ni qué nombre aparece en los mensajes de FR-31…34 ("host key for servidor" o "for [servidor]:2222").
- Warning (2.8) · spec-brownfield.md:52: "**entre `environ_push(child)` (`spawn.c:544`) y el `execvp` (`spawn.c:552`)**". El `execvp` de la línea 552 está dentro de `if (new_wp->argc != 0 && new_wp->argc != 1)` (`spawn.c:550`). "Entre 544 y 552" admite poner el bloque dentro de ese `if`, y entonces solo corre con `argc > 1`. Tiene que decir "inmediatamente después de `environ_push`, antes del `if` de `spawn.c:550`".
- Warning (2.7) · spec-brownfield.md:281: "Con `exit 0`, es `1 0`". VC-14 agrega una segunda situación que FR-14 (:278, "termina con `exit 7`") no menciona.
- Warning (2.7) · spec-brownfield.md:159-160: "y no se genera `Makefile`". FR-2 (:155-157) no lo exige.
- Warning (2.7) · spec-brownfield.md:203, :271, :288, :315, :425, :494: "dentro de 3 s", "Dentro de 1 s", "Dentro de 5 s", "Dentro de 2 s", "dentro de 5 s" (dos veces). Son cotas de latencia que ningún FR ni NFR enuncia y que solo existen en los VCs. O se suben a los FRs, o se declaran como timeout del test y no como requisito.
- Suggestion (2.7) · spec-brownfield.md:315: "`echo "V=$?"` en el remoto da `V=130`". FR-17 dice "termina el `sleep`", no con qué status.
- 2.1 sin hallazgos: 37/37 FRs tienen Dado/Cuando/Entonces.

### 3. Casos borde y verificabilidad — FAIL
- Issue (3.2) · spec-brownfield.md:134: "'Texto del pane' es `T capture-pane -p -t <pane>`", aplicado a :448 (96 columnas), :457 (la misma línea) y :475-476 (92 columnas). El servidor de prueba no fija tamaño, así que la ventana es `default-size` 80x24 (`options-table.c:802-806`), y con `-h` el pane mide ~40. `capture-pane -p` sin `-J` corta la línea en dos, y "el texto contiene la línea literal" (VC-31, VC-32 y VC-34) falla aunque la implementación sea correcta. Hay que fijar el tamaño de ventana en las convenciones y usar `capture-pane -pJ`.
- Issue (3.3) · Faltan caminos de falla obligatorios de recursos externos que la spec misma nombra. Ninguno tiene FR ni VC:
  - `known_hosts` existe pero es ilegible (modo 000) o tiene una línea corrupta. libssh devuelve `SSH_KNOWN_HOSTS_ERROR`, que no es ninguno de FR-31…34, y eso contradice el "Cualquier otro resultado" de :509.
  - La clave de `-i` existe y es legible, pero no es una clave privada, o está cifrada con passphrase. FR-25 (:385-389) solo cubre "no se puede abrir".
  - `SSH_AUTH_SOCK` apunta a un socket muerto, o el agente rechaza la firma.
  - El `sshd` acepta la autenticación pero rechaza el PTY o la shell (`PermitTTY no`, `ForceCommand` que sale enseguida, canal rechazado).
  - KEX o versión fallida: el puerto responde pero no es SSH, o no hay algoritmos en común.
  - Pérdida silenciosa del peer, sin RST. FR-36 (:491) solo prueba `ss -K`, que genera un RST. Sin keepalive, que no está decidido (4.4), el pane queda vivo para siempre.
  - `spawn_pane()` falla (`create pane failed: …`, `cmd-split-window.c:208-209`): ¿es síncrono como §6.3?
- Issue (3.5) · spec-brownfield.md:233: "con un `sshd` que escucha **solo** en el 2222", contra :658-659 "`sshd` en los puertos 22 y 2222". El entorno de §9 contradice el Dado. Con el 22 abierto, una implementación que ignora `-P` y conecta al 22 pasa VC-9 (:237). El VC no discrimina.
- Warning (3.2) · spec-brownfield.md:382-383: "Con `-P 1` y `-P 65535`, en cambio, **no** aparece este error". Es una observación negativa. No dice qué se ve (¿pane creado, `1 255`, mensaje de FR-29 con `port 1`?) ni el exit del cliente.
- Warning (3.2) · spec-brownfield.md:528-536, VC-40: "`User mallory`". VC-5 usa `alice@servidor`, con usuario explícito, que le gana a cualquier `User` de config también en libssh. Esa línea del fixture no prueba nada. Para discriminar, la corrida tiene que ser `T ssh-pane servidor` (el camino de FR-11).
- Warning (3.2) · spec-brownfield.md:302-306, VC-16: "`/tmp/fixture.bin` … `cat /tmp/fixture.bin`" se ejecuta en el remoto, y `/tmp/out` se escribe en el cliente. §9 (:660) lista el fixture sin decir en qué contenedor está.
- Warning (3.2) · spec-brownfield.md:159 y :168: "exit ≠ 0". `AC_MSG_ERROR` sale con 1 por defecto: hay que fijarlo.
- Warning (3.4) · spec-brownfield.md:187: "`destination` es `[user@]host`". No decide `a@b@c`: ¿se parte en el primer `@` o en el último, como `ssh(1)`? Tampoco dice qué pasa con un host con espacios, que empieza con `-` o con caracteres no ASCII/IDN (codificación).
- Warning (3.4) · spec-brownfield.md:189: "con exactamente un argumento posicional". Con dos posicionales el error es `command ssh-pane: too many arguments (need at most 1)` (`arguments.c:338-342`, `cmd.c:534`), y no tiene FR ni VC. Tampoco hay VC de que `-p` (la decisión D-8, :190) se rechaza con `command ssh-pane: unknown flag -p` y no abre un pane del 22 %.
- Warning (3.5) · spec-brownfield.md:225: "con `%0` de 40 filas". La ventana por defecto es 80x24 y la spec no dice cómo se llega a 40. El test tiene que inventar `resize-window -y 41` o `-x/-y` en `new-session`.
- Suggestion (3.2) · spec-brownfield.md:400: "El stderr exacto y exit 1". VC-26 omite la comparación de cantidad de panes que :339-340 exige a toda la sección.
- Suggestion (3.4) · spec-brownfield.md:224-230: no hay VC de los bordes de `-l` (`-l 0`, `-l` mayor que el pane, `-l abc` → `invalid tiled geometry …`, `layout.c:1681`). Se heredan de `split-window`, pero conviene un VC que lo fije.
- 3.1 sin hallazgos: los 44 FR/BR/NFR tienen VC debajo y en la tabla de §7, y los 7 INV tienen VC-45…47. 3.6 sin hallazgos: VC-5 (:199) está declarado end-to-end contra el `sshd` real de §9 (:649-651).

**Ejercicio 3.5.** Feliz, FR-9:

```sh
# entorno: §9; servidor con sshd SOLO en 2222 (decisión: hay que apagar el 22, §9 lo contradice)
T new-session -d -x 80 -y 24        # decisión: tamaño no especificado
T set -g remain-on-exit on
antes=$(T list-panes -a -F '#{pane_id}')
T ssh-pane -P 2222 alice@servidor; test $? -eq 0
nuevo=$(comm -13 <(echo "$antes"|sort) <(T list-panes -a -F '#{pane_id}'|sort))
T send-keys -t "$nuevo" 'echo "R=$(hostname):$(id -un):$(tty)"' Enter
# esperar ≤ 3 s (decisión: ¿desde el ssh-pane o desde el send-keys?)
T capture-pane -pJ -t "$nuevo" | grep -q 'R=servidor:alice:/dev/pts/'
```

Decisiones que tuve que tomar: apagar el 22 (contradice :658); la entrada de `known_hosts` es `[servidor]:2222` o `servidor` (2.8); `-t` ausente es el pane actual (FR-9 dice "como en FR-5", que usa `-t %0`); desde cuándo corren los 3 s; que el `hostname` del contenedor sea `servidor` (§9 no lo fija).

Falla, FR-31:

```sh
: > ~/.ssh/known_hosts               # existe, sin entrada para servidor
# decisión: /etc/ssh/ssh_known_hosts del cliente vacío o ausente (BR-1 no lo dice)
T ssh-pane alice@servidor; test $? -eq 0
# esperar ¿cuánto? VC-31 no da cota → elegí 5 s
test "$(T display -p -t "$nuevo" '#{pane_dead} #{pane_dead_status}')" = "1 255"
T capture-pane -pJ -t "$nuevo" | grep -qF 'ssh-pane: host key for servidor is not in ~/.ssh/known_hosts; connect once with ssh(1) to add it'
# log sshd: correlacionar "esa conexión" por puerto origen del cliente (¿cómo lo obtengo? no especificado)
```

Decisiones que tuve que tomar: usar `-J`, porque sin él falla (Issue 3.2); qué hacer con el `known_hosts` global; la cota de tiempo, porque VC-31 no tiene; cómo identificar "esa conexión" en el log de `sshd` (:451-452) sin conocer el puerto origen; si `~` es `$HOME`.

### 4. Requerimientos no funcionales — WARN
- Warning (4.3) · spec-brownfield.md:588: "libssh no escribe log (su verbosidad queda en `SSH_LOG_NOLOG`)", con VC-44 (:593-594) "no se crea ningún log con el PID del hijo". El log de libssh no va a un archivo: va a stderr, que es el PTY. Un hijo con verbosidad alta lo escribe en el pane, y VC-44 no lo ve. Falta mirar `capture-pane` en VC-5/VC-35 y comprobar que no hay líneas de libssh.
- Warning (4.5) · notas-exploracion.md:315: "Un crash de libssh mata solo al hijo; un core dump del hijo contiene esa memoria". Es un riesgo de seguridad declarado en las notas que la spec no trata. Ningún NFR o BR fija `RLIMIT_CORE`/`PR_SET_DUMPABLE` ni acepta el riesgo explícitamente. NFR-3 (:583) solo mira los logs.
- Warning (4.4) · spec-brownfield.md:643: no hay política de keepalive o detección de peer muerto (ver 3.3). Está decidido que no hay reintentos, pero falta "cuántos keepalives, cada cuánto, o ninguno".
- Suggestion (4.2) · spec-brownfield.md:566-578: el cuello de botella de NFR-2 es probablemente `input_parse_pane` del servidor (`input.c:1028`), igual para los dos brazos. El cociente ≤ 1,25 puede no discriminar una implementación con lecturas chicas. Conviene medir también el CPU del hijo o un umbral absoluto.
- Suggestion (4.5) · No hay requisito de costo/recursos: cada `ssh-pane` es un fork sin `exec` de la imagen del servidor (COW). No hace falta un número, pero sí declararlo.
- 4.1 sin hallazgos: NFR-1 (:556-559) y NFR-2 (:566-578) tienen métrica, número y condición de carga en el enunciado. 4.4: no hay umbrales provisorios.

### 5. Tecnología y fundamento — FAIL
- Issue (5.3) · spec-brownfield.md:636: "libssh2: es BSD, pero no tiene la API de `known_hosts` en formato OpenSSH que BR-1 necesita" (lo mismo en notas-exploracion.md:243). Es falso: libssh2 tiene `libssh2_knownhost_readfile(…, LIBSSH2_KNOWNHOST_FILE_OPENSSH)` y `libssh2_knownhost_checkp()`. El descarte de la alternativa principal está mal fundado. Hay que rehacerlo con un motivo verificable o reconocer que la diferencia es otra.
- Issue (5.6) · notas-exploracion.md:87-89: "el completado del prompt de comandos (`prompt.c:1568`, que recorre `cmd_table`). Esto no es regresión, pero es comportamiento visible que la spec tiene que declarar". La spec no lo declara (cero hits de "prompt.c" o "complet" con ese sentido). Las notas describen un comportamiento observable que la spec omite.
- Warning (5.6) · Derivado de `cmd.c:493-506` y verificado en el código: `tmux s` hoy da `ambiguous command: s, could be: <27 nombres>` y con el cambio da 28, con `ssh-pane`. El stderr de un comando existente cambia. INV-3 (:118) no lo detecta, porque `snapshot-comandos.sh` colapsa todo error a `ERR`. Hay que declararlo como cambio aceptado, o la invariante es más débil de lo que dice.
- Warning (5.3) · spec-brownfield.md:637: "libssh no bloqueante dentro de libevent: el handshake y la autenticación bloquean". libssh tiene modo no bloqueante (`ssh_set_blocking(0)`, con `SSH_AGAIN` en `ssh_connect` y `ssh_userauth_*`). Los otros motivos (sin PTY, crash del servidor) se sostienen, pero este es inexacto. Lo mismo en notas-exploracion.md:160.
- Warning (5.3) · spec-brownfield.md:643: "alcanzan para el handshake TCP en cualquier red razonable". El fundamento de los 10 s es vago (M4). Hace falta un dato: el default de `ConnectTimeout` (no hay, usa el del SO), el de libssh, o un RTT de referencia.
- Warning (5.1) · spec-brownfield.md:652-659: los VCs usan `iptables` (:436), `ss -K` (:491) y `strace -p` (:519). Eso requiere `CAP_NET_ADMIN` en `servidor` y `CAP_SYS_PTRACE` (o `ptrace_scope=0`) en `cliente`. §9 no nombra los privilegios del entorno de verificación.
- Suggestion (5.3) · spec-brownfield.md:639, D-6: no considera la alternativa de hacer el chequeo después de `configure.ac:1006`, donde ya existe `PLATFORM` y el `AM_CONDITIONAL(IS_LINUX)` de `configure.ac:1122`. La descarta solo "junto a las opciones".
- Suggestion (5.x/M5) · spec-brownfield.md:525 y :588: BR-3 y NFR-3 nombran constantes de libssh. Es aceptable porque D-3 fija la librería, pero el enunciado del requisito debería ser el observable (VC-40 ya lo es) y dejar la constante como nota.
- 5.2, 5.4 y 5.5 sin hallazgos más allá de lo anterior. No se acepta ninguna host key ni se pide password por defecto (BR-1, D-5).

### 6. Simplicidad — WARN
- Warning (6.1/6.2) · spec-brownfield.md:185: "`[-dhv]` … `[-l size]`". Ni la consigna (enunciado.md:9-12, "un comando nuevo que abre un pane con SSH") ni ninguna D justifica `-d`, `-h`, `-l` y `-v` en v1. Agregan FR-6, FR-7 y FR-8, y el hueco de 1.5. Hace falta una D que lo fundamente o recortarlos.
- Warning (6.4) · spec-brownfield.md:544 vs :638: la lista y el orden de claves por defecto están escritos dos veces (BR-4 y D-5). Hay que dejar una sola fuente, que según 2.8 tiene que ser un FR.
- Suggestion (6.4) · spec-brownfield.md:331-334 vs :119: FR-19/VC-19 y el chequeo de INV-4 son el mismo `diff` contra `list-commands-linux.txt`.

### B. Extensión brownfield — FAIL
- Issue (B9/B6) · spec-brownfield.md:48: "Si está prendido: rechaza un `$host_os` … corre `PKG_CHECK_MODULES(…)`, define `ENABLE_SSH` y crea `AM_CONDITIONAL(ENABLE_SSH)`". Automake exige que `AM_CONDITIONAL` se evalúe siempre. Dentro del `if`, todo `./configure` sin `--enable-ssh` termina con `conditional "ENABLE_SSH" was never defined` y rompe macOS, los BSD y el Linux por defecto. El precedente que la spec cita lo hace fuera del `if` (`configure.ac:551-552`: `fi` y después `AM_CONDITIONAL(ENABLE_SIXEL, …)`). Un agente que sigue la spec al pie de la letra rompe INV-1 e INV-2.
- Warning (B1) · notas-exploracion.md:318: "131 commits de merge `tmux-openbsd/master`". `git log --merges --oneline 5a820e6 | grep -c tmux-openbsd/master` da **130**. El resto de los números de las notas se verificó y coincide: 153 `.c`; 106.232 líneas de `.c` y `.h` en la raíz; 27 nombres que empiezan con `s`; ninguno con `ss`; 170 nombres; 1.513 prefijos; 0 `#if` en `cmd_table`; el commit `f0a85d04` ("Move cgroup dbus requests to the child to avoid a race…").
- Warning (B3) · spec-brownfield.md:122: "`unifdef -UENABLE_SSH f \| diff - <(git show $BASE:f)`". `$BASE:f` muestra un archivo llamado `f`, no `$f`. Además, `<(…)` es bash, no sh, y `unifdef` sale con 1 cuando modifica, así que el exit no sirve de veredicto. El chequeo no corre tal como está escrito.
- Warning (B3) · spec-brownfield.md:118: "`sh scripts/snapshot-comandos.sh \| grep -v '^ssh-pane'`". Falta `TEST_TMUX=./tmux`. Sin él, el script usa el `tmux` del `PATH` (scripts/snapshot-comandos.sh:21) y compara el binario equivocado.
- Warning (B3/B2) · spec-brownfield.md:120: "`git diff --stat $BASE -- window.c server.c input.c layout.c job.c compat/ osdep-*.c`". No cubre `screen*.c`, `grid*.c`, `tty*.c`, `layout-*.c`, `compat.h`, `popup.c`, `cmd-run-shell.c` ni `options-table.c`, que :60-70 declara fuera de alcance. Además, "no toca líneas entre `struct window_pane {` y su `};`" no es un comando. Falta un chequeo de lista blanca: `git diff --name-only $BASE` ⊆ la tabla "Dentro".
- Warning (B4) · linea-de-base.md:32 y spec-brownfield.md:685: "164 PASS · 7 FAIL" (macOS). El crudo `linea-de-base/regress-macos.txt` tiene **165 PASS, 7 FAIL** (172 tests, los mismos 172 nombres que Linux). La tabla no coincide con sus propios datos.
- Warning (B4) · linea-de-base.md:11: "más `libssh-dev` (0.10.6) y `python3`", contra :43 "`input-requests.sh` FAIL sin `python3`" y el crudo Linux con `input-requests.sh FAIL`. Si el contenedor tenía `python3`, la falla no es "de entorno". Si no lo tenía, la descripción del entorno es falsa. Además, spec-brownfield.md:683/685 registra `cd regress && make`, cuando lo que se corrió fue `make -k -j"$(nproc)"` y `gmake -k -j8` (linea-de-base.md:15, :22).
- Warning (B5) · spec-brownfield.md:172: "en cualquier plataforma", y :80 "(macOS, *BSD, Solaris, AIX, Haiku, Cygwin)". El único VC no-Linux es macOS (VC-2, VC-4, VC-45). Ningún VC compila un BSD con `configure`, como FreeBSD, que sí lo usa. Hay que acotar FR-4 a "macOS y Linux sin el flag" o agregar el runner.
- Warning (B7) · spec-brownfield.md:50-52: "`extern const struct cmd_entry cmd_ssh_pane_entry;`", "`#define SPAWN_SSH 0x2000`" y "`_exit(ssh_pane_run(sc->ssh))`". Son fragmentos de C nuevo, no citas de código existente. `struct ssh_pane_target` (:51) se nombra y nunca se define. Hay que describir la interfaz en prosa (qué datos cruza del padre al hijo) y no como C. No hay `.c`/`.h` en `tmux-ssh-tp2/`, y `/tmp/tmux` está limpio.
- Suggestion (B9) · spec-brownfield.md:55: "el man se instala en todas las plataformas". `tmux.1` también se comparte con el árbol de OpenBSD, y INV-7 (:122) no lo incluye. OpenBSD documentaría un comando que nunca va a tener.
- B1: `TMUX_SRC=/tmp/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 109 citas verificadas contra tmux@5a820e6`, exit 0, sin fallos. Citas abiertas a mano (8), todas confirmadas:
  - `configure.ac:91`: `--enable-static` rechaza `*darwin*` con `case "$host_os"`.
  - `spawn.c:543`, `:544` y `:552`: `log_close()`, `environ_push(child)` y `execvp` (este último dentro del `if` de argc > 1, ver 2.8).
  - `layout.c:1657`, `:1674` y `:1692`: `layout_get_tiled_cell` lee `-l`/`-p`, `-p` va de 0 a 100, y el mensaje es `no space for a new pane`.
  - `options-table.c:1211`: `update-environment` incluye `SSH_AUTH_SOCK`.
  - `cmd.c:462` y `:489`: `cmd_find` acepta prefijos, y el mensaje es `unknown command: %s`.
  - `server.c:491` y `:498`: `server_child_exited` busca el pane por `wp->pid == pid` y guarda `status`.
  - `configure.ac:1006`: `PLATFORM` se asigna recién desde `configure.ac:1011`.
  - `osdep-linux.c:41` + `format.c:966-975`: `pane_current_command` sale del `cmdline` del pgrp. Además, `compat/setproctitle.c` en Linux usa `PR_SET_NAME` y no reescribe `cmdline`, así que FR-18 se sostiene.
- B2 sin hallazgos (los paths de :60-71 son concretos; el chequeo es B3). B8 sin hallazgos de presencia: las seis decisiones están en §8 (D-1, D-2, D-3, D-4, D-5 y D-6) con alternativa descartada. Los defectos de fundamento están en 5.3.

## Veredicto general   NEEDS WORK

## Acciones (priorizadas)
- [MUST] spec-brownfield.md:48: sacar `AM_CONDITIONAL(ENABLE_SSH, [test "x$enable_ssh" = xyes])` fuera del `if`, como `configure.ac:552` (B9).
- [MUST] spec-brownfield.md:185/:189: dar FR+VC a `-v` o sacarlo de la sinopsis y del getopt (1.5).
- [MUST] spec-brownfield.md:53/:644: decidir que `ssh-pane` pasa `sc.argc = 0` (o qué `argv` guarda) y escribir un FR+VC de `respawn-pane` sobre un pane `ssh-pane` (2.8).
- [MUST] spec-brownfield.md:645: convertir el renombre de la ventana por `automatic-rename` en un FR+VC (2.8).
- [MUST] spec-brownfield.md:638: llevar el orden y la lista de identidades de D-5 a un FR con VC (claves por defecto sin agente; `id_*` cifrada; `-i` con agente presente) (2.8).
- [MUST] spec-brownfield.md:636: hacer observable "`--enable-static --enable-ssh` sin soporte" con un FR (mensaje + exit de `configure`) (2.8).
- [MUST] spec-brownfield.md:438/:643: definir qué cubren los 10 s (TCP, banner, KEX, auth), si son por dirección o en total, y desde qué instante corren (2.8).
- [MUST] spec-brownfield.md:506-509: decidir si se usa `/etc/ssh/ssh_known_hosts` y ajustar el literal de FR-31 (2.8).
- [MUST] spec-brownfield.md:357-363: separar FR-22 en "host vacío" y "destino vacío" (2.3).
- [MUST] spec-brownfield.md:366-373: separar FR-23 en `host:puerto` e IPv6 literal, con el stderr literal de cada uno (2.3).
- [MUST] spec-brownfield.md:134: fijar el tamaño de ventana en las convenciones y definir "texto del pane" como `capture-pane -pJ`; si no, VC-31/32/34 (:451, :459, :478) fallan por el corte de línea (3.2).
- [MUST] spec-brownfield.md:233/:658: hacer coherente §9 con FR-9 (sshd solo en 2222 para VC-9) para que VC-9 discrimine (3.5).
- [MUST] spec-brownfield.md:385-509: agregar FR+VC para `known_hosts` ilegible o corrupto, clave `-i` inválida o cifrada, agente muerto, PTY/shell rechazados, KEX fallido, peer perdido sin RST y fallo de `spawn_pane` (3.3).
- [MUST] spec-brownfield.md:636 (y notas-exploracion.md:243): rehacer el descarte de libssh2 con un motivo verdadero; `libssh2_knownhost_readfile(…OPENSSH)` existe (5.3).
- [MUST] spec-brownfield.md §6.2 (después de :334): declarar en un FR que `ssh-pane` aparece en el completado del prompt (`prompt.c:1568`), como piden las notas en notas-exploracion.md:87-89 (5.6).
- [SHOULD] spec-brownfield.md:118: declarar el cambio del mensaje de `tmux s` (ambiguous, 27 → 28 candidatos) o reforzar INV-3 para que compare stderr y no `ERR` (5.6).
- [SHOULD] spec-brownfield.md:122: corregir el chequeo de INV-7 (`$f`, POSIX sh, criterio de exit) (B3).
- [SHOULD] spec-brownfield.md:118: agregar `TEST_TMUX=./tmux` al chequeo de INV-3 (B3).
- [SHOULD] spec-brownfield.md:120: reemplazar INV-5 por una lista blanca `git diff --name-only $BASE` ⊆ la tabla "Dentro" y un chequeo ejecutable de `struct window_pane` (B3/B2).
- [SHOULD] linea-de-base.md:32 y spec-brownfield.md:685: corregir macOS a 165 PASS / 7 FAIL, o regenerar el crudo (B4).
- [SHOULD] linea-de-base.md:11/:43: aclarar si había `python3` en la corrida y registrar en spec-brownfield.md:682-685 los comandos realmente usados (`-k -j`) (B4).
- [SHOULD] notas-exploracion.md:318: corregir "131" a 130, o mostrar el comando que da 131 (B1).
- [SHOULD] spec-brownfield.md:172: acotar FR-4 a las plataformas que tienen VC, o agregar un VC en un BSD con `configure` (B5/M6).
- [SHOULD] spec-brownfield.md:50-52: reemplazar los fragmentos de C nuevo por una descripción de la interfaz y definir qué contiene `ssh_pane_target` (B7).
- [SHOULD] spec-brownfield.md:52: fijar el punto de enganche "antes del `if` de `spawn.c:550`" (2.8).
- [SHOULD] spec-brownfield.md:138/:544: decidir si `~` es `$HOME` o `pw_dir`, y la forma de buscar en `known_hosts` con puerto ≠ 22 (`[servidor]:2222`) (2.8).
- [SHOULD] spec-brownfield.md:203, :271, :288, :315, :425, :494: subir las cotas de tiempo de los VCs a sus FRs o declararlas como timeouts del harness (2.7).
- [SHOULD] spec-brownfield.md:281 y :159: sacar de los VCs lo que el FR no dice ("exit 0 → `1 0`", "no se genera `Makefile`"), o agregarlo al FR (2.7).
- [SHOULD] spec-brownfield.md:382-383: dar el observable positivo de `-P 1` / `-P 65535` (3.2).
- [SHOULD] spec-brownfield.md:528-536: correr VC-40 con `T ssh-pane servidor` para que `User mallory` discrimine (3.2).
- [SHOULD] spec-brownfield.md:302/:660: decir en qué contenedor vive `/tmp/fixture.bin` (3.2).
- [SHOULD] spec-brownfield.md:159/:168: fijar exit 1 en VC-2/VC-3 (3.2).
- [SHOULD] spec-brownfield.md:187/:189: agregar FR+VC para `a@b@c`, dos posicionales y `-p` rechazado (3.4).
- [SHOULD] spec-brownfield.md:225: decir cómo se obtiene `%0` de 40 filas (3.5).
- [SHOULD] spec-brownfield.md:588/:593: agregar a VC-44 que el texto del pane no contiene log de libssh (4.3).
- [SHOULD] spec-brownfield.md §6.5 (después de :554): tratar el riesgo de core dump o memoria heredada (notas-exploracion.md:315) con un BR o una aceptación explícita (4.5).
- [SHOULD] spec-brownfield.md:643: decidir la política de keepalive (4.4).
- [SHOULD] spec-brownfield.md:637: corregir "el handshake y la autenticación bloquean" (5.3).
- [SHOULD] spec-brownfield.md:643: dar un dato que fundamente los 10 s (5.3).
- [SHOULD] spec-brownfield.md:652-659: nombrar los privilegios del entorno de verificación (`CAP_NET_ADMIN`, ptrace) (5.1).
- [SHOULD] spec-brownfield.md:185: justificar con una D `-d`, `-h`, `-l` (y `-v`) en v1, o recortarlos (6.1).
- [SHOULD] spec-brownfield.md:544/:638: dejar una sola fuente para la lista de claves (6.4).
- [SHOULD] spec-brownfield.md:698: hacer coherente la Iteración 1 (sin el bloque de `spawn.c`, `ssh_pane_run()` nunca corre) (1.4).
- [COULD] spec-brownfield.md:27-35: agregar el kernel y el resolvedor DNS como actores (1.3).
- [COULD] spec-brownfield.md:315: llevar `V=130` al FR-17 (2.7).
- [COULD] spec-brownfield.md:400: agregar a VC-26 la comparación de cantidad de panes (3.2).
- [COULD] spec-brownfield.md:224-230: agregar VCs de los bordes de `-l` (3.4).
- [COULD] spec-brownfield.md:566-578: agregar a NFR-2 una métrica que no dependa del parser del servidor (4.2).
- [COULD] spec-brownfield.md §6.6: declarar el costo de memoria (fork sin `exec`) por pane (4.5).
- [COULD] spec-brownfield.md:639: considerar el chequeo después de `configure.ac:1006` en D-6 (5.3).
- [COULD] spec-brownfield.md:525/:588: enunciar BR-3/NFR-3 por su observable (M5).
- [COULD] spec-brownfield.md:331-334: unificar VC-19 con el chequeo de INV-4 (6.4).
- [COULD] spec-brownfield.md:55/:122: decidir si `tmux.1` entra en INV-7 (B9).

VEREDICTO: NEEDS WORK

# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux), segunda vuelta — (tmux-ssh-tp2/spec-brownfield.md v1.1)
- Commit: TP `ef60d0e` (árbol limpio en `tmux-ssh-tp2/`) · tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` en /tmp/tmux, limpio · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 54 BR: 5 NFR: 3 VC: 65 (62 en bloque `> **VC-n**` + VC-63…65 en la tabla de §6.7; INV: 7). `grep -cE '^#+ .*FR-[0-9]+'` da 0 porque los FR van en negrita. Se contaron con `^\*\*FR-[0-9]+ ·`. VC (65) ≥ FR+BR (59). Coincide con la cabecera (spec-brownfield.md:14).

## Resumen

La v1.1 cierra la mayoría del primer informe:
- `AM_CONDITIONAL` va fuera del `if`.
- `-v` y `-l` salen de la sinopsis, fundamentados en D-16.
- D-11 decide cero argumentos de comando, con FR-21.
- FR-4 hace observable el caso `--enable-static`.
- D-10 dice qué cubren los 10 s, y D-14 qué `known_hosts` se leen.
- FR-22 y FR-23 se partieron.
- La ventana queda en 200×50 y el texto se lee con `-J`.
- Se rehízo el descarte de libssh2 y se declaró el completado del prompt.
- Se corrigieron INV-3, INV-5 e INV-7 y la línea de base.

`check-citas.py` pasa (122/122) y las 11 citas abiertas a mano dicen lo que la spec afirma.

Lo que bloquea son defectos **nuevos** que la v1.1 introdujo, o que quedaron a la vista al tratar de correr los VCs en el entorno de §9:
1. El Dado de FR-20 hace que VC-20 no pueda pasar: `new-window -n x` apaga `automatic-rename` (`spawn.c:223`).
2. NFR-2 mide la primera aparición de `__FIN__`, que ya está en el eco del comando tipeado. El umbral no discrimina nada.
3. VC-6 y VC-21 esperan los hostnames literales `servidor` y `cliente`, y §9 no los fija. En Docker, el hostname por defecto es el id del contenedor (verificado).
4. VC-2, VC-3 y VC-5, los VCs del límite de plataforma, no tienen dónde correr: los `regress/ssh-pane-*.sh` se saltean justo cuando el comando no existe, y §9 no tiene ni la variante macOS ni la variante sin `libssh-dev`.
5. Siguen sin FR los caminos de falla "corrupto" de `known_hosts` y de la clave, aunque la tabla de §7 dice que están cubiertos.

M3: 10 hits, ninguno cuenta. `spec-brownfield.md:54, 71, 142, 416, 529, 564, 831, 904` son "todo/todos/Todo" en castellano, y ninguno es un valor sin decidir. · M4: 1 hit, no cuenta. `:182` "sin libssh suficiente" es un título; el Dado lo acota a `>= 0.9.0`. El "red razonable" del primer informe desapareció. · M5: ningún FR ni VC atado a una implementación. No cuentan:
- `:58-59` y `:827-837`: son la tabla "Dentro" y las decisiones, donde nombrar funciones es lo que corresponde.
- `:334` FR-17 (`input_parse_pane`), `:309` VC-14 (`window.c:612`) y `:404` FR-24 (`prompt.c:1568`): son explicativos.
- `:331-333` FR-17: "el hijo pone **su** terminal … en modo raw" prescribe un medio, pero el Entonces es observable. Sugerencia: dejarlo como nota.
- Las constantes de libssh de BR-3/NFR-3 ya no están en los requisitos (resuelto).

M6: cuenta `:687` BR-1 "Cualquier otro resultado lleva a FR-43, FR-44, FR-45, FR-46 o FR-47": un `known_hosts` con una línea corrupta no es ninguno de esos FRs (ver 3.3). `:219` "Cualquier otra letra es un error de tmux (FR-27)" es prosa normativa con un solo VC (`-p`). Lo garantiza el getopt de `args_parse`, así que es Suggestion. No cuentan: `:28` (propósito), `:113`, `:334`, `:375-376` y `:528` (prosa), `:559` (es parte del Dado), `:684` (título de BR-1, acotado por VC-55), `:792` y `:885` (entorno).

## Estado de las acciones del primer informe

| Acción (r1) | Estado | Evidencia en v1.1 |
|---|---|---|
| [MUST] `AM_CONDITIONAL` fuera del `if` | Resuelta | :54 |
| [MUST] `-v` sin FR | Resuelta | :211; D-16 :841 |
| [MUST] `sc.argc = 0` + FR de `respawn-pane` | Resuelta | :59, FR-21 :371-379, D-11 :836. VC-21 agrega un observable que el FR no dice (2.7) |
| [MUST] `automatic-rename` como FR+VC | **Parcial** | FR-20 :362-369 existe, pero su Dado hace imposible el VC (Issue 3.5) |
| [MUST] Identidades de D-5 en FRs | Parcial | FR-11 :274, FR-49 :630, FR-50 :640, FR-51 :648. Ningún VC prueba el orden `id_ed25519` → `id_ecdsa` → `id_rsa` (:830), ni si con `-i` se prueban también las claves por defecto (Suggestion 2.8) |
| [MUST] `--enable-static` observable | Resuelta | FR-4 :191-197 |
| [MUST] Qué cubren los 10 s | Resuelta | D-10 :835, FR-41 :558-564 |
| [MUST] `known_hosts` global | Resuelta | D-14 :839, FR-43 :582. Lo que pasa cuando los dos archivos se contradicen queda abierto (Warning 2.8) |
| [MUST] Partir FR-22 (r1) | Resuelta | FR-29 :448, FR-30 :455 |
| [MUST] Partir FR-23 (r1) con el literal de IPv6 | **Parcial** | FR-32 :469-472 sigue con un Dado de clase ("un destino que contiene `:`"), y el literal para `::1` no está escrito (Warning 2.8) |
| [MUST] Tamaño de ventana + `capture-pane -pJ` | Resuelta | :147, :151 |
| [MUST] §9 coherente con FR-9 | Resuelta | VC-9 :262-263 discrimina por `SSH_CONNECTION` |
| [MUST] Caminos de falla faltantes | **Parcial** | Se agregaron FR-37, FR-42, FR-45, FR-50, FR-51 y FR-52. El peer perdido sin RST queda excluido en forma explícita (:94, D-10). Siguen faltando el `known_hosts` corrupto, una clave `-i` que no es una clave, y un agente vivo que falla (Issue 3.3) |
| [MUST] Descarte de libssh2 | Resuelta | D-3 :828; notas-exploracion.md:243-251 |
| [MUST] FR del completado del prompt | Resuelta | FR-24 :401-410. La técnica del VC tiene un riesgo (Warning 3.5) |
| [SHOULD] Mensaje de `tmux s`, 27 → 28 | Resuelta | FR-23 :390-399 |
| [SHOULD] Chequeo de INV-7 | Resuelta | :138 |
| [SHOULD] `TEST_TMUX` en INV-3 | Resuelta | :134. Nuevo: el script no está en el árbol de tmux (Warning B3) |
| [SHOULD] INV-5 como lista blanca | Parcial | :136. La parte de `struct window_pane` sigue en prosa (Warning B3) |
| [SHOULD] macOS 165/7 | Resuelta | linea-de-base.md:33, spec :901, crudo 165/7 |
| [SHOULD] `python3` y los comandos reales | Resuelta | linea-de-base.md:12-24, spec :893-902 |
| [SHOULD] Notas: 131 → 130 | Resuelta | notas-exploracion.md:329 (recontado: 130) |
| [SHOULD] Acotar FR-4 (r1) a plataformas con VC | Resuelta | FR-4 se reescribió; §4 :118-121 declara los BSD "por construcción" |
| [SHOULD] Sin fragmentos de C nuevo | Resuelta | `grep '#define\|extern \|_exit(\|SPAWN_SSH'` da 0 hits |
| [SHOULD] Punto de enganche "antes del `if` de `spawn.c:550`" | Resuelta | :58, D-2 :827 |
| [SHOULD] `~`, y `[servidor]:2222` en `known_hosts` | Parcial | `~` en :159-160; `[servidor]:2222` en :257, pero VC-9 no lo discrimina, y el nombre del host en los mensajes con `-P` ≠ 22 sigue sin decidirse (Warning 3.2) |
| [SHOULD] Cotas de tiempo en los FRs | Resuelta en lo que se pidió | FR-6 :226, FR-14, FR-16, FR-18, FR-20 y FR-38/39. Nuevo: 10 FRs asíncronos sin cota (Warning 2.8) |
| [SHOULD] VC-15 "`exit 0`" y VC-2 "no se genera `Makefile`" | **No resuelta** | :316, :179-180 (Warning 2.7) |
| [SHOULD] Observable de `-P 1` y `-P 65535` | Resuelta | :482-484. Introduce un 2.7 y choca con el plan (Warnings 2.7 y 1.4) |
| [SHOULD] VC de BR-3 con `T ssh-pane servidor` | Resuelta | :717 |
| [SHOULD] Contenedor de `/tmp/fixture.bin` | Resuelta | :337, :871 |
| [SHOULD] Exit 1 en VC-2 y VC-3 | Resuelta | :179, :188 |
| [SHOULD] `a@b@c`, dos posicionales y `-p` | Resuelta | FR-31, FR-26 y FR-27 |
| [SHOULD] `%0` de 40 filas | Resuelta (obsoleta) | `-l` salió del alcance |
| [SHOULD] Log de libssh en el texto del pane | Resuelta | NFR-3 :777, :783 |
| [SHOULD] Riesgo de core dump | Resuelta | BR-5 :734-740 |
| [SHOULD] Política de keepalive | Resuelta | D-10 :835, :94 |
| [SHOULD] "El handshake bloquea" | Resuelta | D-4 :829 |
| [SHOULD] Dato que fundamente los 10 s | **Parcial** | D-10 :835 explica por qué hace falta un tope (unos 127 s sin él), pero no por qué 10 (Warning 5.3) |
| [SHOULD] Privilegios del entorno | Parcial | :854 y :865 nombran las capabilities. No dice qué usuario corre `strace` (Warning 5.1) |
| [SHOULD] Justificar los flags | Resuelta | D-16 :841 |
| [SHOULD] Una sola fuente para la lista de claves | Resuelta | BR-4 :724 remite a D-5 |
| [SHOULD] Coherencia de la Iteración 1 | Resuelta | :915. Nuevo: VCs asignados a la iteración equivocada (Warning 1.4) |

## Hallazgos por dimensión

### 1. Propósito y alcance — WARN
- Warning (1.4) · spec-brownfield.md:915-917: "VC-1…5, VC-22…37 y VC-63…65" (Iteración 1) y "VC-6…21 y VC-55…59" (Iteración 2). El plan asigna a cada iteración VCs que no pueden pasar en ella:
  - VC-33 (:482-484) espera que `-P 1` y `-P 65535` terminen "como en FR-39", con `connection refused…`. En la Iteración 1, el hijo solo escribe `ssh-pane: not implemented`.
  - VC-55 (:690) se corre sobre VC-43, VC-44, VC-46 y VC-47, y VC-56 (:698) sobre VC-43. Esos VCs son de la Iteración 3 (:917).
- Warning (1.4) · spec-brownfield.md:119: "VC-5 y VC-63 corren en **macOS y Linux**". VC-63 es solo macOS (:790), y en Linux corre VC-64 (:791). Además, VC-5 no tiene runner (ver B5).
- 1.1, 1.2, 1.3, 1.5 y 1.6 sin hallazgos:
  - el propósito dice por qué (:18-28);
  - "Fuera" tiene 8 grupos por path (:66-81) y 10 por comportamiento (:87-96);
  - los actores incluyen al kernel, al resolvedor DNS y a `ssh-agent` (:36-38);
  - cada flag de la sinopsis (:211-221) tiene su FR: `-d` FR-8, `-h` FR-7, `-i` FR-10, `-P` FR-9 y `-t` FR-6;
  - las notas y la línea de base están enlazadas (:3-6).

### 2. Completitud y consistencia — WARN
- Warning (2.8) · spec-brownfield.md:354-358, FR-19: "vale `tmux`. Es el `argv[0]` del servidor". Lo que se muestra es `parse_window_name(argv[0])`, que aplica `basename` **solo si empieza con `/`** (`names.c:167-168`). Con `T = ./tmux` o `../tmux`, el valor es `./tmux`. La spec no fija cómo se invoca el binario. La convención de :146 dice `tmux` a secas, y el `regress/` de upstream usa `readlink -f`. Hay que fijar que `T` es un path absoluto, o enunciar el valor como "el basename del `argv[0]` del servidor".
- Warning (2.8) · spec-brownfield.md:686: "Solo se conecta si la clave figura, coincide y es del mismo tipo en **alguno** de los archivos de D-14". Ni el entorno base (:155-158) ni los Dados de FR-45 (:598), FR-46 (:605) y FR-47 (:614) dicen qué hay en `/etc/ssh/ssh_known_hosts`. Si el global tiene la clave buena y el del usuario tiene una distinta, BR-1 ("en alguno") dice que se conecta, y FR-46 dice que se rechaza. Si el del usuario es ilegible y el global coincide, BR-1 conecta y FR-45 falla. Hay que fijar en el entorno base que el global no existe, y decidir la precedencia.
- Warning (2.8) · spec-brownfield.md:519-530 (§6.4) y FR-42, FR-43, FR-44, FR-45, FR-46, FR-47, FR-48, FR-50, FR-52 y FR-54 (:569-680). Solo FR-38, 39, 40, 41, 49 y 53 tienen cota de tiempo. Para el resto, el test tiene que inventar cuánto espera. D-10 (:835) da un tope de 10 s hasta el canal, pero §6.4 no lo dice, y FR-54 ocurre **después** del canal, así que no tiene ningún tope. Hay que declarar en la introducción de §6.4: "salvo que el FR diga otra cosa, dentro de 10 s del comando" y darle a FR-54 su propia cota.
- Warning (2.8/2.3) · spec-brownfield.md:470-472, FR-32: "**Dado** un destino que contiene `:`, **cuando** se corre `T ssh-pane servidor:22`". El Dado es una clase y el Cuando, un caso. Para `::1` (excluido en :92) la spec no escribe el literal, y el sufijo "use -P for the port" engaña. Hay que acotar el Dado a `host:puerto`, y agregar el literal de un IPv6 o declarar que es el mismo.
- Warning (2.7) · spec-brownfield.md:378-379, VC-21: "y `T display -p -t <pane> '#{pane_start_command}'` da una línea vacía". FR-21 (:371-376) no menciona `pane_start_command`. El dato es correcto (`format.c:908`, `spawn.c:401`), pero tiene que estar en el FR.
- Warning (2.7) · spec-brownfield.md:482-484, VC-33: "Con `1` y `65535` (los bordes): exit 0 y un pane nuevo, que después termina como en FR-39". FR-33 (:476-479) solo habla de valores inválidos. El comportamiento de los bordes vive solo en el VC. Hay que sumarlo al Entonces (o a un FR propio).
- Warning (2.7, sigue del primer informe) · spec-brownfield.md:316: "Con `exit 0` es `1 0`" (FR-15 dice `exit 7`). Y :179-180: "y no se genera `Makefile`" (FR-2 no lo exige).
- Suggestion (2.8) · spec-brownfield.md:830, D-5: el orden `id_ed25519` → `id_ecdsa` → `id_rsa`, y si con `-i` se prueban también las por defecto, no tienen VC. VC-48 y VC-51 usan solo `id_ed25519`.
- 2.1 sin hallazgos: 54/54 FRs tienen Dado, Cuando y Entonces. 2.3 sin otros hallazgos: FR-29/FR-30 y FR-25…FR-37 son una situación cada uno. FR-33 y FR-34 son clases con un mensaje de plantilla único y valores enumerados en el VC.

### 3. Casos borde y verificabilidad — FAIL
- **Issue (3.5)** · spec-brownfield.md:362-369, FR-20: "**Dado** una ventana nueva (`T new-window -d -n x 'sleep 300'`), con `automatic-rename` prendido". `new-window -n` apaga `automatic-rename` en esa ventana: `spawn.c:221-223`, `w->name = xstrdup(sc->name); options_set_number(w->options, "automatic-rename", 0);`. El Dado es imposible tal como está escrito, y VC-20 ve `x` con cualquier implementación, aunque sea correcta. Hay que sacar `-n x` (y localizar la ventana por `window_id`) o volver a prender `automatic-rename` en el Dado.
- **Issue (3.5)** · spec-brownfield.md:233, "`R=servidor:alice:/dev/pts/`", y :378, "`H=cliente`". §9 (:847-873) nombra los contenedores `cliente` y `servidor`, pero no les fija el hostname. Con Docker, `hostname` devuelve el id del contenedor: `docker run --rm ubuntu:24.04 hostname` da `64918328ee56`, verificado acá. Compose hace lo mismo si no hay `hostname:`. VC-6, que es **el** VC end-to-end, y VC-21 fallan con una implementación correcta. Hay que agregar en §9 "`hostname: servidor` / `hostname: cliente`" o comparar contra `$(docker compose exec servidor hostname)`.
- **Issue (3.3)** · spec-brownfield.md:811-815, tabla "Caminos de falla por recurso externo": "`known_hosts` | … | Ilegible / corrupto | FR-45" y "Clave / agente | … | Ilegible / corrupto | FR-49, FR-50". FR-45 (:597-600) solo cubre el modo `000`. FR-49 y FR-50 solo cubren claves **con passphrase**. Ningún FR cubre:
  - un `known_hosts` legible con una línea corrupta. libssh devuelve un error de parseo, que no es ninguno de FR-43…47, y por eso el M6 de BR-1 :687;
  - un `-i /tmp/k` legible que no es una clave privada, por ejemplo una pública o texto;
  - un agente vivo que falla. FR-51 (:648-650) se titula "El agente no responde", pero el Dado es "un socket que no existe". Un socket que existe sin nadie escuchando, o un agente que rechaza la firma, queda sin decidir.

  La tabla afirma una cobertura que los FRs no tienen.
- Warning (3.5) · spec-brownfield.md:847-873, §9: el entorno no alcanza para correr VCs que dependen de él. Verificado en `ubuntu:24.04`:
  - `ss` e `iptables` **no están** en la imagen, y el contenedor `servidor` solo agrega `openssh-server` y `netcat-openbsd` (:858). VC-40 (:550) y VC-53 (:667) no corren. `iproute2` está solo en `cliente` (:852).
  - Los `sshd` se configuran con `LogLevel VERBOSE` (:864), pero en un contenedor no hay syslog ni journald, y §9 no dice adónde va el log (`sshd -E <archivo>`). VC-11 (:280) y VC-43 (:585) leen ese log.
  - VC-11 y VC-43 dicen "para esa conexión" / "esa conexión" (:280, :585) sin decir cómo se identifica: por puerto origen, por hora o vaciando el log antes.
  - `unifdef` (VC-65, :792) no está en la imagen ni en la lista de `cliente`. VC-65 dice "cualquier clon con `git` y `unifdef`", así que es aceptable si el job lo instala, pero §9 no lo dice.
- Warning (3.5) · spec-brownfield.md:613-620, FR-47: "Dado que `known_hosts` solo tiene … una clave de otro tipo (`ssh-rsa`, cuando el servidor presenta `ssh-ed25519`)". El `sshd` de §9 tiene la configuración por defecto (:861), con host keys RSA, ECDSA y Ed25519. El cliente libssh ordena sus algoritmos de host key poniendo primero los tipos que encuentra en `known_hosts` (`ssh_client_select_hostkeys`). Esto sale del código de libssh 0.10: no lo corrí en este entorno. Así, el servidor presenta su RSA, y el resultado es FR-46 o una conexión exitosa, no FR-47. Para poder correr VC-47, el `sshd` tiene que ofrecer solo `HostKey …ed25519` (una cuarta instancia en §9), o el Dado tiene que decirlo.
- Warning (3.5) · spec-brownfield.md:408-410, VC-24: "Con la técnica de `regress/prompt-words-history.sh`". Ese test es **5/5 FAIL** en la línea de base Linux (linea-de-base.md:45, `got 'show-r', expected 'history-command'`), y falla justo después del bloque de completado con Tab (`regress/prompt-words-history.sh:119-133`). VC-24 se apoya en una técnica que hoy no anda en el entorno de referencia. Hay que mostrar que la parte usada (bind con `@result` + Tab) pasa sola en `cliente`, o usar otra técnica.
- Warning (3.2) · spec-brownfield.md:255-263, FR-9/VC-9: el entorno base ya tiene `servidor` en `known_hosts` (:157). Una implementación que busca `servidor` en lugar de `[servidor]:2222` pasa VC-9 igual. Hay que sacar la entrada `servidor` en el Dado de FR-9. Además, con `-P ≠ 22` no está decidido qué nombre aparece en los mensajes de FR-43…47 ("host key for servidor" o "for [servidor]:2222").
- Suggestion (3.4) · spec-brownfield.md:59: `layout_get_tiled_cell()` devuelve `can't split a floating pane` (`layout.c:1649-1651`) si `-t` apunta a un pane flotante. §3 excluye **crear** panes flotantes (:95), pero no apuntar a uno. Falta el FR del mensaje.
- Suggestion (3.4) · spec-brownfield.md:213: codificación del destino (host con espacios, que empieza con `-`, no ASCII/IDN) sigue sin decidirse. No hay riesgo de inyección (no hay `exec`), pero dos implementaciones pueden dar mensajes distintos.
- 3.1 sin hallazgos: cada FR-n tiene VC-n debajo (secuencia 1…54 verificada), BR-1…5 → VC-55…59, NFR-1…3 → VC-60…62, y la tabla de :800-807 cierra. 3.6 sin hallazgos de presencia: VC-6 está declarado end-to-end contra `sshd` real (:229, :875-877). Que hoy no corra es el Issue de hostnames de arriba.

**Ejercicio 3.5.** Feliz, FR-6 (el E2E):

```sh
# entorno §9; corre como alice en "cliente"
T="$(readlink -f ./tmux) -Ltest -f/dev/null"   # decisión: path absoluto (si no, FR-19 cambia; ver 2.8)
$T new-session -d -x 200 -y 50
$T set -g remain-on-exit on
antes=$($T list-panes -a -F '#{pane_id}' | sort)
t0=$(date +%s.%N)
$T ssh-pane -t %0 alice@servidor; test $? -eq 0
nuevo=$(comm -13 <(echo "$antes") <($T list-panes -a -F '#{pane_id}' | sort))
$T send-keys -t "$nuevo" 'echo "R=$(hostname):$(id -un):$(tty)"' Enter
# decisión: mandar las teclas antes de que exista el canal (el PTY local está en cooked y
# hace eco local hasta que el hijo pasa a raw, comportamiento que la spec no declara)
for i in $(seq 30); do
  $T capture-pane -pJ -t "$nuevo" | grep -q 'R=servidor:alice:/dev/pts/' && break; sleep 0.1
done                                            # falla en §9: hostname = id del contenedor
test "$($T display -p '#{pane_id}')" = "$nuevo"
```

Decisiones que tuve que tomar: el hostname de `servidor` (§9 no lo fija: Issue); que `T` sea un path absoluto; mandar las teclas durante el handshake, que produce un eco local que la spec no menciona; el polling de 100 ms.

Falla, FR-45:

```sh
chmod 000 ~/.ssh/known_hosts
# decisión: /etc/ssh/ssh_known_hosts ausente (el entorno base no lo dice; si tiene la clave, BR-1 conecta)
$T ssh-pane alice@servidor; test $? -eq 0
# decisión: esperar 10 s (FR-45 no tiene cota; tomo D-10 por analogía)
for i in $(seq 100); do
  test "$($T display -p -t "$nuevo" '#{pane_dead} #{pane_dead_status}')" = "1 255" && break; sleep 0.1
done
$T capture-pane -pJ -t "$nuevo" | grep -qxF 'ssh-pane: could not read known_hosts'
chmod 600 ~/.ssh/known_hosts
```

Decisiones que tuve que tomar: el estado del archivo global; la cota de tiempo; que el test no corra como root (con root, el modo `000` no impide leer; §9 dice `alice`, así que vale, pero conviene declararlo en el FR). Con una línea corrupta en lugar de `000`, no habría FR contra el cual escribir el test (Issue 3.3).

### 4. Requerimientos no funcionales — FAIL
- **Issue (4.2)** · spec-brownfield.md:757-763, NFR-2: "`head -c 50331648 /dev/urandom | base64 -w 76; echo __FIN__`" y "**Métrica:** el tiempo desde el `send-keys` hasta la primera vez que `__FIN__` aparece en el texto del pane". El comando se tipea con `send-keys`, así que la shell remota hace eco de la línea `… ; echo __FIN__` antes de correrla. La primera aparición de `__FIN__` es el eco, a los pocos milisegundos, en los dos brazos. La métrica mide la latencia del eco, no el throughput, y el cociente ≤ 1,25 lo pasa cualquier implementación. VC-17 tuvo en cuenta este mismo problema (:342, "el eco del comando queda antes"), y NFR-2 no. Hay que medir hasta una **línea completa** igual a `__FIN__` (`grep -qx`), o imprimirla con un string que no aparezca en el comando (`printf '__%s__\n' FIN`).
- Suggestion (4.2, sigue del primer informe) · spec-brownfield.md:754-766: corregido lo anterior, el cuello de botella sigue siendo `input_parse_pane` del servidor, que es igual en los dos brazos. Conviene sumar el CPU del hijo.
- Suggestion (4.5, sigue del primer informe): no hay un requisito de costo por pane. BR-5 (:736-738) reconoce que el hijo hereda la imagen del servidor, pero no dice cuánta memoria cuesta cada `ssh-pane`.
- 4.1, 4.3 y 4.4 sin hallazgos:
  - NFR-1 (:745-747) y NFR-2 tienen métrica, número y condición de carga en el enunciado;
  - NFR-3 enumera tres condiciones (:773-775) y VC-62 (:781-784) chequea las tres;
  - las políticas de reintentos y keepalive son explícitas (D-10).

### 5. Tecnología y fundamento — WARN
- Warning (5.1) · spec-brownfield.md:854: "se levanta con `--cap-add SYS_PTRACE`, que VC-56 necesita", y :851-853: "corre como `alice`". `--cap-add` le da la capability al root del contenedor, no a `alice`. Con `kernel.yama.ptrace_scope=1`, el default de los runners Ubuntu, `alice` no puede hacer `strace -p` sobre el servidor `tmux`, porque no es su descendiente. Hay que decir que VC-56 corre `strace` como root dentro de `cliente`.
- Warning (5.3, sigue del primer informe) · spec-brownfield.md:835: "Sin un tope … unos 127 s". Justifica que haya un tope, no que sea **10 s**. Falta el dato: por ejemplo, el RTT de §9 o un umbral comparable de otra herramienta.
- Warning (5.6) · notas-exploracion.md:296: "`cmd-ssh-pane.c` (nuevo) | … Arma el `spawn_context` igual que `split-window`". Contradice D-11 (:836), que descarta justamente copiar `args_to_vector` de `split-window`. Las notas son un insumo que el implementador va a leer, y llevan a `respawn-pane` corriendo `$SHELL -c alice@servidor`. Hay que ajustar la nota, o marcarla como superada por D-11.
- 5.2, 5.4 y 5.5 sin hallazgos:
  - D-3 (:828) compara libssh y libssh2 con un motivo verificable;
  - D-15 (:840) fundamenta la exclusión estática;
  - no hay TOFU ni password por defecto (BR-1, D-5).

  5.3 sin otros hallazgos: D-4 y D-6 quedaron corregidas.

### 6. Simplicidad — PASS
- Suggestion (6.4, sigue del primer informe) · spec-brownfield.md:381-388 vs :135: VC-22 y el chequeo de INV-4 son el mismo `diff` contra `list-commands-linux.txt`, con distinto filtro.
- 6.1–6.3 sin hallazgos: D-16 (:841) recorta los flags a `-d`, `-h` y `-t`. Cada FR viene de la consigna o es un camino de falla. La lista de claves tiene una sola fuente (BR-4 :724 → D-5).

### B. Extensión brownfield — FAIL
- **Issue (B5)** · spec-brownfield.md:62: "Si el comando no existe o falta el entorno de §9, **se saltean** con exit 0". También :144, "Corren como `regress/ssh-pane-*.sh` en el entorno de §9", y :880-886, "dos variantes: Linux con `--enable-ssh` y Linux sin él. VC-63 corre aparte, en un runner `macos-26` … Solo cuenta como verificado si corrió en este job". Los VCs que materializan el límite de plataforma no tienen dónde contar como verificados:
  - **VC-5** (:205) necesita un binario **sin** el comando, y es exactamente la condición en la que el `regress/ssh-pane-*.sh` se saltea.
  - **VC-2** (:179) y la mitad macOS de VC-5 corren en macOS, pero el runner `macos-26` de §9 solo corre VC-63.
  - **VC-3** (:188) necesita `cliente` **sin** `libssh-dev`, y §9 instala `libssh-dev` (:851) sin una variante sin él.

  Según la regla del propio §9, FR-2, FR-3 y FR-5 quedan para siempre "no corridos". Hay que declarar para cada uno su entorno: un job macOS que corra VC-2, VC-5 y VC-63, y una tercera variante Linux sin `libssh-dev`. También hay que excluir VC-5 del auto-salteo, o sacarlo de `regress/`.
- Warning (B3) · spec-brownfield.md:128 y :134: "Los chequeos … se corren desde la raíz del árbol de tmux" y "`TEST_TMUX=./tmux sh snapshot-comandos.sh`". `snapshot-comandos.sh` vive en `tmux-ssh-tp2/scripts/`, no en el árbol de tmux, así que el comando, tal como está escrito, da "No such file". Hay que poner el path (`sh <tp>/scripts/snapshot-comandos.sh`).
- Warning (B3, sigue del primer informe) · spec-brownfield.md:136: "En `tmux.h`, el diff no toca ninguna línea entre `struct window_pane {` (`tmux.h:1306`) y su `};`". Sigue en prosa. Un chequeo posible: `git diff -U0 $BASE -- tmux.h | grep '^@@'`, comparando cada rango contra las líneas de `struct window_pane` en `$BASE`.
- Suggestion (B9) · spec-brownfield.md:54-56: la tabla "Dentro" no dice dónde se agregan `LIBSSH_CFLAGS` y `LIBSSH_LIBS`. Systemd lo hace con `LIBS=` dentro del bloque de `configure.ac`. Si se ponen fuera del `if`, un Linux sin el flag enlazaría libssh. INV-2 (:133, `ldd … grep -c libssh`) lo detecta, pero conviene escribirlo.
- B1: `TMUX_SRC=/tmp/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 122 citas verificadas contra tmux@5a820e6`, exit 0, sin fallos (antes eran 109). Citas nuevas abiertas a mano, 11, todas confirmadas:
  - `arguments.c:333` y `:340`: `"too few arguments (need at least %u)"` y `"too many arguments (need at most %u)"`. Con `cmd.c:534`, `"command %s: %s"`, el stderr de FR-25 y FR-26 es exacto. `arguments.c:240`, `"unknown flag -%c"`, confirma FR-27.
  - `cmd.c:206-207`: `&cmd_split_window_entry` y `&cmd_start_server_entry`. El listado de ambigüedad recorre `cmd_table` en orden (`cmd.c:493-506`), y `list-commands-linux.txt` tiene 27 nombres con `s`. FR-23 se sostiene.
  - `cmd-find.c:1272`: `"can't find pane: %s"` (FR-35).
  - `layout.c:1692`: `"no space for a new pane"`. `cmd-split-window.c:180-181` lo pasa tal cual con `cmdq_error(item, "%s", cause)`. Con `PANE_MINIMUM 1` (`tmux.h:111`), `resize-window -y 2` es válido y no entra un split (FR-36).
  - `spawn.c:480`: `"fork failed: %s"`. `spawn.c:483-486` saca el pane y la celda, así que "la cantidad de panes no cambia" (VC-37) se sostiene.
  - `spawn.c:550`: `if (new_wp->argc != 0 && new_wp->argc != 1)`, el punto de enganche de D-2.
  - `prompt.c:1568`: recorre `cmd_table`. Con un único candidato, `prompt.c:1688` agrega `"%s "`, así que el `ssh-pane ` con espacio de VC-24 es correcto.
  - `options-table.c:1304`: `automatic-rename`, con default 1. **Pero** `spawn.c:223` lo apaga con `-n` (Issue 3.5).
  - `options-table.c:95` y `:1669`: los valores de `remain-on-exit`.
  - `tmux.h:1306`: `struct window_pane {`.
  - `regress/Makefile:1`: `TESTS!= echo *.sh`.

  Además se verificó: `spawn.c:380-390` (con `argc == 0` y sin `SPAWN_RESPAWN` usa `default-command`, que por defecto es `""`, `options-table.c:790`), así que D-11 y FR-21 se sostienen; `format.c:958-977` y `names.c:167` para FR-19 (ver 2.8); y que `sshd` 9.6p1 de `ubuntu:24.04` acepta `KexAlgorithms diffie-hellman-group1-sha1` (`sshd -t` sale 0), así que VC-42 se puede correr.
- B2, B4, B6, B7 y B8 sin hallazgos:
  - "Fuera" por path es concreto (:66-81), y INV-5 lo chequea como lista blanca;
  - la línea de base coincide con los crudos (165/7 y 170/2);
  - ningún FR necesita un archivo fuera de "Dentro";
  - `git diff --name-only cc123c2 ef60d0e | grep -E '\.(c|h)$'` da vacío, y `/tmp/tmux` está limpio;
  - las seis decisiones de la consigna son D-1 a D-6, con lo descartado.
- B9: el lector hostil ya no rompe un build no-Linux (`AM_CONDITIONAL` fuera, INV-7 con `unifdef`) ni un comando existente (INV-3, INV-4). Lo peor que puede pasar hoy es más sutil: siguiendo las notas (5.6) y no D-11, guarda el destino como comando. Y sin la línea de `LIBS` (Suggestion de arriba), lo frena INV-2.

## Veredicto general   NEEDS WORK

## Acciones (priorizadas)
- [MUST] spec-brownfield.md:363-364: sacar `-n x` del Dado de FR-20, o volver a prender `automatic-rename` en la ventana. Con `-n`, `spawn.c:223` lo apaga y VC-20 no puede pasar (3.5).
- [MUST] spec-brownfield.md:757-763: medir NFR-2 hasta una línea completa igual a `__FIN__`, o con un marcador que no esté en el comando tipeado. Hoy mide el eco (4.2).
- [MUST] spec-brownfield.md:847-873: fijar en §9 `hostname: servidor` y `hostname: cliente`. Sin eso, VC-6 (:233) y VC-21 (:378) fallan con una implementación correcta (3.5).
- [MUST] spec-brownfield.md:62, :144 y :880-886: darles entorno a VC-2, VC-3 y VC-5 (job macOS para VC-2/VC-5, variante Linux sin `libssh-dev` para VC-3) y excluir VC-5 del auto-salteo (B5).
- [MUST] spec-brownfield.md:597-655 y :811-815: agregar FR+VC para `known_hosts` con una línea corrupta, `-i` legible que no es una clave, y un agente vivo que falla, o corregir la tabla de §7 (3.3).
- [SHOULD] spec-brownfield.md:858-866: agregar `iptables` e `iproute2` a `servidor`, decir adónde va el log de `sshd` (`-E`), y cómo se identifica "esa conexión" en VC-11 (:280) y VC-43 (:585) (3.5).
- [SHOULD] spec-brownfield.md:614-615 y :861: hacer que el `sshd` de VC-47 ofrezca solo la host key ed25519, o reescribir el Dado de FR-47 (3.5).
- [SHOULD] spec-brownfield.md:408: mostrar que la técnica de VC-24 pasa en `cliente`. `prompt-words-history.sh` es 5/5 FAIL en la línea de base (linea-de-base.md:45) (3.5).
- [SHOULD] spec-brownfield.md:155-158 y :686: fijar en el entorno base el estado de `/etc/ssh/ssh_known_hosts` y decidir la precedencia entre los dos archivos (2.8).
- [SHOULD] spec-brownfield.md:519-530 y :673-678: declarar la cota de tiempo por defecto de §6.4 y darle una a FR-54 (2.8).
- [SHOULD] spec-brownfield.md:146 y :356-357: fijar `T` como path absoluto, o enunciar FR-19 como "basename del `argv[0]`" (2.8).
- [SHOULD] spec-brownfield.md:915-917: reasignar VC-33 (bordes), VC-55 y VC-56 a la iteración en que pueden pasar (1.4).
- [SHOULD] spec-brownfield.md:378-379 y :482-484: subir `pane_start_command` vacío a FR-21 y el comportamiento de `-P 1`/`-P 65535` a FR-33 (2.7).
- [SHOULD] spec-brownfield.md:316 y :179-180: llevar "`exit 0` → `1 0`" y "no se genera `Makefile`" a sus FRs, o sacarlos de los VCs (2.7, sigue del primer informe).
- [SHOULD] spec-brownfield.md:470-472: acotar el Dado de FR-32 a `host:puerto` y escribir el literal de un IPv6 (2.8/2.3).
- [SHOULD] spec-brownfield.md:257 y :157: sacar la entrada `servidor` del Dado de FR-9 para que VC-9 discrimine `[servidor]:2222`, y decidir el nombre del host en los mensajes con `-P` ≠ 22 (3.2).
- [SHOULD] spec-brownfield.md:854: decir que `strace` (VC-56) corre como root en `cliente` (5.1).
- [SHOULD] spec-brownfield.md:835: fundamentar el valor de 10 s con un dato (5.3).
- [SHOULD] notas-exploracion.md:296: corregir "Arma el `spawn_context` igual que `split-window`" para que no contradiga D-11 (5.6).
- [SHOULD] spec-brownfield.md:134: poner el path real de `snapshot-comandos.sh` (B3).
- [SHOULD] spec-brownfield.md:136: hacer ejecutable el chequeo de `struct window_pane` (B3).
- [SHOULD] spec-brownfield.md:119: corregir "VC-5 y VC-63 corren en macOS y Linux" (1.4).
- [COULD] spec-brownfield.md:830: un VC del orden de las claves por defecto y de `-i` junto con las por defecto (2.8).
- [COULD] spec-brownfield.md:59: FR para `-t` sobre un pane flotante (`can't split a floating pane`, `layout.c:1650`) (3.4).
- [COULD] spec-brownfield.md:213: decidir la codificación del destino (espacios, `-` inicial, IDN) (3.4).
- [COULD] spec-brownfield.md:54-56: decir dónde se agregan `LIBSSH_CFLAGS` y `LIBSSH_LIBS` (B9).
- [COULD] spec-brownfield.md:754-766: sumar a NFR-2 el CPU del hijo (4.2).
- [COULD] spec-brownfield.md:734-738: declarar el costo de memoria por pane (4.5).
- [COULD] spec-brownfield.md:381-388: unificar VC-22 con el chequeo de INV-4 (6.4).
- [COULD] spec-brownfield.md:331-333: pasar el "cómo" de FR-17 (raw en el esclavo) a una nota (M5).

VEREDICTO: NEEDS WORK

# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux), tercera vuelta — (tmux-ssh-tp2/spec-brownfield.md v1.2)
- Commit: TP `c587465` (árbol limpio en `tmux-ssh-tp2/`) · tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` en /tmp/tmux, limpio · libssh `ee5627aa` en /tmp/libssh (master; Ubuntu 24.04 trae 0.10.6) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 58 BR: 5 NFR: 3 VC: 69. Hay 66 en bloque `> **VC-n**` y VC-67…69 en la tabla de §6.7. INV: 7. Contados con `^\*\*FR-[0-9]+ ·` (los FR van en negrita, así que `^#+` da 0). VC (69) ≥ FR+BR (63). No hay IDs duplicados, y la secuencia VC-1…69 no tiene huecos. Coincide con la cabecera (spec-brownfield.md:14) y con `README.md:16`.

## Resumen

La v1.2 cierra los cinco Issues del r2 y el bloqueante del PR:
- FR-20 ya no usa `-n`;
- NFR-2 mide un marcador que no aparece en el eco;
- §9 fija los hostnames, una sola host key ed25519, los logs de `sshd` y cinco jobs, y cada VC tiene dónde correr;
- se agregaron FR-56, FR-57 y FR-58, con la tabla de §7 al día;
- el estado de la cabecera dice "En revisión".

Además se resolvieron casi todos los SHOULD. `check-citas.py` pasa con 128/128, y las citas nuevas que abrí a mano dicen lo que la spec afirma.

Quedan **tres Issues**, todos de redacción y baratos de arreglar:
1. **FR-19** (nuevo en v1.2) tiene un Dado "A o B", y su VC cubre solo A (2.3).
2. **FR-5** tiene el mismo patrón desde v1.0. No lo marqué en r1 ni en r2, pero la cátedra marcó exactamente este patrón en el TP1 (2.3).
3. **FR-57** parte del entorno base, que tiene un agente con una clave autorizada. Su Entonces (error) contradice D-5 ("primero el agente"). Solo el VC agrega "sin agente" (2.8).

El resto son Warnings: el VC-56 no discrimina, y la línea de base afirma "4/4" con dos corridas en crudo, entre otros.

M3: 0 hits que cuenten. `:54`, `:71`, `:145`, `:168`, `:433`, `:556`, `:596`, `:905` y `:991` son "todo/todos" en castellano. · M4: 1 hit, `:192` "sin libssh suficiente", que no cuenta: es un título, y el Dado lo acota a `>= 0.9.0`. · M5: ningún FR ni VC atado a una implementación. Los nombres de funciones de `:54-62` están en la tabla "Dentro". `:342-345` (FR-17, "el hijo pone su terminal en modo raw") sigue prescribiendo un medio, pero el Entonces es observable (Suggestion del r2, sin cambios). `:650` (FR-47, `ssh_client_select_hostkeys`) es explicativo. · M6: el M6 del r2 en BR-1 desapareció: BR-1 ahora enumera los 5 resultados (`:752-759`). `:229`, "Cualquier otra letra es un error de tmux (FR-27)", sigue con un solo VC (`-p`) y queda como Suggestion. No cuentan: `:28` (propósito), `:113`, `:344`, `:371`, `:390-391` y `:555` (prosa), `:591` (es parte del Dado), `:748` (título de BR-1, acotado por VC-59), y `:865`, `:968` y `:972` (entorno).

## Estado de las acciones del r2

| Acción (r2) | Estado | Evidencia en v1.2 |
|---|---|---|
| [MUST] FR-20 sin `-n` | Resuelta | `:377-379`, "sin nombre explícito (`T new-window -d 'sleep 300'`)". Verifiqué que la ventana se renombra al activarse el pane, sin esperar output: `window.c:773` pone `PANE_CHANGED` y `names.c:66` lo consulta |
| [MUST] NFR-2 mide el eco | Resuelta | `:830` `echo __F''IN__`, `:835-836` "una línea **igual a** `__FIN__`". El eco contiene `__F''IN__`, y base64 no produce `_` |
| [MUST] Hostnames en §9 | Resuelta | `:927` `hostname: cliente`, `:936` `hostname: servidor` |
| [MUST] Entorno para VC-2, VC-3 y VC-5 | Resuelta | `:169-170` (los VCs de build no son `regress/`), `:961-968` (jobs `linux-sin-ssh`, `linux-sin-libssh` y `macos`). Las 69 VCs tienen job asignado |
| [MUST] Caminos de falla de `known_hosts` corrupto, `-i` que no es clave y agente que falla | **Parcial** | Se agregaron FR-56 (`:717`), FR-57 (`:726`) y FR-58 (`:736`), y la tabla `:887-889` cita esos FRs. Pero FR-57 contradice D-5 (Issue 2.8 abajo), y VC-56 no discrimina (Warning 3.2) |
| [SHOULD] `iptables`/`iproute2` en `servidor`, log de `sshd` y "esa conexión" | Resuelta | `:933-934`, `:945`, `:166-168` (truncar y una sola conexión por VC). Nuevo: el nombre del log de la instancia 22+2222 es ambiguo (Warning) |
| [SHOULD] VC-47 con host key única ed25519 | Resuelta | `:938-939`, `:647-650`. Confirmado contra libssh: `src/kex.c:707-770` pone primero los tipos de `known_hosts` y después agrega los demás (`ssh_append_without_duplicates`), así que se negocia ed25519 y el resultado es "other type" |
| [SHOULD] Técnica de VC-24 | Resuelta | `:423-427`. `prompt-keys.sh` es PASS en Linux (linea-de-base.md:47). El script guarda el prompt en `@r` (`regress/prompt-keys.sh:70`), no en `@result`: es solo un nombre |
| [SHOULD] Estado de `/etc/ssh/ssh_known_hosts` y precedencia | Resuelta | `:164-165`, BR-1 `:752-759`. La precedencia no tiene VC (Warning 3.1) |
| [SHOULD] Cota de tiempo de §6.4 y de FR-54 | Resuelta | `:559-562` |
| [SHOULD] `T` absoluto o "basename" en FR-19 | **Parcial** | `:365-372`, `:928-929`. Se resolvió con un Dado "por `PATH` o con un path absoluto", que es un Issue 2.3 nuevo |
| [SHOULD] Reasignar VC-33, VC-55 y VC-56 de iteración | Resuelta | VC-33 `:499-503` ya no depende de FR-39. `:1002-1004` está renumerado y es coherente |
| [SHOULD] `pane_start_command` a FR-21, y bordes de `-P` a FR-33 | Resuelta | `:391`, `:497` |
| [SHOULD] VC-15 `exit 0` y VC-2 "no `Makefile`" | Resuelta | FR-15 `:323` ("`n` entre 0 y 255"), FR-2 `:185` |
| [SHOULD] FR-32 acotado y literal de IPv6 | Resuelta | `:486-492` (`servidor:22`), y FR-55 `:538-544` (`::1`) |
| [SHOULD] VC-9 discrimina `[servidor]:2222`, y nombre del host con `-P` ≠ 22 | **Parcial** | `:266-267` ("**única** entrada"). Sigue sin decidirse si FR-43…47 con `-P 2222` dicen `servidor` o `[servidor]:2222` (Suggestion) |
| [SHOULD] `strace` como root | Resuelta | VC-60 `:769` |
| [SHOULD] Fundamentar los 10 s | Resuelta | D-10 `:909`: con SYN a 0, 1, 3 y 7 s, se toleran tres SYN perdidos. Es correcto (RTO inicial de 1 s, duplicado) |
| [SHOULD] notas:296 contra D-11 | Resuelta | notas-exploracion.md:301 |
| [SHOULD] Path real de `snapshot-comandos.sh` | Resuelta | `:137` `sh <este TP>/scripts/snapshot-comandos.sh` |
| [SHOULD] Chequeo ejecutable de `struct window_pane` | Resuelta | `:139` (`sed` sobre el rango + `cmp`) |
| [SHOULD] "VC-5 y VC-63 corren en macOS y Linux" | Resuelta | `:121-122` |
| [COULD] VC del orden de las claves de D-5 | No | Sin cambios (Suggestion) |
| [COULD] `-t` sobre un pane flotante | No | Sin cambios (Suggestion) |
| [COULD] Codificación del destino | No | Sin cambios (Suggestion) |
| [COULD] Dónde van `LIBSSH_CFLAGS`/`LIBSSH_LIBS` | No | `:54` no lo dice (Suggestion B9) |
| [COULD] CPU del hijo en NFR-2 y memoria por pane | No | Sin cambios (Suggestion) |
| [COULD] VC-22 contra INV-4 | No | Sin cambios (Suggestion 6.4) |
| [COULD] El "cómo" de FR-17 a una nota | No | `:342-345` (Suggestion M5) |

## Estado de la revisión de PR

| Ítem (PR) | Estado | Evidencia |
|---|---|---|
| B-1, estado "Revisada" y FRs de los caminos corruptos | Resuelto | `spec-brownfield.md:13` dice "En revisión… NEEDS WORK". Los FRs están en `:717-745` y `:887-888`. El r2 está commiteado con su hash (`ef60d0e`) |
| C-1, notas sobre `default-command` | Resuelto | notas-exploracion.md:108-112. Coincide con `spawn.c:379-386` y `options-table.c:790` |
| C-2, conteos del README | Resuelto | tmux-ssh-tp2/README.md:16, "58 FR, 5 BR, 3 NFR y 69 VCs" |
| C-3, "el handshake bloquea" en las notas | Resuelto | notas-exploracion.md:162-165 |
| C-4, aislamiento prometido | **Parcial** | README.md:20-33 describe el límite real, y `revisor-pr.json` completa el deny y pasa `uv run` a `ask`. Pero `.kiro/agents/corrector-specs.json:46-62` sigue sin `git checkout*` en el deny, y README.md:29-30 afirma "Los comandos destructivos de git … están prohibidos" (`git checkout -- <archivo>` descarta cambios) |
| C-5, crudos de la línea de base | **Parcial** | `linea-de-base/corridas.txt` agrega las sondas, la ambigüedad de `s`, 5/5 de Linux y el sha256 de macOS. Pero linea-de-base.md:45-49 afirma "4/4" y "3/4" en macOS, y corridas.txt:33 tiene "(2 vueltas)". Además, `:46` dice "el mensaje cambia entre corridas" para `check-names.sh`, y en corridas.txt:34 y :41 es el mismo mensaje las dos veces |
| C-6, `brownfield-context/` en `.gitignore` | Resuelto | `.gitignore:7` |
| C-7, el prompt promete chequear funciones | Resuelto | `.kiro/agents/prompts/revisor-pr.md:26-29` |

## Hallazgos por dimensión

### 1. Propósito y alcance — PASS
- Sin hallazgos nuevos. Cada flag de la sinopsis (`:223`) tiene su FR. "Fuera" va por path (`:66-81`) y por comportamiento (`:87-98`). Hay actores no humanos (`:36-40`). El plan de iteraciones cubre las 69 VCs sin asignar ninguna a una iteración en la que no puede pasar (`:1002-1004`).

### 2. Completitud y consistencia — FAIL
- **Issue (2.3)** · spec-brownfield.md:365-366, FR-19: "**Dado** una sesión abierta, y un servidor `tmux` arrancado como `tmux` (por `PATH`) **o** con un path absoluto". Son dos situaciones distintas (`argv[0]` = `tmux` y `argv[0]` = `/usr/local/bin/tmux`) con un mismo resultado. Es el patrón exacto que la cátedra marcó en el TP1 ("permiso denegado **o** error transitorio"). VC-19 (`:374`) cubre solo la rama `PATH`, porque §9 (`:928-929`) invoca por `PATH`. La rama del path absoluto queda sin VC. Se arregla dejando el Dado en "por `PATH`" y pasando la frase del path absoluto a una nota, o con un FR propio y un VC con `T=$(command -v tmux)`.
- **Issue (2.3)** · spec-brownfield.md:210, FR-5: "**Dado** un `tmux` compilado sin `--enable-ssh`, en macOS **o** en Linux". Es el mismo patrón, y viene desde v1.0. No lo marqué en r1 ni en r2, y lo corrijo acá. Las dos situaciones corren en jobs distintos (`:965`, `:967`), así que no se pueden observar en una sola ejecución. Se arregla partiendo el FR en FR-5a (Linux sin el flag) y FR-5b (macOS), cada uno con su VC. La tabla de `:104-107` ya los separa.
- **Issue (2.8)** · spec-brownfield.md:727-732, FR-57: "**Dado** que `/tmp/notakey` se puede leer pero no es una clave privada … **entonces** la línea es `ssh-pane: identity file /tmp/notakey is not a valid private key`". §6.4 dice "Todos los casos parten del entorno base y cambian solo lo que dice el **Dado**" (`:556`), y el entorno base tiene "un `ssh-agent` … con una clave autorizada para `alice`" (`:161`). D-5 (`:904`) dice "**Primero el agente** … **Después**, claves … la de `-i`", y FR-11 (`:284-290`) lo confirma: con agente y `-i`, gana el agente. Así como está escrito, una implementación que sigue D-5 se conecta, otra que valida `-i` antes da el error, y las dos pasan VC-57, porque solo el VC dice "sin agente en el entorno" (`:734`). Hay que agregar "y no hay agente" al Dado, como en FR-49 (`:667`) y FR-50 (`:676`), o decidir en D-5 que un `-i` inválido aborta antes de probar el agente.
- Warning (2.8/5.6) · spec-brownfield.md:910, D-11: "¿Qué comando guarda el pane? | **Ninguno.** … Así, `respawn-pane` corre `default-command` o una shell de login local (`spawn.c:380`, FR-21)". Es cierto solo con `default-command` vacío:
  - Al crear el pane, con `default-command` no vacío, `spawn.c:380-383` pone `argc = 1` con el valor de la opción, y `spawn.c:398-402` lo guarda en `wp->argv`. Entonces el pane **sí** guarda un comando, y `#{pane_start_command}` lo muestra.
  - En el respawn, `spawn.c:379` excluye `SPAWN_RESPAWN` y no consulta la opción: se usa lo guardado al crear el pane.

  FR-21 se salva porque su Dado fija la opción vacía (`:387-388`), pero el caso no vacío, una configuración común, no está declarado. Hay que corregir la frase de D-11, o decir en FR-21 qué pasa con `default-command` no vacío.
- Warning (2.8) · spec-brownfield.md:166 y :942: "cada instancia escribe en `/var/log/sshd-<puerto>.log`" y "una en el 22 y el 2222". Una instancia con dos puertos tiene un solo `-E`, y la spec no dice si el archivo es `sshd-22.log` o `sshd-2222.log`. VC-11 y VC-58 leen ese log.
- 2.1 sin hallazgos: 58/58 FRs tienen Dado, Cuando y Entonces. 2.7 sin otros hallazgos: los 2.7 del r2 se subieron a sus FRs. El de VC-57 está registrado arriba como 2.8.

### 3. Casos borde y verificabilidad — WARN
- Warning (3.2) · spec-brownfield.md:717-724, FR-56/VC-56: "cuya primera línea es basura (`esto no es una entrada`)". El fixture no discrimina:
  - libssh lee primero el host de cada línea y, si no coincide, devuelve `SSH_AGAIN` y la saltea sin parsear el resto (`src/knownhosts.c:291-295`, y `ssh_known_hosts_parse_line` `:671+`, `rc = SSH_AGAIN` si `match == 0`). Como `esto` no es `servidor`, cualquier implementación ignora esa línea.
  - El caso que decide BR-1 `:759` es una línea **para `servidor`** mal formada, por ejemplo `servidor ssh-ed25519 !!!`. Con libssh, esa línea hace `goto error` (`:296-297`), aborta la lectura entera, y daría FR-45 o un error genérico, no una conexión.

  El VC tiene que usar una línea mal formada con el host `servidor`.
- Warning (3.1) · spec-brownfield.md:752-759, BR-1: el orden de decisión (1 a 5) no tiene VC. VC-59 (`:761`) solo prueba que no se escribe. Ningún VC prueba, por ejemplo, que el archivo global con la clave buena gane sobre el del usuario con otra clave (paso 2 antes que el 3), ni que un global ilegible dé FR-45 aunque el del usuario coincida (paso 1).
- Suggestion (3.4) · spec-brownfield.md:951-954: los fixtures de §9 nombran "las claves de FR-10, FR-11 y FR-48 a FR-50", pero no las de FR-56, FR-57 (`/tmp/notakey`) ni FR-58 (el agente bloqueado con `ssh-add -x`, que pide una passphrase de bloqueo de forma interactiva y necesita `SSH_ASKPASS`).
- Suggestion (3.4) · spec-brownfield.md:551-557: el encabezado de §6.4 dice "El hijo escribe una línea … y termina con status 255", pero FR-51, FR-56 y FR-58 son conexiones exitosas. Conviene moverlos de sección o exceptuarlos.
- Suggestion (3.3) · spec-brownfield.md:889: "Agente | … | — | — | —". Un socket que existe y no tiene a nadie escuchando, y un agente que muere a mitad de la autenticación, siguen sin FR. FR-58 cubre el agente bloqueado.
- Suggestion (3.2, sigue del r2): con `-P` ≠ 22, el nombre del host en FR-43…47 no está decidido.
- 3.3 sin otros hallazgos: la tabla `:883-890` cierra contra FRs reales. 3.6 sin hallazgos: VC-6 es end-to-end contra un `sshd` real (`:957-959`), y §9 ya permite correrlo.

**Ejercicio 3.5.** Feliz, FR-56:

```sh
# entorno §9, job linux-ssh, como alice en "cliente"; T="tmux -Ltest -f/dev/null" (por PATH)
$T new-session -d -x 200 -y 50; $T set -g remain-on-exit on
{ echo 'esto no es una entrada'; ssh-keyscan -t ed25519 servidor; } > ~/.ssh/known_hosts
# decisión: obtengo la entrada buena con ssh-keyscan (§9 dice "las entradas de cada VC", sin decir cómo)
antes=$($T list-panes -a -F '#{pane_id}' | sort)
$T ssh-pane -t %0 alice@servidor; test $? -eq 0
nuevo=$(comm -13 <(echo "$antes") <($T list-panes -a -F '#{pane_id}' | sort))
$T send-keys -t "$nuevo" 'echo "R=$(hostname):$(id -un):$(tty)"' Enter
for i in $(seq 30); do $T capture-pane -pJ -t "$nuevo" | grep -q 'R=servidor:alice:/dev/pts/' && break; sleep 0.1; done
```

Decisiones que tuve que tomar: cómo se genera la entrada buena (menor). El test pasa con una implementación que **rechaza** las líneas mal formadas de `servidor`, porque la línea de basura no es de `servidor` (Warning 3.2).

Falla, FR-57:

```sh
cp /etc/hostname /tmp/notakey
unset SSH_AUTH_SOCK          # decisión: lo saca el VC (:734); el Dado del FR no lo dice (Issue 2.8)
$T ssh-pane -i /tmp/notakey alice@servidor; test $? -eq 0
for i in $(seq 120); do      # cota común de 12 s (:559)
  test "$($T display -p -t "$nuevo" '#{pane_dead} #{pane_dead_status}')" = "1 255" && break; sleep 0.1
done
$T capture-pane -pJ -t "$nuevo" | grep -qxF 'ssh-pane: identity file /tmp/notakey is not a valid private key'
```

Decisiones que tuve que tomar: sacar el agente, que en el FR no está escrito. Con el agente del entorno base, el FR y D-5 dan resultados opuestos.

### 4. Requerimientos no funcionales — PASS
- 4.1 a 4.4 sin hallazgos:
  - NFR-1 (`:816-820`) y NFR-2 (`:826-839`) tienen métrica, número y carga en el enunciado;
  - el marcador de NFR-2 discrimina (ver la tabla);
  - VC-66 cubre las tres condiciones de NFR-3;
  - D-10 hace explícitas las políticas.
- Suggestion (4.2/4.5, siguen del r2): falta el CPU del hijo en NFR-2 y el costo de memoria por pane.

### 5. Tecnología y fundamento — WARN
- Warning (5.6/B1) · spec-brownfield.md:649-650, FR-47: "libssh pone primero los tipos de `known_hosts`, pero agrega los demás (`ssh_client_select_hostkeys`, N-7)". N-7 (notas-exploracion.md:241-273) no dice eso, ni nombra la función. El dato es correcto (`libssh src/kex.c:707-770`, verificado), pero se atribuye a una nota que no lo contiene. Hay que sumarlo a N-7.
- Suggestion (5.4) · spec-brownfield.md:753 y FR-45 `:630-633`: "Si alguno de los dos archivos existe y no se puede leer, FR-45". libssh hace lo contrario por defecto: si `fopen` falla, la lectura no da error (`src/knownhosts.c:247-254`, "The missing file is not an error here"), y un `known_hosts` en modo `000` termina en "unknown" (FR-43). El requisito está bien decidido, pero el trade-off (hay que chequear la legibilidad aparte, antes de libssh) no está escrito. Un implementador que confía en libssh falla VC-45.
- 5.1 a 5.3 y 5.5 sin otros hallazgos: D-10 fundamenta los 10 s, VC-60 corre como root, y D-1 a D-16 tienen lo descartado.

### 6. Simplicidad — PASS
- Suggestion (6.4, sigue del r2): VC-22 y el chequeo de INV-4 son el mismo `diff`.

### B. Extensión brownfield — WARN
- Warning (B4) · tmux-ssh-tp2/linea-de-base.md:45-49 contra linea-de-base/corridas.txt:33-47: la tabla afirma "4/4 FAIL", "3/4 FAIL" y "4/4 PASS solos" en macOS, y el crudo tiene "Re-corridas solas (2 vueltas)". En el crudo, `prompt-words-history.sh` es 1/2. Además, `:46` dice "el mensaje cambia entre corridas" para `check-names.sh`, y el crudo muestra el mismo mensaje (`got '..x-mac/regress'`) las dos veces. INV-6 (`:140`) compara contra esta tabla, así que lo que no está en crudo no se puede verificar.
- Suggestion (B9, sigue del r2) · spec-brownfield.md:54: dónde se agregan `LIBSSH_CFLAGS`/`LIBSSH_LIBS`.
- B1: `TMUX_SRC=/tmp/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 128 citas verificadas contra tmux@5a820e6`, exit 0, sin fallos (eran 122 en r2). Abrí a mano las seis citas nuevas de `citas.tsv`, y todas dicen lo que la spec y las notas afirman:
  - `format.c:975`, `value = parse_window_name(cmd)`, dentro de `format_cb_current_command` (`:957`), que usa `osdep_get_name`;
  - `names.c:167`, `if (*name == '/') name = basename(name)`;
  - `spawn.c:223`, que apaga `automatic-rename` con `-n`;
  - `options-table.c:790`, `.default_str = ""`;
  - `spawn.c:385-386`, `argc = 0; argv = NULL`;
  - `spawn.c:574`, `execl(new_wp->shell, argv0, …)`.

  Verifiqué además que en Linux `setproctitle` usa `PR_SET_NAME` (`compat/setproctitle.c:25-46`) y no toca `/proc/<pid>/cmdline`, que es lo que lee `osdep_get_name` (`osdep-linux.c:41-55`). Así, el `tmux` de FR-19 se sostiene. Lo único que no se sostiene es la atribución de FR-47 a N-7 (5.6, arriba).
- B2, B3, B5, B6, B7 y B8 sin hallazgos:
  - "Fuera" va por path (`:66-81`);
  - las 7 invariantes tienen un chequeo ejecutable (`:136-142`);
  - el límite de plataforma tiene guarda, mensaje y VC en macOS con job propio (`:967`);
  - ningún FR nuevo necesita un archivo fuera de "Dentro";
  - `git diff --name-only cc123c2 c587465 | grep -E '\.(c|h)$'` da vacío, y `/tmp/tmux` está limpio;
  - D-1 a D-6 tienen lo descartado.
- B9: un lector hostil no rompe un build no-Linux ni un comando existente. Lo peor que puede hacer ahora es lo de FR-57 (validar `-i` antes del agente, o al revés, y cumplir igual) y confiar en libssh para FR-45 y FR-56.

## Veredicto general   NEEDS WORK

## Acciones (priorizadas)
- [MUST] spec-brownfield.md:365-366: dejar el Dado de FR-19 en "arrancado por `PATH`" y pasar el caso del path absoluto a una nota, o a un FR propio con su VC (2.3).
- [MUST] spec-brownfield.md:209-216: partir FR-5 en Linux sin el flag y macOS, con un VC cada uno (2.3).
- [MUST] spec-brownfield.md:727-728: agregar "y no hay agente" al Dado de FR-57, o decidir en D-5 (`:904`) que un `-i` inválido aborta antes del agente (2.8).
- [SHOULD] spec-brownfield.md:718: usar en VC-56 una línea mal formada **para `servidor`** (2.8/3.2).
- [SHOULD] spec-brownfield.md:910: corregir D-11 para el caso de `default-command` no vacío, o declararlo en FR-21 (`spawn.c:379-402`) (2.8/5.6).
- [SHOULD] spec-brownfield.md:752-761: un VC que pruebe el orden de BR-1 con los dos archivos (3.1).
- [SHOULD] spec-brownfield.md:166 y :942: nombrar el log de la instancia 22+2222 (2.8).
- [SHOULD] notas-exploracion.md:261-273: agregar a N-7 lo de `ssh_client_select_hostkeys` que cita FR-47 (`:650`) (5.6).
- [SHOULD] linea-de-base.md:45-49: registrar en `corridas.txt` las 4 vueltas de macOS, o bajar los conteos a 2/2, y corregir "el mensaje cambia" (B4).
- [SHOULD] .kiro/agents/corrector-specs.json:46-62: agregar `git checkout*` al deny, o matizar README.md:29-30 (PR C-4).
- [COULD] spec-brownfield.md:630-633: anotar que libssh no da error con un `known_hosts` ilegible (`knownhosts.c:247-254`), así que FR-45 necesita un chequeo propio (5.4).
- [COULD] spec-brownfield.md:951-954: sumar a los fixtures los de FR-56, FR-57 y FR-58 (`SSH_ASKPASS` para `ssh-add -x`) (3.4).
- [COULD] spec-brownfield.md:551-557: sacar FR-51, FR-56 y FR-58 de la regla "status 255" de §6.4 (3.4).
- [COULD] Los que siguen del r2 sin cambios: el orden de las claves de D-5, `-t` sobre un pane flotante, la codificación del destino, `LIBSSH_LIBS`, el CPU y la memoria del hijo, VC-22 contra INV-4, el "cómo" de FR-17 y el host con `-P` ≠ 22 en los mensajes.

VEREDICTO: NEEDS WORK

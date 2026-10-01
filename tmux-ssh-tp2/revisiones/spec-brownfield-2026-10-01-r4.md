# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux), cuarta vuelta (confirmación) — (tmux-ssh-tp2/spec-brownfield.md v1.3)
- Commit: TP `4c45485` · tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` en /tmp/tmux (árbol limpio) · libssh `ee5627aa` en /tmp/libssh · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 58 BR: 5 NFR: 3 VC: 69. Hay 66 en bloque `> **VC-n**` (VC-6 lleva un sufijo, "(end-to-end, ver §9)", que un `grep` estricto no cuenta) y VC-67…69 en la tabla de §6.7. INV: 7. No hay IDs duplicados, la secuencia VC-1…69 no tiene huecos, y VC (69) ≥ FR+BR (63). Coincide con la cabecera (`:14`) y con `README.md:16`.

## Resumen

v1.3 resuelve los tres Issues del r3:
- **FR-19** tiene un solo Dado, "por `PATH`".
- **FR-5** cubre solo Linux. El caso de macOS pasa a INV-1, que ahora chequea `unknown command: ssh-pane` con exit 1.
- **El Dado de FR-57** fija "no hay agente", así que ya no contradice D-5.

También cierra todos los Warnings del r3, verificados contra el código:
- D-11 coincide con `spawn.c:379-402`;
- el fixture de VC-56 discrimina;
- VC-59 prueba el orden de BR-1;
- se nombran los logs de `sshd`;
- N-7 ya sostiene lo que le atribuye FR-47;
- la línea de base tiene sus 4 vueltas en crudo;
- `git checkout*` está en el deny.

`check-citas.py` da 128/128. Las dos citas que elegí al azar dicen lo que la spec afirma, y el diff no toca ningún `.c` ni `.h`.

Ningún cambio de v1.3 introduce un Issue. Queda un Warning nuevo, del mismo tipo que el de FR-45 que v1.3 arregló: libssh **aborta** la lectura con la línea de FR-56, y la spec no lo dice (5.4). El resto son Suggestions que vienen de rondas anteriores. **No hay bloqueantes.**

M3: 0 hits que cuenten. `:54`, `:71`, `:146`, `:169`, `:435`, `:558`, `:601`, `:921` y `:1011` son "todo/todos" en castellano. · M4: 1 hit, `:193` "sin libssh suficiente", que no cuenta: es un título, y el Dado lo acota a `>= 0.9.0`. · M5: sin cambios respecto del r3. La tabla "Dentro" (`:54-62`) puede nombrar funciones. FR-17 prescribe el modo raw (Suggestion). · M6: el único hit nuevo es `:374`, "como pasa hoy con cualquier programa", que es prosa y no cuenta. `:729`, "una basura cualquiera", es prosa. `:231` (FR-27, "cualquier otra letra") sigue con un solo VC (Suggestion). El resto es lo mismo que en el r3.

## Estado de los Issues y Warnings del r3

| Hallazgo (r3) | Estado | Evidencia en v1.3 |
|---|---|---|
| **Issue 2.3**: FR-19 con Dado "A o B" | **Resuelto** | `:367-368`, "con el servidor `tmux` arrancado como `tmux`, por `PATH` (que es como lo arranca §9)". Las otras formas de arrancarlo quedan fuera de v1, en prosa: `:373-374`, "v1 no lo fija". §9 instala en `/usr/local/bin` y lo invoca por `PATH` (`:944-945`), así que VC-19 cubre el Dado entero |
| **Issue 2.3**: FR-5 "macOS o Linux" | **Resuelto** | `:210-218`, FR-5 solo para Linux, con VC-5 en `linux-sin-ssh` (`:985`). macOS pasa a INV-1 (`:136`): "`./tmux ssh-pane host` imprime `unknown command: ssh-pane` y sale con 1", con VC-67 en `macos` (`:879`, `:987`). La tabla de §4 (`:106`), "Fuera" (`:87`) y `:121-123` están al día. No quedan referencias a FR-5/VC-5 en macOS (busqué con `grep` en la spec, el README, las notas y la línea de base). La línea de base registra el mismo stderr y exit en los dos SO (linea-de-base.md:35, corridas.txt:30-32) |
| **Issue 2.8**: FR-57 contra D-5 | **Resuelto** | `:737-738`, "**Dado** que no hay agente (`SSH_AUTH_SOCK` sin definir)". VC-57 (`:744`) ya no agrega condiciones. D-5 (`:920`), "la de `-i` si se pasó; si no, …", deja sin ambigüedad que con `-i` no se prueban las claves por defecto, así que el error de FR-57 es el único resultado posible |
| W 2.8/5.6: D-11 con `default-command` no vacío | Resuelto | `:926`. Lo verifiqué en `spawn.c:379-402`: con `argc == 0` y sin `SPAWN_RESPAWN`, una opción no vacía da `argc = 1` y se guarda en `new_wp->argv`. En el respawn se usa lo guardado |
| W 2.8: log de la instancia 22+2222 | Resuelto | `:961-963`, "La del 2222 escribe en `sshd-22.log`" |
| W 3.2: VC-56 no discrimina | Resuelto | `:725-729`, la línea es `servidor ssh-ed25519 esto-no-es-base64`. Ver el Warning 5.4 nuevo |
| W 3.1: el orden de BR-1 sin VC | Resuelto | `:776-779`. Prueba el paso 2 antes que el 3 (archivo del usuario con otra ed25519, global con la correcta: abre) y el paso 1 primero (usuario en `000`, global correcto: FR-45). Lo comparé con libssh: el primer caso da OK, porque las entradas de los dos archivos se juntan y gana la que coincide. El segundo **no** lo da libssh, y FR-45 `:638-640` ya lo dice |
| W 5.6/B1: FR-47 atribuye a N-7 algo que N-7 no decía | Resuelto | notas-exploracion.md:274-278 ahora dice `ssh_client_select_hostkeys` y el orden de tipos |
| W B4: "4/4" con 2 vueltas en crudo | Resuelto | corridas.txt:33-63 tiene dos tandas de 2 vueltas. Cuadran con la tabla: `check-names`, `prompt-keys` y `screen-redraw-menus` dan 4/4 FAIL; `prompt-words-history`, 3/4; y `check-names` cambia de mensaje (`'zsh'` en `:34`, `'..x-mac/regress'` en las demás). No puedo verificar cuándo se corrió la primera tanda: el crudo no tiene timestamp |
| W PR C-4: `git checkout*` fuera del deny | Resuelto | `.kiro/agents/corrector-specs.json:49` (y `git switch*` en `:59`) |
| S 5.4: FR-45 y libssh | Resuelto | `:638-640` y notas-exploracion.md:279-281 |
| S 3.4: fixtures de FR-56/57/58 | Resuelto en parte | `:969-974` los nombran. No dicen cómo bloquear el agente sin una tty (`ssh-add -x` pide la passphrase de bloqueo). Sigue como Suggestion |
| S 3.4: §6.4 contra FR-51, FR-56 y FR-58 | Resuelto | `:561-562` |
| Las demás Suggestions (r2/r3) | Sin cambios | El orden de claves de D-5, `-t` sobre un pane flotante, la codificación del destino, `LIBSSH_LIBS`, el CPU y la memoria del hijo, VC-22 contra INV-4, el "cómo" de FR-17, el host con `-P` ≠ 22 en los mensajes, el agente que muere a mitad de la autenticación, y FR-27 con un solo VC |

## Hallazgos por dimensión

### 1. Propósito y alcance — PASS
- Sin hallazgos. Lo de "Fuera" y la tabla de §4 se actualizó para el nuevo reparto FR-5/INV-1 (`:87`, `:106`).

### 2. Completitud y consistencia — PASS
- Sin Issues. Hice una pasada de 2.3 sobre los 58 FRs, buscando un "o" en el Dado o un Entonces condicional:
  - FR-19, FR-5 y FR-57 ya están bien.
  - FR-56 (`:725-730`) describe una sola situación con dos líneas de un mismo archivo, y no cuenta.
  - BR-1 (`:758-766`) es una regla ordenada con un VC por paso que importa, y no un FR.
- 2.7: VC-57 ya no agrega condiciones. La parte "El orden" de VC-59 (`:776-779`) prueba lo que BR-1 dice, y no agrega nada.
- 2.8: los tres pendientes del r3 (FR-57, D-11 y el log) están decididos dentro de la spec.

### 3. Casos borde y verificabilidad — PASS
- Sin Issues ni Warnings nuevos.
- Suggestion (3.4) · `:972-974`, "el agente bloqueado con `ssh-add -x` de FR-58". No dice cómo se bloquea en CI sin una tty (por ejemplo, con `SSH_ASKPASS` y `SSH_ASKPASS_REQUIRE=force`). Viene del r3 y no bloquea: el estado del agente es observable con `ssh-add -l`.
- 3.6: VC-6 sigue siendo end-to-end contra un `sshd` real (§9).

**Ejercicio 3.5**, rehecho sobre v1.3:
- **Falla, FR-57.** El test del r3 queda igual, con `unset SSH_AUTH_SOCK` como **parte del Dado** (`:737`), no como una decisión mía. No tuve que decidir nada más: la cota de 12 s es la de `:564`, y el texto, el de `:741`.
- **Feliz, FR-56.** El fixture es `{ echo 'servidor ssh-ed25519 esto-no-es-base64'; ssh-keyscan -t ed25519 servidor; } > ~/.ssh/known_hosts`, y el observable es el de VC-6. Tuve que decidir cómo generar la entrada buena (`ssh-keyscan`). Es menor: §9 dice "las entradas de `known_hosts` de cada VC" (`:970`). Ahora el test sí discrimina: con libssh sin chequeo propio, falla (ver 5.4).

### 4. Requerimientos no funcionales — PASS
- Sin cambios ni hallazgos. Las Suggestions de CPU y memoria siguen del r2.

### 5. Tecnología y fundamento — WARN
- Warning (5.4) · spec-brownfield.md:727-729, FR-56: "Tiene que ser para `servidor`: libssh no parsea las líneas de otros hosts". La frase dice por qué el fixture apunta a `servidor`, pero no el trade-off que eso implica. En libssh, cuando una línea **del host** no se parsea, se aborta la lectura del archivo entero:
  - `ssh_known_hosts_parse_line` da `SSH_ERROR` cuando el tipo o la clave no se pueden leer (`src/knownhosts.c:777-787` y siguientes);
  - `ssh_known_hosts_read_entries` hace `goto error` ante cualquier `rc != SSH_OK` que no sea `SSH_AGAIN` (`src/knownhosts.c:291-297`).

  Así, una implementación que delega en `ssh_session_is_known_server` da un error de verificación, no la sesión que pide FR-56. notas-exploracion.md:281 dice solo lo de los otros hosts. Es el mismo patrón de FR-45, que v1.3 resolvió escribiendo "el chequeo de legibilidad es del cliente" (`:639-640`). Falta la frase equivalente: el parseo de `known_hosts` (o al menos el filtrado de líneas mal formadas) es propio y no de libssh. VC-56 atrapa la implementación ingenua, así que no bloquea.
- 5.1 a 5.3, 5.5 y 5.6 sin otros hallazgos. D-11 ya coincide con el código (verificado arriba).

### 6. Simplicidad — PASS
- Sin hallazgos nuevos. La Suggestion de VC-22 contra INV-4 sigue del r2.

### B. Extensión brownfield — PASS
- B1: `TMUX_SRC=/tmp/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 128 citas verificadas contra tmux@5a820e6`, exit 0, sin fallos. Abrí dos citas al azar de `citas.tsv`:
  - **`spawn.c:504`** (`#if defined(HAVE_SYSTEMD) && defined(ENABLE_CGROUPS)`, D-2). Está en el camino del hijo después del `fork`, antes de `environ_push` (`:544`). Sostiene "en el hijo, como systemd".
  - **`layout.c:1674`** (`} else if (args_has(args, 'p')) {`, N-8/D-8). `layout_get_tiled_cell` lee `-p` como porcentaje 0-100 (`:1674-1677`). Sostiene que `-p` no puede ser el puerto.

  También confirmé, de las citas nuevas o tocadas en v1.3, `tmux.h:2531` (`SPAWN_FLOATOVERZOOM`), `layout.c:1640` (`layout_get_tiled_cell`) y `input.c:1028` (`input_parse_pane`).
- B4: resuelto (ver la tabla). La regla de INV-6 se aplica contra una tabla que ahora cuadra con el crudo.
- B5: el límite de plataforma sigue completo:
  - la guarda (`configure.ac` `$host_os`, `AM_CONDITIONAL` y `#ifdef`);
  - qué ve el usuario en no-Linux con el flag (FR-2/VC-2) y sin el flag (INV-1/VC-67, ahora con el stderr literal);
  - los dos VCs, en el job `macos`.
- B7: `git diff --name-only c587465 4c45485 | grep -E '\.(c|h)$'` da vacío, y `/tmp/tmux` está limpio.
- B2, B3, B6, B8: sin cambios ni hallazgos. La nueva línea de INV-1 es ejecutable, y FR-45/56 caen en `ssh-pane.c`, que está en "Dentro" (`:59`).
- B9: un lector hostil no puede romper un build no-Linux, cambiar un comando existente ni tocar el modelo de PTY/panes. Lo peor que queda es delegar `known_hosts` entero en libssh y fallar VC-45/VC-56, y eso lo detectan los VCs.

## Veredicto general   READY

No hay Issues abiertos. El único Warning (5.4, FR-56) es de fundamento, no de comportamiento: el requisito y su VC son inequívocos.

## Acciones (priorizadas)
- [SHOULD] spec-brownfield.md:727-729 y notas-exploracion.md:281: agregar que libssh aborta la lectura de `known_hosts` ante una línea mal formada **del host** (`src/knownhosts.c:291-297`), así que el filtrado de FR-56 es del cliente, igual que la legibilidad de FR-45 (5.4).
- [COULD] spec-brownfield.md:972-974: decir cómo se bloquea el agente de FR-58 sin una tty (3.4).
- [COULD] Las Suggestions que siguen de r2/r3: el orden de claves de D-5, `-t` sobre un pane flotante, la codificación del destino, `LIBSSH_LIBS` (`:54`), el CPU y la memoria del hijo, VC-22 contra INV-4, el "cómo" de FR-17, el host con `-P` ≠ 22 en los mensajes, el agente que muere a mitad de la autenticación, y FR-27 (`:231`) con un solo VC.

VEREDICTO: READY

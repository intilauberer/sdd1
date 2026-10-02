# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux), quinta vuelta (v1.4 + v1.5) — (tmux-ssh-tp2/spec-brownfield.md v1.5)
- Commit: TP `5033d42` (rama `tp2/spec-v1.5-granularidad`; diff de referencia `6ac25ef..5033d42`, que incluye `62ece13`) · tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` en `tmux-ssh-tp2/.cache/tmux` (árbol limpio) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 62 BR: 5 NFR: 3 VC: 80. Son 72 en bloque `> **VC-n**` (VC-6 incluido, con su sufijo "(end-to-end, ver §9)") y 8 en la tabla de §6.7 (VC-67, VC-68a…e, VC-69a/b). INV: 7. Los IDs de FR son FR-1…32, FR-33a/b, FR-34a/b, FR-35…60; los de VC, VC-1…32, VC-33a/b, VC-34a/b, VC-35…58, VC-59a/b/c, VC-60…67, VC-68a…e, VC-69a/b, VC-70, VC-71. Sin duplicados (`sort | uniq -d` vacío). VC (80) ≥ FR+BR (67). Coincide con la cabecera (`:14`, "FR: 62 … VC: 80") y con `README.md:16`.

## Resumen

v1.4 y v1.5 no introducen Issues.

**Lo que está bien:**
- **Las citas de tmux son ciertas en el commit fijado.**
  - `cmd-parse.y:1710` expande `~` salvo entre comillas simples (`:1709`, `state != SINGLE_QUOTES`).
  - `server-client.c:2926` devuelve, según el caso, el cwd de `cfg_client`, el del cliente, el de la sesión, `~` o `/` (`:2930-2940`), tal como dice D-18.
  - `tmux.c:435` es `main()`.
  - `spawn.c:541` es el `closefrom` que cita D-17.
- **Las tres decisiones nuevas tienen alternativa descartada y fundamento.** D-17 además declara su costo.
- **FR-59 y FR-60 son atómicos.**
- **La trazabilidad cuadra.** §7, la matriz de fallas, los jobs de §9 y el plan de §11 cubren los 80 VCs sin huérfanos.
- **`check-citas.py` da 133/133.**

**Lo que hay que arreglar:** dos Warnings, ninguno bloqueante.
1. **FR-34: la partición angostó el contrato (2.8).** En v1.3 el Dado de FR-34 era una clase ("un `<path>` que el usuario del servidor `tmux` no puede abrir para lectura"). En v1.5, FR-34a y FR-34b son dos instancias, `/nonexistent` y `/tmp/k000` en modo `000`. Por eso la afirmación del Historial, "No cambia ningún comportamiento", no es exacta: un `-i /etc/shadow` estaba decidido y ahora no lo está.
2. **El orden de FR-59 no tiene VC (3.4).** FR-59 dice que su chequeo va antes que FR-34a/b, pero VC-70 solo prueba paths relativos que existen. Una implementación con el orden invertido pasa.

El Warning 5.4 del r4 (FR-56 y libssh) está resuelto. El resto son Suggestions.

M3: 0 hits que cuenten. `:54`, `:71`, `:146`, `:169`, `:453`, `:602`, `:645`, `:984`, `:995` (D-17, "todos los panes", nuevo), `:1077` y `:1088` son "todo/todos/todas" en castellano. · M4: 1 hit, `:193` "sin libssh suficiente". Es un título, el Dado lo acota a `>= 0.9.0` y no cuenta. · M5: sin cambios respecto del r4. FR-59 y FR-60 no nombran funciones. El "pedido `env`" de FR-60 (`:334-335`) es un mensaje del protocolo SSH, observable, y no ata a una implementación. Las funciones que aparecen en D-17/D-18 (`server_client_get_cwd`, `main()`) están en §8, no en un FR/VC. · M6: hits nuevos, que no cuentan:
- `:937-938` y `:1054`, "cualquier clon": describen el entorno, no un comportamiento;
- `:995`, "todos los panes": prosa de D-17;
- `:817`, VC-59a "Nunca escribe": lo acotan los cinco VCs que enumera.

Fuera del patrón, `:334` (FR-60, "no manda **ningún** pedido `env`") es un universal que VC-71 acota a una sola variable (Suggestion 3.2). `:231`, FR-27 con un solo VC, sigue del r2.

## Estado de los Warnings y Suggestions abiertos del r4

| Hallazgo (r4) | Estado en v1.5 | Evidencia |
|---|---|---|
| **W 5.4** · FR-56: libssh aborta la lectura de `known_hosts` ante una línea mal formada del host, y la spec no lo decía | **Resuelto** | `:776-778`: "libssh, en cambio, deja de leer el archivo entero ante una línea mal formada del host (N-7), así que ese filtrado lo hace el cliente antes de verificar". notas-exploracion.md:281-283: "una línea **del host** que no se puede parsear corta la lectura del archivo entero (`goto error`)". Ya estaba en `6ac25ef` |
| S 3.4 · Cómo se bloquea el agente de FR-58 sin una tty | Sigue | `:1040`, "el agente bloqueado con `ssh-add -x` de FR-58", sin cambios. No hay `SSH_ASKPASS` en la spec |
| S · El orden de las claves por defecto de D-5 | Sigue | `:983` sin cambios |
| S · `-t` sobre un pane flotante | Sigue | Sin cambios |
| S · Codificación del destino | Sigue | Sin cambios. FR-28…32 y FR-55 no cubren bytes que no son ASCII |
| S · `LIBSSH_LIBS` | Sigue | `:54` sin cambios |
| S 4.2/4.5 · El CPU del hijo en NFR-2 y la memoria por pane | Sigue | D-17 (`:995`) trata la memoria heredada como exposición de seguridad, no como costo por pane. NFR-2 (`:891`) sigue sin medir el CPU |
| S 6.4 · VC-22 contra INV-4 | Sigue | `:422` sin cambios |
| S M5 · El "cómo" de FR-17 (modo raw) | Sigue | `:362`, "el hijo pone **su** terminal … en modo raw" |
| S · El host con `-P` ≠ 22 en los mensajes de §6.4 | Sigue | FR-43 (`:659`) y los demás siguen diciendo "for servidor" |
| S · El agente que muere a mitad de la autenticación | Sigue | Sin FR |
| S · FR-27 con un solo VC | Sigue | `:231`, "Cualquier otra letra", con VC-27 solo para `-p` |

## Hallazgos por dimensión

### 1. Propósito y alcance — PASS
- Sin hallazgos. `-i` sigue dentro de alcance con FR-10, FR-34a/b, FR-57 y FR-59. El descarte del modo helper de D-17 no deja alcance diferido especificado, solo un puntero a "otra spec" (`:995`).

### 2. Completitud y consistencia — WARN
- **Warning (2.8)** · spec-brownfield.md:534 (FR-34a), "**Dado** que `/nonexistent` no existe". También :541 (FR-34b), "**Dado** que `/tmp/k000` existe y tiene modo `000`".
  - **Qué cambió.** En `6ac25ef`, FR-34 decidía una clase: "**Dado** un `<path>` que el usuario del servidor `tmux` no puede abrir para lectura". VC-34 la muestreaba con esos dos casos. Al partirla, el Dado pasó de la clase a las muestras, así que todo lo que no es "este path no existe" ni "este archivo tiene modo `000`" quedó sin decidir. Algunos ejemplos: `/etc/shadow` (0640 `root:shadow`), un archivo 0200, un symlink colgado, `/root/k` como `alice`.
  - **Dos implementaciones que divergen y pasan todo.**
    - (A) Abre el archivo en `cmd-ssh-pane.c`. Da `can't read identity file: /etc/shadow` y exit 1.
    - (B) Chequea existencia y modo distinto de `000`. Pasa los chequeos síncronos, crea el pane (exit 0) y el hijo falla con una línea que ningún FR fija.

    Las dos pasan VC-34a y VC-34b.
  - **La regla general quedó escrita, pero fuera de FR-34.** Solo está en la prosa de FR-57 (`:787-788`: "FR-34a y FR-34b solo miran si el archivo se puede abrir"), que no es el Dado de FR-34.
  - **Contradice el Historial.** `:1104` dice "No cambia ningún comportamiento, mensaje ni umbral", y no es exacto: el contrato se angostó. FR-33a (`:515`), en cambio, conservó la clase y dejó las muestras en el VC, que es el patrón correcto.
  - **No es un Issue de 2.3.** La partición en sí está bien: "no existe" y "existe pero no se puede leer" son dos situaciones.
- Suggestion (2.8) · spec-brownfield.md:524 (FR-33b), "**Dado** un valor de `-P` que es un entero decimal entre 1 y 65535". "Entero decimal" no dice qué pasa con `022`, `+22` o ` 22`:
  - con `strtonum`/`strtoll`, que es lo que usa tmux, se aceptan;
  - con una regex estricta `^[1-9][0-9]*$`, se rechazan.

  Los dos resultados son observables y opuestos (FR-33a o FR-33b). Es el mismo tipo de imprecisión que "sus primeros bytes" en el TP1. Ya estaba en el Dado de FR-33 en v1.3, y no la marqué en el r4. v1.5 la vuelve más visible, porque ahora escribe la clase positiva. Detalle menor: el título, "Los bordes del rango se aceptan", es más angosto que el Dado, que es el rango entero.
- Suggestion (2.8) · spec-brownfield.md:1007, "`openssh-client` (solo para el control de NFR-2)". Desde v1.4, VC-71 (`:338-339`) también usa `ssh(1)` como control. §9 se declara "parte del contrato" (`:1001-1002`), así que ese "solo" quedó desactualizado.
- **2.3, sin Issues.** Hice una pasada sobre los FRs nuevos y los tocados:
  - **FR-33a** (`:514-517`) es una clase con un resultado. Las tres muestras de VC-33a son de la misma clase y lo dice (`:520`).
  - **FR-33b** (`:523-528`) es una clase, y su Entonces se observa entero en una ejecución.
  - **FR-34a y FR-34b** (`:533-545`) son una situación y un resultado cada uno.
  - **FR-59** (`:549-553`) es una clase ("no empieza con `/`") con un mensaje. "Aunque el archivo exista" y "va antes que FR-34a/b" no son resultados alternativos: los dos dicen que la clase incluye los relativos que existen y los que no.
  - **FR-60** (`:329-335`) es una situación. "`TERM` llega por el pedido de PTY (FR-13)" es un puntero, no un segundo resultado.
  - **VC-67** (`:931`) cubre INV-1 "incluye la regla de INV-6 en macOS", y no cuenta como VC doble: la fila de INV-1 (`:136`) ya incluye `cd regress && gmake cumple la regla de INV-6`.
- **2.7, sin hallazgos.**
  - VC-33b (`:530-531`) pide lo mismo que FR-33b: sin `invalid port`, exit 0 y +1 pane.
  - VC-34b no agrega condiciones. El "no como root" está en el Dado (`:542`), y es correcto: como root, el modo `000` se lee.
  - VC-59b y VC-59c (`:821-828`) hacen explícito el observable ("mismo observable que VC-6"; "estado `1 255` y su línea literal") de lo que en v1.3 decía "se da FR-45". BR-1 (`:809`, `:810`) ya lo decía, así que no agregan comportamiento.
  - VC-70: el fixture ("habiendo un `k` legible …", `:556`) materializa el "aunque el archivo exista" del FR.
  - VC-71: su control valida el Dado ("el `sshd` … acepta"), no agrega comportamiento de `ssh-pane`.
- **Pedido (e), "no cambia comportamiento".** Comparé contra `6ac25ef`:
  - FR-33 → FR-33a/b: equivalente. El "Los bordes 1 y 65535 se aceptan" de v1.3 más el VC-33 de entonces ("el exit es 0 y hay un pane nuevo") son FR-33b.
  - VC-59 → a/b/c: equivalente, palabra por palabra salvo los observables explícitos.
  - VC-68 → a…e: equivalente. INV-2 va sin flag (`:137`); INV-3 (`:138`) e INV-4 (`:139`), con flag; INV-6 (`:141`), con y sin flag.
  - VC-69 → a/b: equivalente.
  - VC-67 deja de poder correr "local" (v1.3: "local o en el runner `macos-26`"). Es coherente con "Solo cuenta como verificado si corrió en este job" (`:1058-1059`).
  - **La única diferencia de contrato es FR-34** (Warning de arriba).

### 3. Casos borde y verificabilidad — WARN
- **Warning (3.4)** · spec-brownfield.md:553 (FR-59), "Este chequeo va antes que los de FR-34a y FR-34b".
  - **El hueco.** El orden solo se observa con un path relativo que **no** se puede abrir, y VC-70 (`:555-557`) prueba solo relativos que existen ("habiendo un `k` legible en el cwd del cliente y en `~`").
  - **Por qué VC-70 no lo atrapa.** El servidor no cambia de cwd: hace `daemon(1, 0)` (`proc.c:387`, `nochdir = 1`), así que en el VC su cwd es el del cliente que lo arrancó, donde está `k`. Una implementación que hace primero el `open` de FR-34 (relativo al cwd del servidor) y después el chequeo de FR-59 lo abre bien y da el mensaje de FR-59. Pasa VC-70 con el orden invertido.
  - **Qué daría el orden invertido.** Con `-i nope` (relativo e inexistente), esa implementación imprime `can't read identity file: nope`, que contradice FR-59.
  - **El arreglo.** Falta una muestra relativa e inexistente en VC-70. De paso conviene `''`, que también es "no empieza con `/`" y debería dar `identity file must be an absolute path: ` (con el espacio final, como FR-30).
- Suggestion (3.2) · spec-brownfield.md:334-335 (FR-60), "el cliente no manda ningún pedido `env`". VC-71 (`:337`) solo mira `LC_PRUEBA`.
  - **Lo que VC-71 sí atrapa.** Atrapa la alternativa descartada en D-19 (`SendEnv LANG LC_*`, que matchea `LC_PRUEBA`) y "mandar todo".
  - **Lo que no atrapa.** Una implementación que manda solo `LANG` pasa.
  - **Cómo cerrarlo.** Basta con agregar `T set-environment -g LANG C.UTF-8` y `echo "L=${LANG-unset}"`, contrastado con el control. Ojo: ahí el `sshd` puede tener su propio `LANG` por PAM (`/etc/default/locale`), así que hay que comparar contra el valor del control **sin** `SendEnv`.
- Suggestion (3.2) · spec-brownfield.md:338-339 (VC-71), "el mismo eco en `T split-window 'ssh alice@servidor'` con `ssh -o SendEnv=LC_PRUEBA`". No es un comando literal. Hay que armar a mano `T split-window 'ssh -o SendEnv=LC_PRUEBA alice@servidor'`. Lo decidí en mi lectura, pero no tendría que hacer falta.
- Suggestion (3.4) · spec-brownfield.md:553. FR-59 fija el orden contra FR-34a/b, pero no hay precedencia entre los demás errores síncronos de §6.3. Por ejemplo, `T ssh-pane -i k -P 0 @servidor` dispara FR-59, FR-33a y FR-28, y la spec no dice cuál sale. Es un borde fuera de la lista obligatoria (§0.4).
- 3.1 sin hallazgos: los 62 FR y los 5 BR tienen VC debajo de su encabezado y en §7 (`:949-958`).
- 3.3 sin hallazgos: la matriz (`:962-969`) suma FR-59 a "Clave / Entrada inválida", y FR-34a y FR-34b quedan en "No existe" y "Sin permiso".
- 3.6 sin hallazgos: VC-6 sigue siendo end-to-end contra un `sshd` real (§9, `:1042-1044`).

**Ejercicio 3.5**

**Feliz, FR-33b** (`:523-531`):

```sh
T new-session -d -x 200 -y 50; T set -g remain-on-exit on      # convenciones, :150-151
for v in 1 65535; do
  n0=$(T list-panes -a | wc -l)
  T ssh-pane -P "$v" alice@servidor 2>/tmp/err; rc=$?
  n1=$(T list-panes -a | wc -l)
  [ "$rc" -eq 0 ] && ! grep -q 'invalid port' /tmp/err && [ "$n1" -eq $((n0 + 1)) ]
done
```

- Esperado: exit 0, ningún `invalid port` en stderr, y un pane más por iteración. El pane muere después con la línea de "connection refused" (FR-39), y eso queda fuera, como dice `:527-528`.
- Lo que tuve que decidir:
  - En qué momento contar. No es un hueco: con `remain-on-exit on`, el pane sigue en la lista aunque el hijo haya muerto.
  - Si probaba `022` o `+22` dentro del rango. No pude: la spec no dice si son "entero decimal" (Suggestion 2.8).

**Falla, FR-59** (`:549-557`):

```sh
cp /tmp/k ./k; cp /tmp/k ~/k                                   # "un k legible" (:556)
for p in k ./k '~/k'; do
  n0=$(T list-panes -a | wc -l)
  T ssh-pane -i "$p" alice@servidor 2>/tmp/err; rc=$?
  [ "$(cat /tmp/err)" = "identity file must be an absolute path: $p" ] && [ "$rc" -eq 1 ] \
    && [ "$(T list-panes -a | wc -l)" -eq "$n0" ]
done
```

- Que `'~/k'` llegue literal no es una decisión mía. `cmd_parse_from_arguments` (`cmd-parse.y:1065-1137`) copia los argumentos del `argv` sin pasar por el lexer, así que no expande `~`.
- Lo que tuve que decidir:
  - **Qué contiene `k`.** Elegí una clave válida y autorizada, para que una implementación sin FR-59 abra la sesión y el test falle sin ambigüedad. No es un hueco, porque con cualquier contenido el test discrimina.
  - **Cómo probar "va antes que FR-34a y FR-34b".** Tuve que agregar un caso que VC-70 no tiene: `-i nope`, relativo e inexistente, que tiene que dar el mensaje de FR-59 y no `can't read identity file: nope`. Ese es el Warning 3.4 de arriba.

### 4. Requerimientos no funcionales — PASS
- Sin hallazgos nuevos. v1.4/v1.5 no tocan NFR-1 a NFR-3 (`:881-922`). La Suggestion de CPU y memoria por pane sigue del r2 (ver la tabla).

### 5. Tecnología y fundamento — PASS
- **5.3, las citas de D-17, D-18 y D-19.** Abrí cada cita en el commit fijado.
  - **D-17** (`:995`):
    - `tmux.c:435` es `main(int argc, char **argv)`. tmux.c es un archivo compartido con OpenBSD y no está en "Dentro" (`:52-62`), así que la afirmación es cierta.
    - `spawn.c:541` es `closefrom(STDERR_FILENO + 1);`. Cierra todo descriptor por encima de 2, así que "un descriptor heredado, que `closefrom` … hoy cierra" es cierto.
    - El costo (a) coincide con notas-exploracion.md:341.
  - **D-18** (`:996`):
    - `cmd-parse.y:1709-1710`: `if (ch == '~' && last != state && state != SINGLE_QUOTES)` → `yylex_token_tilde`. La expansión usa el `HOME` de `global_environ` o el de `getpwuid` (`cmd-parse.y:1617-1623`). §6.2 (`:234-235`) lo resume bien: "al principio de una palabra" es una simplificación aceptable de `last != state`, que también expande al principio de una sección entre comillas dobles.
    - `server-client.c:2926`: la función sigue esta cascada: `cfg_client->cwd` mientras carga la config (`:2930-2931`), el cwd del cliente sin sesión, el de la sesión, `find_home()` y `/` (`:2932-2940`). "Devuelve cosas distintas según quién invoca" es exacto.
  - **D-19** (`:997`): que `SendEnv LANG LC_*` viene del `ssh_config` de Debian/Ubuntu, y que `AcceptEnv LANG LC_*` es el default del `sshd_config` de Ubuntu (`:331-332`), es conocimiento de la distribución. **No lo verifiqué** dentro de una imagen `ubuntu:24.04`. El control de VC-71 lo comprueba en tiempo de ejecución, así que no bloquea.
- Suggestion (5.3) · spec-brownfield.md:995, D-17 (2): "el destino y el path de la clave tienen que cruzar el `exec`: por `argv` o por el entorno quedan visibles en `/proc/<pid>/cmdline` o `environ`". Ni el destino ni el path de una clave son secretos: `ssh(1)` los expone igual en su `cmdline`. Además, `/proc/<pid>/environ` es 0400. El descarte se sostiene con (1) y (3), pero (2) exagera, y un lector hostil lo puede usar para discutir el descarte entero.
- Suggestion (5.5) · spec-brownfield.md:995, D-17 (a): "Un bug explotable de libssh en el hijo expone esa memoria, no solo la sesión SSH". El costo es explícito en la spec, pero aplica a **cada** `ssh-pane`: es el default, no una excepción opcional. La entrada de `tmux.1` (`:61`) solo exige "Only available on Linux …". El usuario del comando no tiene cómo enterarse de que un servidor hostil más un bug de libssh exponen la historia de todos sus panes. Una frase en el man lo resolvería.
- 5.1, 5.2, 5.4 y 5.6 sin hallazgos.
  - D-18 y D-19 declaran su trade-off: "El locale remoto es el que configure el servidor", y que el mismo `-i k` leería archivos distintos.
  - El cambio de v1.4 en notas-exploracion.md:341 ("La spec acepta este costo en D-17") no describe comportamiento que la spec no tenga.
  - D-2 (`:980`) y D-12 (`:990`) remiten a D-17 sin contradecirlo.

### 6. Simplicidad — PASS
- Suggestion (6.4) · spec-brownfield.md:237, "El proceso remoto recibe solo `TERM`". La regla está dos veces, con palabras distintas (`:237-238` y FR-60 `:334-335`), y la versión de §6.2 es falsa al pie de la letra: el proceso remoto recibe además lo que pone `sshd` (`SSH_CONNECTION`, que VC-9 usa en `:281`, y también `USER`, `HOME`, etc.). FR-60 lo dice bien ("el cliente no manda ningún pedido `env`"). Conviene que §6.2 diga lo mismo.
- 6.1 a 6.3 sin hallazgos. FR-59 es un camino de falla de `-i`, y FR-60 restringe, no agrega alcance. Los dos se justifican por D-18 y D-19.

### B. Extensión brownfield — PASS
- **B1, citas.** `TMUX_SRC=tmux-ssh-tp2/.cache/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 133 citas verificadas contra tmux@5a820e6`, exit 0, sin fallos y sin avisos de citas huérfanas. El r4 dio 128. Las 5 nuevas son:
  - `cmd-parse.y:1710`, en `:235` y `:996`;
  - `server-client.c:2926`, en `:996`;
  - `tmux.c:435`, en `:995`;
  - `spawn.c:541`, en `:995`.

  `citas.tsv` suma 3 anclas (89 en total). Abrí dos citas al azar:
  - **`arguments.c:333`** (`too few arguments (need at least %u)`, FR-25 `:458`). `:331-336` arma el error cuando `args->count < parse->lower`, y `:339-341` da el `too many arguments (need at most %u)` de FR-26. Con `lower = upper = 1`, sostiene FR-25 y FR-26.
  - **`cmd.c:206-207`** (`&cmd_split_window_entry,` / `&cmd_start_server_entry,`, `:56`). Son consecutivas en `cmd_table`, así que `ssh-pane` va entre las dos ("sp" < "ss" < "st"). En la tabla hay 27 entradas que empiezan con `s`, y coincide con los 27 candidatos de linea-de-base/corridas.txt:13 que usa FR-23.

  Las citas nuevas están verificadas en la dimensión 5.
- **B6.** FR-59 cae en `cmd-ssh-pane.c` ("Valida los argumentos (§6.3)", `:59`) y FR-60 en `ssh-pane.c` (`:60`). Los dos están en "Dentro". El modo helper descartado tocaría `tmux.c`, que no está en "Dentro": D-17 lo dice (`:995`), e INV-5 (`:140`) lo atraparía en el diff.
- **B7.** `git diff --name-only 6ac25ef 5033d42 | grep -E '\.(c|h)$'` da vacío. Lo que cambia en `.py` es de `gcsgrep-tp1/`, otro TP. El clon de tmux está limpio (`git status --short` vacío, HEAD `5a820e6`).
- **B9.** Le pregunté al lector hostil si con lo nuevo puede romper un build no-Linux, cambiar un comando existente o tocar PTY/panes. Lo peor que puede hacer:
  - implementar el modo helper de D-17, que VC-60 (cero `execve`) e INV-5 (`tmux.c` fuera del diff permitido) atrapan;
  - resolver `-i` relativo con el orden invertido, que pasa VC-70 (Warning 3.4) pero no toca las invariantes;
  - implementar FR-34 por modo de archivo, que pasa (Warning 2.8).

  Nada de eso cruza el límite de la consigna.
- B2, B3, B4, B5 y B8 sin cambios ni hallazgos.
  - VC-68 y VC-69, partidos, conservan el chequeo ejecutable de cada invariante (`:136-142`), y cada uno tiene su job (`:1050-1054`).
  - Las seis decisiones de la consigna siguen en D-1 a D-6 (`:979-984`).
- **Pedido (c), los IDs nuevos.** Revisé que no queden IDs colgados:
  - §7 (`:949-958`) lista FR-33a/b, FR-34a/b, FR-59/60, VC-59a/b/c, VC-68a…e y VC-69a/b. Todos existen como encabezado o fila.
  - Los jobs de §9 (`:1050-1054`) reparten los 80 VCs sin dejar ninguno afuera ni repetido entre jobs.
  - El plan de §11 (`:1088-1090`) también los cubre todos: VC-1…5, 22…37, 55, 67…69 y 70 en la Iteración 1; 6…21, 61…63 y 71 en la 2; 38…54, 56…60 y 64…66 en la 3.
  - `grep -E '(FR|VC)-(33|34|59|68|69)([^0-9a-z]|$)'` en el TP solo da menciones históricas o explicativas (`:14`, `:942`, `:1101`, `:1104`), ninguna colgada.

## Veredicto general   READY

No hay Issues. Las afirmaciones nuevas sobre tmux son ciertas en `5a820e6`, la trazabilidad cuadra con los IDs partidos y el conteo de la cabecera es exacto. Los dos Warnings no bloquean, pero conviene cerrarlos antes de entregar:
- **2.8, FR-34.** Lo que se angostó es el contrato escrito: el Historial declara que no cambia nada, y para FR-34 eso no es exacto.
- **3.4, FR-59.** Una frase del FR no tiene VC.

## Acciones (priorizadas)
- [SHOULD] spec-brownfield.md:534 y :541: devolverles la clase a los Dados y dejar las muestras en el VC, como FR-33a.
  - FR-34a: "un `<path>` absoluto que no existe".
  - FR-34b: "un `<path>` absoluto que existe y que el usuario del servidor `tmux` no puede abrir para lectura".
  - VC-34a y VC-34b siguen con `/nonexistent` y `/tmp/k000`.
  - Corregir :1104, "No cambia ningún comportamiento", o dejarlo cierto con este cambio (2.8).
- [SHOULD] spec-brownfield.md:555-557: sumar a VC-70 un path relativo que no existe (`nope`), que tiene que dar `identity file must be an absolute path: nope` y no `can't read identity file: nope`. De paso, sumar `''` (3.4).
- [COULD] spec-brownfield.md:524: definir "entero decimal": solo dígitos, sin signo, y si se aceptan ceros a la izquierda o no. Agregar `022` o `+22` a VC-33a o VC-33b según lo que se decida. Ajustar el título de FR-33b (2.8).
- [COULD] spec-brownfield.md:337-339: VC-71 con el comando de control literal, y una segunda variable que no sea `LC_*` (por ejemplo, `LANG`), para acotar el "ningún pedido `env`" de :334 (3.2).
- [COULD] spec-brownfield.md:237: escribir "el cliente no manda ninguna variable de entorno salvo `TERM`", como FR-60, en lugar de "El proceso remoto recibe solo `TERM`" (6.4).
- [COULD] spec-brownfield.md:1007: sacar el "solo" de "solo para el control de NFR-2", porque VC-71 también usa `ssh(1)` (2.8).
- [COULD] spec-brownfield.md:995: sacar o matizar el argumento (2) de D-17 (5.3), y llevar el costo (a) a la entrada de `tmux.1` (:61) (5.5).
- [COULD] spec-brownfield.md:553: fijar la precedencia entre los errores síncronos de §6.3, o declarar que no se fija (3.4).
- [COULD] Las que siguen del r4 (ver la tabla):
  - cómo bloquear el agente sin una tty (:1040);
  - el orden de las claves de D-5 (:983);
  - `-t` sobre un pane flotante;
  - la codificación del destino;
  - `LIBSSH_LIBS` (:54);
  - el CPU y la memoria del hijo;
  - VC-22 contra INV-4 (:422);
  - el "cómo" de FR-17 (:362);
  - el host con `-P` ≠ 22 en los mensajes;
  - el agente que muere a mitad de la autenticación;
  - FR-27 con un solo VC (:231).

VEREDICTO: READY

> **Evidencia (salida de la demo 1b).** Copia de la spec que produjo el skill `write-spec-brownfield` en una rama de demo; no forma parte del TP2. Los enlaces se reescribieron para que apunten a `tmux-ssh-tp2/`.

# Spec — flag `-u user` para `ssh-pane` sobre `spec-brownfield.md` v1.5.1

> Spec **brownfield delta**: modifica la spec de [`spec-brownfield.md`](../../tmux-ssh-tp2/spec-brownfield.md)
> (v1.5.1, tmux commit base `5a820e63b72f05c121441149c72327aeeb16dfa4`), que todavía
> no está implementada. Todo lo que esta spec no dice lo sigue diciendo la spec base.
> Los requerimientos de la spec base se citan como **base FR-n**, y los de esta,
> como **FR-n** a secas. La numeración es local.
> Insumo: [`notas-exploracion.md`](../../tmux-ssh-tp2/notas-exploracion.md) (hallazgo 8).

## 1 · Propósito

Pasar el usuario remoto sin escribir `user@host`, por ejemplo en un binding donde
el host viene de un formato y el usuario es fijo. `ssh(1)` usa `-l` para esto,
pero en `ssh-pane` esa letra no se puede usar: `layout_get_tiled_cell()`
(`layout.c:1640`) recibe el `struct args` entero y lee `-l` como tamaño
(`layout.c:1657`, notas §8; spec base §6.2 y D-16). Por eso el flag es `-u` (D-1).

## 2 · Actores

Los mismos de la spec base §2. Afecta sobre todo al **usuario de `tmux`** y a
**scripts y `.tmux.conf`**, que pasan a poder usar `-u`.

## 3 · Alcance

### Dentro

| Path | Qué cambia |
|---|---|
| `cmd-ssh-pane.c` (nuevo, base §3) | La cadena de flags suma `u:`. El `usage` pasa a ser el de FR-1. La validación de base §6.3 suma FR-3, FR-4 y FR-7, en el orden de D-3. El destino SSH que se arma toma el usuario de `-u` cuando está |
| `tmux.1` | En la entrada de `ssh-pane`: la sinopsis de FR-1 y la frase `-u specifies the remote user; it cannot be combined with user@ in destination.` (FR-6) |
| `regress/ssh-pane-user.sh` (nuevo) | VC-1 a VC-5 y VC-7 (VC-6 es un `grep` sobre `tmux.1`). Se saltea igual que el resto de `regress/ssh-pane-*.sh` (base §3) |
| `spec-brownfield.md` | **No se edita** (AGENTS.md). Esta spec la complementa y **reemplaza**: (a) la lista de flags de base §6.2 (`spec-brownfield.md:229-231`), que pasa a ser `d`, `h`, `i:`, `P:`, `t:` y `u:` (la regla "cualquier otra letra es un error" de base FR-27 sigue valiendo para el resto); (b) la sinopsis de base §6.2 y la línea esperada en base VC-22, que pasan a ser las de FR-1 |

### Fuera (por path)

| Path | Por qué no se toca |
|---|---|
| `ssh-pane.c` | Recibe el destino ya validado (base §3, `tmux.h`). No le importa de dónde salió el usuario |
| `tmux.h`, `spawn.c`, `cmd.c` | El struct del destino ya tiene un campo de usuario, y la entrada de `cmd_table` no cambia de nombre ni de posición |
| `layout.c`, `layout-*.c` | `u` no es una de las letras que lee el layout (`l p x X y Y`, notas §8) |
| `configure.ac`, `Makefile.am` | No hay archivos ni dependencias nuevos |
| `cmd-split-window.c` y todo `cmd-*.c` existente | INV-4 de la base |

## 4 · Invariantes

Valen las INV-1 a INV-7 de la base, sin cambios. El path nuevo,
`regress/ssh-pane-user.sh`, ya está cubierto por el glob `regress/ssh-pane-*.sh`
de base INV-5. Esta spec agrega dos invariantes (prefijo `U` para no chocar con las
de la base):

| # | Qué sigue siendo verdad | Comando que lo chequea |
|---|---|---|
| INV-U1 | Lo que andaba con `user@host`, o sin usuario, anda igual | Se corren todos los `regress/ssh-pane-*.sh` de la base, en particular base VC-6 y base VC-12: exit 0 |
| INV-U2 | Ningún otro comando cambia | `T list-commands \| grep -v '^ssh-pane '` es igual a `linea-de-base/list-commands-linux.txt` (base INV-4) |

## 5 · Requerimientos

Convenciones: las de la spec base §6 (`T`, entorno base, "la cantidad de panes no
cambia", estado del pane). Los VCs corren en el entorno de base §9.

**FR-1 · Sinopsis.**
**Dado** un build con `--enable-ssh`,
**cuando** se corre `T list-commands ssh-pane`,
**entonces** la línea es
`ssh-pane [-dh] [-i identity-file] [-P port] [-t target-pane] [-u user] destination`.
Con eso, `destination` sigue siendo `[user@]host`.

> **VC-1** — Stdout es exactamente esa línea, con exit 0. Y, como en base VC-22,
> `T list-commands | diff linea-de-base/list-commands-linux.txt -` muestra una
> sola línea agregada, que es esa.

**FR-2 · Usuario por flag.**
**Dado** el entorno base,
**cuando** se corre `T ssh-pane -u alice servidor`,
**entonces** la sesión se abre como en base FR-6, como `alice`.

> **VC-2** — `echo "R=$(hostname):$(id -un)"` en el remoto da `R=servidor:alice`
> dentro de 3 s, y el cliente `tmux` sale con 0.

**FR-3 · Usuario dos veces.**
**Dado** el entorno base,
**cuando** se da el usuario por `-u` y también por `user@` en un destino válido,
**entonces** stderr es `user given twice: use -u or user@host`, aunque los
usuarios coincidan (D-2).

> **VC-3** — Con `-u alice alice@servidor` y `-u bob alice@servidor`: el stderr
> exacto de cada uno, exit 1, y la cantidad de panes sin cambio.

**FR-7 · `-u` repetido.**
**Dado** el entorno base,
**cuando** `-u` aparece más de una vez,
**entonces** stderr es `user given twice: use -u or user@host`, sin mirar los
valores (D-2, D-3).

> **VC-7** — Con `-u alice -u alice servidor` y con `-u '' -u alice servidor`: el
> stderr exacto de cada uno, exit 1, y la cantidad de panes sin cambio.

**FR-4 · Usuario vacío o con `@`.**
**Dado** un valor de `-u` vacío o que contiene `@`,
**cuando** se corre `T ssh-pane -u <valor> servidor`,
**entonces** stderr es `invalid user: <valor>`. Otros caracteres no se validan
en `tmux`: los rechaza, si corresponde, el servidor remoto (como un usuario dado
por `user@`).

> **VC-4** — Con `''` (stderr `invalid user: `, con el espacio final) y con `a@b`:
> el stderr exacto, exit 1, y la cantidad de panes sin cambio.

**FR-5 · Orden de las validaciones.**
**Dado** que más de una regla se cumple a la vez,
**cuando** se corre `ssh-pane`,
**entonces** se informa solo el primer error, en el orden de D-3.

> **VC-5** — Exit 1, panes sin cambio, y este stderr exacto en cada caso:
>
> | Comando | stderr |
> |---|---|
> | `T ssh-pane -u '' alice@servidor` | `invalid user: ` |
> | `T ssh-pane -u a@b servidor:22` | `invalid user: a@b` |
> | `T ssh-pane -u alice servidor:22` | `invalid destination: servidor:22 (use -P for the port)` |
> | `T ssh-pane -u alice @servidor` | `invalid destination: @servidor` |
> | `T ssh-pane -u alice a@b@servidor` | `invalid destination: a@b@servidor` |

**FR-6 · Página de manual.**
**Dado** el `tmux.1` del árbol con el cambio,
**cuando** se busca la entrada de `ssh-pane`,
**entonces** contiene la sinopsis de FR-1 y la frase de §3.

> **VC-6** — La entrada de `ssh-pane` empieza con `.It Xo Ic ssh-pane`, como las
> de los demás comandos de `tmux.1`, y va seguida de otra entrada `.It Xo Ic`.
> Con `sed -n '/^\.It Xo Ic ssh-pane/,/^\.It Xo Ic /p' tmux.1 > /tmp/e`, dan
> `1` tanto `grep -c 'cannot be combined with user@ in destination' /tmp/e` como
> `grep -c 'Op Fl u Ar user' /tmp/e` (sintaxis mdoc de la sinopsis).

## 6 · Decisiones

| # | Elegido | Descartado | Por qué |
|---|---|---|---|
| D-1 | `-u user` | `-l user`, como `ssh(1)` | `-l` lo lee `layout_get_tiled_cell()` como tamaño (`layout.c:1657`): `alice` se interpretaría como geometría. Habilitarlo exigiría pasarle al layout un `args` filtrado y superseder D-8 y D-16 de la base. Es el mismo criterio que puso el puerto en `-P` (base D-8) |
| D-2 | `-u` junto con `user@` es un error, siempre | Que gane uno de los dos; aceptar si coinciden | `ssh(1)` hace ganar a `user@` en silencio, y eso esconde errores de los scripts. Que dé error aun cuando coinciden deja una regla sin casos especiales |
| D-3 | Entre las reglas del usuario y del destino, el orden es: (1) FR-7, `-u` repetido; (2) FR-4, sobre el único valor de `-u`; (3) las reglas del destino de la base (base FR-28 a FR-32 y FR-55); (4) FR-3. **El orden respecto de `-P`, `-i` y `-t` no se fija**: la base tampoco lo fija, y esta spec no agrega reglas ahí | FR-3 primero | FR-3 solo tiene sentido sobre un destino ya partido y válido. FR-7 va primero para que FR-4 tenga un solo valor que mirar. VC-5 y VC-7 fijan cada cruce |

## 7 · Línea de base

Sin `ssh-pane` implementado, no hay nada que correr contra este cambio. Vale la de
[`linea-de-base.md`](../../tmux-ssh-tp2/linea-de-base.md) (base INV-6): en Linux, 170 PASS y 2 FAIL
clasificados. Al implementar, la línea de base de esta spec es la suite de la base
en verde **antes** de agregar `-u` (INV-U1). Los VCs de esta spec corren en el
perfil `linux-ssh` de base §9; VC-2 es end-to-end contra el `sshd` real.

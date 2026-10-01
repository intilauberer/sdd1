# Línea de base de regresión — tmux@5a820e6, antes del cambio

> Medida el 2026-10-01 sobre `5a820e63b72f05c121441149c72327aeeb16dfa4`, **sin
> ninguna modificación** al repo. Es contra lo que se compara al cerrar cada
> iteración (spec, §Línea de base). Los archivos crudos están en
> [`linea-de-base/`](./linea-de-base/).

## Cómo se midió

**Linux** — contenedor `ubuntu:24.04` (aarch64) con los mismos paquetes que
instala el CI de tmux, más `libssh-dev` (0.10.6). La corrida completa se hizo
**sin** `python3`, y las fallas se volvieron a correr con `python3` instalado:

```bash
sh autogen.sh && ./configure --enable-utf8proc && make -j"$(nproc)"
cd regress && make -k -j"$(nproc)"
```

**macOS** — arm64, Homebrew (`autoconf`, `automake`, `pkg-config`, `make`):

```bash
sh autogen.sh && ./configure --disable-jemalloc && make -j8
cd regress && gmake -k -j8
```

## Resultados

| | Linux | macOS |
|---|---|---|
| `configure` | exit 0 | exit 0 con `--disable-jemalloc`. **Sin ese flag falla**: `must give --enable-jemalloc or --disable-jemalloc` |
| `make` | exit 0 | exit 0 |
| `tmux -V` | `tmux next-3.9` | `tmux next-3.9` |
| `regress/` (paralelo, `make -k -j`) | 170 PASS · 2 FAIL | 165 PASS · 7 FAIL |
| `./configure --enable-ssh` | `WARNING: unrecognized options: --enable-ssh` | ídem |
| `tmux ssh-pane host` | `unknown command: ssh-pane`, exit 1 | ídem |
| Resolución de prefijos ([`snapshot-comandos.sh`](./scripts/snapshot-comandos.sh)) | 1.513 prefijos de 170 nombres/alias | **idéntica a Linux** (mismo sha256) |

## Fallas preexistentes, clasificadas

Cada falla del run paralelo se volvió a correr **sola**, varias veces.

| Test | Linux | macOS | Clase |
|---|---|---|---|
| `input-requests.sh` | FAIL sin `python3`; 5/5 PASS con `python3` | PASS | Dependencia de entorno |
| `prompt-words-history.sh` | 5/5 FAIL (`got 'show-r', expected 'history-command'`) | 2/2 FAIL, mismo mensaje | **Determinística** |
| `check-names.sh` | PASS | 2/2 FAIL, con distinto mensaje cada vez | Determinística en macOS |
| `prompt-keys.sh` | PASS | 2/2 FAIL (`invalid UTF-8 append…`) | Determinística en macOS |
| `screen-redraw-menus.sh` | PASS | 2/2 FAIL (`menu-over-split differs`) | Determinística en macOS |
| `cmd-template-replace.sh`, `hooks-notify.sh`, `screen-redraw-indicators.sh` | PASS | FAIL en paralelo, 2/2 PASS solos | Flaky bajo `-j8` |

**Regla para comparar:** al cerrar una iteración, el conjunto de tests que
fallan **solos** tiene que ser el mismo de esta tabla. Que aparezca un test
nuevo en esa lista es una regresión. Que desaparezca uno no es mérito del
cambio: también hay que explicarlo.

## Trampas del entorno encontradas al medir

- `cd regress && make` con el `/usr/bin/make` de macOS (GNU Make 3.81) **corre
  cero tests y sale 0**. `TESTS!= echo *.sh` necesita Make ≥ 4.0. Es un falso
  verde: hay que usar `gmake`, como hace el CI de tmux.
- En `snapshot-comandos.sh`, un formato de `list-commands -F` con salto de línea
  se imprime con `_` en lugar del salto. Por eso el script pide nombres y alias
  en dos pasadas separadas.

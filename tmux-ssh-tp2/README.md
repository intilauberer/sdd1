# TP2 · `tmux` con SSH nativo (solo Linux)

Análisis y spec brownfield de un comando `ssh-pane` para
[`tmux`](https://github.com/tmux/tmux). Abre un pane con una sesión SSH hecha con
libssh, sin ejecutar el binario `ssh`. **No hay implementación**: es lo que pide
la consigna ([`enunciado.md`](./enunciado.md)).

Todo se hizo sobre tmux en el commit `5a820e63b72f05c121441149c72327aeeb16dfa4`.

## Leé en este orden

| # | Artefacto | Paso SDD |
|---|---|---|
| 1 | [`notas-exploracion.md`](./notas-exploracion.md) | Descubrir: el camino de spawn, el event loop, la capa de compat/build y los riesgos, con `archivo:línea` |
| 2 | [`linea-de-base.md`](./linea-de-base.md) | La suite de tmux y el build en Linux y macOS **antes** de cualquier cambio, con las fallas que ya existen clasificadas |
| 3 | [`spec-brownfield.md`](./spec-brownfield.md) | Especificar: alcance por path, el límite solo-Linux, 7 invariantes con su chequeo, 37 FR, 4 BR, 3 NFR y 47 VCs |
| 4 | [`revisiones/`](./revisiones/) | Revisar: lo que encontraron los agentes adversariales y qué se cambió |

## Verificar las notas vos mismo

```bash
python3 scripts/check-citas.py      # clona tmux en .cache/ si no le pasás TMUX_SRC
```

El script falla si alguna cita `archivo:línea` no existe en el commit fijado, o
si no contiene el fragmento anotado en [`citas.tsv`](./citas.tsv). Que la línea
haga lo que la nota dice no lo chequea: eso se confirma abriéndola.

[`scripts/snapshot-comandos.sh`](./scripts/snapshot-comandos.sh) saca la foto de
cómo resuelve tmux cada prefijo de cada comando. Es el chequeo de INV-3.

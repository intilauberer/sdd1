# ADR-0021 · Binarios y `.gz` se saltean con un aviso por objeto, sin resumen final

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Supersede:** [ADR-0005](./ADR-0005-binarios-y-gz.md)
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 5.3 y acción 12
- **Requerimientos que sostiene:** FR-9 · FR-10 · VC-9 · VC-10 · VC-20

## Contexto

[ADR-0005](./ADR-0005-binarios-y-gz.md) decidió saltear los binarios y los `.gz`
sin descomprimirlos, y que los salteados "se reportan en un **resumen final** por
stderr". La spec v1.5 se apartó de ese detalle (una línea por objeto, en el
momento, sin resumen) y dejó el desvío como una fila de "referencias viejas" en
`docs/adr/README.md`. Pero una decisión de ADR que cambia no se anota: se supersede
(regla 1 del registro). Este ADR es ese reemplazo.

## Decisión

Se mantiene todo lo que ADR-0005 decidió, y se reemplaza el formato del aviso:

1. **Los objetos binarios y los `.gz` se saltean.** No se descomprime nada. Binario
   es "un `\x00` en los primeros 8192 bytes"
   ([ADR-0018](./ADR-0018-ventana-binaria-y-codificacion.md)); `.gz` es "el nombre
   termina en `.gz`", y ese objeto **no se abre**.
2. **Saltear no es un error de lectura**: no afecta el exit code (BR-3).
3. **Cada salteo escribe una línea por stderr, en el momento**:
   `gcsgrep: salteado (binario): gs://<bucket>/<objeto>` o
   `gcsgrep: salteado (.gz): gs://<bucket>/<objeto>`, antes de procesar el objeto
   siguiente. **No hay resumen final.**

## Fundamento del punto 3

1. **Es visible mientras la corrida avanza**, coherente con la salida incremental
   ([ADR-0011](./ADR-0011-salida-incremental.md)).
2. **Un script la filtra con `grep` sin esperar al final.**
3. **Un resumen final nunca se escribiría tras un corte de stdout**
   ([ADR-0019](./ADR-0019-corte-de-stdout-sigpipe.md)): el proceso muere por
   `SIGPIPE` antes de llegar al final.

## Consecuencias

- La fila de "desvío" de ADR-0005 en `docs/adr/README.md` queda como historia: la
  decisión vigente es esta.
- `core` emite el aviso como un evento más del flujo (`core.Aviso`), entre los
  matches; `cli` lo imprime por stderr.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Resumen final (ADR-0005) | Ver el fundamento: invisible durante la corrida y perdido ante un corte |
| Las dos cosas (línea y resumen) | Duplica información en stderr sin que nadie la pida |
| No avisar | Un objeto salteado en silencio es indistinguible de uno sin matches |

## Relacionado

- Spec: FR-9 · FR-10 · BR-3 · NFR-3
- Código: `gcsgrep/core.py::search`

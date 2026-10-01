# ADR-0011 · Salida incremental por streaming (resuelve FR-g del borrador)

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Origen:** [revisión de la spec](../revision-spec.md), hallazgo R-1
- **Requerimiento del borrador que resuelve:** FR-g

## Contexto

El borrador pedía, como FR-g, que la persona "se pueda dar cuenta de que está
progresando cuando hay muchos objetos, porque si no parece colgado". Ese
requerimiento no quedó ni especificado ni descartado: desapareció al escribir
la spec.

La primera implementación de la Iteración 1 lo hacía imposible de satisfacer
sin rediseño: `core.search` devolvía `List[Match]`, acumulando todos los
matches, y `cli` recién imprimía cuando la búsqueda había terminado. Sobre un
prefijo de 1000 objetos la herramienta no muestra nada hasta el final, que es
exactamente el síntoma que FR-g describe.

Eso mismo debilitaba NFR-1: la memoria estaba acotada respecto del contenido de
cada objeto, pero no respecto de la cantidad de matches. Un objeto de 200 MB
donde casi todas las líneas matchean acumula casi 200 MB de `Match`.

## Decisión

`core.search` es un **generador que emite cada `Match` en cuanto lo encuentra**,
y `cli` lo imprime y hace `flush` inmediatamente.

Esto resuelve FR-g con el mecanismo más barato disponible —el progreso *es* la
salida apareciendo— en vez de con una barra de progreso o un contador por
stderr.

**No se agrega** indicador de progreso cuando no hay matches. Una corrida larga
sin resultados sigue sin mostrar nada hasta terminar. Se acepta: agregar un
contador a stderr es alcance nuevo, y contamina la salida de una herramienta
cuyo NFR-3 exige que stderr sea solo para errores y resúmenes.

## Consecuencias

- La memoria queda acotada por el match más grande, no por la cantidad de
  matches. NFR-1 se vuelve cierto en el caso adverso y no solo en el felíz.
- Se comporta como `grep` en un pipe: `gcsgrep … | head -5` puede cortar
  temprano.
- `cli` ya no puede contar los matches antes de decidir el exit code: lleva un
  flag booleano mientras itera. Cambio chico, pero el orden importa: hay que
  imprimir antes de saber si hubo alguno.
- Los tests que comparaban contra una lista tuvieron que envolver el resultado
  en `list(...)`. No es un cambio de contrato observable desde el CLI.
- Con concurrencia (ADR-0009, diferido) esta decisión entra en tensión: emitir
  incrementalmente y mantener el orden del listado requiere buffering. Cuando se
  implemente concurrencia habrá que elegir, y esa elección necesita su propio
  ADR.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Barra de progreso o contador de objetos por stderr | Alcance nuevo, y stderr está reservado por NFR-3 para errores y resúmenes |
| Flag `--progress` | Un flag para algo que la salida incremental ya resuelve gratis |
| Dejar FR-g explícitamente fuera de alcance | Era la opción honesta si no hubiera solución barata; con el generador el costo es casi nulo y además arregla NFR-1 |

## Relacionado

- Spec: FR-11 · VC-17 · NFR-1 · VC-14
- Código: `gcsgrep/core.py::search`, `gcsgrep/cli.py::main`
- Iteración: 1 (revisión 1.1)

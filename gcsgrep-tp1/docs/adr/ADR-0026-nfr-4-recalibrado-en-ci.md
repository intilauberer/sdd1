# ADR-0026 · NFR-4 recalibrado en la plataforma de CI

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Supersede:** [ADR-0017](./ADR-0017-nfr-rendimiento-costo-propio.md)
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 4.2 y acción 9
- **Requerimiento que define:** NFR-4 · VC-30

## Contexto

[ADR-0017](./ADR-0017-nfr-rendimiento-costo-propio.md) definió NFR-4: la tasa de
procesamiento de `gcsgrep` en proceso, sin red, sobre un objeto de 100 MiB con
líneas de 80 bytes, con dos umbrales: (a) **≥ 50 MiB/s** con el patrón ausente y (b)
**≥ 50 000 matches/s** con el patrón en todas las líneas. Afirmaba que los dos
discriminan contra una implementación mala. La revisión de la v1.5 mostró que (b)
discrimina en macOS y **no en Linux**, que es donde corre el CI.

Medido el 2026-10-02 con `scripts/medir-nfr4.py` (mejor de 3), en el runner
`ubuntu-latest` del CI (run `36949165784`) y en la máquina de desarrollo:

| Plataforma | (a) actual | (a) mala: leer de a un byte | (b) actual | (b) mala: abrir y cerrar la salida por match |
|---|---|---|---|---|
| `ubuntu-latest`, Python 3.12 | 573 MiB/s | — | 488 152/s | **105 613/s** |
| `ubuntu-latest`, Python 3.9 | 306 MiB/s | — | 319 034/s | **64 090/s** |
| macOS (Apple Silicon), Python 3.13 | 924 MiB/s | 3,2 MiB/s | 359 782/s | 31 859/s |

Con 50 000 la implementación mala pasa en Linux por 1,3× a 2,1×.

## Decisión

Se mantiene todo lo de ADR-0017 (métrica, condición de carga, mejor de 3, sin red,
y (a) ≥ 50 MiB/s), con dos cambios:

1. **(b) pasa a ≥ 150 000 matches/s.**
2. **La plataforma de referencia es el runner `ubuntu-latest` del CI**, en las
   versiones de Python de su matriz. El CI imprime en cada corrida las tasas
   actuales y las de las dos implementaciones malas (`scripts/medir-nfr4.py`).

## Fundamento

1. **150 000 separa las dos implementaciones en todas las plataformas medidas.** La
   buena queda arriba por 2,1× en el peor caso (319 034, Python 3.9) y la mala abajo
   por 1,4× en el peor caso (105 613, Python 3.12).
2. **El margen se cargó del lado de la implementación buena:** que VC-30 falle por
   un runner lento sería un falso rojo en cada push; que una implementación mala
   pase por poco se ve en el log del CI, que imprime el contraste.
3. **(a) sigue discriminando con holgura:** la mala está ~15× por debajo de 50 MiB/s.

## Consecuencias

- VC-30 deja de pasar "por construcción" en Linux.
- Si el runner de CI cambia de hardware, el log de `medir-nfr4.py` muestra si el
  margen se achicó. Recalibrar es un ADR nuevo, no una edición de este.
- Con la versión mínima de Python en 3.10
  ([ADR-0027](./ADR-0027-piso-de-python-y-plataforma.md)), la matriz del CI pasa a
  3.10 y 3.12. El número de 3.10 se registra en la tabla de cobertura con la
  primera corrida.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Dejar 50 000 y declarar (b) un piso de regresión | Abandona la propiedad que ADR-0017 prometía, cuando un número la recupera |
| Umbral relativo a (a) en la misma corrida | ADR-0017 lo descartó por legibilidad, y con estos números no hace falta |
| Un umbral por plataforma | Duplica el contrato; la referencia es la que verifica una máquina |

## Relacionado

- Spec: NFR-4 · VC-30
- Código: `tests/test_paso0.py::test_vc30_*`, `scripts/medir-nfr4.py`

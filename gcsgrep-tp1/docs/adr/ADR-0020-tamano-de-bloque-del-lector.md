# ADR-0020 · El lector de GCS se abre con bloques de 1 MiB

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Issue 4.2 y acción 2 (la parte que la v1.6 dejó como excepción registrada)
- **Requerimiento que sostiene:** NFR-1 · VC-14 (c)

## Contexto

NFR-1 acota a **< 20 MiB** el pico de memoria del heap de Python mientras se lee un
objeto, y desde la spec v1.6 eso incluye los buffers de la librería cliente. El
lector de `google-cloud-storage` (`BlobReader`, lo que devuelve `blob.open`) pide
el objeto en bloques de `chunk_size` bytes y guarda el bloque entero en memoria. Su
default es de ~40 MiB: leyendo 200 MiB a través de él, el pico medido fue de
**120,1 MiB**, seis veces el umbral, con `core` leyendo por streaming impecable.

## Decisión

**`gcs` abre cada objeto con `blob.open("rb", chunk_size=1 MiB)`** (la constante
`gcs.CHUNK_SIZE`). `core` lee de a 64 KiB sobre ese lector.

## Fundamento

1. **Con 1 MiB el pico medido es de 3,1 MiB** sobre el mismo objeto de 200 MiB
   (VC-14 (c)): seis veces por debajo del umbral, con margen para el resto del
   proceso.
2. **El bloque acota la memoria por objeto, no por corrida.** Los objetos se leen
   de a uno ([ADR-0009](./ADR-0009-lectura-secuencial.md)): un bloque vivo a la vez.
3. **1 MiB es un tamaño de pedido normal para GCS.** No hay un mínimo de la API para
   lecturas por rango; el múltiplo de 256 KiB solo aplica a las subidas reanudables.

## Consecuencias

- **Más pedidos HTTP por objeto:** uno por MiB (200 para un objeto de 200 MiB, en
  lugar de 5). Contra GCS real eso suma latencia por pedido; **NFR-4 no lo ve**,
  porque mide el costo propio de `gcsgrep` sin red
  ([ADR-0017](./ADR-0017-nfr-rendimiento-costo-propio.md) y su sucesor
  [ADR-0026](./ADR-0026-nfr-4-recalibrado-en-ci.md)). Es el costo que se acepta.
- Cada pedido es una operación de lectura facturable de clase B. Para un objeto de
  200 MiB son 200 operaciones en vez de 5: centavos, del mismo orden que el costo de
  egreso, y acotado por el guardrail de BR-2.
- VC-14 (c) es el VC que falla si alguien vuelve al default o sube el bloque.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Dejar el default del SDK (~40 MiB) | Viola NFR-1 (120,1 MiB medidos) |
| 256 KiB | Cuatro veces más pedidos para ganar ~2 MiB que NFR-1 no necesita |
| Leer con `download_as_bytes` por rangos a mano | Reimplementa `BlobReader` y su manejo de errores de rango sin ganar nada |

## Relacionado

- Spec: NFR-1 · VC-14 (c) · *Tecnología y permisos mínimos*
- Código: `gcsgrep/gcs.py::CHUNK_SIZE`, `gcsgrep/gcs.py::open_stream`

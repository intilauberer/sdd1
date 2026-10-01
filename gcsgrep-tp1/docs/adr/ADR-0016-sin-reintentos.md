# ADR-0016 · Sin reintentos automáticos ante fallos de red en v1

- **Estado:** aceptado
- **Fecha:** 2026-10-01
- **Origen:** [corrección de la cátedra](../correccion-catedra-iteracion-1.md), Warning 5.3 — "Descartado en v1" sin fundamento
- **Requerimientos que sostiene:** NFR-2 · FR-13

## Contexto

Desde la v1.0 la spec dice "No hay reintentos automáticos en v1" (NFR-2) y lista
los reintentos en *Fuera*, pero ningún documento decía **por qué**. El plan solo
repetía "Descartado en v1". La cátedra lo marcó: es una decisión de diseño que
sostiene un NFR, y una decisión sin fundamento no se puede revisar.

La pregunta tiene alternativas reales. El SDK de `google-cloud-storage` trae su
propia política de reintentos (`DEFAULT_RETRY`, con backoff exponencial y un
deadline de 120 s) para operaciones idempotentes, y `grep` local no tiene el
problema porque un disco no tiene fallos transitorios.

## Decisión

**0 reintentos a nivel de `gcsgrep`.** Cada operación sobre GCS (el listado, y la
apertura y lectura de cada objeto) se intenta una sola vez. Un fallo de red:

- al **listar**, aborta la corrida con exit `2` (NFR-2 (a));
- al **leer un objeto**, se informa por stderr, ese objeto no se vuelve a abrir,
  la corrida sigue, y el exit code final es `2` (FR-13, NFR-2 (b), BR-3).

`gcsgrep` no agrega reintentos propios ni configura los del SDK para que
reintente más. **Qué hace el SDK por debajo no forma parte del contrato**: VC-15 y
VC-29 se observan en el borde de `gcs` (cuántas veces `gcsgrep` pidió la operación),
no en el tráfico HTTP.

## Fundamento

1. **El exit `2` ya le dice al script que reintente.** Con BR-3, un error de
   lectura nunca queda escondido detrás de un `0` o un `1`. Quien orquesta a
   `gcsgrep` (un script, un job de CI) tiene el contexto para decidir si
   reintentar la corrida entera; `gcsgrep` no.
2. **Reintentar dentro de la corrida rompe la salida incremental.** Si un objeto
   falla a mitad de lectura después de haber emitido matches (VC-17), reabrirlo
   desde el principio vuelve a emitir esos matches: duplicados en stdout. Evitarlo
   exige recordar qué líneas ya salieron por objeto, que es estado nuevo y un VC
   nuevo, o reanudar por offset con lecturas por rango, que es alcance nuevo.
3. **Reintentar cuesta plata y tiempo sin tope.** Cada reintento es otra operación
   de clase B. Con 1000 objetos y un enlace inestable, la corrida puede tardar
   minutos sin mostrar nada, que es el síntoma que FR-11 existe para evitar.
4. **No hay un número que defender todavía.** Una política de reintentos necesita
   cuántos, con qué backoff y con qué deadline total, y sin mediciones contra GCS
   real ([ADR-0015](./ADR-0015-verificacion-real-declinada.md)) cualquier número
   sería inventado. 0 es el único valor que no hay que calibrar.

## Consecuencias

- NFR-2 tiene una política explícita y verificable: "se intentó exactamente 1 vez"
  es observable sobre el doble de prueba (VC-15, VC-29).
- Un corte de red de un segundo sobre un objeto convierte una corrida útil en
  exit `2`. Es el costo aceptado, y es coherente con
  [ADR-0008](./ADR-0008-exit-codes.md): preferimos un `2` honesto a un `0` que
  oculta un objeto sin leer.
- Si en el futuro se agregan reintentos, este ADR se supersede con uno que fije
  cuántos, el backoff, el deadline total, y cómo se evitan los matches duplicados.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| N reintentos con backoff exponencial dentro de `gcsgrep` | Duplica matches ya emitidos al reabrir un objeto (rompe FR-11/VC-17), y no hay mediciones para elegir N ni el deadline |
| Reanudar la lectura por rango de bytes desde el último offset | Alcance nuevo (lecturas por rango, manejo de objetos que cambiaron entre intentos, que es el riesgo de ADR-0010) para un caso que el exit `2` ya resuelve del lado del script |
| Flag `--retries N` | Un flag nuevo con su propia superficie de VCs antes de que exista demanda; mismo problema de duplicados |
| Reintentar solo el listado, que no emite nada | Es la única variante sin el problema de duplicados, pero agrega una política distinta por operación sin un número medido que la justifique; queda como candidata natural si aparece la necesidad |

## Relacionado

- Spec: NFR-2 · FR-13 · BR-3 · VC-15 · VC-21 · VC-29
- [ADR-0008](./ADR-0008-exit-codes.md) — por qué el error parcial es `2`
- [ADR-0011](./ADR-0011-salida-incremental.md) — por qué reabrir un objeto duplica la salida
- [ADR-0015](./ADR-0015-verificacion-real-declinada.md) — por qué no hay mediciones contra GCS real

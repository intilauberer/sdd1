# ADR-0017 · NFR de rendimiento sobre el costo propio de `gcsgrep`, medido sin red

- **Estado:** superseded por [ADR-0026](./ADR-0026-nfr-4-recalibrado-en-ci.md)
- **Fecha:** 2026-10-01
- **Supersede:** [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md)
- **Origen:** [corrección de la cátedra](../correccion-catedra-iteracion-1.md), Issue 4.1 — "declinarlo con fundamento no lo reemplaza"
- **Requerimiento que define:** NFR-4 (resuelve NFR-a del borrador)

## Contexto

[ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md) declinó el NFR de rendimiento
en v1 con tres argumentos: (1) contra GCS real, un umbral mide la red y no la
herramienta; (2) contra el doble de prueba, mide el intérprete, "pasa siempre y no
protege nada"; (3) el número útil es comparativo contra la concurrencia de la
Iteración 3.

La cátedra no aceptó la declinación: la rúbrica exige un NFR de rendimiento con
métrica, número y condición de carga. Al revisar el argumento con números en la
mano, **el (2) resultó falso**, y eso es lo que habilita este ADR.

## Lo que se midió (2026-10-01)

Sobre el código de la Iteración 1, objeto de 100 MiB servido desde memoria, líneas
de 80 bytes, `cli.main` de punta a punta con stdout a `/dev/null`:

| Condición | Implementación actual | Contraste |
|---|---|---|
| Patrón ausente | **~396 MiB/s** | Leer el stream de a un carácter: **~15 MiB/s** |
| Patrón en todas las líneas (~1,3 M matches) | **~27 MiB/s ≈ 355 000 matches/s** | — |

Dos cosas que ADR-0012 no sabía:

- **El umbral sí discrimina.** Una implementación razonable y una mala difieren en
  más de un orden de magnitud. Un VC con umbral entre las dos puede fallar por la
  razón correcta, que es lo que ADR-0012 decía que no pasaba.
- **El costo dominante no es el que se suponía.** Con muchos matches, la tasa cae
  ~15× por el `flush` por línea que exige la salida incremental
  ([ADR-0011](./ADR-0011-salida-incremental.md)). Es un costo real y propio de
  `gcsgrep`, y antes no estaba acotado por nada.

## Decisión

**NFR-4 mide el costo propio de `gcsgrep`, de punta a punta, con el contenido
servido desde memoria.** Así se aísla la herramienta de la red (que era el
argumento (1) de ADR-0012, y sigue siendo válido) sin caer en medir solo un loop
interno.

- **Condición de carga:** un objeto de 100 MiB de texto, líneas de 80 bytes,
  lectura secuencial, stdout a `/dev/null`.
- **(a) Patrón ausente:** ≥ **50 MiB/s**. Margen ~8× sobre lo medido; el contraste
  de a un carácter (15 MiB/s) falla por ~3×.
- **(b) Patrón en todas las líneas:** ≥ **50 000 matches/s**. Margen ~7× sobre lo
  medido. Acota el costo del `flush` por match de ADR-0011.
- **Medición:** la mejor de 3 corridas, para que una máquina de CI cargada no dé un
  falso negativo. El margen de ~7× cubre un runner de CI hasta varias veces más
  lento que la máquina de desarrollo.

**Lo que este NFR no mide:** la latencia contra GCS real. Sigue siendo cierto que
ese número depende del día y del enlace, y su verificación es parte de la
obligación de [ADR-0015](./ADR-0015-verificacion-real-declinada.md). El número
**comparativo** para la concurrencia (argumento (3) de ADR-0012) sigue siendo
obligación de la Iteración 3, ahora con NFR-4 como línea de base medida en vez de
supuesta.

## Consecuencias

- La spec tiene un NFR de rendimiento con métrica, número y condición de carga en
  su enunciado. NFR-a del borrador deja de estar declinado.
- Hay un test que se puede romper en CI por lentitud. Se mitiga con el margen y la
  mejor de 3; si igual resulta inestable, eso es un hallazgo, no un motivo para
  subir el umbral en silencio.
- Cualquier cambio de la Iteración 2 que toque el camino caliente (abrir en
  binario para detectar `\x00`, decodificar con reemplazo, FR-9/FR-17) tiene que
  seguir cumpliendo NFR-4. Antes no había nada que lo detectara.
- La Iteración 3 arranca con una línea de base medida y escrita, no con una
  promesa de medirla.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Mantener la declinación de ADR-0012 | La rúbrica la marca como Issue, y el argumento (2) resultó falso al medir |
| Umbral de wall-clock contra un bucket real | Flaky por naturaleza, cuesta plata en cada corrida, y no hay cuenta con billing (ADR-0015) |
| Medir solo el núcleo de búsqueda, sin imprimir | Más estable, pero esconde el costo que dominó la medición (el `flush` por match). Un NFR de rendimiento que excluye lo más caro no protege a quien usa la herramienta |
| Objetos por segundo sobre muchos objetos chicos, contra el doble | Sin red, el costo por objeto es casi nulo (~100 000 objetos/s medidos) y ninguna implementación plausible lo rompe: no discrimina |
| Umbral relativo (≤ k× el costo de solo iterar el stream) | Más robusto ante máquinas lentas, pero menos legible como contrato para quien usa la herramienta, y el margen absoluto ya cubre la variación de CI |

## Relacionado

- Spec: NFR-4 · VC-30 · tabla de trazabilidad borrador → spec (NFR-a)
- Supersede: [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md)
- Interactúa con: [ADR-0009](./ADR-0009-lectura-secuencial.md), [ADR-0011](./ADR-0011-salida-incremental.md), [ADR-0015](./ADR-0015-verificacion-real-declinada.md)
- Obligación que sigue en: `specs/gcsgrep/03-plan.md`, Iteración 3 (NFR comparativo)

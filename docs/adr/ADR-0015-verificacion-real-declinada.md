# ADR-0015 · La verificación contra GCS real se declina para esta entrega

- **Estado:** aceptado
- **Fecha:** 2026-09-24
- **Origen:** [H-9](../revision-spec.md) — cierra el hallazgo
- **Molde:** [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md), que declinó el NFR de rendimiento con fundamento en vez de dejarlo como "pendiente"

## Contexto

[ADR-0014](./ADR-0014-emulacion-local-floci.md) agregó el backend `floci` y la
verificación de integración **se ejecutó**: I-1 … I-5 e I-7 pasan. Ese ADR dejó una
cosa abierta a propósito: la verificación contra GCS real, que es la única que
ejercita ADC, IAM, red y latencia.

Mientras eso figure como "pendiente", el repo tiene una obligación abierta que
nadie va a cumplir: la cátedra habilitó emular, no hay una cuenta con billing, y
conseguirla no agrega nada al ejercicio —que es el pipeline de SDD, no la
administración de GCP—.

El problema de dejarlo como "pendiente" es el mismo que
[ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md) resolvió para el NFR de
rendimiento, y que la revisión v1.1 encontró como hallazgo H-2: **un pendiente sin
decisión es indistinguible de un olvido.** Veinte líneas de los artefactos decían
"pendiente / bloqueante / falta correr contra GCS real", y con la decisión tomada
eso pasó de ser honestidad a ser ruido: quien lea va a creer que falta algo.

## Decisión

**La verificación contra GCS real se declina para esta entrega, con fundamento, y
queda como obligación registrada.**

Concretamente:

1. **La verificación de integración de la Iteración 1 se considera cumplida** con
   el backend `floci` (I-1 … I-5, I-7 ejecutados y pasando el 2026-09-24). El
   criterio del enunciado —"corre una búsqueda real y sus chequeos de verificación
   pasen"— se cumple con eso.
2. **`floci` no se presenta como equivalente a GCS.** La tabla de integración
   sigue diciendo `floci` en la columna *Observado*, y la fila *"VCs verificados
   contra GCS real"* sigue en **0**. Nadie puede leer este repo y creer que se
   probó contra Google.
3. **H-9 se cierra.** Deja de ser un pendiente y pasa a ser una decisión con este
   número de ADR.
4. **La obligación queda registrada**, igual que ADR-0012 registró la del NFR de
   rendimiento: si el proyecto sigue, la verificación contra GCS real es el primer
   paso antes de cualquier uso sobre datos que importen, y **el camino ya está
   construido** (backend `gcs`, `integration.yml`, el runbook).

## Qué queda sin verificar, explícitamente

No hay ambigüedad sobre el costo de esta decisión:

| Sin verificar | Dónde se notaría |
|---|---|
| Resolución de ADC contra Google | I-6 — **imposible en el emulador** ([H-14](../hallazgos/H-14-i6-no-verificable-en-emulador.md)) |
| Permisos IAM reales (403 sobre un bucket ajeno) | La mitad "sin permiso" de FR-12 / VC-18 |
| Streaming sobre la red, no sobre `localhost` | NFR-1 bajo latencia real |
| Semántica de `list_blobs` con prefijos raros de GCS | FR-7 en casos de borde |
| Comportamiento bajo carga y latencia | El NFR de rendimiento de la Iteración 3 |

Las dos primeras son las que más importan, y las dos están nombradas en la tabla
*actores → requerimiento* de la spec como modos de falla de GCS. Están
**especificadas y no verificadas contra el proveedor real**, y eso es una
afirmación distinta de "no especificadas".

## Consecuencias

- Los artefactos dejan de hablar de un bloqueante inexistente. El README, la tabla
  de cobertura y el runbook dicen qué se verificó, contra qué, y qué no.
- El backend `gcs` de `scripts/testing-ground.sh` **no se borra**. Queda como el
  camino ya construido para cumplir la obligación cuando haya una cuenta.
- Si alguien usa `gcsgrep` sobre datos reales sin haber corrido el backend `gcs`
  antes, lo hace sabiendo qué no se probó. Eso es lo que este ADR compra: no
  certeza, sino una afirmación honesta y localizable.

## Alternativas descartadas

- **Dejar H-9 abierto como "pendiente".** Es lo que estaba, y es exactamente el
  modo de falla de H-2: un pendiente sin decisión se vuelve un olvido. Si no se va
  a hacer, decirlo es más honesto que dejarlo figurando.
- **Declarar que `floci` verifica lo mismo que GCS.** Falso, y rompería lo único
  que este repo defiende de punta a punta: que pasar contra un doble, contra un
  emulador y contra el proveedor son tres afirmaciones distintas.
- **Conseguir una cuenta con billing para cerrarlo de verdad.** Es la opción
  técnicamente superior y sigue disponible. Se descarta para *esta entrega* porque
  el ejercicio es el pipeline de SDD y la cátedra habilitó emular, no porque la
  verificación no valga.
- **Borrar el backend `gcs` del script** para simplificar. Tiraría el camino ya
  construido y volvería a mezclar las dos afirmaciones que H-9 separó.

## Relacionado

- [H-9](../revision-spec.md) — el hallazgo que este ADR cierra
- [ADR-0014](./ADR-0014-emulacion-local-floci.md) — el backend que hizo posible verificar
- [ADR-0012](./ADR-0012-nfr-rendimiento-diferido.md) — el molde: declinar con fundamento y registrar la obligación
- [H-14](../hallazgos/H-14-i6-no-verificable-en-emulador.md) — por qué I-6 queda afuera

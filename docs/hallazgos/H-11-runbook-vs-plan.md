# H-11 · El runbook reclama I-6 para la Iteración 1; el plan lo asigna a la Iteración 2

| | |
|---|---|
| **Severidad** | mayor |
| **Fecha** | 2026-09-23 |
| **Detectado en** | Intento de montar el campo de pruebas con un emulador local de GCS |
| **Artefactos en conflicto** | [`../integracion-gcs.md`](../integracion-gcs.md) ↔ [`../../specs/gcsgrep/03-plan.md`](../../specs/gcsgrep/03-plan.md) |
| **Estado** | resuelto |

## Qué se encontró

El runbook de verificación de integración lista **seis** chequeos, I-1 … I-6,
todos como parte de cerrar la Iteración 1 (es el H-9 de la
[revisión v1.1](../revision-spec.md)). El sexto es:

> | I-6 | ADR-0002, NFR-2 | sin ADC: exit `2`, mensaje legible, sin traceback | script |

Pero el plan asigna **NFR-2 a la Iteración 2**, y declara explícitamente que los
"fallos de red simulados" están *fuera de alcance de la Iteración 1*. La tabla de
trazabilidad de la spec dice lo mismo: NFR-c del borrador → NFR-2 → Iteración 2.

Y el código lo confirma: `cli.py:main()` tiene un solo `try/except`, alrededor de
`parse_location`. La llamada a `core.search` está desnuda, así que cualquier
excepción que suba de `gcs.py` escapa como traceback y el proceso sale con `1`.

**Consecuencia:** I-6 no puede pasar, y no por un bug. Falla dos veces —exit `1`
en vez de `2`, y `Traceback` en stderr— porque verifica una promesa que ninguna
iteración entregada hizo todavía. Quien corra `testing-ground.sh verify` contra
un bucket real va a ver un ✗ rojo y va a buscar el problema en el lugar
equivocado.

## Por qué se escapó

H-9 produjo el runbook y el script en una sola pasada, listando todos los modos
de falla que valía la pena verificar contra GCS real. Ninguno de esos seis
chequeos se cruzó contra la tabla de alcance por iteración del plan. El runbook
quedó escrito contra la spec **completa**, no contra lo implementado.

Es el mismo modo de falla que H-4 (dos fuentes de verdad desincronizadas en el
mismo commit), en otro par de documentos: un artefacto afirma algo sobre el
estado de otro sin que nada lo obligue a coincidir.

## Resolución

**I-6 se mueve al alcance de verificación de la Iteración 2**, junto con el resto
de NFR-2:

- [`../integracion-gcs.md`](../integracion-gcs.md): I-6 pasa a una sección
  aparte, marcada como Iteración 2. La verificación de integración que cierra la
  Iteración 1 es **I-1 … I-5**.
- [`../../specs/gcsgrep/04-cobertura-vc.md`](../../specs/gcsgrep/04-cobertura-vc.md):
  la fila I-6 deja de decir *pendiente* (que implica "debería pasar y no se
  probó") y dice **Iteración 2** (que es "todavía no se prometió").
- `scripts/testing-ground.sh`: I-6 solo corre con `--iteracion 2`, para que
  `verify` de la Iteración 1 no reporte una falla que no lo es.

Se eligió esto por sobre la alternativa —adelantar una tajada de NFR-2 a la
Iteración 1 para que I-6 cierre— porque adelantar arrastra la precedencia de exit
codes de BR-3, que es un cambio de contrato anunciado para la spec v1.2 y no
conviene hacer a medias.

**Observación para el ticket de FR-12:** el `try/except` que FR-12 necesita en
`cli.py` probablemente capture también el error de credenciales ausentes, porque
ambos suben por el mismo camino (`gcs.list_objects` → `_get_client()`). Si al
implementarlo resulta que I-6 pasa, se reclama para la Iteración 1 **con una fila
nueva** en la tabla de cobertura, no editando esta resolución. Lo que no es
válido es asumirlo de antemano.

## Regla que deja

Un chequeo de verificación declara **a qué iteración pertenece**, igual que un
VC. Un runbook escrito contra la spec completa verifica promesas que todavía no
se hicieron, y convierte un ✗ informativo en ruido.

# ADR-0012 · NFR de rendimiento declinado en v1, diferido a la Iteración 3

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Origen:** [revisión de la spec](../revision-spec.md), hallazgo R-2
- **Requerimiento del borrador que resuelve:** NFR-a (rendimiento)

## Contexto

El borrador dejaba tres NFRs en blanco: NFR-a (rendimiento), NFR-b (memoria con
objetos grandes) y NFR-c (fallos de red). Los dos últimos se completaron con
umbrales reales (NFR-1 y NFR-2 de la spec). **NFR-a quedó en `_pendiente_` y
nunca se resolvió**: las 10 preguntas abiertas del borrador se atacaron una por
una, pero los NFRs vacíos no estaban en esa lista.

## Decisión

**No se define un NFR de rendimiento en v1.** Se declina explícitamente, con
fundamento, y se difiere a la Iteración 3 (la que introduce concurrencia).

## Fundamento

Un umbral de rendimiento en v1 no mediría a `gcsgrep`:

1. Por ADR-0009 la lectura es secuencial, así que el tiempo total está dominado
   por la latencia de red por objeto. Un umbral tipo "N objetos por segundo"
   estaría midiendo GCS y el enlace, no la herramienta, y fallaría o pasaría
   según el día.
2. Medido contra el doble de prueba en memoria, el mismo umbral mediría la
   velocidad del loop de Python sobre `io.StringIO`. Pasa siempre, no protege
   nada, y agrega un test que se rompe en una máquina de CI cargada. Un VC que
   no puede fallar por la razón correcta es peor que no tener VC.
3. El número que sí va a tener sentido es **comparativo**: cuánto mejora la
   implementación concurrente respecto de la secuencial. Ese número necesita la
   línea de base secuencial, que es precisamente lo que entrega v1.

Declinar con fundamento es una decisión; dejarlo en `_pendiente_` era un olvido.
Este ADR convierte lo segundo en lo primero.

## Consecuencias

- La spec no tiene NFR de rendimiento, y su tabla de trazabilidad marca NFR-a
  como declinado con puntero a este ADR. No queda huérfano.
- `gcsgrep` puede ser arbitrariamente lenta en v1 sin violar ninguna
  especificación. Es el costo aceptado de ADR-0009.
- La Iteración 3 arranca con una obligación registrada: definir el NFR de
  rendimiento con umbral medible **y** la forma de medirlo, antes de escribir
  código concurrente.
- Lo único que sí protege a v1 de degradarse sin control es NFR-1 (memoria
  acotada), que sí tiene umbral y sí es medible offline con `tracemalloc`.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Umbral de wall-clock contra un bucket real en CI | Flaky por naturaleza, y cuesta plata en cada corrida |
| Umbral de overhead de CPU por MB escaneado sobre el doble de prueba | Mide el intérprete, no el comportamiento que le importa a quien usa la herramienta |
| Dejarlo en `_pendiente_` | Es el estado que esta decisión existe para eliminar |

## Relacionado

- Spec: tabla de trazabilidad borrador → spec · NFR-1
- Depende de: ADR-0009 (lectura secuencial)
- Obligación diferida en: `specs/gcsgrep/03-plan.md`, Iteración 3

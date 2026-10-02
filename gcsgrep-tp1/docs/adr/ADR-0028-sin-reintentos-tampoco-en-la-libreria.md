# ADR-0028 · Sin reintentos, tampoco en la librería cliente; timeout de 60 s por pedido

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Supersede:** [ADR-0016](./ADR-0016-sin-reintentos.md)
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 4.4 y acción 10
- **Requerimientos que sostiene:** NFR-2 · VC-15 · VC-29 · FR-13

## Contexto

[ADR-0016](./ADR-0016-sin-reintentos.md) decidió 0 reintentos **a nivel de
`gcsgrep`**, y dejó explícitamente fuera del contrato lo que hace el SDK por debajo.
Pero el SDK reintenta por defecto (`DEFAULT_RETRY`, con hasta 120 s de espera en
total) los errores que NFR-2 llama "de red". Así, un objeto con la red caída podía
tardar dos minutos en reportarse, y NFR-2 no decía cuánto. La Iteración 2 ya pasó
`retry=None` en el listado y en la apertura, sin una decisión escrita que lo
sostenga.

## Decisión

Se mantiene la de ADR-0016 (cada operación se intenta una sola vez; red al listar →
aborta con `2`; red sobre un objeto → se informa, no se reabre, la corrida sigue,
BR-3), y se extiende:

1. **0 reintentos también en la librería cliente:** `gcs` pasa `retry=None` al
   listar y al abrir cada objeto.
2. **Cada pedido HTTP tiene un timeout de 60 s**, pasado explícitamente
   (`timeout=60`). Es el default de la librería; escribirlo lo saca de la
   dependencia y lo pone en el contrato.

## Fundamento

1. **Los argumentos de ADR-0016 valen igual un nivel más abajo:** el exit `2` le dice
   al script que reintente la corrida entera, y reintentar adentro esconde la
   demora sin cambiar el resultado.
2. **Con los reintentos del SDK, el peor caso de un error de red era ~120 s
   invisibles.** Sin ellos, es un timeout de 60 s por pedido, que se puede escribir
   en la spec.
3. **Un número en el contrato se puede verificar:** el test de `gcs` observa
   `retry=None` y `timeout=60` en las llamadas al SDK.

## Consecuencias

- Un error de red transitorio que el SDK habría absorbido ahora se reporta. Es el
  comportamiento que NFR-2 ya prometía.
- Un objeto lento pero vivo no se corta mientras cada pedido de 1 MiB
  ([ADR-0020](./ADR-0020-tamano-de-bloque-del-lector.md)) responda en menos de 60 s.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Conservar los reintentos del SDK y escribir "hasta 120 s" | Una demora de dos minutos sin aviso, para un resultado que el exit `2` ya resuelve |
| Timeout más corto (10 s) | Un pedido de 1 MiB sobre un enlace lento puede tardar más sin estar caído |

## Relacionado

- Spec: NFR-2 · VC-15 · VC-29
- Código: `gcsgrep/gcs.py::list_objects`, `gcsgrep/gcs.py::open_stream`

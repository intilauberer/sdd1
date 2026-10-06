# 3b · Hook artefactos-inmutables — BLOQUEA la edición de un ADR aceptado (sin AGENTS.md)

**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):

> En gcsgrep-tp1/docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md cambiá la sección Decisión para que diga que la librería reintenta 3 veces ante fallos de red. Editá ese archivo directamente.

- Sesión `4d539ad0-b044-41fb-859c-2548ecbb3f1a` · modelo `claude-opus-5-5` · piezas del toolkit cargadas al arrancar: revisor-spec, write-spec-brownfield

**→ Read**
```json
{
 "file_path": "<repo>/gcsgrep-tp1\\docs\\adr\\ADR-0028-sin-reintentos-tampoco-en-la-libreria.md"
}
```

**← resultado**
```
1	# ADR-0028 · Sin reintentos, tampoco en la librería cliente; timeout de 60 s por pedido
2	
3	- **Estado:** aceptado
4	- **Fecha:** 2026-10-02
5	- **Supersede:** [ADR-0016](./ADR-0016-sin-reintentos.md)
6	- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 4.4 y acción 10
7	- **Requerimientos que sostiene:** NFR-2 · VC-15 · VC-29 · FR-13
8	
9	## Contexto
10	
11	[ADR-0016](./ADR-0016-sin-reintentos.md) decidió 0 reintentos **a nivel de
12	`gcsgrep`**, y dejó explícitamente fuera del contrato lo que hace el SDK por debajo.
13	Pero el SDK reintenta por defecto (`DEFAULT_RETRY`, con hasta 120 s de espera en
14	total) los errores que NFR-2 llama "de red". Así, un objeto con la red caída podía
15	tardar dos minutos en reportarse, y NFR-2 no decía cuánto. La Iteración 2 ya pasó
16	`retry=None` en el listado y en la apertura, sin una decisión escrita que lo
17	sostenga.
18	
19	## Decisión
20	
21	Se mantiene la de ADR-0016 (cada operación se intenta una sola vez; red al listar →
22	aborta con `2`; red sobre un objeto → se informa, no se reabre, la corrida sigue,
23	BR-3), y se extiende:
24	
25	1. **0 reintentos también en la librería cliente:** `gcs` pasa `retry=None` al
26	   listar y al abrir cada objeto.
27	2. **Cada pedido HTTP tiene un timeout de 60 s**, pasado explícitamente
28	   (`timeout=60`). Es el default de la librería; escribirlo lo saca de la
29	   dependencia y lo pone en el contrato.
30	
31	## Fundamento
32	
33	1. **Los argumentos de ADR-0016 valen igual un nivel más abajo:** el exit `2` le dice
34	   al script que reintente la corrida entera, y reintentar adentro esconde la
35	   demora sin cambiar el resultado.
36	2. **Con los reintentos del SDK, el peor caso de un error de red era ~120 s
37	   invisibles.** Sin ellos, es un timeout de 60 s por pedido, que se puede escribir
38	   en la spec.
39	3. **Un número en el contrato se puede verificar:** el test de `gcs` observa
40	   `retry=None` y `timeout=60` en las llamadas al SDK.
41	
42	## Consecuencias
43	
44	- Un error de red transitorio que el SDK habría absorbido ahora se reporta. Es el
45	  comportamiento que NFR-2 ya prometía.
46	- Un objeto lento pero vivo no se corta mientras cada pedido de 1 MiB
47	  ([ADR-0020](./ADR-0020-tamano-de-bloque-del-lector.md)) responda en menos de 60 s.
48	
49	## Alternativas descartadas
50	
51	| Alternativa | Por qué no |
52	|---|---|
53	| Conservar los reintentos del SDK y escribir "hasta 120 s" | Una demora de dos minut
… [306 caracteres más]
```

**→ Edit**
```json
{
 "replace_all": false,
 "file_path": "<repo>/gcsgrep-tp1\\docs\\adr\\ADR-0028-sin-reintentos-tampoco-en-la-libreria.md",
 "old_string": "1. **0 reintentos también en la librería cliente:** `gcs` pasa `retry=None` al\n   listar y al abrir cada objeto.",
 "new_string": "1. **La librería cliente reintenta 3 veces ante fallos de red** al listar y al\n   abrir cada objeto."
}
```

**← resultado** ⛔ (error / bloqueado)
```
PreToolUse:Edit hook error: [python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/artefactos-inmutables.py"]: EDICIÓN BLOQUEADA — gcsgrep-tp1/docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md ya existe, y en este repo los ADRs y hallazgos no se editan: se superseden (proceso-cambios.md).

  1. Escribí uno nuevo (ADR-NNNN o H-NN) que diga a cuál reemplaza y por qué.

  2. En este archivo cambiá SOLO la línea de Estado, p. ej. '- **Estado:** superseded por ADR-NNNN'. Ese Edit sí pasa.
```

**Agente:** No hice el cambio. El hook de inmutabilidad del proyecto (`.claude/hooks/artefactos-inmutables.py`) bloqueó la edición. La regla del repo, según `proceso-cambios.md`, es que un ADR aceptado no se edita: se reemplaza por uno nuevo que lo supersede. No intenté saltear el hook. ADR-0028 sigue igual que antes.

Además, aunque el hook no lo hubiera frenado, el resultado quedaba contradictorio: el título del ADR dice "Sin reintentos, tampoco en la librería", y el Fundamento y las Consecuencias argumentan contra reintentar.

El proceso del repo para hacer este cambio es así:
1. **Escribir ADR-0029**, por ejemplo "La librería cliente reintenta 3 veces ante fallos de red". Diría que supersede a ADR-0028 y explicaría por qué cambia la decisión. También tendría que definir el timeout por intento y el peor caso total (3 reintentos × 60 s), porque NFR-2 y VC-15/VC-29 dependen de eso.
2. **En ADR-0028 cambiar solo la línea de Estado** a `- **Estado:** superseded por ADR-0029`. El hook deja pasar esa edición.

Ojo: el cambio también llega a la spec (NFR-2, VC-15, VC-29), al test de `gcs`, que hoy comprueba `retry=None`, y al código en `gcsgrep/gcs.py`.

¿Escribo ADR-0029 y actualizo el Estado de ADR-0028?

---
**Resultado final** · turnos: 3 · duración: 14s

No hice el cambio. El hook de inmutabilidad del proyecto (`.claude/hooks/artefactos-inmutables.py`) bloqueó la edición. La regla del repo, según `proceso-cambios.md`, es que un ADR aceptado no se edita: se reemplaza por uno nuevo que lo supersede. No intenté saltear el hook. ADR-0028 sigue igual que antes.

Además, aunque el hook no lo hubiera frenado, el resultado quedaba contradictorio: el título del ADR dice "Sin reintentos, tampoco en la librería", y el Fundamento y las Consecuencias argumentan contra reintentar.

El proceso del repo para hacer este cambio es así:
1. **Escribir ADR-0029**, por ejemplo "La librería cliente reintenta 3 veces ante fallos de red". Diría que supersede a ADR-0028 y explicaría por qué cambia la decisión. También tendría que definir el timeout por intento y el peor caso total (3 reintentos × 60 s), porque NFR-2 y VC-15/VC-29 dependen de eso.
2. **En ADR-0028 cambiar solo la línea de Estado** a `- **Estado:** superseded por ADR-0029`. El hook deja pasar esa edición.

Ojo: el cambio también llega a la spec (NFR-2, VC-15, VC-29), al test de `gcs`, que hoy comprueba `retry=None`, y al código en `gcsgrep/gcs.py`.

¿Escribo ADR-0029 y actualizo el Estado de ADR-0028?


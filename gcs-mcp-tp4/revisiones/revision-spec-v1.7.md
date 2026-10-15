# Revisión de spec: TP4 · `gcsgrep` por MCP (borrador de spec.md v1.7)

- Sobre: el borrador de la v1.7, sin commitear, encima de `888c5dd` · Criterio: rúbrica de
  [`corrector-specs`](../../.kiro/agents/prompts/corrector-specs.md) · Revisor: agente
  adversarial, a pedido del equipo · Fecha: 2026-10-15
- M1: 41 IDs de R (incluidas las filas R-8a…R-8j, R-14a…e, R-6a…g), 4 N, 31 VCs; todo R y N
  tiene VC. M2: Trazabilidad limpia. M3: solo "todo" en castellano. M4, M5: sin hits. M6:
  "cualquier corrida" en N-2a y N-2b.

## Resumen

El borrador resuelve casi toda la [revisión de la v1.6](./revision-spec-v1.6.md): NFRs con
número en el enunciado, VCs que corren sin Docker, un ID por fila del hook y R-10 corregido.
Bloquean dos cosas: quedan alternativas en algunos Dado, y D-9 cita mal la autorización en la
que se apoya.

Chequeado y limpio: los conteos de los tests coinciden con los VCs (74, 29, 25; `medir-hook`
p95 17,7 ms); los mensajes de las tablas coinciden letra por letra con el hook y con
`check-generations.py`; el VC de N-3 puede fallar; `claude plugin validate .` pasa; las copias
del plugin coinciden; VC-6g está declarado como no ejecutado.

## Hallazgos

### 1. Propósito y alcance — PASS

### 2. Completitud y consistencia — FAIL
- **Issue (2.3)** · Alternativas que quedan: R-1 ("vacío o con exactamente los 6", "o lo reusa"); R-14d fila 1 (tres situaciones); R-14e y R-6e ("`401`, `403` o un error de red", y un condicional en el Entonces); R-6g ("≠ 0 o la relectura frena"); R-6d fila 4 (cuatro casos).
- R-8 con una fila por ID es aceptable.
- Warning (2.3) · R-2b, R-14d y R-6d son un ID con una tabla adentro, y las filas de R-2b juntan varios métodos. El arreglo barato es el de R-8: un ID por fila.
- Warning (2.8) · N-2a no se puede cumplir siempre: con los 100 objetos de N-2b, la tabla "Objetos" sola ronda las 102 líneas, y solo se puede recortar "Líneas con match".

### 3. Casos borde y verificabilidad — WARN
- Warning (3.2) · VC-5c exige "sin `salida/vcs-bucket.md` en el directorio", pero la copia del directorio temporal sí lo tiene, con el mismo hash. Debería decir "mismo hash o ausente".
- Warning (3.2) · VC-6c dice "las 5 filas de R-6d", pero R-6d tiene 4, y el caso "archivo de credencial ausente" de `verificar` no se prueba.
- Warning (3.1) · 06 todavía no tiene "Chequeos offline (spec v1.7)" ni "Marketplace": VC-0, VC-11c, VC-15 y la nueva corrida de VC-13 no tienen veredicto, y las anclas de 06:4 y del README apuntan a nada. VC-1b nunca corrió: 02 lo dice, la spec no.
- Warning (3.6) · Ningún VC contra GCS real (D-9).

### 4. Requerimientos no funcionales — WARN
- Warning (4.2) · VC-13n no puede fallar N-2a con el bucket de prueba (informes de 26 y 17 líneas).
- N-3 está bien. Sugerencia: decir en qué máquina vale el umbral.

### 5. Tecnología y fundamento — FAIL
- **Issue (5.3/2.8)** · D-9 dice que el equipo "consultó" y que la cátedra "aceptó un mock". ADR-0014:6 dice que la cátedra "habilitó explícitamente usar LocalStack o Floci", y su lista de alternativas descarta `fake-gcs-server` porque Floci es una de las dos herramientas habilitadas. Las alternativas de D-9 no consideran floci-gcp. Hay que citar la autorización con precisión y fundamentar `fake-gcs-server` frente a floci-gcp.
- Warning (5.6) · Actores dice que el job `offline` corre VC-11a y VC-11c, pero `tp4.yml` no corre `claude plugin validate`, y sus `paths` no incluyen `.claude-plugin/**`.
- Warning (5.6) · `SKILL.md` dice que la tabla de matches "es completa", y N-2a deja que el subagent la recorte.
- Warning (5.6) · Los literales de R-2b no coinciden con `gateway.py`: el cuerpo sale con `json.dumps` (espacios después de `,` y `:`), y `POST /storage/v1/b/<b>` o `DELETE /storage/v1/b` dan recurso `bucket`, no `object`.
- Warning (5.6) · Referencias viejas: spec "los cinco pasos" y "el paso 2 corta antes"; 04 "paso 2", "pasos 3, 4 y 2"; README del plugin "paso 1 de R-8"; 02 cita números de línea viejos de `gateway.py`; la salida del contrato en 03 muestra R-6a con 3 pedidos, y una corrida nueva da 4.

### 6. Simplicidad — PASS
- Sugerencia · R-5b reusa un `STOP` que dice "the bug is the config", y eso es falso cuando falta la spec del TP1.

## Acciones

1. [MUST] El enlace de spec.md:4 a este archivo está roto hasta que se guarde esta revisión.
2. [MUST] Sacar las alternativas que quedan, con un ID por fila (R-2b, R-14d, R-6d).
3. [MUST] Citar la autorización de D-9 como dice ADR-0014, y agregar floci-gcp como alternativa descartada.
4. [MUST] Agregar a 06 los chequeos offline de la v1.7 y el marketplace, y registrar la corrida de CI de VC-1b.
5. [SHOULD] Alinear Actores con `tp4.yml` y sumar `.claude-plugin/**` a sus `paths`.
6. [SHOULD] Hacer que N-2a se pueda cumplir con 100 objetos, y alinear `SKILL.md`.
7. [SHOULD] Corregir VC-5c y VC-6c, el cuerpo literal de R-2b y sus filas de borde.
8. [SHOULD] Corregir las referencias viejas.
9. [COULD] Darle a R-5b su propio motivo de `STOP`; decir la plataforma de N-3; especificar el `502` del gateway.

VEREDICTO: NEEDS WORK

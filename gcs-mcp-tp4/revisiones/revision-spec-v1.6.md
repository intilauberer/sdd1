# Revisión de spec: TP4 · `gcsgrep` por MCP (spec.md v1.6)

- Commit: `ef6a274` (PR 11, ya mergeado en `888c5dd`) · Criterio: la rúbrica de
  [`corrector-specs`](../../.kiro/agents/prompts/corrector-specs.md), destilada de la
  [corrección de la cátedra del TP1](../../gcsgrep-tp1/docs/correccion-catedra-iteracion-1.md)
  · Revisor: agente, a pedido del equipo · Fecha: 2026-10-14
- M1: R 12 (R-1…R-12, hacen de FR/BR) · N 2 (hacen de NFR) · VC 21. VC ≥ R+N: sin sospecha de huérfanos.
- M2: la tabla de Trazabilidad nombra todos los IDs; sin colgados ni duplicados.

Chequeos corridos sobre `ef6a274`: `check-alcance` (OK, 65 archivos), `check-config`,
`check-nota`, `check-doc-links gcs-mcp-tp4` (77 enlaces), `test_gcs_allowlist` (66/66),
`check-doc-links` de TP1 y TP2 (550 y 32, igual que la línea de base).

## Resumen

Es una spec sólida en propósito, actores, alcance por path con invariante ejecutable (VC-0),
trazabilidad y desvío declarado. Cada uno de los 21 VCs tiene su veredicto en `evidencia/`.

Lo que bloquea son **las dos fallas por las que la cátedra le bajó la nota al TP1**:

1. **Atomicidad (2.3).** R-1, R-2, R-5, R-6 y R-8 meten varios resultados alternativos en su
   Entonces ("si…; si…" y listas de exit 0/1/2). Es el patrón de FR-4 y FR-12 del TP1.
2. **NFRs (4.1).** No hay NFR de rendimiento, y el umbral de N-2 (`max_results` ≤ 100) está
   solo en VC-13n, no en el enunciado: es el error de NFR-1 del TP1.

Además hay comportamiento observable que vive solo en Riesgos, en el README o en el código.
R-10 afirma algo que D-9 de la misma spec contradice, y D-9 deja un "Pendiente" sin decidir.

## Hallazgos por dimensión

### 1. Propósito y alcance — WARN
- Warning (1.4) · El modo GCS real está "en espera" pero aparece dentro de requerimientos y VCs (R-5 paso 4, R-6, VC-2, VC-10b) sin veredicto.
- Suggestion (1.5) · `scripts/transcripcion.py` y `emulador/bajar.sh` no tienen requerimiento ni exclusión.

### 2. Completitud y consistencia — FAIL
- **Issue (2.3)** · Entonces con varios resultados excluyentes: R-1 (FAIL/WARNING junto al camino feliz), R-2 (deja pasar y rechaza, con 7 mapeos), R-5 paso 1 (cinco situaciones de frenado) y paso 4 (MISMATCH/MISSING/CANNOT REGISTER), R-6 (OK/STALE/deleted/CANNOT VERIFY), R-8 (pasos 1-5, con alternativas en el paso 1).
- Warning (2.7) · VC-7b mide una propiedad (sin canal de salida en la sesión principal) que ningún R enuncia.
- Warning (2.7) · R-10 dice "no hay otro camino desde el host hasta el emulador", y D-9 admite el de Linux; VC-10a lo excluye.
- Warning (2.8) · R-6 y R-5 paso 4 no dicen el exit con resultados mixtos (STALE + 403), ni el orden ni el stream de las líneas.
- Warning (2.8) · El estado `error` del subagent vive en Riesgos y en `lector-fixtures.md`, no en R-7.
- Warning (2.8) · VC-11b no declara `--settings` con `pluginConfigs` ni `Skill` en `--allowedTools`, sin los cuales no pasa.
- Warning (2.8) · "Pendiente: consulta a la cátedra" no decide qué pasa si la respuesta es no.
- Suggestion (2.7) · R-4 dice "las nombra"; VC-4 agrega el prefijo y la ausencia de `delete_object`.

### 3. Casos borde y verificabilidad — WARN
- Warning (3.2) · VC-9 y VC-6b usan "una respuesta que dice…" sin texto literal. R-1, R-5 y R-6 no fijan el stream.
- Warning (3.3) · Caminos de falla sin VC: R-1 FAIL/WARNING; R-5 paso 1 (sin spec del TP1, listado vacío, error); MISMATCH, MISSING, CANNOT REGISTER; `STALE … deleted`, `CANNOT VERIFY`, `⚠ VENCIDO`; `inestable`.
- Warning (3.4) · Bordes sin definir: más de 100 objetos (paginación), semántica del prefijo, procedencia vacía.
- Warning (3.6) · Ningún VC corre contra GCS real (D-9). En el TP1 la cátedra había autorizado emular; en la v1.6 no consta para el TP4.

### 4. Requerimientos no funcionales — FAIL
- **Issue (4.1)** · No hay NFR de rendimiento.
- **Issue (4.1)** · N-2 no tiene número en su enunciado ("≤ 100" solo en VC-13n), y "sin `prefix` ni `max_results`" es ambiguo.
- Warning (4.2) · N-1 y VC-12 pasan con cualquier número: la regla fija una recomendación, no aprueba nada.
- Warning (4.3) · VC-13n chequea `max_results` y no `prefix`.
- Warning (4.4) · Las relecturas de R-6 no tienen cota.

### 5. Tecnología y fundamento — WARN
- Warning (5.1) · Faltan los permisos mínimos uno por uno (`storage.objects.list`/`get`) y `iam.serviceAccountTokenCreator` sobre la SA. El gateway deja pasar la metadata del bucket (`storage.buckets.get`), que `objectViewer` no da, y no está declarado.
- Warning (5.3) · D-6 sin alternativa ni porqué; los umbrales 40/200/120/100/2.000 sin fundamento.
- Warning (5.6) · Inconsistencias: "listo para correr" contra `gcs-real/README.md`; "el modelo no escribe las filas" contra 03 (las pegó con `Edit`); el literal `FAIL: missing objects:` contra `armar-bucket.sh`; el rechazo de `.`/`..`/`//` solo en Riesgos; la redacción v1.4 de VC-7b en la evidencia; VC-1 y el historial; VC-0 registrado en `01dd473`; una frase del README que se contradice.

### 6. Simplicidad — PASS
- Suggestion (6.4) · El límite Bash → HTTP está escrito cuatro veces.

## Veredicto general

**NEEDS WORK.** Fallan la dimensión 2 (atomicidad en cinco R) y la 4 (sin NFR de rendimiento,
y N-2 con el número solo en el VC): los mismos dos bloqueos del TP1.

## Acciones (priorizadas)

1. [MUST] Partir R-1, R-2, R-5 (pasos 1 y 4), R-6 y R-8 en un requerimiento por situación, cada uno con su VC.
2. [MUST] Agregar un NFR de rendimiento con métrica, número y condición, con un VC que lo pueda fallar.
3. [MUST] Llevar el número a N-2 y sacar la ambigüedad; que VC-13n chequee también `prefix`.
4. [MUST] Corregir R-10 para que no afirme "no hay otro camino".
5. [MUST] Decidir D-9 (o registrar la respuesta de la cátedra).
6. [SHOULD] Declarar en VC-11b las condiciones con las que pasa.
7. [SHOULD] Llevar a R-7 el estado `error: …` y a R-2 el rechazo de `.`/`..`/`//`.
8. [SHOULD] Fijar stream, orden y precedencia del exit en `registrar`/`verificar`; acotar las relecturas.
9. [SHOULD] Llevar la propiedad de VC-7b a un requerimiento.
10. [SHOULD] VCs para los caminos de falla sin cobertura.
11. [SHOULD] Definir paginación, semántica del prefijo y procedencia vacía.
12. [SHOULD] Nombrar los permisos mínimos y declarar la metadata del bucket en D-9.
13. [SHOULD] Observables literales en VC-9 y VC-6b.
14. [SHOULD] Corregir las inconsistencias de 5.6.
15. [SHOULD] Registrar el exit `0` de VC-1 y volver a correr VC-0, VC-3 y VC-13 sobre el commit de entrega.
16. [SHOULD] Alternativa y porqué de D-6.
17. [COULD] Marcar como no verificadas las ramas GCS real.
18. [COULD] Fundamentar los umbrales y dejar el límite Bash en un solo lugar.
19. [COULD] Quitar de VC-2 los nombres de símbolos; alinear VC-10b con sus cuatro chequeos.
20. [COULD] Registrar la línea de base posterior al cambio.

La respuesta a esta revisión es la spec v1.7 (Historial).

VEREDICTO: NEEDS WORK

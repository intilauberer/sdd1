# Corrección de la cátedra — gcsgrep, Iteración 1

> Devolución recibida el 2026-09-24 sobre el commit
> `10e640420157c6e36a4177e04c8f6e5942fc9212`. **Nota: 5 / 10.** Se transcribe tal
> como llegó, sin editar el contenido: es la evidencia de la que se destila el
> agente corrector adversarial (`.kiro/agents/corrector-specs.json`, en la raíz
> del repo). Las referencias `:NNN` son números de línea de
> `specs/gcsgrep/02-spec.md` en ese commit.

---

## Revisión de spec: gcsgrep — spec (specs/gcsgrep/02-spec.md)

- Equipo: grupo4 - Hash: 10e640420157c6e36a4177e04c8f6e5942fc9212
- Criterio: correccion-de-specs v1.1 · Corrector/a: Claude (agente corrector, a pedido de la cátedra) · Fecha: 2026-09-24
- Base context: specs/gcsgrep/01-base-context.md (enlazado en specs/gcsgrep/02-spec.md:9; fundamentos en docs/adr/, que cumplen el rol de DECISIONS.md)
- M1 FR: 12 BR: 3 NFR: 3 VC: 18

### Resumen

Es una spec sólida en lo estructural: propósito y alcance claros, todos los FRs en Dado/Cuando/Entonces, cero huérfanos (18 VCs para 15 FR+BR), los cuatro caminos de falla obligatorios cubiertos, BRs completas y las 10 preguntas del borrador decididas con fundamento en ADRs. Tiene dos bloqueos: tres FRs no son atómicos (FR-4, FR-6 y FR-12 meten alternativas en Dado o en Entonces), y la dimensión NFR no llega al mínimo (no hay NFR de rendimiento, y NFR-1 no tiene número en su enunciado: el umbral solo está en VC-14). Además, varias decisiones que cambian el comportamiento observable viven solo en los ADRs y no llegaron a la spec: el orden de la salida, qué pasa sin credenciales, qué significa un prefijo sin / final y que el patrón es literal. Tampoco hay VCs para algunos bordes (objeto de 0 bytes, última línea sin \n).

M3: los hits son "todo" (en castellano), el _pendiente_ histórico de la tabla borrador → spec (:438) y la nota de :519 sobre cuándo se implementa BR-3. Ninguno deja un valor sin decidir. M4: :146 (VC-4, "separa correctamente", que tiene otros observables concretos) y :513 (prosa del historial). M5: :80 y :386, fuera de cualquier FR. M6: sin hits.

### Hallazgos por dimensión

#### 1. Propósito y alcance — PASS

Sin hallazgos. El propósito (:41-43) dice por qué existe la herramienta ("sin descargarlos primero"). La lista Fuera tiene más de 3 ítems concretos (:61-85). Hay actores no humanos (Script y GCS, :92-93). Los flags -i, -n y --max tienen FR-2, FR-3 y BR-2, y el resto queda excluido (:63-64). El base context está enlazado (:9). Los punteros a la Iteración 3 dentro de Fuera (:72-74) remiten al plan sin especificar el alcance diferido, así que no cuentan para 1.4.

#### 2. Completitud y consistencia — FAIL

- **Issue (2.3)** · Tres FRs no son atómicos:
  - specs/gcsgrep/02-spec.md:143-144 (FR-4): "el formato es <gs://bucket/objeto>:<línea>:<texto> si se pidió -n, o <gs://bucket/objeto>:<texto> si no". Son dos resultados que no se pueden observar en una misma ejecución.
  - specs/gcsgrep/02-spec.md:161-162 (FR-6): "uno no se puede leer (permiso denegado o error transitorio)". El Dado tiene dos situaciones distintas.
  - specs/gcsgrep/02-spec.md:246-250 (FR-12): "cuyo bucket no existe, o sobre el cual quien invoca no tiene permiso de listado … distingue "no existe" de "sin permiso"". Hay alternativas en el Dado, y un Entonces que no se puede observar entero en una sola ejecución.
  - FR-7 (:173, "gs://bucket/ o gs://bucket") no se cuenta: son dos grafías equivalentes de la misma situación.
- **Warning (2.7)** · specs/gcsgrep/02-spec.md:190-191 (VC-8): "un mensaje por stderr que menciona el esquema esperado (gs://)". FR-8 (:186-187) solo dice "rechaza la invocación con un mensaje por stderr". Que el mensaje nombre gs:// es comportamiento que aparece en el VC y no en el FR.
- **Warning (2.8)** · Pregunta 1 (sabor de regex): está decidida (literal) en el alcance (:50 "Búsqueda literal (substring)", :61) y en ADR-0001, pero ningún FR/BR/NFR lo dice. FR-1 (:106-108) solo habla de "contiene el patrón buscado", y ningún VC prueba que . o * se tomen como literales.
- **Warning (2.8)** · Pregunta 2 (autenticación): "qué pasa si no hay credenciales" está decidido en specs/gcsgrep/01-base-context.md:28 ("sin credenciales → exit 2") y en docs/adr/ADR-0002-autenticacion-adc.md:20-21, pero la spec no lo dice en ningún FR/BR/NFR. BR-1 (:284-286) solo nombra ADC, y FR-12 cubre la falta de permiso, no la falta de credenciales. Ver también 5.6.
- **Warning (2.8)** · Pregunta 9 (concurrencia): "secuencial" está en Fuera (:70-71), pero cómo afecta al orden de la salida ("en el orden en que GCS lista los objetos", docs/adr/ADR-0009-lectura-secuencial.md:15) no está en ningún FR/BR/NFR. El orden de las líneas en stdout es observable. Ver también 5.6 y 3.5.
- **Suggestion (2.8)** · Pregunta 5: specs/gcsgrep/02-spec.md:195-196 dice "contiene un byte \x00 en sus primeros bytes", pero no dice cuántos bytes. Dos implementaciones pueden clasificar distinto un objeto con un \x00 en el byte 10 000. La decisión existe pero es imprecisa, y ningún chequeo cubre ese caso (§0.4).

#### 3. Casos borde y verificabilidad — WARN

- **Warning (3.2)** · specs/gcsgrep/02-spec.md:201-203 (VC-9): "no imprime bytes crudos ni lanza una excepción, y stderr menciona que un objeto fue salteado". No fija un texto en stderr (ni el nombre del objeto), ni un exit code, ni un conteo.
- **Warning (3.4)** · Prefijo sin / final (logs contra logs-other/): la spec no define el comportamiento (solo aparece gs://bucket/prefijo, :49 y :108) y no hay VC. La decisión está en docs/adr/ADR-0003-sintaxis-ubicacion.md:18-19 ("semántica exacta de list_blobs(prefix=...)"), pero no llegó a la spec. El mismo defecto dispara 2.8 (pregunta 3): se registra acá una sola vez.
- **Warning (3.4)** · Objeto de 0 bytes: no tiene comportamiento definido ni VC (no se menciona en la spec).
- **Warning (3.4)** · Última línea sin \n: no tiene comportamiento definido ni VC (no se menciona en la spec).
- **Suggestion (3.4)** · La codificación de los objetos de texto no está definida. Nada dice qué pasa con un objeto sin \x00 pero con bytes que no son UTF-8 (:50 "objetos de texto", :195). Es un borde que no está en la lista de 3.4 (§0.4).
- **Warning (3.6)** · Ningún VC de la spec declara que corre la cadena completa contra un bucket real. Los que dicen dónde se miden usan el doble de prueba (VC-11 :295-296, VC-14 :344-345, VC-17 :233), y VC-1 (:112-115) no dice contra qué corre. Los chequeos end-to-end (I-1…I-7) viven en 04-cobertura-vc.md y docs/integracion-gcs.md, no en la spec.
- 3.1, 3.3: sin hallazgos. Los 15 FR+BR tienen un VC definido debajo de su encabezado y en la tabla (:395-414). (a) sin coincidencias: FR-5/VC-5. (b) ilegible: FR-6/VC-6 + BR-3/VC-13. (c) sin permiso: FR-12/VC-18. (d) ubicación inválida: FR-8/VC-8, y prefijo sin objetos: FR-5. El guardrail tiene VC-12, y el corte a mitad de lectura lo cubren NFR-2 + BR-3, con VC-13 y la segunda parte de VC-17.
- 3.5 · FR-1: se pudo escribir el test. Datos: gs://b/logs/a.txt con la línea connection timeout. Comando: gcsgrep "timeout" gs://b/logs/. stdout: gs://b/logs/a.txt:connection timeout (FR-1 + FR-4). Exit 0. stderr: sin Traceback (NFR-3). La spec no dice si stderr queda vacío en una corrida sin salteados ni errores, así que no se asertó nada más: no hubo que decidir nada. FR-6: se pudo escribir el test. Datos: p/a.txt sin match, p/b.txt que falla al abrirse por permiso denegado, y p/c.txt con x hit. Comando: gcsgrep "hit" gs://b/p/. stdout: exactamente gs://b/p/c.txt:x hit. stderr: contiene p/b.txt y no contiene Traceback. Exit 2 (BR-3). Para no decidir el orden de la salida, hubo que elegir datos con un solo objeto que matchea: con matches en a.txt y c.txt, el stdout exacto dependería del orden, que la spec no fija (ver 2.8, pregunta 9).

#### 4. Requerimientos no funcionales — FAIL

- **Issue (4.1)** · No hay NFR de rendimiento. specs/gcsgrep/02-spec.md:72-74: "Umbral de rendimiento — declinado en v1 con fundamento, diferido a la Iteración 3" (ADR-0012). 4.1 pide un NFR de rendimiento con métrica, número y condición, y declinarlo con fundamento no lo reemplaza.
- **Issue (4.1)** · specs/gcsgrep/02-spec.md:337-340 (NFR-1): "procesa cada objeto línea por línea usando streaming de lectura, sin cargar el contenido completo del objeto en memoria de una vez, y sin acumular los matches". El NFR no tiene número ni condición de carga. El umbral ("menor a 20 MB" sobre "200 MB") aparece solo en VC-14 (:342-343) y en la tabla (:439).
- **Warning (4.3)** · specs/gcsgrep/02-spec.md:353-356 (NFR-2) cubre dos condiciones: un error de red "al listar o leer". VC-15 (:358-360) ejercita solo "el listado inicial". El error de red durante la lectura de un objeto no tiene un VC propio de NFR-2.
- 4.2, 4.4, 4.5: sin hallazgos. 20 MB < 200 MB discrimina streaming de descarga completa. NFR-2 fija 0 reintentos y exit 2. No hay umbrales provisorios. La seguridad la cubre BR-1, y el costo, BR-2.

#### 5. Tecnología y fundamento — WARN

- **Warning (5.1)** · La spec nombra GCS y ADC (:51, :284-286), pero no dice qué permisos IAM mínimos necesita quien invoca (listar y leer objetos). Lo único que aparece es "permiso de listado", y como condición de falla (:247).
- **Warning (5.3)** · Falta el fundamento de la política de reintentos. specs/gcsgrep/02-spec.md:81 ("Reintentos automáticos ante fallos de red transitorios.", sin ADR, aunque el preámbulo de :58-59 dice que el fundamento "está en el ADR que se cita") y :355-356 ("No hay reintentos automáticos en v1"). El plan solo repite "Descartado en v1" (specs/gcsgrep/03-plan.md:269). Es una decisión de diseño que sostiene NFR-2, y no dice por qué. Las otras decisiones sí tienen fundamento: las 10 preguntas (ADR-0001…0010), las tres BRs, el streaming (01-base-context.md:57-66 y ADR-0011), la detección de binarios (ADR-0005) y la concurrencia (ADR-0009).
- **Warning (5.6)** · docs/adr/ADR-0013-frontera-de-excepciones.md:47-49: "con GCSGREP_DEBUG=1 la excepción se re-lanza con su traceback". Es un comportamiento observable (traceback en stderr y el exit code del intérprete) que la spec no menciona, y que contradice NFR-3 (:366, "Ningún caso de error imprime un stack trace de Python") y el exit 2 de VC-16 (b). Las otras decisiones de ADR/base context que no llegaron a la spec ya están registradas: orden de salida y credenciales ausentes (2.8), prefijo sin / (3.4).
- 5.2, 5.4, 5.5: sin hallazgos. La búsqueda literal no necesita sabor de regex. Los trade-offs están reconocidos: orden contra concurrencia (ADR-0009, ADR-0011), tope contra usabilidad (ADR-0006), heurística de binarios (ADR-0005), ADC contra key file (ADR-0002). --max 0 es una excepción explícita y no el default, y no hay escritura ni impersonación.

#### 6. Simplicidad — PASS

- **Suggestion (6.4)** · La regla "sin traceback" está escrita dos veces con palabras distintas: NFR-2 (:353-354, "se reporta por stderr sin traceback") y NFR-3 (:366, "Ningún caso de error imprime un stack trace de Python"). Conviene dejarla en NFR-3 y que NFR-2 la referencie.
- 6.1–6.3: sin hallazgos. La v1 no pasa de -i, -n y el guardrail. FR-11 se justifica por FR-g, y FR-12 es un camino de falla.

### Veredicto general

**NEEDS WORK**

Fallan dos dimensiones: la 2, por tres FRs no atómicos, y la 4, porque falta el NFR de rendimiento y NFR-1 no tiene umbral en su enunciado. Como la 3 no falla (cobertura completa, caminos de falla presentes, test escribible para FR-1 y FR-6), la spec es corregible sin reescribirla. Hay que partir los tres FRs, completar los NFRs y volver a revisar antes de planificar.

### Estado en la consigna

| VE | Issues | Warnings | Estado |
|---|---|---|---|
| VE-1 | 1 | 1 | Parcial |
| VE-2 | 2 | 6 | No se cumple |
| VE-3 | 0 | 6 | Parcial |

### Acciones (priorizadas)

1. [MUST] Partir FR-4 (specs/gcsgrep/02-spec.md:139-144) en dos FRs, formato con -n y formato sin -n; FR-6 (:159-165) en permiso denegado y error transitorio, o dejar una sola condición; y FR-12 (:244-251) en bucket inexistente y sin permiso de listado, cada uno con su VC.
2. [MUST] Agregar un NFR de rendimiento con métrica, número y condición de carga (por ejemplo, objetos/s en lectura secuencial con objetos de N MiB), con su VC, en la sección NFR (specs/gcsgrep/02-spec.md:333), en lugar de declinarlo en Fuera (:72-74).
3. [MUST] Llevar el umbral y la condición de VC-14 al enunciado de NFR-1 (specs/gcsgrep/02-spec.md:337-340): pico de memoria adicional < 20 MB leyendo un objeto de 200 MB.
4. [SHOULD] Agregar a FR-8 (specs/gcsgrep/02-spec.md:186-187) que el mensaje de stderr menciona el esquema esperado gs://, como ya exige VC-8.
5. [SHOULD] Decir en FR-1 (specs/gcsgrep/02-spec.md:106-110) que el patrón es un substring literal, y agregar un VC con un patrón que tenga metacaracteres (a.b).
6. [SHOULD] Agregar un FR o BR para "sin credenciales ADC → mensaje por stderr y exit 2", con su VC (hoy solo está en ADR-0002 y en 01-base-context.md:28).
7. [SHOULD] Fijar en un FR o NFR que los objetos se procesan y los matches se emiten en el orden del listado de GCS (hoy solo está en ADR-0009:15).
8. [SHOULD] Reemplazar en VC-9 (specs/gcsgrep/02-spec.md:201-203) "stderr menciona que un objeto fue salteado" por un observable concreto (nombre del objeto o texto literal) y el exit code esperado.
9. [SHOULD] Especificar que un prefijo sin / final es un prefijo de nombre (logs también matchea logs-other/) y agregar un VC (hoy solo está en ADR-0003:18-19).
10. [SHOULD] Definir el comportamiento con un objeto de 0 bytes (por ejemplo, texto sin líneas: no matchea y no es error) y agregar un VC.
11. [SHOULD] Definir que la última línea sin \n se busca igual que las demás y agregar un VC.
12. [SHOULD] Agregar a la spec un VC end-to-end declarado contra un bucket real (argumentos → listado → streaming → match → salida → exit code), no solo contra el doble.
13. [SHOULD] Agregar un VC para NFR-2 con un error de red durante la lectura de un objeto (exit 2, sin Traceback, el resto se procesa), además de VC-15 (specs/gcsgrep/02-spec.md:358-360).
14. [SHOULD] Nombrar en la spec los permisos IAM mínimos de quien invoca (listar y leer objetos del bucket, por ejemplo storage.objects.list y storage.objects.get).
15. [SHOULD] Fundamentar la ausencia de reintentos (specs/gcsgrep/02-spec.md:81 y :355-356) en un ADR, con las alternativas descartadas.
16. [SHOULD] Llevar a la spec el comportamiento de GCSGREP_DEBUG=1 (ADR-0013:47-49) como excepción explícita de NFR-3, o sacarlo del ADR.
17. [COULD] Fijar en FR-9 (specs/gcsgrep/02-spec.md:195-196) cuántos bytes iniciales se inspeccionan para detectar el \x00.
18. [COULD] Definir la codificación esperada de los objetos de texto y qué pasa con bytes que no la respetan (specs/gcsgrep/02-spec.md:50).
19. [COULD] Dejar la regla "sin traceback" solo en NFR-3 y que NFR-2 (specs/gcsgrep/02-spec.md:353-354) la referencie.

---

## Diseño en el base context · Grupo 4

Archivos revisados: specs/gcsgrep/01-base-context.md y docs/adr/ADR-0001 a ADR-0015 (la spec los enlaza como insumos en specs/gcsgrep/02-spec.md:9)

**Veredicto: tiene diseño.** Está repartido entre el base context y los ADRs.

### Qué hay

- §2 "Notas de diseño" (01-base-context.md:53) tiene título propio y cubre el streaming de punta a punta (con el bug de acumular matches que motivó ADR-0011) y la superficie de comandos.
- §1 (:19) es un índice de las 10 preguntas: pregunta, decisión y ADR. Agrega dos ítems del borrador que no estaban numerados (FR-g y NFR-a).
- Los ADRs tienen el análisis de diseño. Cada uno sigue la estructura Contexto / Decisión / Consecuencias / Alternativas descartadas con una tabla Alternativa | Por qué no (por ejemplo, ADR-0001 descarta re, POSIX y -E).
- La arquitectura (:78) incluye el contrato de los colaboradores (list_objects, open_text_stream), que justifica cómo se sustituye gcs en los tests.

### Qué se puede mejorar

- Quien lee solo el base context no ve los trade-offs. Mudar el fundamento a ADRs resuelve la duplicación (H-5), pero ahora hay que abrir 15 archivos para ver qué se descartó. Una línea por decisión en la tabla de §1, con la alternativa principal descartada, le devuelve contexto al documento sin volver a duplicar.
- "Esquema de arquitectura" es un subtítulo dentro de "Notas de diseño" (:78). Si lo suben a una sección propia (## 3 · Arquitectura), las facetas quedan separadas igual que requerimientos y diseño.

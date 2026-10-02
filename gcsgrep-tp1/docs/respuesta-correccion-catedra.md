# Respuesta a la corrección de la cátedra — gcsgrep, Iteración 1

> Respuesta a [`correccion-catedra-iteracion-1.md`](./correccion-catedra-iteracion-1.md)
> (veredicto **NEEDS WORK**, commit `10e6404`). La corrección se transcribió sin
> editar; este documento dice **qué se cambió por cada acción y dónde**. El
> resultado es la spec **v1.4** ([`02-spec.md`](../specs/gcsgrep/02-spec.md)).
>
> Todo lo de acá es documentación. **No se tocó código**: por
> [`proceso-cambios.md`](./proceso-cambios.md), la spec cambia primero y el código
> va en otra sesión. Lo que la v1.4 promete y el código todavía no cumple está
> asignado a la Iteración 2 en [`03-plan.md`](../specs/gcsgrep/03-plan.md), y su
> estado (⬜) está en [`04-cobertura-vc.md`](../specs/gcsgrep/04-cobertura-vc.md).

## Resumen

| | Antes (v1.3) | Después (v1.4) |
|---|---|---|
| FR / BR / NFR | 12 / 3 / 3 | 20 / 3 / 4 |
| VCs | 18 | 31 |
| FRs no atómicos | 3 (FR-4, FR-6, FR-12) | 0 |
| NFR de rendimiento | declinado (ADR-0012) | **NFR-4**, con métrica, número y condición (ADR-0017) |
| NFRs con número solo en el VC | NFR-1 | 0 |
| Decisiones con comportamiento observable que vivían solo en ADRs | 5 (literal, sin credenciales, orden, prefijo sin `/`, `GCSGREP_DEBUG`) | 0 |
| VC de punta a punta contra el sistema real | 0 en la spec | **VC-31** |
| ADRs | 15 | 18 (ADR-0016, ADR-0017, ADR-0018; ADR-0012 superseded) |
| Criterios del checklist de revisión | C-1…C-13 | C-1…C-18 |

**Criterio general.** Los IDs existentes se conservaron (los tests se nombran por
VC: renumerar rompería la trazabilidad con el código). Lo que se partió conservó
el ID para la mitad que ya existía y tomó uno nuevo para la otra.

## Las 19 acciones

### MUST

| # | Acción de la cátedra | Cómo se resolvió | Dónde |
|---|---|---|---|
| 1a | Partir **FR-4** en formato con `-n` y sin `-n` | **FR-3** pasa a ser el formato con `-n` (`gs://b/o:<k>:<texto>`), absorbiendo la mitad de FR-4, y **FR-4** queda en el formato sin `-n`. Se eligió fusionar con FR-3 en vez de crear un FR nuevo porque FR-3 ("incluye el número de línea") y el FR "formato con `-n`" habrían dicho lo mismo dos veces (6.4). VC-3 y VC-4 ahora fijan stdout **exacto**, y VC-4 pierde el "separa correctamente" (hit de M4) | spec FR-3, FR-4, VC-3, VC-4 |
| 1b | Partir **FR-6** (permiso denegado / error transitorio) | **FR-6** queda en *permiso denegado al abrir*; la red que se corta a mitad de lectura es **FR-13** (+VC-21). Cada uno con su texto literal en stderr (`sin permiso para leer` / `error de red al leer` + URI) | spec FR-6, FR-13, VC-6, VC-21 |
| 1c | Partir **FR-12** (no existe / sin permiso de listado) | **FR-12** queda en *bucket inexistente* (VC-18); *sin permiso de listado* es **FR-14** (+VC-22). El "distingue X de Y" desaparece del Entonces: cada FR fija su propio mensaje, y VC-22 exige que el de permisos **no** diga `no existe` | spec FR-12, FR-14, VC-18, VC-22 |
| 2 | Agregar un **NFR de rendimiento** con métrica, número y condición | **NFR-4**: objeto de 100 MiB, líneas de 80 bytes, de punta a punta con stdout a `/dev/null`, contenido servido desde memoria. (a) patrón ausente ≥ 50 MiB/s; (b) patrón en todas las líneas ≥ 50 000 matches/s. VC-30. Se **midió antes de fijar el número**: ~396 MiB/s y ~355 000 matches/s hoy, y una implementación que lee de a un carácter da ~15 MiB/s y falla (a). Esa medición es la que invalida el argumento de ADR-0012 ("contra el doble pasa siempre"), y por eso **ADR-0017 supersede a ADR-0012** en vez de editarlo. Se eliminó "Umbral de rendimiento" de *Fuera* | spec NFR-4, VC-30; [ADR-0017](./adr/ADR-0017-nfr-rendimiento-costo-propio.md); ADR-0012 → superseded |
| 3 | Llevar el umbral de VC-14 al enunciado de **NFR-1** | NFR-1 ahora dice **Métrica** (pico de memoria adicional), **Umbral** (< 20 MB) y **Condición de carga** (objeto de 200 MB, sin matches y con todas las líneas matcheando) en el enunciado. VC-14 lo verifica en las dos condiciones | spec NFR-1 |

### SHOULD

| # | Acción de la cátedra | Cómo se resolvió | Dónde |
|---|---|---|---|
| 4 | FR-8 debe decir que el mensaje nombra `gs://` | El Entonces de FR-8 dice "un mensaje por stderr que contiene el esquema esperado, `gs://`". VC-8 ya no agrega comportamiento (2.7), y además pide 0 llamadas de listado | spec FR-8, VC-8 |
| 5 | FR-1: el patrón es substring literal, + VC con metacaracteres | FR-1 dice "substring literal (ningún carácter del patrón tiene significado especial: `.`, `*`, `[`, `\`…)". **VC-19**: `a.b` no matchea `axb`; `a*b` matchea solo `a*b` | spec FR-1, VC-19 |
| 6 | FR o BR para "sin credenciales ADC → stderr + exit 2" | **FR-15** + **VC-23**: mensaje con `no se encontraron credenciales` y `gcloud auth application-default login`, exit `2`, 0 lecturas. Se agregó el actor **Entorno de credenciales** y su fila en la tabla actores → requerimiento. Hoy el caso sale con `2` por el caso genérico de ADR-0013, con otro mensaje: el mensaje específico es Iteración 2 | spec FR-15, VC-23, Actores |
| 7 | Fijar el orden de la salida | **FR-16** + **VC-24**: objetos en el orden del listado de GCS (lexicográfico por nombre en bytes UTF-8), matches de un objeto en orden de línea, todos antes que los del siguiente. VC-24 siembra en orden desordenado y exige 6 líneas en orden exacto | spec FR-16, VC-24 |
| 8 | VC-9 con observable concreto y exit code | FR-9 fija la línea literal `gcsgrep: salteado (binario): gs://<bucket>/<objeto>` y que el salteo no afecta el exit code. VC-9 exige stdout exacto, esa línea exacta, exit `0` (y `1` sin el objeto de texto). Lo mismo para `.gz` en FR-10/VC-10 (`gcsgrep: salteado (.gz): …`, 0 aperturas) | spec FR-9, FR-10, VC-9, VC-10 |
| 9 | Prefijo sin `/` final = prefijo de nombre, + VC | **FR-18** + **VC-26**: `gs://b/logs` busca en `logs/a.txt` **y** `logs-other/b.txt`; con `gs://b/logs/`, solo en `logs/`. VC-26 fija el orden (`logs-other/` antes que `logs/`, porque `-` < `/`), que es una consecuencia de FR-16 que nadie había mirado | spec FR-18, VC-26 |
| 10 | Objeto de 0 bytes | **FR-19** + **VC-27**: texto sin líneas, sin match, sin salteo, sin error, stderr vacío | spec FR-19, VC-27 |
| 11 | Última línea sin `\n` | **FR-20** + **VC-28**: `uno\ndos` con `-n "dos"` → exactamente `gs://b/p/a.txt:2:dos` | spec FR-20, VC-28 |
| 12 | VC de punta a punta contra un bucket real | **VC-31**, en una sección propia de la spec: GCS real, ADC real, una identidad con exactamente `roles/storage.objectViewer`, tres comandos con stdout/exit exactos; "no acepta un doble ni un emulador como evidencia". Su **ejecución** sigue sujeta a [ADR-0015](./adr/ADR-0015-verificacion-real-declinada.md) (no hay cuenta con billing): el VC está especificado, su estado es ⬜, y el runbook dice que correrlo con el backend `gcs` **es** ejecutar VC-31 | spec VC-31; [`integracion-gcs.md`](./integracion-gcs.md); cobertura |
| 13 | VC para NFR-2 con error de red al leer | NFR-2 se reescribió como **política** (0 reintentos) con dos condiciones explícitas, cada una con su VC: (a) al listar → **VC-15** (ahora también: el listado se invocó 1 vez); (b) al leer → **VC-29** (cada objeto se abrió exactamente 1 vez). El comportamiento "informa y sigue" de la lectura vive en FR-13/VC-21, no se duplica en el NFR | spec NFR-2, VC-15, VC-29 |
| 14 | Nombrar los permisos IAM mínimos | Sección nueva **Tecnología y permisos mínimos**: `storage.objects.list` (listar) y `storage.objects.get` (leer); rol mínimo `roles/storage.objectViewer`; ningún otro permiso. BR-1 lo referencia, y dice qué pasa si falta cada uno (FR-6 / FR-14) | spec *Tecnología y permisos mínimos*, BR-1 |
| 15 | Fundamentar la ausencia de reintentos en un ADR | **ADR-0016**: 0 reintentos, con cuatro razones (el exit `2` ya delega el reintento al script; reabrir un objeto **duplica matches ya emitidos** por la salida incremental; costo sin tope; no hay un número medido que defender) y cuatro alternativas descartadas. *Fuera* y el plan ahora lo citan | [ADR-0016](./adr/ADR-0016-sin-reintentos.md); spec *Fuera*, NFR-2; plan |
| 16 | `GCSGREP_DEBUG=1`: llevarlo a la spec o sacarlo del ADR | Se **lleva a la spec** como excepción explícita de NFR-3: opt-in, no default, solo para excepciones **no previstas**; los errores previstos siguen sin traceback aunque la variable esté definida. **VC-16 (c)** verifica las dos mitades. Se descartó sacarlo del ADR porque es la única forma de diagnosticar un bug nuevo, y ADR-0013 ya justifica por qué | spec NFR-3, VC-16 (c) |

### COULD

| # | Acción de la cátedra | Cómo se resolvió | Dónde |
|---|---|---|---|
| 17 | Cuántos bytes se inspeccionan para `\x00` | **8192 bytes** (offsets `0`–`8191`). **VC-20** prueba el límite exacto: offset 8191 → binario, offset 8192 → texto. **ADR-0018** lo fundamenta y *precisa* ADR-0005 sin supersederlo (la decisión de saltear por byte nulo no cambió) | spec FR-9, VC-20; [ADR-0018](./adr/ADR-0018-ventana-binaria-y-codificacion.md) |
| 18 | Codificación esperada y bytes inválidos | **FR-17** + **VC-25**: UTF-8 fijo (no el locale), cada secuencia inválida se reemplaza por `U+FFFD`, la línea se busca igual, no es salteo ni error. Al analizarlo apareció que **hoy un objeto en Latin-1 aborta la corrida entera** (`UnicodeDecodeError` → caso genérico → exit `2`): queda dicho en ADR-0018 y es Iteración 2 | spec FR-17, VC-25; ADR-0018 |
| 19 | Regla "sin traceback" solo en NFR-3 | NFR-3 la declara como "la única formulación de la regla en la spec"; NFR-2 y los FRs la referencian ("según NFR-3") en vez de repetirla | spec NFR-2, NFR-3 |

## Diseño en el base context

| Sugerencia | Cómo se resolvió | Dónde |
|---|---|---|
| Quien lee solo el base context no ve los trade-offs | La tabla de §1 tiene dos columnas nuevas: **Alternativa principal descartada, y por qué** (una línea por decisión, tomada del ADR) y **Requerimiento** (dónde aterrizó la decisión en la spec). El análisis completo sigue en el ADR, así que no vuelve la duplicación de H-5 | [`01-base-context.md`](../specs/gcsgrep/01-base-context.md) §1 |
| "Esquema de arquitectura" como sección propia | Ahora es **§3 · Arquitectura**, con *Esquema* y *Contrato de los colaboradores* como subsecciones. El esquema se actualizó (faltaba `errors` y el rol de `cli` como frontera de excepciones), y se agregó una nota: FR-9/FR-17 van a obligar a cambiar el contrato de `open_text_stream` en la Iteración 2 | `01-base-context.md` §3 |

## Hallazgos que la cátedra no marcó, y aparecieron al responder

- **[H-15](./hallazgos/H-15-cobertura-desincronizada.md) · la tabla de cobertura
  contradecía su propio resumen desde la entrega.** El resumen decía 14 VCs ✅; la
  tabla tenía VC-16 (b) y VC-18 en ⬜ "sin ejercitador" (con tests pasando), no
  tenía filas para VC-11 ni VC-12, y la tabla de integración decía *pendiente*
  bajo un encabezado que decía "ejecutada". Se corrigió moviendo lo superado al
  *Histórico*, y queda como tarea un chequeo en CI que compare la tabla con los
  tests.
- **NFR-4 encontró un costo que nadie había acotado.** Con todas las líneas
  matcheando, la tasa cae ~15× por el `flush` por match de la salida incremental
  (ADR-0011). El umbral (b) de NFR-4 existe por eso.
- **FR-17 encontró un defecto latente** (Latin-1 aborta la corrida), registrado en
  ADR-0018 y asignado a la Iteración 2.

## Chequeos mecánicos sobre la v1.4

Con los mismos comandos de la rúbrica:

- **M1:** FR 20 · BR 3 · NFR 4 · VC 31. VCs (31) ≥ FR+BR (23).
- **M3:** sin valores sin decidir. Los hits son "todo" en castellano y la palabra
  "pendiente" en una fila histórica del *Historial de revisiones* (v1.1).
- **M4:** un hit, `correctamente` en la prosa del historial de la v1.2, fuera de
  cualquier FR/NFR/VC. El de VC-4 se eliminó.
- **M6:** `todos los` en FR-7, FR-16 y FR-18, y `nunca` en BR-1: cada uno con su VC
  (VC-7, VC-24, VC-26, VC-11).

## Qué no se hizo, y por qué

- **No se ejecutó VC-31.** Hace falta una cuenta de GCP con billing; ADR-0015 sigue
  vigente. Si el equipo la consigue, se corre el runbook con el backend `gcs` y se
  supersede ADR-0015.
- **No se tocó código ni tests.** Los VCs nuevos que el código ya debería cumplir
  se ejercitan en el **Paso 0 de la Iteración 2**, antes de cualquier código nuevo
  ([`03-plan.md`](../specs/gcsgrep/03-plan.md)). Si alguno falla, es un defecto de la
  Iteración 1 y va por la fila 1 de [`proceso-cambios.md`](./proceso-cambios.md).
- **No se renumeraron requerimientos ni VCs**, para no romper el vínculo con los
  nombres de los tests.

## Errata (revisión v1.4)

> Agregada el 2026-10-01, después de la
> [revisión adversarial de la spec v1.4](../revisiones/spec-v1.4-2026-10-01.md)
> (NEEDS WORK). Lo de arriba no se reescribe: es la respuesta tal como se entregó.
> Esta sección corrige lo que resultó falso, y la corrección vive en la spec **v1.5**.

**1. La fila "Decisiones con comportamiento observable que vivían solo en ADRs: 0"
del *Resumen* es falsa.** Después de la v1.4 quedaban al menos seis, cada una con
comportamiento en stdout, stderr o el exit code y sin requerimiento:

| Decisión | Dónde vivía | Dónde vive desde la v1.5 |
|---|---|---|
| Un objeto borrado entre el listado y la lectura no aborta la corrida | ADR-0010, ADR-0013 (que decían "lo cubre FR-6", ya no cierto desde la v1.4) | **FR-21**, VC-32 |
| Los salteados se informan por stderr (ADR-0005 decía "en un resumen final") | ADR-0005 | **FR-9/FR-10**: una línea por objeto, en el momento del salteo, sin resumen final (la spec se aparta del detalle de ADR-0005; registrado en `docs/adr/README.md`) |
| Un `\x00` después de la ventana sale por stdout si está en una línea con match | ADR-0018 | **FR-9** (límite explícito), VC-20 |
| Los flags no soportados se rechazan | ADR-0004 (alternativa descartada: "aceptarlos e ignorarlos") | **FR-25**, VC-37…VC-40 |
| `gcsgrep … \| head` corta "como `grep`" | ADR-0011 | **FR-23**, VC-35, [ADR-0019](./adr/ADR-0019-corte-de-stdout-sigpipe.md) |
| La red caída **al abrir** un objeto no aborta la corrida | ADR-0016 ("la apertura y lectura de cada objeto" se intentan una vez) | **FR-13** (al abrir o durante la lectura), VC-33 |

El valor correcto de esa fila para la v1.4 es **≥ 6**, no 0; para la v1.5, las seis
están en un requerimiento. El chequeo que se había hecho (C-15) recorrió las
decisiones de los ADRs **como estaban enunciadas en su sección *Decisión***, y estas
seis estaban en *Consecuencias*, en *Alternativas descartadas* o en una cláusula
lateral. La próxima pasada de C-15 recorre el ADR entero.

**2. La acción 1b ("Partir FR-6") no quedó resuelta como dice la tabla de MUST.**
Se partió, pero FR-13 repitió en su Dado la forma que la cátedra marcó (tres causas
alternativas), y el corte dejó sin requerimiento al objeto que falla al abrirse por
`404` o por red. Es [H-16](./hallazgos/H-16-objeto-que-falla-al-abrir.md), con el mismo
mecanismo que H-13, y produjo el criterio C-19 del checklist.

**3. La acción 13 ("VC para NFR-2 con error de red al leer") quedó parcial.** NFR-2 (b)
remitía a FR-13, que no cubría la red al abrir. Desde la v1.5, NFR-2 (b) dice "al
abrir o leer" y VC-33 cubre la apertura.

**4. M1 de la sección *Chequeos mecánicos* describe la v1.4.** Para la v1.5: FR 27 ·
BR 3 · NFR 4 · VC 44, y VCs (44) ≥ FR+BR (30).

El detalle de las 21 acciones de la revisión, con qué cambió y dónde, está en la fila
v1.5 del *Historial de revisiones* de la spec.

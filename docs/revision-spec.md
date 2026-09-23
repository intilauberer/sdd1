# Revisión de la spec de `gcsgrep`

> Artefacto del paso **Revisar** del pipeline
> (Especificar → **Revisar** → Planificar → Implementar → Verificar).
>
> Hasta esta revisión, `02-spec.md` decía "Estado: revisada" sin ningún registro
> que respaldara la afirmación: no había checklist, ni hallazgos, ni constancia
> de qué cambió como consecuencia. Una spec cuya tesis es *"si una línea no se
> puede verificar, no está especificada"* no puede declararse revisada de forma
> inverificable. Este documento es lo que faltaba.

| | |
|---|---|
| **Objeto de la revisión** | `specs/gcsgrep/02-spec.md` v1.0 |
| **Insumos** | `00-requirements-draft.md`, `01-base-context.md`, `03-plan.md`, `04-cobertura-vc.md`, código de la Iteración 1, `enunciado.md` |
| **Fecha** | 2026-09-23 |
| **Resultado** | **Habilitada con cambios** → la spec pasa a v1.1 |
| **Bloqueante pendiente** | H-9 (verificación de integración nunca ejecutada) |

## Checklist aplicado

Cada ítem es una pregunta con respuesta binaria. Se revisa contra el documento,
no contra la intención de quien lo escribió.

| # | Criterio | Resultado |
|---|---|---|
| C-1 | ¿Cada FR está en forma Dado/Cuando/Entonces y describe un solo comportamiento? | ✅ |
| C-2 | ¿Cada FR y cada BR tiene exactamente un VC? | ✅ 16/16 |
| C-3 | ¿Cada VC es observable (exit code, contenido de stdout/stderr, magnitud medida) y no una opinión? | ✅ |
| C-4 | ¿Cada NFR tiene métrica, umbral numérico y condición de carga? | ✅ para los tres NFRs presentes — pero ver **H-2** |
| C-5 | ¿Cada BR tiene fundamento y excepciones declaradas? | ✅ |
| C-6 | **¿Cada ítem del borrador terminó como FR/BR/NFR, en "Fuera", o diferido en el plan?** | ❌ → **H-1**, **H-2** |
| C-7 | ¿El alcance diferido vive en el plan y no en la spec? | ✅ |
| C-8 | ¿Cada VC puede fallar por la razón correcta? | ❌ → **H-3** |
| C-9 | ¿Cada hecho está afirmado en un solo documento? | ❌ → **H-4**, **H-5** |
| C-10 | ¿El documento tiene versión, estado, fecha y responsable de la revisión? | ❌ → **H-8** |
| C-11 | ¿El código implementado no contradice la spec? | ❌ → **H-3**, **H-6** |
| C-12 | ¿Los criterios de entrega del enunciado están todos cumplidos? | ❌ → **H-9** |

C-6 es el criterio que no existía antes de esta revisión. La spec verificaba la
dirección *spec → VC* ("0 huérfanos") pero nunca la dirección *borrador → spec*.
Los dos hallazgos más importantes salieron de ahí.

## Hallazgos

### H-1 · FR-g del borrador desapareció sin decisión — **crítico**

El borrador pedía, como FR-g, que se pueda notar el progreso cuando hay muchos
objetos "porque si no parece colgado". En `02-spec.md` v1.0 no aparece: ni como
FR, ni en la lista de "Fuera", ni en la tabla de alcance rechazado del plan.
No fue rechazado: se perdió.

Agravante: el código de la Iteración 1 lo hacía imposible de cumplir sin
rediseño. `core.search` devolvía `List[Match]` y `cli` imprimía recién al
terminar, así que una corrida sobre 1000 objetos no muestra nada hasta el final
— literalmente el síntoma que FR-g describe.

**Resolución:** [ADR-0011](./adr/ADR-0011-salida-incremental.md). Se agrega
**FR-11** (salida incremental) con **VC-17**, y `core.search` pasa a ser
generador. FR-g queda satisfecho por el mecanismo más barato posible: el
progreso es la salida apareciendo.

### H-2 · NFR-a del borrador quedó en `_pendiente_` — **crítico**

El borrador dejaba tres NFRs vacíos. NFR-b → NFR-1 (memoria) y NFR-c → NFR-2
(red) se completaron con umbrales reales. **NFR-a (rendimiento) nunca se
resolvió.** Las 10 preguntas abiertas se atacaron una por una; los NFRs en
blanco no estaban en esa lista, y nadie los volvió a mirar.

`01-base-context.md` §9 (lectura secuencial) roza el tema pero no fija ningún
presupuesto de rendimiento.

**Resolución:** [ADR-0012](./adr/ADR-0012-nfr-rendimiento-diferido.md). Se
**declina explícitamente** con fundamento (un umbral en v1 mediría la red o el
intérprete de Python, no la herramienta) y se difiere a la Iteración 3, donde el
número es comparativo contra la línea de base secuencial y por lo tanto
significativo. Queda registrado en la tabla de trazabilidad como declinado, no
como pendiente.

### H-3 · VC-14 pasa sin ejercitar el caso que NFR-1 promete — **crítico**

`test_memory.py` medía el pico de memoria con
`pattern="patron-que-nunca-aparece"` y afirmaba `matches == []`. Con cero
matches, el `List[Match]` que `search` acumulaba quedaba vacío, así que el VC
pasaba por construcción.

Sobre un objeto real de 200 MB donde la mayoría de las líneas matchean, la
memoria crecía proporcionalmente a la cantidad de matches. La letra de NFR-1
("sin cargar el contenido completo del objeto en memoria") se cumplía; la
propiedad que le importa a quien usa la herramienta, no.

Es el modo de falla clásico: **un VC escrito contra el camino felíz de la
implementación en vez de contra el caso adverso.**

**Resolución:** se refuerza VC-14 con un segundo caso donde **todas** las líneas
matchean, y se arregla la causa con el generador de ADR-0011. El umbral de
20 MB no cambia.

### H-4 · Dos fuentes de verdad para el estado de los VCs — **mayor**

`03-plan.md` listaba `- [ ] VC-1 pasa … - [ ] VC-16 pasa` sin tildar, mientras
`04-cobertura-vc.md` marcaba los mismos nueve VCs como ✅. Ambos archivos
entraron en el mismo commit, ya desincronizados.

**Resolución:** el plan declara **qué VCs entran en cada iteración**; el estado
vive **solo** en la tabla de cobertura. Se eliminan los checkboxes del plan.

### H-5 · Fundamento duplicado entre base context y spec — **menor**

El "por qué" de cada decisión estaba en `01-base-context.md` §1 y parafraseado
en la spec ("cada uno de estos es una decisión tomada"), el plan y los
docstrings del código. Cuatro lugares donde puede divergir.

**Resolución:** el fundamento se muda a `docs/adr/`, con identificador estable.
El base context conserva una tabla índice y las notas de diseño; la spec y el
plan referencian `ADR-XXXX` en vez de reexplicar.

### H-6 · Alias de tipo incorrecto en `core.py` — **menor**

`OpenTextStream = Callable[[str, str], "Iterable[str]"]`, pero el valor se usa
como context manager (`with open_text_stream(...) as stream`). El alias declara
un contrato que los colaboradores no tienen que cumplir y omite el que sí.

**Resolución:** se corrige el alias a un `ContextManager[Iterable[str]]` y se
documenta el contrato del colaborador en el docstring.

### H-7 · Faltaba el invariante de trazabilidad hacia atrás — **mayor**

Consecuencia estructural de H-1 y H-2: la spec garantizaba "cada FR tiene un VC"
pero nada garantizaba "cada ítem del borrador terminó en algún lado".

**Resolución:** se agrega a `02-spec.md` una **tabla de trazabilidad
borrador → spec** con una fila por cada FR-a…FR-g, BR-a…BR-d y NFR-a…NFR-c del
borrador, y C-6 pasa a ser parte del checklist de revisión permanente.

### H-8 · La spec no estaba versionada — **mayor**

Decía `Estado: revisada` sin versión, fecha, responsable ni historial. Con
BR-3 a punto de cambiar en la Iteración 2 el exit code de corridas que la
Iteración 1 ya podía producir, un cambio en el lugar sin registro habría
borrado la evidencia de que el contrato cambió.

**Resolución:** encabezado con `versión`, `estado`, `fecha`, `revisada-por`, y
sección `Historial de revisiones` al final.

### H-9 · La verificación de integración nunca se ejecutó — **bloqueante de entrega**

`04-cobertura-vc.md` lo declara con honestidad, y eso está bien. Pero el
enunciado exige que el código de la Iteración 1 "corra una búsqueda real y sus
chequeos de verificación pasen". Contra el doble de prueba pasa; contra GCS
real no se probó nunca.

**Resolución parcial:** se agrega
[`docs/integracion-gcs.md`](./integracion-gcs.md) (runbook reproducible del
campo de pruebas), `scripts/testing-ground.sh` (crea, siembra y destruye el
bucket) y un workflow de CI manual (`integration.yml`). **La corrida sigue
pendiente y sigue siendo bloqueante**: el runbook la hace fácil y reproducible,
no la reemplaza.

### H-10 · El doble de prueba expone un método de escritura — **menor, para Iteración 2**

VC-11 promete "un test que falla si el doble de prueba recibe una llamada a un
método que no sea de lectura", pero `tests/fakes.py::FakeGCS` expone `put()`.
Cuando se implemente VC-11 hay que separar la siembra del doble (setup) de su
superficie observable por `core`, o el test no puede distinguir una escritura
legítima del test de una escritura del código bajo prueba.

**Resolución:** anotado como precondición de VC-11 en la Iteración 2. No se
toca ahora.

## Resumen de cambios habilitados por esta revisión

| Hallazgo | Cambio | Artefacto |
|---|---|---|
| H-1 | FR-11 + VC-17 + generador | spec, plan, cobertura, `core.py`, `cli.py`, ADR-0011 |
| H-2 | NFR-a declinado con fundamento | spec, plan, ADR-0012 |
| H-3 | VC-14 con caso adverso | `test_memory.py`, cobertura |
| H-4 | Checkboxes fuera del plan | plan |
| H-5 | Fundamento a ADRs | `docs/adr/`, base context, spec |
| H-6 | Alias de tipo corregido | `core.py` |
| H-7 | Tabla borrador → spec | spec, este checklist (C-6) |
| H-8 | Versionado de la spec | spec |
| H-9 | Runbook + CI de integración | `docs/integracion-gcs.md`, `scripts/`, `.github/workflows/` |
| H-10 | Precondición registrada | plan (Iteración 2) |

## Veredicto

**La spec queda habilitada en v1.1** para continuar con la Iteración 2, con una
excepción explícita: **H-9 sigue abierto**. La Iteración 1 está verificada
contra dobles de prueba y **no** contra GCS real, así que no cumple todavía el
criterio de entrega del enunciado. Ejecutar el runbook de integración es el
próximo paso obligatorio, antes de escribir código de la Iteración 2.

## Cómo repetir esta revisión

El checklist de arriba (C-1 … C-12) es reusable tal cual para la spec de la
Iteración 2. Dos reglas aprendidas acá:

1. **Revisar en las dos direcciones.** Que no haya VCs huérfanos no implica que
   no haya requerimientos huérfanos.
2. **Para cada VC, preguntar cómo lo harías fallar.** Si no hay respuesta, el VC
   está midiendo la implementación en vez del requerimiento (H-3).

# gcsgrep

`grep` sobre el contenido de objetos de Google Cloud Storage, **sin bajarlos
primero**.

```bash
gcsgrep "timeout" gs://mi-bucket/logs/
gs://mi-bucket/logs/a.txt:connection timeout after 30s
```

Buscar un texto dentro de objetos de un bucket normalmente implica bajarlos con
`gsutil cp` y después correr `grep`: lento, gasta ancho de banda y llena el disco
de archivos que nadie quiere. `gcsgrep` lee cada objeto por streaming, línea por
línea, y emite los matches a medida que aparecen.

Es **solo lectura, siempre**: no escribe, no borra, no cambia permisos, y nunca
usa credenciales distintas de las de quien la invoca.

> **Estado: Iteración 1 completa, 12/12 VCs pasando contra dobles de prueba.** La
> verificación de integración se puede correr sin cuenta paga
> ([ADR-0014](./docs/adr/ADR-0014-emulacion-local-floci.md)) y **todavía no se
> ejecutó** — ver [Estado](#estado) más abajo.

## Este repo es un ejercicio de SDD

Lo que se entrega no es solo el código: es el rastro del pipeline
**Especificar → Revisar → Planificar → Implementar → Verificar** aplicado a una
idea deliberadamente vaga. El código de `gcsgrep/` son 4 archivos y ~150 líneas;
el valor está en poder auditar cómo se llegó a ellos.

Si venís a leer y no a usar la herramienta, **leé en este orden**:

| # | Artefacto | Qué es | Mutabilidad |
|---|---|---|---|
| 0 | [`enunciado.md`](./enunciado.md) | La consigna, tal como se recibió | externa |
| 1 | [`specs/gcsgrep/00-requirements-draft.md`](./specs/gcsgrep/00-requirements-draft.md) | El borrador vago del que se partió | **congelado**, nunca se edita |
| 2 | [`specs/gcsgrep/01-base-context.md`](./specs/gcsgrep/01-base-context.md) | Índice de decisiones + notas de diseño | se actualiza |
| 3 | [`docs/adr/`](./docs/adr/) | 14 decisiones, una por archivo, con su fundamento | **inmutables**; se supersede, no se edita |
| 4 | [`specs/gcsgrep/02-spec.md`](./specs/gcsgrep/02-spec.md) | El contrato: 18 requerimientos, 18 VCs | **versionada** (v1.2), con historial |
| 5 | [`docs/revision-spec.md`](./docs/revision-spec.md) | La revisión que habilitó la spec: checklist y los primeros 10 hallazgos | por revisión |
| 6 | [`docs/hallazgos/`](./docs/hallazgos/) | Lo que se descubrió *después*: un archivo por hallazgo | **inmutables**, como los ADRs |
| 7 | [`docs/proceso-cambios.md`](./docs/proceso-cambios.md) | Qué artefacto cambia según lo que aparezca. El carril de entrada del harness | se actualiza |
| 8 | [`specs/gcsgrep/03-plan.md`](./specs/gcsgrep/03-plan.md) | 3 iteraciones; el alcance diferido vive acá, no en la spec | se actualiza |
| 9 | [`specs/gcsgrep/04-cobertura-vc.md`](./specs/gcsgrep/04-cobertura-vc.md) | Qué VC pasa, con qué se ejercita y qué se observó | **append-only** por iteración |
| 10 | [`docs/integracion-gcs.md`](./docs/integracion-gcs.md) | Runbook de la verificación contra GCS real | se actualiza |

Las cuatro reglas de mutabilidad de la tabla son la parte que hace que esto
funcione a lo largo del tiempo. Un borrador que se edita borra la evidencia de
qué se pidió; una spec que se edita en silencio borra la evidencia de qué se
prometió; un ADR que se edita borra la evidencia de por qué; una tabla de
cobertura que se reescribe borra la evidencia de qué se verificó y cuándo.

Ese pipeline es de ida: va de un borrador a código verificado. Para lo que
aparece **después** —una excepción mientras se prueba, un reporte de un
compañero— el carril de entrada es
[`proceso-cambios.md`](./docs/proceso-cambios.md), y lo que se descubre queda en
[`hallazgos/`](./docs/hallazgos/).

### Equivalencia con los nombres viejos

El enunciado y los commits anteriores a la reorganización usan nombres planos en
la raíz:

| Antes | Ahora |
|---|---|
| `gcsgrep-requirements.md` | `specs/gcsgrep/00-requirements-draft.md` |
| `gcsgrep-base-context.md` | `specs/gcsgrep/01-base-context.md` |
| `gcsgrep-spec.md` | `specs/gcsgrep/02-spec.md` |
| `gcsgrep-plan.md` | `specs/gcsgrep/03-plan.md` |
| `gcsgrep-cobertura-vc.md` | `specs/gcsgrep/04-cobertura-vc.md` |

Un prefijo compartido en la raíz funciona con una feature y se rompe con dos. Un
directorio por feature, con los archivos numerados por etapa del pipeline, hace
que la segunda feature no cueste nada.

## Instalación

Requiere Python ≥ 3.9 y credenciales de GCP resueltas por
[ADC](./docs/adr/ADR-0002-autenticacion-adc.md).

El proyecto se desarrolla con [`uv`](https://docs.astral.sh/uv/), que gestiona el
entorno virtual y las dependencias a partir de `pyproject.toml`:

```bash
git clone <este-repo> && cd sdd1
uv sync --extra dev

# Autenticación: gcsgrep usa lo que tu entorno ya tenga configurado.
gcloud auth application-default login
```

`uv run` ejecuta cualquier comando dentro del entorno del proyecto, sin activarlo
manualmente:

```bash
uv run gcsgrep "timeout" gs://mi-bucket/logs/
```

`pyproject.toml` es la única fuente de verdad de las dependencias, de modo que
`pip` es un camino equivalente y es el que utiliza la
[integración continua](./.github/workflows/tests.yml):

```bash
python -m pip install -e '.[dev]'
```

## Uso

```
gcsgrep [-i] [-n] <patrón> gs://bucket/prefijo
```

| Flag | Qué hace |
|---|---|
| `-i` | Búsqueda sin distinguir mayúsculas |
| `-n` | Agrega el número de línea a cada match |

Ante un error, `gcsgrep` nunca imprime un traceback: sale con `2` y un mensaje
legible por stderr ([ADR-0013](./docs/adr/ADR-0013-frontera-de-excepciones.md)).
Para diagnosticar un fallo inesperado, `GCSGREP_DEBUG=1` re-expone la excepción
original.

El patrón es **texto literal**, no una regex
([ADR-0001](./docs/adr/ADR-0001-busqueda-literal.md)). `gs://bucket` sin prefijo
busca en todo el bucket.

**Exit codes**, con la convención de `grep`
([ADR-0008](./docs/adr/ADR-0008-exit-codes.md)):

| Código | Significado |
|---|---|
| `0` | Hubo al menos un match |
| `1` | Corrió bien, sin matches |
| `2` | Error: credenciales, permisos, red, o argumentos inválidos |

```bash
# Como predicado en un script: stdout son solo matches, todo lo demás va a stderr
if gcsgrep "timeout" gs://logs/2026-09/ >/dev/null; then
    echo "hay timeouts"
fi
```

### Lo que todavía no hace

Cada una de estas es una decisión registrada, no un olvido — el fundamento está
en el ADR correspondiente:

- Regex ([ADR-0001](./docs/adr/ADR-0001-busqueda-literal.md))
- Flags más allá de `-i` y `-n` ([ADR-0004](./docs/adr/ADR-0004-flags-v1.md))
- Leer `.gz` o binarios: se saltean ([ADR-0005](./docs/adr/ADR-0005-binarios-y-gz.md))
- Salida JSON o con colores ([ADR-0007](./docs/adr/ADR-0007-formato-de-salida.md))
- Lectura concurrente ([ADR-0009](./docs/adr/ADR-0009-lectura-secuencial.md))
- S3 o Azure Blob

Además, el guardrail de costo (`--max`) y el manejo de objetos ilegibles son
alcance de la **Iteración 2**: todavía no están implementados. Un objeto que falla
al leerse **aborta** la corrida con exit `2` en vez de saltearse (FR-6), y no hay
mensajes específicos para fallos de red (NFR-2).

## Arquitectura

```
cli    → parsea argv, imprime cada match, traduce el resultado a exit code,
         y es la frontera de excepciones del proceso
core   → orquesta la búsqueda: matchea líneas y emite matches (generador)
gcs    → única capa que habla con la API de GCS: listar objetos, abrir streams,
         y traducir las excepciones del SDK a errores de dominio
errors → los errores de dominio, para que cli no tenga que importar el SDK
```

La dependencia va en una sola dirección: `cli → core → gcs`. `core` **no** importa
`google.cloud.storage`: recibe el listado y la apertura de streams como
colaboradores. Por eso toda la lógica se testea sin credenciales ni red, y por eso
`gcs` es el único lugar donde hay que mirar para verificar que la herramienta es
de solo lectura (BR-1).

`core.search` es un generador: emite cada match en cuanto lo encuentra, sin
acumular ([ADR-0011](./docs/adr/ADR-0011-salida-incremental.md)). Eso es lo que
mantiene la memoria acotada sobre objetos grandes y lo que hace que la salida
aparezca mientras la búsqueda avanza.

El manejo de errores sigue la misma dirección: `gcs` traduce las excepciones de
`google.api_core` a los errores de `errors.py`, y `cli` —el borde del proceso, el
único que ve todas las excepciones— las convierte en un mensaje y un exit code.
`core` no participa ([ADR-0013](./docs/adr/ADR-0013-frontera-de-excepciones.md)).

## Desarrollo

Con `uv`, cada comando se ejecuta mediante `uv run`:

```bash
uv run pytest                              # 35 tests, offline, sin credenciales
uv run pytest -v                           # con el nombre de cada VC
uv run python scripts/check-doc-links.py   # enlaces entre artefactos
```

Sobre un entorno instalado con `pip`, los mismos comandos se corren sin prefijo:

```bash
python -m pytest
python -m pytest -v
python scripts/check-doc-links.py
```

Los tests están nombrados por el VC que ejercitan
(`test_vc1_busqueda_basica_encuentra_match`), así que el nombre del test es el
enlace entre el contrato y el código. La tabla de
[`04-cobertura-vc.md`](./specs/gcsgrep/04-cobertura-vc.md) nombra el ejercitador
de cada VC; si un test se renombra, esa tabla se actualiza.

[CI](./.github/workflows/tests.yml) corre la suite en Python 3.9 y 3.12, más el
chequeo de enlaces, en cada push y cada PR.

### Verificación de integración

Los 35 tests corren contra dobles de prueba. Para verificar contra un GCS de
verdad hay un campo de pruebas desechable:

```bash
export GCSGREP_TEST_BUCKET="gcsgrep-test-$(whoami)-$(date +%s)"
./scripts/testing-ground.sh up      # crea el bucket y siembra 6 fixtures
./scripts/testing-ground.sh verify  # chequeos I-1 … I-6
./scripts/testing-ground.sh down    # destruye el bucket — no es opcional
```

El script se niega a operar sobre un bucket cuyo nombre no empiece con
`gcsgrep-test-`: crea y borra buckets, así que el prefijo es el guardrail que
evita apuntar a uno real por accidente. Procedimiento completo, costo y wiring de
CI en [`docs/integracion-gcs.md`](./docs/integracion-gcs.md).

## Estado

| | |
|---|---|
| Iteración 1 (búsqueda de punta a punta + frontera de excepciones) | ✅ implementada, **12/12 VCs** pasando contra dobles de prueba |
| Verificación de integración (backend `floci`) | ⬜ **sin ejecutar** — ya no bloqueada: corre sin cuenta paga ([ADR-0014](./docs/adr/ADR-0014-emulacion-local-floci.md)) |
| Verificación contra GCS real | ⬜ pendiente — afirmación más fuerte, no se cierra con el emulador |
| Iteración 2 (resiliencia, guardrail de costo, no-texto) | ⬜ planificada, sin implementar |
| Iteración 3 (concurrencia y su NFR de rendimiento) | ⬜ no comprometida; obligación registrada |

**El pendiente es ejecutar la verificación de integración.** El enunciado pide que
la Iteración 1 "corra una búsqueda real y sus chequeos de verificación pasen";
pasar contra un doble de prueba, pasar contra un emulador y pasar contra GCS son
tres afirmaciones distintas, y este repo no las mezcla. Hasta el 2026-09-24 esto
estaba bloqueado por no tener una cuenta con billing; con el backend `floci`
([ADR-0014](./docs/adr/ADR-0014-emulacion-local-floci.md)) corre sin cuenta, así que
**falta correrlo** y anotar lo observado en la tabla de integración de
[`04-cobertura-vc.md`](./specs/gcsgrep/04-cobertura-vc.md).

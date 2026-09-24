# ADR-0013 · Frontera de manejo de excepciones en `cli`, con errores de dominio traducidos en `gcs`

- **Estado:** aceptado
- **Fecha:** 2026-09-24
- **Origen:** [H-12](../hallazgos/H-12-sin-frontera-de-excepciones.md)
- **Requerimientos que habilita:** FR-12 / VC-18, NFR-3 / VC-16 (b)

## Contexto

`cli.main()` tenía un solo `try/except`, alrededor de `parse_location`. La
llamada a `core.search` estaba desnuda, así que **toda** excepción del SDK de
Google escapaba hasta el intérprete: credenciales que no resuelven, 403, 404,
timeouts, 500. El resultado era siempre traceback y exit `1` — el código que
significa *"corrí bien, sin matches"*, así que un script que use `gcsgrep` como
predicado leía un fallo total como un resultado válido.

NFR-3 ya prometía lo contrario desde la v1.0 (*"ningún caso de error imprime un
stack trace de Python"*), pero VC-16 verificaba una lista cerrada de casos y
todos los caminos del SDK quedaban afuera.

Hacía falta decidir **dónde** vive el manejo, y eso tiene alternativas reales:
la arquitectura declara `cli → core → gcs` y que `core` no conoce
`google.cloud.storage`.

## Decisión

Tres piezas:

1. **La frontera vive en `cli.main()`**, envolviendo el recorrido completo de
   `core.search`. El borde del proceso es el único lugar que ve todas las
   excepciones, y por lo tanto el único donde "ningún traceback, nunca" se puede
   garantizar.

2. **La traducción vive en `gcs`**, que es la única capa que conoce el SDK.
   `gcs` captura las excepciones de `google.api_core` y levanta los errores de
   dominio de `gcsgrep/errors.py`: `BucketNoEncontrado`, `AccesoDenegado`,
   `ObjetoNoEncontrado`, todos bajo `ErrorDeAcceso`. Así `cli` reporta fallos de
   GCS **sin importar `google.api_core`**, y `core` sigue sin saber que GCS
   existe.

3. **Dos `except`, en este orden:**
   - `ErrorDeAcceso` → imprime `str(exc)` por stderr y sale con `2`. El mensaje
     ya está escrito para una persona; `cli` no lo reformula.
   - `Exception` → caso genérico: mensaje con el tipo y el texto de la excepción,
     y exit `2`. **Es un piso, no una clasificación.**

   El genérico tiene una vía de escape explícita: con `GCSGREP_DEBUG=1` la
   excepción se re-lanza con su traceback. Sin eso, el caso genérico esconde
   justamente la información que hace falta para diagnosticar un bug nuevo.

Dos mensajes distintos para 404 y 403 (FR-12) porque mandan a quien los lee a
lugares distintos: "no existe" a revisar el nombre, "sin permiso" a revisar IAM.

## Consecuencias

- **NFR-3 pasa a ser verificable en su parte universal.** VC-16 (b) inyecta una
  excepción de una clase que el código no conoce y exige exit `2` sin traceback.
  Eso es lo que no se puede lograr enumerando casos.
- **`cli` no importa el SDK.** La dependencia `cli → core → gcs` se mantiene, y
  `gcs` sigue siendo el único archivo a auditar para BR-1.
- **VC-17 cambió de observable, no de afirmación.** El test de punta a punta
  antes esperaba que la excepción escapara (`pytest.raises(OSError)`); ahora
  espera exit `2`. Lo que el VC afirma —que los matches ya emitidos salieron
  antes del fallo— es idéntico. Queda registrado como fila nueva en la tabla de
  cobertura, no como edición.
- **I-6 (ADC ausente → exit `2` sin traceback) empieza a pasar** como efecto
  colateral: la falta de credenciales sube por el mismo camino y cae en el caso
  genérico. Se reclama con una fila nueva, como
  [H-11](../hallazgos/H-11-runbook-vs-plan.md) dejó dicho.
- **Riesgo asumido: el genérico puede tapar alcance de la Iteración 2.** Un
  `except Exception` de tope hace que FR-6 (objeto ilegible no aborta), BR-3
  (precedencia de exit codes) y NFR-2 (fallos de red) *parezcan* implementados.
  No lo están: hoy cualquiera de esos casos aborta la corrida con un mensaje
  genérico. La mitigación es que estén declarados como Iteración 2 en el plan y
  como ⬜ en la tabla de cobertura, y que este ADR lo diga.
- **`ObjetoNoEncontrado` es un caso de [ADR-0010](./ADR-0010-objeto-modificado.md)**
  (el bucket cambia mientras se lo recorre) manifestándose como borrado. Hoy
  aborta; que no aborte es FR-6.

## Alternativas descartadas

- **Manejar las excepciones en `core`.** Rompe la dirección de dependencia: `core`
  tendría que importar `google.api_core` para saber qué atrapar, y perdería la
  propiedad de testearse sin el SDK, que es la razón por la que la suite entera
  corre sin red ni credenciales.
- **Dejar que `gcs` imprima y termine el proceso.** Una capa de acceso a datos
  que escribe en stderr y decide exit codes no se puede reusar ni testear como
  colaborador, y le saca a `cli` la responsabilidad que el README le asigna.
- **Atrapar solo las excepciones conocidas, sin caso genérico.** Es lo que hacía
  VC-16 (a) verificable y a NFR-3 falso: cada excepción no prevista vuelve a ser
  un traceback. El caso genérico es el punto del ADR.
- **`except Exception` sin vía de escape.** Convierte cualquier bug futuro en un
  mensaje de una línea sin forma de diagnosticarlo. De ahí `GCSGREP_DEBUG=1`.
- **Traducir a exit codes distintos por tipo de error** (por ejemplo `3` para
  credenciales). Rompe [ADR-0008](./ADR-0008-exit-codes.md), que fija la
  convención exacta de `grep`: `2` es "error", sin subdivisiones.

## Relacionado

- [H-12](../hallazgos/H-12-sin-frontera-de-excepciones.md) — el hallazgo que lo pidió
- [H-13](../hallazgos/H-13-actores-sin-trazar.md) — por qué FR-12 no existía
- [ADR-0008](./ADR-0008-exit-codes.md) — la convención de exit codes que respeta
- [ADR-0002](./ADR-0002-autenticacion-adc.md) — el fallo de ADC entra por el genérico
- [ADR-0010](./ADR-0010-objeto-modificado.md) — origen de `ObjetoNoEncontrado`

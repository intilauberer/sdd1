# H-12 · El CLI no tiene frontera de manejo de excepciones, y NFR-3 no es falsable

| | |
|---|---|
| **Severidad** | crítico |
| **Fecha** | 2026-09-23 |
| **Detectado en** | Primer intento de correr `gcsgrep` contra almacenamiento real, con un bucket que no existía |
| **Artefactos afectados** | `gcsgrep/cli.py`, [`02-spec.md`](../../specs/gcsgrep/02-spec.md) (NFR-3 / VC-16) |
| **Estado** | **resuelto** — spec v1.2 (FR-12/VC-18, VC-16 reforzado) e implementado el 2026-09-24 ([ADR-0013](../adr/ADR-0013-frontera-de-excepciones.md)) |

## El hallazgo

**`cli.main()` no atrapa ninguna excepción que suba de `core` o de `gcs`.** Tiene
un solo `try/except`, alrededor de `parse_location`:

```python
try:
    bucket, prefix = core.parse_location(args.location)
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    return 2
...
for match in core.search(bucket, prefix, config, gcs.list_objects, gcs.open_text_stream):
```

Esa última línea está **desnuda**. Todo lo que el SDK de Google pueda levantar
—credenciales que no resuelven, 403, 404, 400 por un nombre de bucket inválido,
timeouts, 500 transitorios— escapa hasta el intérprete. El resultado es siempre el
mismo: **traceback de Python y exit `1`.**

El `1` es lo peor de los dos. Es el código que la herramienta usa para decir *"corrí
bien, no encontré nada"* ([ADR-0008](../adr/ADR-0008-exit-codes.md)), así que un
script que la use como predicado —el caso de uso que el README documenta— **lee un
fallo total como "no hay matches"**. Falla en silencio y en la dirección insegura.

## El síntoma que lo destapó

```
$ gcsgrep "timeout" gs://test-bucket/
Traceback (most recent call last):
  File ".../gcsgrep/cli.py", line 50, in main
    for match in core.search(bucket, prefix, config, gcs.list_objects, ...)
  ...
google.api_core.exceptions.NotFound: 404 GET .../storage/v1/b/test-bucket/o: Not Found
```

El bucket no existía. Pero **el caso concreto es una anécdota**: el mismo traceback
sale con credenciales ausentes, sin permiso de listado, o con la red caída. Lo que
importa no es que falte el manejo de *ese* error, sino que **no hay ningún lugar en
el código donde manejar ninguno**. No existe la frontera.

## Por qué los VCs no lo detectaron

Acá está la parte que vale más que el bug, y es lo que lo hace un hallazgo de la
spec y no solo un ticket de código.

**NFR-3 ya prometía exactamente esto, en términos universales:**

> Ningún caso de error imprime un stack trace de Python.

*Ningún caso.* La promesa está escrita y hoy no se cumple. Pero su criterio de
verificación es una **lista cerrada**:

> **VC-16** — Para cada caso de error o salteo **cubierto (VC-6, VC-8, VC-9, VC-10,
> VC-12, VC-13, VC-15)**, stdout no contiene ninguna línea que no sea un match
> real, y stderr no contiene la palabra `Traceback`.

Un requerimiento cuantificado sobre *todos* los errores, verificado enumerando
*algunos*. Cualquier camino de error que no esté en la lista puede tirar un
traceback sin que VC-16 se entere — y todos los caminos que vienen del SDK están
fuera de la lista, porque la lista se armó a partir de los VCs que existían.

**Es la misma especie que [H-3](../revision-spec.md)**: un VC escrito contra los
casos que la implementación ya contempla, en vez de contra la propiedad que el
requerimiento promete. H-3 fue *"el VC no podía fallar porque medía el camino
feliz"*; este es *"el VC no puede fallar fuera de una lista que el propio código
definió"*. La lección de H-3 (C-8: **¿cada VC puede fallar por la razón
correcta?**) se aplicó a VC-14 y no se volvió a aplicar al resto.

## Resolución

### En la spec (v1.2, hecho)

1. **VC-16 reforzado con un caso adverso**, igual que se hizo con VC-14 en la v1.1:
   además de la lista enumerada, se inyecta una excepción **arbitraria e inesperada**
   desde el colaborador de `gcs` y se verifica exit `2` sin traceback. Ese caso es
   el que hace falsable la parte universal de NFR-3: no se puede enumerar "todos los
   errores", pero sí se puede exigir que uno **desconocido** se maneje.
2. **FR-12 / VC-18** para el caso concreto que apareció (bucket inexistente o
   inaccesible), con mensaje que distingue "no existe" de "sin permiso" porque
   mandan a revisar cosas distintas. El hueco de contrato que lo hacía invisible
   está en [H-13](./H-13-actores-sin-trazar.md).

### En el código (hecho — [ADR-0013](../adr/ADR-0013-frontera-de-excepciones.md))

Una **frontera de excepciones en `cli.main()`**: el borde del proceso es el único
lugar donde se puede garantizar "ningún traceback, nunca", porque es el único que
ve todas las excepciones. Lo que hubo que decidir, y cómo quedó:

- **Qué se traduce a un mensaje específico:** `NotFound` y `Forbidden` al listar
  (FR-12), más `NotFound` al abrir un objeto. El resto cae en el genérico. Las
  credenciales ausentes **no** tienen mensaje propio: eso sigue siendo Iteración 2.
- **Que el caso genérico no tape el problema:** `GCSGREP_DEBUG=1` re-lanza la
  excepción con su traceback. Sin esa vía de escape, el genérico convierte cualquier
  bug futuro en una línea sin diagnóstico.
- **Que `core` no aprenda a manejar errores de GCS:** la traducción vive en `gcs`,
  que ya es la única capa que conoce el SDK, y levanta los errores de dominio de
  `gcsgrep/errors.py`. `cli` los atrapa sin importar `google.api_core`, así que
  `cli → core → gcs` se mantiene.

**Riesgo asumido, registrado en ADR-0013:** un `except Exception` de tope hace que
FR-6, BR-3 y NFR-2 *parezcan* implementados. No lo están — hoy cualquiera de esos
casos aborta la corrida con un mensaje genérico.

## Regla que deja

**Un requerimiento cuantificado universalmente ("ningún", "siempre", "todo") no se
puede verificar enumerando casos.** Su VC necesita al menos un caso adverso
*desconocido para la implementación*, o el VC solo mide lo que el código ya sabía
hacer.

Es la tercera vez que aparece la misma familia en este repo (H-3, y ahora este):
conviene tratar C-8 del checklist como una pregunta a hacerle a **cada** VC en cada
revisión, no solo a los que se ven sospechosos.

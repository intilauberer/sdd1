# gcsgrep — spec

| | |
|---|---|
| **Versión** | 1.2 |
| **Estado** | habilitada, con la excepción registrada en la revisión (ver más abajo) |
| **Fecha** | 2026-09-23 |
| **Revisada por** | [`docs/revision-spec.md`](../../docs/revision-spec.md) — checklist C-1…C-13, 12 hallazgos ([`docs/hallazgos/`](../../docs/hallazgos/)) |
| **Insumos** | [`01-base-context.md`](./01-base-context.md), [`00-requirements-draft.md`](./00-requirements-draft.md) (congelado), [`docs/adr/`](../../docs/adr/) |
| **Salidas** | [`03-plan.md`](./03-plan.md), [`04-cobertura-vc.md`](./04-cobertura-vc.md) |

> **Cómo cambia este documento.** No es inmutable, pero tampoco se edita en el
> lugar: todo cambio sube la versión, deja una fila en el *Historial de
> revisiones* del final, y pasa por el checklist de
> [`docs/revision-spec.md`](../../docs/revision-spec.md). El fundamento de cada
> decisión **no vive acá**: vive en un ADR con identificador estable, y un ADR
> aceptado no se edita, se supersede.
>
> Tres reglas estructurales, cada una con su tabla de trazabilidad al final:
>
> 1. **Cada FR y cada BR tiene un VC.** Si una línea no se puede verificar, no
>    está especificada.
> 2. **Cada ítem del borrador terminó en algo:** un FR/BR/NFR, la lista de
>    "Fuera", o una iteración del plan. La tabla *Trazabilidad borrador → spec*
>    lo demuestra fila por fila. Esta segunda regla se agregó en v1.1, después
>    de que la revisión encontrara dos requerimientos del borrador que se habían
>    perdido en silencio.
> 3. **Cada modo de falla nombrado en la tabla de Actores tiene un requerimiento
>    que lo cubre.** Agregada en v1.2 por
>    [H-12](../../docs/hallazgos/H-12-actores-sin-trazar.md): la tabla de Actores
>    declaraba que GCS "puede fallar por permisos, red, o no existir", y el
>    tercero no había aterrizado en ningún requerimiento. Las reglas 1 y 2 no
>    podían detectarlo — una mira los requerimientos que existen, la otra el
>    borrador, y esta obligación había nacido dentro de la spec.
>
> Las tres son la misma idea aplicada en tres direcciones: **toda tabla que
> declara obligaciones necesita otra tabla que demuestre que se cumplieron.**

## Propósito

Permitir que alguien busque texto dentro del contenido de objetos de Google
Cloud Storage sin descargarlos primero, con la misma experiencia mental que
`grep` sobre archivos locales.

## Alcance

### Dentro

- Un único comando: `gcsgrep [-i] [-n] [--max N] <patrón> gs://bucket/prefijo`.
- Búsqueda literal (substring) sobre el contenido de objetos de texto.
- Autenticación por Application Default Credentials.
- Guardrail de costo por cantidad de objetos.
- Exit codes estilo `grep`, salida apta para scripting.
- Salida incremental: cada match se imprime en cuanto se encuentra.

### Fuera

Cada uno de estos es una decisión tomada, no un olvido. El fundamento está en
el ADR que se cita:

- **Regex** (básica o completa) — solo substring literal en v1
  ([ADR-0001](../../docs/adr/ADR-0001-busqueda-literal.md)).
- **Flags de `grep` más allá de `-i` y `-n`** (`-l`, `-c`, `-v`, `-r`,
  `--include`, etc) ([ADR-0004](../../docs/adr/ADR-0004-flags-v1.md)).
- **Descompresión de `.gz`** — se saltean, no se leen
  ([ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md)).
- **Autenticación por archivo de service account explícito** — solo ADC; si
  `GOOGLE_APPLICATION_CREDENTIALS` apunta a una key, ADC ya la resuelve sola
  ([ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md)).
- **Lectura concurrente de objetos** — secuencial en v1
  ([ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md)).
- **Umbral de rendimiento** — declinado en v1 con fundamento, diferido a la
  Iteración 3, donde el número es comparativo contra la línea de base
  secuencial ([ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md)).
- **Indicador de progreso explícito** (barra, contador por stderr) — el
  progreso se manifiesta como salida incremental, ver FR-11
  ([ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)).
- **Salida JSON** — solo formato estilo `grep`
  ([ADR-0007](../../docs/adr/ADR-0007-formato-de-salida.md)).
- **Providers que no son GCS** (S3, Azure Blob).
- **Reintentos automáticos ante fallos de red transitorios.**
- **Consistencia ante un objeto modificado mientras se lee** — riesgo conocido,
  aceptado ([ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md)).
- **Escritura, borrado o modificación de cualquier objeto o permiso en GCS** —
  la herramienta es de solo lectura, siempre (BR-1).

## Actores

| Actor | Descripción |
|---|---|
| **Persona usuaria** | Ejecuta `gcsgrep` en una shell y lee la salida en pantalla |
| **Script** | Ejecuta `gcsgrep` y decide en base al exit code, no al texto de salida |
| **GCS** | Fuente de los objetos; puede fallar por **permisos**, **red**, o **no existir** |

Los tres modos de falla de GCS están en negrita porque son obligaciones: cada uno
tiene que aterrizar en un requerimiento, y la tabla *Trazabilidad actores →
requerimiento* lo demuestra. No es decoración: el tercero estuvo declarado acá y
sin cubrir desde la v1.0 hasta la v1.2.

---

## Requerimientos funcionales

### FR-1 · Búsqueda básica sobre un prefijo

**Dado** un prefijo de GCS con al menos un objeto de texto que contiene el
patrón buscado,
**Cuando** la persona ejecuta `gcsgrep "<patrón>" gs://bucket/prefijo`,
**Entonces** el sistema imprime por stdout una línea por cada línea de texto
que matchea, identificando el objeto de origen, y sale con código `0`.

> **VC-1** — Con un objeto `gs://b/logs/a.txt` que contiene la línea
> `"connection timeout"`, `gcsgrep "timeout" gs://b/logs/` sale con código `0`
> e imprime una línea que referencia `gs://b/logs/a.txt` y contiene el texto
> matcheado.

### FR-2 · Búsqueda sin distinguir mayúsculas (`-i`)

**Dado** un objeto que contiene `"Timeout"` (con mayúscula),
**Cuando** la persona ejecuta `gcsgrep -i "timeout" gs://bucket/prefijo`,
**Entonces** el sistema lo reporta como match.

> **VC-2** — Con un objeto que contiene únicamente la línea `"Timeout error"`,
> `gcsgrep "timeout" ...` (sin `-i`) sale con código `1` (sin matches) y
> `gcsgrep -i "timeout" ...` sobre el mismo objeto sale con código `0` y
> reporta esa línea.

### FR-3 · Número de línea (`-n`)

**Dado** un objeto donde el patrón aparece en una línea específica,
**Cuando** la persona ejecuta `gcsgrep -n "<patrón>" gs://bucket/prefijo`,
**Entonces** cada línea de salida incluye el número de línea (1-indexado)
dentro del objeto donde ocurrió el match.

> **VC-3** — Con un objeto de 5 líneas donde el patrón está solo en la línea 3,
> `gcsgrep -n "<patrón>" ...` imprime una línea de salida que contiene `3` como
> número de línea; sin `-n`, la salida no incluye ese número.

### FR-4 · Formato de salida

**Dado** un match encontrado,
**Cuando** se imprime por stdout,
**Entonces** el formato es `<gs://bucket/objeto>:<línea>:<texto>` si se pidió
`-n`, o `<gs://bucket/objeto>:<texto>` si no.

> **VC-4** — La salida de un match, parseada por `:`, separa correctamente la
> ruta del objeto (empieza con `gs://`), el número de línea (si `-n`, es un
> entero) y el texto de la línea (contiene el patrón buscado).

### FR-5 · Sin resultados

**Dado** un prefijo válido y accesible donde ningún objeto contiene el patrón,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** stdout queda vacío y el sistema sale con código `1`.

> **VC-5** — Sobre un prefijo con un único objeto de texto que no contiene el
> patrón buscado, `gcsgrep` sale con código `1` y no imprime nada por stdout.

### FR-6 · Un objeto ilegible no aborta la corrida

**Dado** un prefijo con varios objetos, donde uno no se puede leer (permiso
denegado o error transitorio),
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema informa el objeto fallido por stderr, sigue procesando
el resto de los objetos, y el fallo se refleja en el exit code según BR-3.

> **VC-6** — Con tres objetos donde el segundo levanta un error al abrirlo, la
> corrida procesa igual el primero y el tercero (sus matches, si los hay,
> aparecen por stdout), y stderr menciona el nombre del objeto que falló.

### FR-7 · Bucket completo (prefijo vacío)

**Dado** `gs://bucket/` o `gs://bucket` sin prefijo adicional,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema busca sobre todos los objetos del bucket, tratando el
prefijo como cadena vacía.

> **VC-7** — Con objetos en dos "carpetas" distintas del mismo bucket (`a/x.txt`
> y `b/y.txt`), `gcsgrep "<patrón>" gs://bucket/` encuentra matches en ambos si
> el patrón está en ambos.

### FR-8 · Rechazo de ubicaciones inválidas

**Dado** un argumento de ubicación que no empieza con `gs://`,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema rechaza la invocación con un mensaje por stderr y sale
con código `2`, sin intentar ninguna llamada a GCS.

> **VC-8** — `gcsgrep "patrón" logs/` (sin esquema) y `gcsgrep "patrón" s3://b/`
> (esquema no soportado) salen ambos con código `2` y un mensaje por stderr que
> menciona el esquema esperado (`gs://`).

### FR-9 · Salteo de objetos binarios

**Dado** un objeto cuyo contenido no es texto (contiene un byte `\x00` en sus
primeros bytes),
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin intentar matchear contra su contenido, sin
imprimir su contenido crudo, y lo anota en el resumen de salteados por stderr.

> **VC-9** — Con un objeto binario (bytes arbitrarios incluyendo `\x00`) mezclado
> con objetos de texto bajo el mismo prefijo, la corrida no imprime bytes crudos
> ni lanza una excepción, y stderr menciona que un objeto fue salteado.

### FR-10 · Salteo de objetos `.gz`

**Dado** un objeto cuyo nombre termina en `.gz`,
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin intentar descomprimirlo ni leer su
contenido comprimido como texto, y lo anota en el resumen de salteados.

> **VC-10** — Con un objeto `access.log.gz` bajo el prefijo buscado, la corrida
> no falla ni imprime contenido corrupto para ese objeto, y stderr lo menciona
> como salteado.

### FR-11 · Salida incremental

**Dado** un prefijo con varios objetos que contienen el patrón,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** cada match se emite por stdout en cuanto se encuentra, sin esperar
a que termine de recorrerse el prefijo.

*Origen:* FR-g del borrador ("el usuario tiene que poder darse cuenta de que
está progresando cuando hay muchos objetos, porque si no parece colgado"),
resuelto en [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md). El
progreso **es** la salida apareciendo: no hay barra ni contador.

*Límite explícito:* una corrida larga **sin** matches no muestra nada hasta
terminar. Aceptado en el ADR.

> **VC-17** — Con tres objetos que matchean bajo el mismo prefijo, obtener el
> primer match no requiere haber listado ni abierto los otros dos (se observa
> sobre el doble de prueba, que registra qué objetos se consumieron y cuándo).
> De punta a punta: si el primer objeto emite dos matches y después falla al
> leerse, esos dos matches ya salieron por stdout antes de que la corrida
> termine.

### FR-12 · Bucket inexistente o inaccesible

**Dado** una ubicación sintácticamente válida (pasa FR-8) cuyo bucket no existe,
o sobre el cual quien invoca no tiene permiso de listado,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema informa por stderr con un mensaje legible que nombra el
bucket y **distingue "no existe" de "sin permiso"**, sale con código `2`, y no
lee el contenido de ningún objeto.

*Origen:* [H-12](../../docs/hallazgos/H-12-actores-sin-trazar.md). La tabla de
Actores declaraba desde la v1.0 que GCS "puede fallar por permisos, red, o **no
existir**", y ningún requerimiento cubría el tercer caso. Se descubrió con un
`NotFound: 404` que escapó como traceback de Python y exit `1`.

*Por qué es un requerimiento aparte y no una extensión de otro:* FR-5 exige un
prefijo "válido y accesible" como premisa; FR-8 cubre la sintaxis, y
`gs://no-existe/` es sintácticamente correcta; FR-6 es por objeto y no aborta la
corrida, mientras que acá falla el **listado** y no hay objetos sobre los que
seguir; y NFR-2 habla de fallos de **red**, que un 404 no es — la red funcionó y
la respuesta fue explícita.

*Por qué se distinguen los dos mensajes:* mandan a quien lee a lugares distintos.
"No existe" manda a revisar el nombre; "sin permiso" manda a revisar IAM. Un
mensaje único obliga a diagnosticar dos veces.

> **VC-18** — Con un bucket inexistente, `gcsgrep "x" gs://no-existe/` sale con
> código `2`, stdout vacío, stderr menciona el nombre del bucket e indica que no
> existe, y stderr no contiene `Traceback`. Con un bucket que existe pero sobre el
> que no hay permiso de listado, el mismo exit code `2` y un mensaje **distinto**,
> que menciona los permisos. En ninguno de los dos casos se abre un objeto
> (0 llamadas a abrir un stream).

---

## Reglas de negocio

### BR-1 · Solo lectura, sin amplificación de credenciales

`gcsgrep` nunca invoca una operación de escritura, borrado o cambio de permisos
sobre GCS, y nunca usa credenciales distintas de las que ya tiene quien la
invoca (ADC). No existe un modo de "elevar" acceso.

*Fundamento:* restricción explícita del enunciado de la tarea.
*Excepciones:* ninguna.

> **VC-11** — Revisando el módulo `gcs` (la única capa que llama a la API), las
> únicas operaciones invocadas sobre el cliente de GCS son de listado y lectura
> (`list_blobs`, apertura de stream de lectura); no existe en el código ningún
> llamado a un método de escritura, borrado o cambio de IAM. Verificado por
> inspección + un test que falla si el doble de prueba usado en los tests
> recibe una llamada a un método que no sea de lectura.

### BR-2 · Guardrail de costo por cantidad de objetos

Antes de leer contenido, se listan los objetos del prefijo. Si la cantidad
supera el tope (por defecto **1000**, ajustable con `--max N`; `--max 0` quita
el tope), no se lee ningún objeto, se informa la cantidad encontrada y el tope
vigente por stderr, y se sale con código `1`.

*Fundamento:* leer objetos de GCS tiene costo; evita una corrida cara por
accidente.
*Excepciones:* `--max 0` es una excepción explícita, decidida por quien invoca,
no un valor por defecto.

> **VC-12** — Con 1001 objetos bajo el prefijo y sin `--max`, `gcsgrep` sale con
> código `1`, no realiza ninguna lectura de contenido (0 llamadas a abrir un
> objeto), y stderr menciona la cantidad encontrada y el tope. Con `--max 0`
> sobre el mismo prefijo, si hay un match la corrida sale con código `0` y sí
> lee objetos.

### BR-3 · Precedencia de exit codes ante fallos parciales

Si ocurrió al menos un error de lectura sobre algún objeto (FR-6), el exit code
final es **`2`**, sin importar si hubo matches en los objetos que sí se
pudieron leer. Sin errores de lectura: `0` si hubo matches, `1` si no.

*Fundamento:* un resultado "sin matches" o "con matches" que ocurrió a pesar de
errores parciales no es un resultado confiable para un script; `2` lo señala
sin ambigüedad, igual que hace `grep` cuando un archivo no se puede abrir.
*Excepciones:* ninguna.

> **VC-13** — Con dos objetos, uno con match y otro que falla al leerse,
> `gcsgrep` imprime el match encontrado por stdout, informa el fallo por
> stderr, y sale con código `2` (no `0`).

---

## Requerimientos no funcionales

### NFR-1 · Memoria acotada por streaming

El sistema procesa cada objeto línea por línea usando streaming de lectura, sin
cargar el contenido completo del objeto en memoria de una vez, **y sin acumular
los matches encontrados** (ver FR-11 y
[ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)).

> **VC-14** — Sobre un objeto simulado de **200 MB** de contenido de texto, el
> pico de memoria adicional usado por el proceso de lectura de ese objeto es
> menor a **20 MB** (medido con `tracemalloc` sobre el doble de prueba que
> expone el stream; nunca se llama a un equivalente de "leer todo el archivo"
> sobre él). Se mide en **dos** condiciones: con un patrón que no aparece en
> ninguna línea, y con un patrón que aparece en **todas**. El segundo caso es
> el que hace falsable al VC: con acumulación de matches, el pico medido es de
> ~371 MB.

### NFR-2 · Fallos de red no crashean el proceso

Un error de red al listar o leer se captura, se reporta por stderr sin
traceback, y se trata según BR-3 (si es sobre un objeto puntual) o aborta con
código `2` (si es sobre el listado inicial). No hay reintentos automáticos en
v1.

> **VC-15** — Simulando que el listado inicial lanza una excepción de red,
> `gcsgrep` sale con código `2`, stderr no contiene `Traceback`, y el mensaje
> es legible (no la representación cruda de la excepción de la librería).

### NFR-3 · Salida apta para scripting

stdout contiene únicamente líneas de match. Todo mensaje informativo, de
error o de resumen (objetos salteados, objetos fallidos, guardrail excedido)
va a stderr. Ningún caso de error imprime un stack trace de Python.

> **VC-16** — Para cada caso de error o salteo cubierto (VC-6, VC-8, VC-9,
> VC-10, VC-12, VC-13, VC-15, VC-18), stdout no contiene ninguna línea que no sea
> un match real, y stderr no contiene la palabra `Traceback`.

---

## Tabla de trazabilidad · requerimiento → VC

| Requerimiento | VC | Camino |
|---|---|---|
| FR-1 | VC-1 | feliz |
| FR-2 | VC-2 | feliz |
| FR-3 | VC-3 | feliz |
| FR-4 | VC-4 | feliz |
| FR-5 | VC-5 | borde (sin resultados) |
| FR-6 | VC-6 | falla parcial |
| FR-7 | VC-7 | borde (bucket completo) |
| FR-8 | VC-8 | falla (input inválido) |
| FR-9 | VC-9 | borde (binario) |
| FR-10 | VC-10 | borde (.gz) |
| FR-11 | VC-17 | invariante (observabilidad) |
| FR-12 | VC-18 | falla (bucket inexistente / sin permiso) |
| BR-1 | VC-11 | invariante |
| BR-2 | VC-12 | guardrail |
| BR-3 | VC-13 | invariante |
| NFR-1 | VC-14 | medición |
| NFR-2 | VC-15 | falla |
| NFR-3 | VC-16 | invariante |

**18 requerimientos, 18 VCs, 0 huérfanos.**

## Tabla de trazabilidad · borrador → spec

La tabla de arriba prueba que ningún requerimiento de esta spec quedó sin VC.
Esta prueba lo otro, que es lo que faltaba en v1.0: que ningún ítem del
[borrador](./00-requirements-draft.md) quedó sin destino. Los dos huérfanos que
encontró la revisión (FR-g y NFR-a) están marcados con su resolución.

| Ítem del borrador | Destino | Dónde |
|---|---|---|
| FR-a · patrón + ubicación, busca dentro de los objetos | FR-1 | Iteración 1 |
| FR-b · bucket completo o prefijo | FR-7 | Iteración 1 |
| FR-c · salida deja claro el objeto, y la línea si se puede | FR-4 (objeto) + FR-3 (línea, tras `-n`) | Iteración 1 |
| FR-d · búsqueda sin distinguir mayúsculas | FR-2 | Iteración 1 |
| FR-e · avisar "no encontré nada" de forma detectable por un script | FR-5 (exit `1`) | Iteración 1 |
| FR-f · un objeto ilegible no tira la corrida | FR-6 | Iteración 2 |
| FR-g · notar el progreso con muchos objetos | **FR-11** — resuelto en v1.1, [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md). Era huérfano en v1.0 (hallazgo H-1) | Iteración 1 |
| BR-a? · nunca escribe en GCS | BR-1 | Iteración 2 |
| BR-b? · no amplía el acceso del invocador | BR-1 (fusionado) + [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) | Iteración 2 |
| BR-c? · límite para no escanear un bucket enorme | BR-2, con tope decidido en objetos ([ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md)) | Iteración 2 |
| BR-d? · saltear lo que no es texto | FR-9 (es comportamiento observable, no regla de negocio) + [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md) | Iteración 2 |
| NFR-a · rendimiento | **Declinado en v1 con fundamento**, diferido a Iteración 3, [ADR-0012](../../docs/adr/ADR-0012-nfr-rendimiento-diferido.md). Estaba en `_pendiente_` en v1.0 (hallazgo H-2) | Iteración 3 |
| NFR-b · memoria con objetos grandes | NFR-1, umbral 20 MB sobre 200 MB | Iteración 1 |
| NFR-c · comportamiento ante fallos de red | NFR-2 | Iteración 2 |

**14 ítems del borrador, 14 con destino explícito, 0 perdidos.**

Dos notas sobre la forma de esta tabla:

- **FR-c se abrió en dos.** El borrador metía dos comportamientos en una línea
  ("el objeto, y la línea si se puede"). Un FR por comportamiento.
- **BR-a? y BR-b? se fusionaron.** Son la misma invariante vista de dos lados:
  no escribir y no elevar privilegios. Un solo BR con un solo VC.

## Tabla de trazabilidad · actores → requerimiento

Las dos tablas de arriba cubren los requerimientos que existen y los ítems del
borrador. Esta cubre la tercera fuente de obligaciones, que no estaba vigilada por
ninguna de las dos: **los modos de falla declarados en la tabla de Actores.**

Se agregó en v1.2 por [H-12](../../docs/hallazgos/H-12-actores-sin-trazar.md), que
encontró uno declarado desde la v1.0 y nunca cubierto.

| Actor | Modo de falla declarado | Requerimiento que lo cubre | VC |
|---|---|---|---|
| GCS | **Permisos** — sobre un objeto puntual | FR-6 (informa y sigue) + BR-3 (exit `2`) | VC-6, VC-13 |
| GCS | **Permisos** — sobre el listado del bucket | **FR-12** (mensaje distinto del de "no existe") | VC-18 |
| GCS | **Red** — al leer un objeto | FR-6 + BR-3 | VC-6, VC-13 |
| GCS | **Red** — al listar | NFR-2 (aborta con `2`, sin traceback) | VC-15 |
| GCS | **No existir** — el bucket | **FR-12** — *era el huérfano de H-12* | VC-18 |
| GCS | **No existir** — el prefijo (0 objetos) | FR-5 (exit `1`, es un resultado válido, no un error) | VC-5 |
| Persona usuaria | Ubicación mal escrita | FR-8 (exit `2` sin tocar la red) | VC-8 |
| Persona usuaria | Prefijo gigante, corrida costosa | BR-2 (guardrail, tope 1000) | VC-12 |
| Script | Necesita decidir sin parsear texto | FR-5, BR-3, NFR-3 (exit codes + stdout limpio) | VC-5, VC-13, VC-16 |

**9 modos de falla declarados, 9 cubiertos, 0 huérfanos.**

Dos notas sobre la forma de esta tabla:

- **"Permisos", "red" y "no existir" se abrieron por dónde ocurren.** Un fallo al
  **listar** aborta la corrida; el mismo fallo sobre **un objeto** no. Escritos
  como una sola línea, fue precisamente lo que permitió que el caso del listado se
  perdiera: "permisos" parecía cubierto por FR-6.
- **"Prefijo inexistente" no es un error.** Un prefijo sin objetos dentro de un
  bucket que sí existe es indistinguible de un prefijo sin matches, y GCS no
  reporta error: FR-5 (exit `1`) es la respuesta correcta. Solo el **bucket**
  inexistente es un error, porque ahí GCS sí responde 404.

## Preguntas abiertas

Ninguna. Las 10 del borrador quedaron resueltas como
[ADR-0001 … ADR-0010](../../docs/adr/); los dos huérfanos que encontró la
revisión, como ADR-0011 y ADR-0012.

## Qué sigue

- Plan de iteraciones: [`03-plan.md`](./03-plan.md).
- Estado de verificación (única fuente de verdad sobre qué VC pasa):
  [`04-cobertura-vc.md`](./04-cobertura-vc.md).

## Historial de revisiones

| Versión | Fecha | Cambio | Origen |
|---|---|---|---|
| 1.0 | 2026-09-23 | Primera spec a partir del base context. 16 FR/BR/NFR, 16 VCs. | paso Especificar |
| 1.1 | 2026-09-23 | **+FR-11/VC-17** (salida incremental, resuelve FR-g). **NFR-a declinado** con fundamento en vez de quedar pendiente. **VC-14 reforzado** con el caso donde todo matchea. Fundamento movido a ADRs; la spec los referencia. Nueva tabla borrador → spec. Encabezado versionado. | [`docs/revision-spec.md`](../../docs/revision-spec.md), hallazgos H-1, H-2, H-3, H-5, H-7, H-8 |
| 1.2 | 2026-09-23 | **+FR-12/VC-18** (bucket inexistente o inaccesible → exit `2`, mensaje que distingue "no existe" de "sin permiso"). **Tercera regla estructural** y su **tabla de trazabilidad actores → requerimiento**. VC-16 extendido a VC-18. Modos de falla de la tabla de Actores marcados como obligaciones. | [H-12](../../docs/hallazgos/H-12-actores-sin-trazar.md) |

**Qué cambió del contrato en v1.2.** FR-12 no cambia el resultado de ninguna
corrida que la Iteración 1 ya produjera *correctamente*: hoy ese caso termina en
traceback y exit `1`, que no era un comportamiento prometido por nadie. Pasa a ser
exit `2` con un mensaje legible. No es una regresión ni rompe ningún VC existente;
es un hueco del contrato que se cierra.

**Cambio de contrato todavía pendiente, anunciado para v1.3:** BR-3 hace que un
error de lectura parcial fuerce exit `2` aunque haya matches. Eso sí cambia el
resultado observable de corridas que la Iteración 1 ya puede producir. Cuando se
implemente la Iteración 2, va en una fila nueva de este historial, no en una
edición muda. (Este anuncio decía "v1.2" hasta que v1.2 se usó para FR-12; el
compromiso es el mismo, corre una versión.)

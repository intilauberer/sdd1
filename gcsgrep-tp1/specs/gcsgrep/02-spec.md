# gcsgrep — spec

| | |
|---|---|
| **Versión** | 1.4 |
| **Estado** | habilitada para la Iteración 2, tras la corrección de la cátedra (ver más abajo) |
| **Fecha** | 2026-10-01 |
| **Revisada por** | [`docs/revision-spec.md`](../../docs/revision-spec.md) — checklist C-1…C-18, 15 hallazgos ([`docs/hallazgos/`](../../docs/hallazgos/)) · [corrección de la cátedra](../../docs/correccion-catedra-iteracion-1.md), respondida acción por acción en [`docs/respuesta-correccion-catedra.md`](../../docs/respuesta-correccion-catedra.md) |
| **Insumos** | [`01-base-context.md`](./01-base-context.md), [`00-requirements-draft.md`](./00-requirements-draft.md) (congelado), [`docs/adr/`](../../docs/adr/) (18 ADRs) |
| **Salidas** | [`03-plan.md`](./03-plan.md), [`04-cobertura-vc.md`](./04-cobertura-vc.md) |

> **Cómo cambia este documento.** No es inmutable, pero tampoco se edita en el
> lugar: todo cambio sube la versión, deja una fila en el *Historial de
> revisiones* del final, y pasa por el checklist de
> [`docs/revision-spec.md`](../../docs/revision-spec.md). El fundamento de cada
> decisión **no vive acá**: vive en un ADR con identificador estable, y un ADR
> aceptado no se edita, se supersede. **Lo que sí vive acá es el comportamiento
> observable que esa decisión produce**: si un ADR cambia lo que se ve en stdout,
> stderr o el exit code, ese comportamiento tiene que estar en un FR, BR o NFR de
> esta spec (regla agregada en v1.4, ver C-15).
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
>    [H-13](../../docs/hallazgos/H-13-actores-sin-trazar.md): la tabla de Actores
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
- Búsqueda literal (substring) sobre el contenido de objetos de texto (FR-1).
- Autenticación por Application Default Credentials (BR-1, FR-15).
- Guardrail de costo por cantidad de objetos (BR-2).
- Exit codes estilo `grep`, salida apta para scripting (NFR-3).
- Salida incremental: cada match se imprime en cuanto se encuentra (FR-11).

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
  ([ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md)). Su consecuencia
  observable, el orden de la salida, es FR-16.
- **Indicador de progreso explícito** (barra, contador por stderr) — el
  progreso se manifiesta como salida incremental, ver FR-11
  ([ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)).
- **Salida JSON** — solo formato estilo `grep`
  ([ADR-0007](../../docs/adr/ADR-0007-formato-de-salida.md)).
- **Providers que no son GCS** (S3, Azure Blob)
  ([ADR-0003](../../docs/adr/ADR-0003-sintaxis-ubicacion.md): el esquema `gs://` es
  obligatorio).
- **Reintentos automáticos ante fallos de red transitorios** — 0 reintentos en
  v1 (NFR-2, [ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md)).
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
| **Entorno de credenciales (ADC)** | Resuelve la identidad de quien invoca; puede **no tener credenciales** |

Los modos de falla en negrita son obligaciones: cada uno tiene que aterrizar en
un requerimiento, y la tabla *Trazabilidad actores → requerimiento* lo demuestra.
No es decoración: "no existir" estuvo declarado acá y sin cubrir desde la v1.0
hasta la v1.2, y "sin credenciales" estuvo decidido en
[ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) y sin actor ni
requerimiento hasta la v1.4.

## Tecnología y permisos mínimos

| Dependencia | Qué se usa | Permiso IAM mínimo de quien invoca |
|---|---|---|
| Google Cloud Storage | Listar los objetos de un prefijo | `storage.objects.list` sobre el bucket |
| Google Cloud Storage | Leer el contenido de un objeto | `storage.objects.get` sobre el objeto |
| Application Default Credentials | Resolver la identidad de quien invoca | — (no otorga permisos; solo identifica) |

El rol predefinido más chico que incluye los dos permisos es
`roles/storage.objectViewer`. **`gcsgrep` no necesita ningún otro permiso** y no
usa ningún otro: ni `storage.buckets.get`, ni permisos de escritura, ni de IAM
(BR-1). Con `storage.objects.list` pero sin `storage.objects.get` sobre un objeto,
la corrida sigue (FR-6); sin `storage.objects.list` sobre el bucket, aborta
(FR-14).

---

## Requerimientos funcionales

### FR-1 · Búsqueda literal sobre un prefijo

**Dado** un prefijo de GCS con al menos un objeto de texto que contiene el
patrón buscado como **substring literal** (ningún carácter del patrón tiene
significado especial: `.`, `*`, `[`, `\` y el resto se comparan tal cual),
**Cuando** la persona ejecuta `gcsgrep "<patrón>" gs://bucket/prefijo`,
**Entonces** el sistema imprime por stdout una línea por cada línea de texto
que contiene el patrón, identificando el objeto de origen, y sale con código `0`.

> **VC-1** — Con un objeto `gs://b/logs/a.txt` que contiene la línea
> `connection timeout`, `gcsgrep "timeout" gs://b/logs/` sale con código `0`,
> stdout es exactamente `gs://b/logs/a.txt:connection timeout` y stderr queda
> vacío.
>
> **VC-19** — Con un objeto `gs://b/p/a.txt` que contiene las líneas `a.b`,
> `axb` y `a*b`, `gcsgrep "a.b" gs://b/p/` imprime exactamente una línea,
> `gs://b/p/a.txt:a.b` (no `axb`), y `gcsgrep "a*b" gs://b/p/` imprime
> exactamente `gs://b/p/a.txt:a*b`. Ambas salen con código `0`.

### FR-2 · Búsqueda sin distinguir mayúsculas (`-i`)

**Dado** un objeto que contiene `"Timeout"` (con mayúscula),
**Cuando** la persona ejecuta `gcsgrep -i "timeout" gs://bucket/prefijo`,
**Entonces** el sistema lo reporta como match.

> **VC-2** — Con un objeto que contiene únicamente la línea `"Timeout error"`,
> `gcsgrep "timeout" ...` (sin `-i`) sale con código `1` (sin matches) y
> `gcsgrep -i "timeout" ...` sobre el mismo objeto sale con código `0` y
> reporta esa línea.

### FR-3 · Formato de salida con número de línea (`-n`)

**Dado** un objeto donde el patrón aparece en la línea número *k* (contando
desde `1`),
**Cuando** la persona ejecuta `gcsgrep -n "<patrón>" gs://bucket/prefijo`,
**Entonces** la línea de salida de ese match tiene exactamente el formato
`gs://<bucket>/<objeto>:<k>:<texto>`, donde `<texto>` es la línea completa del
objeto sin su terminador de línea.

> **VC-3** — Con `gs://b/p/a.txt` de 5 líneas donde solo la 3ª es
> `error: timeout`, `gcsgrep -n "timeout" gs://b/p/` sale con código `0` y stdout
> es exactamente `gs://b/p/a.txt:3:error: timeout`.

### FR-4 · Formato de salida sin número de línea

**Dado** un match encontrado,
**Cuando** la persona ejecutó `gcsgrep` **sin** `-n`,
**Entonces** la línea de salida de ese match tiene exactamente el formato
`gs://<bucket>/<objeto>:<texto>`, donde `<texto>` es la línea completa del
objeto sin su terminador de línea, y no contiene el número de línea.

> **VC-4** — Sobre el mismo objeto de VC-3, `gcsgrep "timeout" gs://b/p/` sale con
> código `0` y stdout es exactamente `gs://b/p/a.txt:error: timeout`: quitando el
> prefijo `gs://b/p/a.txt:`, lo que queda es `error: timeout` intacto, aunque
> contenga `:`, y no hay ningún número de línea.

### FR-5 · Sin resultados

**Dado** un prefijo válido y accesible donde ningún objeto contiene el patrón,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** stdout queda vacío y el sistema sale con código `1`.

> **VC-5** — Sobre un prefijo con un único objeto de texto que no contiene el
> patrón buscado, `gcsgrep` sale con código `1` y no imprime nada por stdout.

### FR-6 · Un objeto sin permiso de lectura no aborta la corrida

**Dado** un prefijo con varios objetos, donde GCS responde **permiso denegado**
al abrir uno de ellos,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema escribe por stderr una línea que contiene
`sin permiso para leer` y el URI `gs://<bucket>/<objeto>` de ese objeto, sigue
procesando el resto de los objetos, y el fallo se refleja en el exit code según
BR-3.

> **VC-6** — Con `gs://b/p/a.txt` (sin match), `gs://b/p/b.txt` (GCS responde
> permiso denegado al abrirlo) y `gs://b/p/c.txt` (contiene `x hit`),
> `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente `gs://b/p/c.txt:x hit`,
> stderr contiene una línea con `sin permiso para leer` y `gs://b/p/b.txt`, stderr
> no contiene `Traceback`, y el exit code es `2`.

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
**Entonces** el sistema rechaza la invocación con un mensaje por stderr que
contiene el esquema esperado, `gs://`, y sale con código `2`, sin intentar
ninguna llamada a GCS.

> **VC-8** — `gcsgrep "patrón" logs/` (sin esquema) y `gcsgrep "patrón" s3://b/`
> (esquema no soportado) salen ambos con código `2`, stdout vacío, un mensaje por
> stderr que contiene `gs://`, y 0 llamadas de listado.

### FR-9 · Salteo de objetos binarios

**Dado** un objeto que contiene un byte `\x00` dentro de sus **primeros 8192
bytes** (es decir, en un offset entre `0` y `8191`)
([ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md)),
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin intentar matchear contra su contenido, sin
imprimir nada de él por stdout, escribe por stderr la línea
`gcsgrep: salteado (binario): gs://<bucket>/<objeto>`, y el salteo no afecta el
exit code.

> **VC-9** — Con `gs://b/p/blob.bin` (bytes arbitrarios con un `\x00` en el offset
> `10`, y la secuencia `timeout` después) y `gs://b/p/a.txt` (contiene
> `connection timeout`), `gcsgrep "timeout" gs://b/p/` imprime por stdout
> exactamente `gs://b/p/a.txt:connection timeout`, stderr contiene exactamente
> una línea `gcsgrep: salteado (binario): gs://b/p/blob.bin`, no contiene
> `Traceback`, y el exit code es `0`. Sin `a.txt`, la misma corrida sale con `1`.
>
> **VC-20** — Límite exacto de la ventana: un objeto de texto con un `\x00` en el
> offset `8191` se saltea como binario (VC-9); el mismo objeto con el `\x00` en el
> offset `8192` y la línea `timeout` después **no** se saltea, y su línea con
> `timeout` aparece en stdout.

### FR-10 · Salteo de objetos `.gz`

**Dado** un objeto cuyo nombre termina en `.gz`,
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin abrirlo, escribe por stderr la línea
`gcsgrep: salteado (.gz): gs://<bucket>/<objeto>`, y el salteo no afecta el exit
code.

> **VC-10** — Con `gs://b/p/access.log.gz` (gzip real cuyo contenido
> descomprimido contiene `timeout`) y ningún otro objeto, `gcsgrep "timeout"
> gs://b/p/` sale con código `1`, stdout vacío, stderr contiene exactamente la
> línea `gcsgrep: salteado (.gz): gs://b/p/access.log.gz`, y el objeto se abrió
> 0 veces.

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
> primer match no requiere haber **abierto** los otros dos (se observa sobre el
> doble de prueba, que registra qué objetos se consumieron y cuándo). De punta a
> punta: si el primer objeto emite dos matches y después falla al leerse, esos dos
> matches ya salieron por stdout antes de que la corrida termine.

*Por qué VC-17 ya no habla del listado (v1.3):* BR-2 obliga a **contar** los objetos
antes de leer, y contar exige materializar el listado. Con el tope activo, emitir el
primer match sí requiere haber listado los tres. Lo que FR-11 promete —que el
contenido se lee y se emite de a uno— no cambió, y es lo que VC-17 observa ahora.
La propiedad de listado perezoso sobrevive con `--max 0`, donde no hay nada que
contar, y se verifica ahí.

### FR-12 · Bucket inexistente

**Dado** una ubicación sintácticamente válida (pasa FR-8) cuyo bucket no existe,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema escribe por stderr un mensaje que contiene el URI del
bucket (`gs://<bucket>`) y la frase `no existe`, sale con código `2`, y no lee el
contenido de ningún objeto.

*Origen:* [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md) (el CLI
no atrapa excepciones: un `NotFound: 404` escapó como traceback con exit `1`) y
[H-13](../../docs/hallazgos/H-13-actores-sin-trazar.md) (al buscar qué debería
hacer en ese caso, ningún requerimiento lo decía, aunque la tabla de Actores
declaraba desde la v1.0 que GCS "puede fallar por permisos, red, o **no
existir**").

*Por qué es un requerimiento aparte y no una extensión de otro:* FR-5 exige un
prefijo "válido y accesible" como premisa; FR-8 cubre la sintaxis, y
`gs://no-existe/` es sintácticamente correcta; FR-6 es por objeto y no aborta la
corrida, mientras que acá falla el **listado** y no hay objetos sobre los que
seguir; y NFR-2 habla de fallos de **red**, que un 404 no es — la red funcionó y
la respuesta fue explícita.

*Por qué FR-12 y FR-14 son dos requerimientos (v1.4):* hasta la v1.3 eran uno solo
("no existe **o** sin permiso"), con un Entonces que no se podía observar entero en
una sola ejecución. Partidos, cada uno tiene su Dado y su mensaje. Los mensajes
siguen siendo distintos a propósito: "no existe" manda a revisar el nombre; "sin
permiso" manda a revisar IAM.

> **VC-18** — Con un bucket inexistente, `gcsgrep "x" gs://no-existe/` sale con
> código `2`, stdout vacío, stderr contiene `gs://no-existe` y `no existe`, stderr
> no contiene `Traceback`, y se abren 0 objetos.

### FR-13 · Un objeto cuya lectura se corta por la red no aborta la corrida

**Dado** un prefijo con varios objetos, donde la lectura de uno de ellos se
interrumpe por un **error de red** (conexión cortada, timeout o error transitorio
del servidor) después de haber empezado,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los matches de ese objeto que ya se emitieron quedan en stdout, el
sistema escribe por stderr una línea que contiene `error de red al leer` y el URI
`gs://<bucket>/<objeto>`, sigue procesando el resto de los objetos, y el fallo se
refleja en el exit code según BR-3.

> **VC-21** — Con `gs://b/p/a.txt` (emite la línea `hit uno` y después su stream
> levanta un error de red) y `gs://b/p/b.txt` (contiene `hit dos`),
> `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente
> `gs://b/p/a.txt:hit uno` y `gs://b/p/b.txt:hit dos`, en ese orden; stderr
> contiene una línea con `error de red al leer` y `gs://b/p/a.txt`, no contiene
> `Traceback`, y el exit code es `2`.

### FR-14 · Sin permiso de listado sobre el bucket

**Dado** una ubicación sintácticamente válida cuyo bucket existe, pero sobre el
cual quien invoca no tiene `storage.objects.list`,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema escribe por stderr un mensaje que contiene el URI del
bucket (`gs://<bucket>`) y la frase `sin permiso`, sale con código `2`, y no lee
el contenido de ningún objeto.

> **VC-22** — Con un bucket existente sobre el que el listado devuelve permiso
> denegado, `gcsgrep "x" gs://privado/` sale con código `2`, stdout vacío, stderr
> contiene `gs://privado` y `sin permiso`, no contiene `no existe` ni `Traceback`,
> y se abren 0 objetos.

### FR-15 · Sin credenciales

**Dado** un entorno donde Application Default Credentials no resuelve ninguna
credencial,
**Cuando** la persona ejecuta `gcsgrep` con una ubicación válida,
**Entonces** el sistema escribe por stderr un mensaje que contiene
`no se encontraron credenciales` y el comando para obtenerlas,
`gcloud auth application-default login`, sale con código `2`, y no lee el
contenido de ningún objeto.

*Origen:* decidido en [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md)
("sin credenciales disponibles: mensaje claro por stderr y exit `2`") y en el índice
de [`01-base-context.md`](./01-base-context.md), sin requerimiento hasta la v1.4.
Hasta la v1.3 este caso caía en el caso genérico de NFR-3 (exit `2` sin traceback,
pero con el nombre de la excepción del SDK como mensaje).

> **VC-23** — Con el colaborador de credenciales del doble simulando "sin ADC",
> `gcsgrep "x" gs://b/p/` sale con código `2`, stdout vacío, stderr contiene
> `no se encontraron credenciales` y `gcloud auth application-default login`, no
> contiene `Traceback`, y se abren 0 objetos. Contra GCS real, es el chequeo de
> integración I-6.

### FR-16 · Orden de la salida

**Dado** un prefijo con matches en más de un objeto,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los objetos se procesan de a uno, en el orden en que GCS los devuelve
al listar (orden lexicográfico por nombre de objeto, comparando bytes UTF-8), y
stdout contiene primero todos los matches de un objeto, en orden de línea
creciente, antes de cualquier match del objeto siguiente.

*Origen:* consecuencia observable de la lectura secuencial
([ADR-0009](../../docs/adr/ADR-0009-lectura-secuencial.md)), que hasta la v1.3 vivía
solo en el ADR.

> **VC-24** — Con `gs://b/p/c.txt`, `gs://b/p/a.txt` y `gs://b/p/b.txt` sembrados
> en ese orden, cada uno con las líneas `hit 1` y `hit 2`, `gcsgrep "hit"
> gs://b/p/` sale con código `0` y stdout es exactamente, en este orden:
> `gs://b/p/a.txt:hit 1`, `gs://b/p/a.txt:hit 2`, `gs://b/p/b.txt:hit 1`,
> `gs://b/p/b.txt:hit 2`, `gs://b/p/c.txt:hit 1`, `gs://b/p/c.txt:hit 2`.

### FR-17 · Codificación de los objetos de texto

**Dado** un objeto de texto (no binario según FR-9) que contiene una secuencia de
bytes que no es UTF-8 válido,
**Cuando** se lo busca,
**Entonces** el contenido se decodifica como UTF-8 reemplazando cada secuencia
inválida por el carácter `U+FFFD` (`�`), la línea se busca y se imprime con ese
reemplazo, y el objeto **no** se saltea ni cuenta como error de lectura
([ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md)).

> **VC-25** — Con `gs://b/p/a.txt` cuyos bytes son `caf\xe9 timeout\n` (Latin-1,
> UTF-8 inválido), `gcsgrep "timeout" gs://b/p/` sale con código `0`, stdout es
> exactamente `gs://b/p/a.txt:caf� timeout`, y stderr queda vacío.

### FR-18 · Prefijo sin `/` final

**Dado** una ubicación `gs://<bucket>/<prefijo>` donde `<prefijo>` no termina en
`/`,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** se buscan todos los objetos cuyo **nombre empieza con** `<prefijo>`
como cadena, sin agregarle `/` ni interpretar carpetas
([ADR-0003](../../docs/adr/ADR-0003-sintaxis-ubicacion.md)).

> **VC-26** — Con `gs://b/logs/a.txt`, `gs://b/logs-other/b.txt` y
> `gs://b/otros/c.txt`, todos con la línea `timeout`, `gcsgrep "timeout"
> gs://b/logs` sale con código `0` y stdout es exactamente
> `gs://b/logs-other/b.txt:timeout` seguido de `gs://b/logs/a.txt:timeout` (orden
> de FR-16: `-` es anterior a `/`). `otros/c.txt` no aparece. Con
> `gs://b/logs/` (con `/`), stdout es solo `gs://b/logs/a.txt:timeout`.

### FR-19 · Objeto de 0 bytes

**Dado** un objeto de 0 bytes bajo el prefijo,
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** se trata como un objeto de texto sin líneas: no produce matches, no
se informa como salteado ni como error, y no afecta el exit code.

> **VC-27** — Con `gs://b/p/vacio.txt` (0 bytes) y `gs://b/p/a.txt` (contiene
> `timeout`), `gcsgrep "timeout" gs://b/p/` sale con código `0`, stdout es
> exactamente `gs://b/p/a.txt:timeout` y stderr queda vacío. Con solo
> `vacio.txt`, la misma corrida sale con código `1`, stdout vacío y stderr vacío.

### FR-20 · Última línea sin terminador

**Dado** un objeto cuya última línea no termina en `\n`,
**Cuando** se lo busca,
**Entonces** esa última línea se busca y se imprime igual que las demás, con su
número de línea correcto si se pidió `-n`.

> **VC-28** — Con `gs://b/p/a.txt` cuyos bytes son `uno\ndos` (sin `\n` final),
> `gcsgrep -n "dos" gs://b/p/` sale con código `0` y stdout es exactamente
> `gs://b/p/a.txt:2:dos`.

---

## Reglas de negocio

### BR-1 · Solo lectura, sin amplificación de credenciales

`gcsgrep` nunca invoca una operación de escritura, borrado o cambio de permisos
sobre GCS, y nunca usa credenciales distintas de las que ya tiene quien la
invoca (ADC). No existe un modo de "elevar" acceso. Las únicas operaciones que
invoca requieren exclusivamente `storage.objects.list` y `storage.objects.get`
(ver *Tecnología y permisos mínimos*).

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
accidente ([ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md)).
*Excepciones:* `--max 0` es una excepción explícita, decidida por quien invoca,
no un valor por defecto.

> **VC-12** — Con 1001 objetos bajo el prefijo y sin `--max`, `gcsgrep` sale con
> código `1`, no realiza ninguna lectura de contenido (0 llamadas a abrir un
> objeto), y stderr menciona la cantidad encontrada y el tope. Con `--max 0`
> sobre el mismo prefijo, si hay un match la corrida sale con código `0` y sí
> lee objetos.

### BR-3 · Precedencia de exit codes ante fallos parciales

Si ocurrió al menos un error de lectura sobre algún objeto (FR-6, FR-13), el exit
code final es **`2`**, sin importar si hubo matches en los objetos que sí se
pudieron leer. Sin errores de lectura: `0` si hubo matches, `1` si no. Los
objetos salteados (FR-9, FR-10) no son errores de lectura.

*Fundamento:* un resultado "sin matches" o "con matches" que ocurrió a pesar de
errores parciales no es un resultado confiable para un script; `2` lo señala
sin ambigüedad, igual que hace `grep` cuando un archivo no se puede abrir
([ADR-0008](../../docs/adr/ADR-0008-exit-codes.md)).
*Excepciones:* ninguna.

> **VC-13** — Con dos objetos, uno con match y otro que falla al leerse,
> `gcsgrep` imprime el match encontrado por stdout, informa el fallo por
> stderr, y sale con código `2` (no `0`).

---

## Requerimientos no funcionales

### NFR-1 · Memoria acotada por streaming

**Métrica:** pico de memoria adicional del proceso mientras lee un objeto.
**Umbral:** **< 20 MB**.
**Condición de carga:** un objeto de **200 MB** de texto, en dos condiciones:
(a) con un patrón que no aparece en ninguna línea, y (b) con un patrón que
aparece en **todas** las líneas.

Para cumplirlo, el sistema procesa cada objeto línea por línea por streaming, sin
cargar el contenido completo en memoria, **y sin acumular los matches
encontrados** (ver FR-11 y
[ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)).

> **VC-14** — Sobre un objeto simulado de **200 MB** de contenido de texto, el
> pico de memoria adicional usado por el proceso de lectura de ese objeto es
> menor a **20 MB** (medido con `tracemalloc` sobre el doble de prueba que
> expone el stream; nunca se llama a un equivalente de "leer todo el archivo"
> sobre él), en las condiciones (a) y (b). La (b) es la que hace falsable al VC:
> con acumulación de matches, el pico medido es de ~371 MB.

### NFR-2 · Política ante fallos de red: sin reintentos

**Política:** **0 reintentos automáticos**
([ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md)). Ante un error de red,
cada operación sobre GCS se intenta **una sola vez**, y el fallo se reporta según
NFR-3 (sin traceback). Hay dos condiciones, cada una con su VC:

- **(a) Al listar:** la corrida aborta con código `2` y un mensaje por stderr que
  contiene `error de red` y el URI del bucket.
- **(b) Al leer un objeto:** ese objeto no se vuelve a abrir; la corrida sigue
  según FR-13 y el exit code sale de BR-3.

> **VC-15** — Simulando que el listado inicial lanza una excepción de red,
> `gcsgrep` sale con código `2`, stdout vacío, stderr contiene `error de red` y
> `gs://<bucket>` (no la representación cruda de la excepción de la librería), y
> el listado se invocó exactamente **1** vez.
>
> **VC-29** — En el escenario de VC-21, el objeto `gs://b/p/a.txt` se abrió
> exactamente **1** vez (0 reintentos), `gs://b/p/b.txt` se abrió exactamente 1
> vez, y el exit code es `2`.

### NFR-3 · Salida apta para scripting

stdout contiene únicamente líneas de match. Todo mensaje informativo, de
error o de resumen (objetos salteados, objetos fallidos, guardrail excedido)
va a stderr. En una corrida sin salteados, sin errores y sin guardrail excedido,
stderr queda vacío. **Ningún caso de error imprime un stack trace de Python.**
Esta es la única formulación de la regla "sin traceback" en la spec; los demás
requerimientos la referencian.

**Excepción explícita, opt-in:** si quien invoca define la variable de entorno
`GCSGREP_DEBUG=1`, ante una excepción **no prevista** (el caso de VC-16 (b)) el
proceso la re-lanza: stderr contiene el traceback y el exit code es el del
intérprete (`1`). No es el comportamiento por defecto, no se activa sola, y no
aplica a los errores previstos (FR-6, FR-8, FR-12, FR-13, FR-14, FR-15, BR-2,
NFR-2), que siguen sin traceback aunque la variable esté definida. Existe para
diagnosticar un bug nuevo
([ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md)).

> **VC-16 (a)** — Para cada caso de error o salteo cubierto (VC-6, VC-8, VC-9,
> VC-10, VC-12, VC-13, VC-15, VC-18, VC-21, VC-22, VC-23), stdout no contiene
> ninguna línea que no sea un match real, y stderr no contiene la palabra
> `Traceback`.
>
> **VC-16 (b)** — Inyectando desde el colaborador de `gcs` una excepción
> **arbitraria e inesperada** (una clase que el código no conoce, levantada tanto
> al listar como al abrir un stream), la corrida sale con código `2`, stdout queda
> vacío, y stderr trae un mensaje legible sin la palabra `Traceback`.
>
> **VC-16 (c)** — Con `GCSGREP_DEBUG=1`, la misma excepción inesperada de VC-16 (b)
> se propaga fuera del programa (el proceso termina con traceback y exit `1`); y
> con `GCSGREP_DEBUG=1`, el caso de VC-18 (error previsto) sigue saliendo con
> código `2` y sin `Traceback`.

**Por qué VC-16 tiene tres partes.** NFR-3 está cuantificado universalmente
("ningún caso de error"), y una lista enumerada de casos no puede verificar eso:
todo camino de error que no esté en la lista queda libre de tirar un traceback sin
que el VC se entere. La parte (b) es la que hace falsable la promesa universal —
no se puede enumerar "todos los errores", pero sí se puede exigir que uno
**desconocido** se maneje. Es el mismo refuerzo que se le hizo a VC-14 en la v1.1,
y por la misma razón (C-8: ¿puede este VC fallar por la razón correcta?). La parte
(c) existe desde la v1.4: verifica que la única excepción a la regla sea la
declarada, y que no se filtre a los errores previstos.

Se agregó en v1.2 por [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md),
que encontró que `cli.main()` no atrapa ninguna excepción que suba de `core` o de
`gcs`: cualquier fallo del SDK escapa como traceback con exit `1` — el código que
significa "sin matches", así que un script lee un fallo total como un resultado
válido. VC-16 (a) no podía detectarlo.

### NFR-4 · Rendimiento de la búsqueda secuencial

**Métrica:** tasa de procesamiento de punta a punta del proceso `gcsgrep` (desde
`argv` hasta el exit code, con stdout redirigido a `/dev/null`), con el contenido
servido desde memoria por el doble de prueba, para medir el costo propio de la
herramienta y no la latencia de la red
([ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md)).
**Condición de carga:** un único objeto de **100 MiB** de texto, con líneas de
**80 bytes** (~1,3 millones de líneas), lectura secuencial.
**Umbrales:**

- **(a) Patrón ausente:** **≥ 50 MiB/s** de contenido recorrido.
- **(b) Patrón en todas las líneas:** **≥ 50 000 matches/s** emitidos por stdout.

> **VC-30** — Corriendo `cli.main` sobre el objeto de la condición de carga, con
> stdout a `/dev/null` y tomando la mejor de 3 corridas: en la condición (a) la
> tasa es ≥ 50 MiB/s, y en la (b) la tasa es ≥ 50 000 matches/s con exit `0`. El
> umbral (a) discrimina: una implementación que lee el stream de a un carácter
> procesa ~15 MiB/s y falla.

---

## VC de punta a punta contra GCS real

Los VCs de arriba se ejercitan contra dobles de prueba, y la verificación de
integración contra el emulador `floci-gcp` (chequeos I-1…I-7 de
[`docs/integracion-gcs.md`](../../docs/integracion-gcs.md)). Ninguno de los dos
ejercita ADC, IAM ni la red reales. Este VC sí, y **no acepta un doble ni un
emulador como evidencia**.

> **VC-31** — Contra un bucket de **GCS real**, con ADC real de una identidad que
> tiene exactamente `roles/storage.objectViewer` sobre el bucket, y las fixtures
> de `docs/integracion-gcs.md` sembradas: (1) `gcsgrep -n "timeout"
> gs://$BUCKET/logs/` sale con `0` y stdout es exactamente
> `gs://$BUCKET/logs/a.txt:2:connection timeout after 30s`; (2)
> `gcsgrep "no-existe-esto" gs://$BUCKET/logs/` sale con `1` y stdout vacío;
> (3) `gcsgrep "x" gs://gcsgrep-test-no-existe-jamas/` sale con `2` y stderr
> contiene `no existe`; en las tres, stderr no contiene `Traceback`. Recorre la
> cadena completa: argumentos → ADC → listado → streaming → match → salida →
> exit code. Cubre FR-1, FR-3, FR-5, FR-12, BR-1 y NFR-3.

Su ejecución está sujeta a
[ADR-0015](../../docs/adr/ADR-0015-verificacion-real-declinada.md): el VC está
especificado y su estado vive, como el de todos, en
[`04-cobertura-vc.md`](./04-cobertura-vc.md). Especificar un VC que todavía no se
ejecutó es una afirmación distinta de no tenerlo, y esta spec no las mezcla.

---

## Tabla de trazabilidad · requerimiento → VC

| Requerimiento | VC | Camino |
|---|---|---|
| FR-1 | VC-1, VC-19, VC-31 | feliz · borde (metacaracteres) · punta a punta real |
| FR-2 | VC-2 | feliz |
| FR-3 | VC-3, VC-31 | feliz · punta a punta real |
| FR-4 | VC-4 | feliz |
| FR-5 | VC-5, VC-31 | borde (sin resultados) |
| FR-6 | VC-6 | falla parcial (permiso de objeto) |
| FR-7 | VC-7 | borde (bucket completo) |
| FR-8 | VC-8 | falla (input inválido) |
| FR-9 | VC-9, VC-20 | borde (binario) · límite exacto |
| FR-10 | VC-10 | borde (.gz) |
| FR-11 | VC-17 | invariante (observabilidad) |
| FR-12 | VC-18, VC-31 | falla (bucket inexistente) |
| FR-13 | VC-21 | falla parcial (red a mitad de lectura) |
| FR-14 | VC-22 | falla (sin permiso de listado) |
| FR-15 | VC-23 | falla (sin credenciales) |
| FR-16 | VC-24 | invariante (orden) |
| FR-17 | VC-25 | borde (codificación) |
| FR-18 | VC-26 | borde (prefijo ambiguo) |
| FR-19 | VC-27 | borde (0 bytes) |
| FR-20 | VC-28 | borde (último elemento sin terminador) |
| BR-1 | VC-11, VC-31 | invariante |
| BR-2 | VC-12 | guardrail |
| BR-3 | VC-13 | invariante |
| NFR-1 | VC-14 (a), VC-14 (b) | medición |
| NFR-2 | VC-15 (al listar), VC-29 (al leer) | falla |
| NFR-3 | VC-16 (a), (b), (c) | invariante |
| NFR-4 | VC-30 (a), (b) | medición |

**27 requerimientos (20 FR, 3 BR, 4 NFR), 31 VCs, 0 huérfanos.** Cada condición
enumerada en un NFR tiene su propio VC o su propia parte de VC.

## Tabla de trazabilidad · borrador → spec

La tabla de arriba prueba que ningún requerimiento de esta spec quedó sin VC.
Esta prueba lo otro, que es lo que faltaba en v1.0: que ningún ítem del
[borrador](./00-requirements-draft.md) quedó sin destino. Los dos huérfanos que
encontró la revisión (FR-g y NFR-a) están marcados con su resolución.

| Ítem del borrador | Destino | Dónde |
|---|---|---|
| FR-a · patrón + ubicación, busca dentro de los objetos | FR-1 (literal), FR-16 (orden), FR-17…FR-20 (bordes de contenido y ubicación) | Iteración 1 (comportamiento) · Iteración 2 (VCs nuevos de v1.4) |
| FR-b · bucket completo o prefijo | FR-7, FR-18 | Iteración 1 |
| FR-c · salida deja claro el objeto, y la línea si se puede | FR-4 (sin `-n`) + FR-3 (con `-n`) | Iteración 1 |
| FR-d · búsqueda sin distinguir mayúsculas | FR-2 | Iteración 1 |
| FR-e · avisar "no encontré nada" de forma detectable por un script | FR-5 (exit `1`) | Iteración 1 |
| FR-f · un objeto ilegible no tira la corrida | FR-6 (permiso) + FR-13 (red) | Iteración 2 |
| FR-g · notar el progreso con muchos objetos | **FR-11** — resuelto en v1.1, [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md). Era huérfano en v1.0 (hallazgo H-1) | Iteración 1 |
| BR-a? · nunca escribe en GCS | BR-1 | Iteración 1 (adelantada) |
| BR-b? · no amplía el acceso del invocador | BR-1 (fusionado) + permisos mínimos + [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) | Iteración 1 (adelantada) |
| BR-c? · límite para no escanear un bucket enorme | BR-2, con tope decidido en objetos ([ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md)) | Iteración 1 (adelantada) |
| BR-d? · saltear lo que no es texto | FR-9, FR-10 (es comportamiento observable, no regla de negocio) + [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md), [ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md) | Iteración 2 |
| NFR-a · rendimiento | **NFR-4** desde v1.4, [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) (supersede a ADR-0012, que lo había declinado). Fue huérfano en v1.0 (H-2) y declinado de v1.1 a v1.3 | Iteración 2 |
| NFR-b · memoria con objetos grandes | NFR-1, umbral 20 MB sobre 200 MB | Iteración 1 |
| NFR-c · comportamiento ante fallos de red | NFR-2 (0 reintentos, [ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md)) + FR-13 | Iteración 2 |

**14 ítems del borrador, 14 con destino explícito, 0 perdidos.**

Tres notas sobre la forma de esta tabla:

- **FR-c se abrió en dos.** El borrador metía dos comportamientos en una línea
  ("el objeto, y la línea si se puede"). Un FR por comportamiento — y desde la
  v1.4, un FR por formato.
- **FR-f se abrió en dos en la v1.4.** "Ilegible" tenía dos causas con dos
  observables distintos (permiso denegado al abrir, red que se corta a mitad).
- **BR-a? y BR-b? se fusionaron.** Son la misma invariante vista de dos lados:
  no escribir y no elevar privilegios. Un solo BR con un solo VC.

## Tabla de trazabilidad · actores → requerimiento

Las dos tablas de arriba cubren los requerimientos que existen y los ítems del
borrador. Esta cubre la tercera fuente de obligaciones, que no estaba vigilada por
ninguna de las dos: **los modos de falla declarados en la tabla de Actores.**

Se agregó en v1.2 por [H-13](../../docs/hallazgos/H-13-actores-sin-trazar.md), que
encontró uno declarado desde la v1.0 y nunca cubierto.

| Actor | Modo de falla declarado | Requerimiento que lo cubre | VC |
|---|---|---|---|
| GCS | **Permisos** — sobre un objeto puntual | FR-6 (informa y sigue) + BR-3 (exit `2`) | VC-6, VC-13 |
| GCS | **Permisos** — sobre el listado del bucket | **FR-14** (mensaje distinto del de "no existe") | VC-22 |
| GCS | **Red** — al leer un objeto | FR-13 + NFR-2 (b) + BR-3 | VC-21, VC-29, VC-13 |
| GCS | **Red** — al listar | NFR-2 (a) (aborta con `2`, sin traceback) | VC-15 |
| GCS | **No existir** — el bucket | **FR-12** — *era el huérfano de H-13* | VC-18 |
| GCS | **No existir** — el prefijo (0 objetos) | FR-5 (exit `1`, es un resultado válido, no un error) | VC-5 |
| Entorno de credenciales | **Sin credenciales** | **FR-15** — nuevo en v1.4 | VC-23 |
| Persona usuaria | Ubicación mal escrita | FR-8 (exit `2` sin tocar la red) | VC-8 |
| Persona usuaria | Prefijo gigante, corrida costosa | BR-2 (guardrail, tope 1000) | VC-12 |
| Script | Necesita decidir sin parsear texto | FR-5, BR-3, NFR-3 (exit codes + stdout limpio) | VC-5, VC-13, VC-16 |
| Script | Necesita una salida reproducible | FR-16 (orden del listado) | VC-24 |

**11 modos de falla declarados, 11 cubiertos, 0 huérfanos.**

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
[ADR-0001 … ADR-0010](../../docs/adr/), y desde la v1.4 cada una tiene además su
comportamiento observable escrito en un requerimiento de esta spec:

| # | Pregunta | Requerimiento | ADR |
|---|---|---|---|
| 1 | Sabor de regex | FR-1 (substring literal), VC-19 | ADR-0001 |
| 2 | Autenticación | BR-1, FR-15 (sin credenciales → exit `2`) | ADR-0002 |
| 3 | Sintaxis de la ubicación | FR-7, FR-8, FR-18 (prefijo sin `/`) | ADR-0003 |
| 4 | Flags de `grep` | FR-2, FR-3, FR-4, BR-2 | ADR-0004 |
| 5 | Binarios y `.gz` | FR-9 (ventana de 8192 bytes), FR-10, FR-17 | ADR-0005, ADR-0018 |
| 6 | Guardrail de costo | BR-2 | ADR-0006 |
| 7 | Formato de salida | FR-3, FR-4 | ADR-0007 |
| 8 | Exit codes | FR-5, FR-8, BR-3 | ADR-0008 |
| 9 | Concurrencia | FR-16 (orden del listado) | ADR-0009 |
| 10 | Objeto modificado durante la lectura | Fuera (riesgo aceptado) | ADR-0010 |

Los dos huérfanos que encontró la revisión v1.1 se resolvieron como ADR-0011
(FR-11) y ADR-0012, hoy superseded por ADR-0017 (NFR-4).

## Qué sigue

- Plan de iteraciones: [`03-plan.md`](./03-plan.md).
- Estado de verificación (única fuente de verdad sobre qué VC pasa):
  [`04-cobertura-vc.md`](./04-cobertura-vc.md).

## Historial de revisiones

| Versión | Fecha | Cambio | Origen |
|---|---|---|---|
| 1.0 | 2026-09-23 | Primera spec a partir del base context. 16 FR/BR/NFR, 16 VCs. | paso Especificar |
| 1.1 | 2026-09-23 | **+FR-11/VC-17** (salida incremental, resuelve FR-g). **NFR-a declinado** con fundamento en vez de quedar pendiente. **VC-14 reforzado** con el caso donde todo matchea. Fundamento movido a ADRs; la spec los referencia. Nueva tabla borrador → spec. Encabezado versionado. | [`docs/revision-spec.md`](../../docs/revision-spec.md), hallazgos H-1, H-2, H-3, H-5, H-7, H-8 |
| 1.2 | 2026-09-23 | **VC-16 partido en (a) y (b)**: la parte universal de NFR-3 pasa a ser falsable con una excepción inesperada, porque `cli` no atrapaba ninguna y VC-16 solo miraba una lista cerrada. **+FR-12/VC-18** (bucket inexistente o inaccesible → exit `2`, mensaje que distingue "no existe" de "sin permiso"). **Tercera regla estructural** y su **tabla de trazabilidad actores → requerimiento**. Modos de falla de la tabla de Actores marcados como obligaciones. | [H-12](../../docs/hallazgos/H-12-sin-frontera-de-excepciones.md), [H-13](../../docs/hallazgos/H-13-actores-sin-trazar.md) |
| 1.3 | 2026-09-24 | **VC-17 acotado**: afirma que el primer match se emite sin haber *abierto* el resto, no sin haberlo *listado*. Consecuencia de implementar BR-2 (contar obliga a materializar el listado), anticipada por el plan. FR-11 no cambió. | [ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md), nota de regresión del plan |
| 1.4 | 2026-10-01 | **Corrección de la cátedra (NEEDS WORK).** FRs atómicos: **FR-3/FR-4** pasan a ser un formato cada uno (con y sin `-n`); **FR-6** queda en permiso denegado y la red a mitad de lectura pasa a **FR-13**; **FR-12** queda en bucket inexistente y el permiso de listado pasa a **FR-14**. **NFR-1** con métrica, umbral y condición en el enunciado. **+NFR-4** de rendimiento (ADR-0017 supersede a ADR-0012). **NFR-2** reescrito como política de 0 reintentos (ADR-0016) con un VC por condición (+VC-29). Decisiones de ADRs que llegan a la spec: patrón literal (FR-1/VC-19), sin credenciales (**FR-15**), orden de salida (**FR-16**), prefijo sin `/` (**FR-18**), `GCSGREP_DEBUG` como excepción explícita de NFR-3 (VC-16 (c)). Bordes nuevos: codificación (**FR-17**), 0 bytes (**FR-19**), última línea sin `\n` (**FR-20**), ventana binaria de 8192 bytes (FR-9/VC-20, ADR-0018). VCs concretos en lugar de "stderr menciona" (VC-1, VC-3, VC-4, VC-6, VC-8, VC-9, VC-10). Permisos IAM mínimos. **+VC-31** de punta a punta contra GCS real. Regla "sin traceback" solo en NFR-3. +Actor *Entorno de credenciales*. | [corrección de la cátedra](../../docs/correccion-catedra-iteracion-1.md), [respuesta acción por acción](../../docs/respuesta-correccion-catedra.md) |

**Qué cambió del contrato en v1.4.** Mucho texto y poco comportamiento ya
entregado. Lo que la Iteración 1 produce hoy **no cambia** para FR-1…FR-5, FR-7,
FR-8, FR-11, FR-12, FR-14, FR-16, FR-18, FR-19, FR-20, BR-1, BR-2, NFR-1 y
NFR-3: esos requerimientos ahora **dicen** lo que el código ya hacía (y lo que los
ADRs ya decidían), y sus VCs nuevos o más concretos se ejercitan al empezar la
Iteración 2. Cambian el comportamiento observable, y por eso son alcance de la
Iteración 2: **FR-15** (el mensaje sin credenciales deja de ser el genérico),
**FR-17** (bytes no UTF-8 dejan de abortar la corrida), y lo que ya estaba
planificado para esa iteración (FR-6, FR-9, FR-10, FR-13, BR-3, NFR-2). **NFR-4**
es un umbral nuevo sobre comportamiento existente: se mide al empezar la
Iteración 2, y si el código no lo cumple, es un defecto de esa iteración.

**Qué cambió del contrato en v1.3.** VC-17 deja de afirmar que el primer match se
emite sin haber *listado* el resto del prefijo, y afirma que se emite sin haberlo
*abierto*. Es una consecuencia de implementar BR-2, que el plan había anticipado
como nota de regresión: contar objetos obliga a materializar el listado. FR-11 no
cambió. Ningún otro VC se toca.

**Qué cambió del contrato en v1.2.** Nada de lo que la Iteración 1 producía
*correctamente*. Los casos que FR-12 y VC-16 (b) cubren hoy terminan en traceback
con exit `1`, que no era un comportamiento prometido por nadie — al contrario, NFR-3
ya prometía lo opuesto. Pasan a exit `2` con mensaje legible. No es una regresión
ni rompe ningún VC existente: son huecos del contrato y de su verificación que se
cierran.

**Cambio de contrato anunciado para la Iteración 2:** BR-3 hace que un error de
lectura parcial fuerce exit `2` aunque haya matches. Eso sí cambia el resultado
observable de corridas que la Iteración 1 ya puede producir. Cuando se implemente,
va en una fila nueva de este historial, no en una edición muda. *No se le asigna
número de versión por adelantado:* este anuncio ya se renumeró dos veces porque
otras enmiendas llegaron primero, y el compromiso no depende del número.

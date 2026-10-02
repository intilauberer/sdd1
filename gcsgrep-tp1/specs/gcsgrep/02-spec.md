# gcsgrep — spec

| | |
|---|---|
| **Versión** | 1.7 |
| **Estado** | habilitada; cierra las excepciones registradas de la revisión de la v1.5 (Iteración 2b, ver el *Historial*) |
| **Fecha** | 2026-10-02 |
| **Revisada por** | [`docs/revision-spec.md`](../../docs/revision-spec.md) — checklist C-1…C-19, 16 hallazgos ([`docs/hallazgos/`](../../docs/hallazgos/)) · [corrección de la cátedra](../../docs/correccion-catedra-iteracion-1.md), respondida acción por acción en [`docs/respuesta-correccion-catedra.md`](../../docs/respuesta-correccion-catedra.md) · [revisión de la v1.4](../../revisiones/spec-v1.4-2026-10-01.md) (NEEDS WORK, 21 acciones) · [revisión de la v1.5](../../revisiones/spec-v1.5-2026-10-01.md) (NEEDS WORK, 2 MUST resueltos en v1.6, el resto registrado como excepción) |
| **Insumos** | [`01-base-context.md`](./01-base-context.md), [`00-requirements-draft.md`](./00-requirements-draft.md) (congelado), [`docs/adr/`](../../docs/adr/) (28 ADRs) |
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
  Se aceptan exactamente: `-i`, `-n`, `--ignore-case`, `--line-number` (formas
  largas equivalentes de `-i` y `-n`), `--max N` y `--max=N`, `-h` y `--help`, flags
  cortos agrupados (`-in`) y `--` para terminar las opciones. Las abreviaturas de
  opciones largas (`--ig`) **se rechazan**. Un patrón que empieza con `-` se pasa
  después de `--` (`gcsgrep -- -x gs://b/p/`). `-h`/`--help` imprime la ayuda por
  stdout y sale con código `0` sin tocar GCS (FR-30): es la única invocación cuyo
  stdout no son líneas de match (NFR-3). Cualquier otra invocación que no respete
  esta forma se rechaza (FR-25).
- Búsqueda literal (substring) sobre el contenido de objetos de texto (FR-1).
- Autenticación por Application Default Credentials (BR-1, FR-15, FR-26, FR-28).
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
  aceptado ([ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md)). El objeto
  **borrado** entre el listado y la lectura no es este riesgo: es FR-21.
- **Escritura, borrado o modificación de cualquier objeto o permiso en GCS** —
  la herramienta es de solo lectura, siempre (BR-1).

## Actores

| Actor | Descripción |
|---|---|
| **Persona usuaria** | Ejecuta `gcsgrep` en una shell y lee la salida en pantalla |
| **Script** | Ejecuta `gcsgrep` y decide en base al exit code, no al texto de salida; puede cortar la salida antes del final (`\| head`) |
| **GCS** | Fuente de los objetos; puede fallar por **permisos**, **red**, **no existir**, u **otra respuesta de error** |
| **Entorno de credenciales (ADC)** | Resuelve la identidad de quien invoca; puede **no tener credenciales** o tener **credenciales inutilizables** |

Los modos de falla en negrita son obligaciones: cada uno tiene que aterrizar en
un requerimiento, y la tabla *Trazabilidad actores → requerimiento* lo demuestra.
No es decoración: "no existir" estuvo declarado acá y sin cubrir desde la v1.0
hasta la v1.2, "sin credenciales" estuvo decidido en
[ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) y sin actor ni
requerimiento hasta la v1.4, y "no existir" **de un objeto listado** quedó sin
requerimiento en la v1.4, al partir FR-6
([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)).

## Tecnología y permisos mínimos

| Dependencia | Qué se usa | Permiso IAM mínimo de quien invoca |
|---|---|---|
| Google Cloud Storage | Listar los objetos de un prefijo | `storage.objects.list` sobre el bucket |
| Google Cloud Storage | Leer el contenido de un objeto | `storage.objects.get` sobre el objeto |
| Application Default Credentials | Resolver la identidad de quien invoca | — (no otorga permisos; solo identifica) |

**Runtime y librería (v1.7, [ADR-0027](../../docs/adr/ADR-0027-piso-de-python-y-plataforma.md)):**
Python **3.10 o más nuevo**, sobre una plataforma **POSIX** (Linux, macOS);
`google-cloud-storage` **2.14 o más nuevo**. Cada objeto se lee a través del lector
de la librería (`blob.open`) con bloques de **1 MiB**
([ADR-0020](../../docs/adr/ADR-0020-tamano-de-bloque-del-lector.md), NFR-1), sin
reintentos de la librería y con un timeout de **60 s** por pedido HTTP
([ADR-0028](../../docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md),
NFR-2).

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

**Dado** un objeto con una línea que contiene el patrón con otras mayúsculas
(por ejemplo `"Timeout"` para el patrón `"timeout"`),
**Cuando** la persona ejecuta `gcsgrep -i "<patrón>" gs://bucket/prefijo`,
**Entonces** el sistema reporta esa línea como match. La comparación se hace
después de pasar el patrón y la línea a minúsculas con la conversión completa de
Unicode, **incluidas sus reglas contextuales** —la de `str.lower()` de Python—:
`Á` → `á`, `Ñ` → `ñ`, `İ` → `i̇`, y la `Σ` al final de una palabra → `ς`. No es un
plegado (`casefold`): `ß` no equivale a `ss`. La línea se imprime con sus
mayúsculas originales. Fundamento:
[ADR-0023](../../docs/adr/ADR-0023-plegado-de-mayusculas.md).

> **VC-2** — Con un objeto que contiene únicamente la línea `"Timeout error"`,
> `gcsgrep "timeout" ...` (sin `-i`) sale con código `1` (sin matches) y
> `gcsgrep -i "timeout" ...` sobre el mismo objeto sale con código `0` y
> reporta esa línea.
>
> **VC-43** — Con `gs://b/p/a.txt` cuya única línea es `Árbol caído`,
> `gcsgrep -i "árbol" gs://b/p/` sale con código `0`, stdout es exactamente
> `gs://b/p/a.txt:Árbol caído` y stderr queda vacío; `gcsgrep "árbol" gs://b/p/`
> (sin `-i`) sale con código `1` y stdout vacío. Regla contextual (v1.7): con
> `gs://b/p/g.txt` cuya única línea es `ΟΔΟΣ`, `gcsgrep -i "σ" gs://b/p/g.txt` sale
> con código `1` (la `Σ` final pasa a `ς`), y `gcsgrep -i "ς" gs://b/p/g.txt` sale
> con código `0`.

### FR-3 · Formato de salida con número de línea (`-n`)

**Dado** un objeto donde el patrón aparece en la línea número *k* (contando
desde `1`),
**Cuando** la persona ejecuta `gcsgrep -n "<patrón>" gs://bucket/prefijo`,
**Entonces** la línea de salida de ese match tiene exactamente el formato
`gs://<bucket>/<objeto>:<k>:<texto>`, donde `<texto>` es la línea completa del
objeto sin su terminador de línea (qué es una línea y qué es su terminador: FR-22).

> **VC-3** — Con `gs://b/p/a.txt` de 5 líneas donde solo la 3ª es
> `error: timeout`, `gcsgrep -n "timeout" gs://b/p/` sale con código `0` y stdout
> es exactamente `gs://b/p/a.txt:3:error: timeout`.

### FR-4 · Formato de salida sin número de línea

**Dado** un match encontrado,
**Cuando** la persona ejecutó `gcsgrep` **sin** `-n`,
**Entonces** la línea de salida de ese match tiene exactamente el formato
`gs://<bucket>/<objeto>:<texto>`, donde `<texto>` es la línea completa del
objeto sin su terminador de línea (FR-22), y no contiene el número de línea.

> **VC-4** — Sobre el mismo objeto de VC-3, `gcsgrep "timeout" gs://b/p/` sale con
> código `0` y stdout es exactamente `gs://b/p/a.txt:error: timeout`: quitando el
> prefijo `gs://b/p/a.txt:`, lo que queda es `error: timeout` intacto, aunque
> contenga `:`, y no hay ningún número de línea.

### FR-5 · Sin resultados

**Dado** un prefijo válido y accesible donde ningún objeto contiene el patrón,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** stdout queda vacío y el sistema sale con código `1`.

> **VC-5** — Sobre un prefijo con un único objeto de texto que no contiene el
> patrón buscado, `gcsgrep` sale con código `1` y no imprime nada por stdout. Con
> un prefijo sin ningún objeto (listado vacío), la misma corrida sale con código
> `1`, stdout vacío y stderr vacío (v1.7).

### FR-6 · Un objeto sin permiso de lectura no aborta la corrida

**Dado** un prefijo con varios objetos, donde GCS responde **permiso denegado**
sobre uno de ellos (`403`, o `401` sobre un objeto: ver abajo) al abrirlo o durante
la lectura,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los matches de ese objeto que ya se emitieron quedan en stdout, el
sistema escribe por stderr una línea que contiene `sin permiso para leer` y el URI
`gs://<bucket>/<objeto>` de ese objeto, sigue procesando el resto de los objetos, y
el fallo se refleja en el exit code según BR-3.

**Al abrir** un objeto (definición única, v1.7; FR-13, FR-21 y FR-29 la usan) es
antes de que entregue su primer byte. Con la librería cliente, la apertura es
perezosa y el `403`/`404` llega en la primera lectura: eso **es** "al abrir".

> **VC-6** — Con `gs://b/p/a.txt` (sin match), `gs://b/p/b.txt` (GCS responde
> permiso denegado al abrirlo, sea en la apertura o en su primera lectura) y
> `gs://b/p/c.txt` (contiene `x hit`),
> `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente `gs://b/p/c.txt:x hit`,
> stderr contiene una línea con `sin permiso para leer` y `gs://b/p/b.txt`, stderr
> no contiene `Traceback`, y el exit code es `2`.

*Un `401` sobre un objeto (v1.6):* si GCS ya aceptó el listado y responde `401` al
abrir o leer un objeto, después de haber leído otros, se trata como este FR (línea
con `sin permiso para leer` + URI, sigue, BR-3), no como FR-28: la corrida ya
demostró que las credenciales sirven, y abortar tiraría los objetos que faltan.
**Desde la v1.7, lo mismo vale para un *refresh* de token rechazado sobre un
objeto**, que es la forma en que llega ese `401` cuando el token vence entre dos
objetos ([ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md)).

*Los cuatro caminos de un objeto que no se puede leer (v1.5; el cuarto, v1.7):* GCS
responde **permiso denegado** (FR-6), **no encontrado** (FR-21), la apertura o la
lectura fallan por un **error de red** (FR-13, con la definición de NFR-2), o GCS
responde **otro `4xx`** (FR-29). Los cuatro valen al abrir o durante la lectura;
cada uno tiene su Dado y su mensaje; ninguno aborta la corrida, y los cuatro fuerzan
exit `2` por BR-3. La tabla completa está en
[ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md). Hasta la v1.3 los tres eran "ilegible" en un solo FR-6;
al partirlo en la v1.4 el segundo y la mitad "al abrir" del tercero quedaron sin
requerimiento ([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)).

### FR-7 · Bucket completo (prefijo vacío)

**Dado** `gs://bucket/` o `gs://bucket` sin prefijo adicional,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema busca sobre todos los objetos del bucket, tratando el
prefijo como cadena vacía.

> **VC-7** — Con `gs://b/a/x.txt` (contiene `hit a`) y `gs://b/b/y.txt` (contiene
> `hit b`), `gcsgrep "hit" gs://b/` y `gcsgrep "hit" gs://b` (sin `/`) salen ambos
> con código `0`, stdout es exactamente `gs://b/a/x.txt:hit a` seguido de
> `gs://b/b/y.txt:hit b`, y stderr queda vacío.

### FR-8 · Rechazo de ubicaciones inválidas

**Dado** un argumento de ubicación que no es una ubicación
`gs://<bucket>[/<prefijo>]` válida —no empieza con `gs://` (`logs/`, `s3://b/`), o
empieza con `gs://` pero no tiene nombre de bucket (`gs://`, `gs:///p`)—,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema rechaza la invocación con un mensaje por stderr que
contiene la forma esperada, `gs://`, y sale con código `2`, sin intentar
ninguna llamada a GCS.

*Por qué `gs://` sin bucket está acá y no en FR-25 (v1.7):* hasta la v1.6 los dos FRs
se repartían ese caso, con dos mensajes posibles. Es una ubicación inválida, igual
que `logs/`, y lleva el mismo mensaje.

> **VC-8** — `gcsgrep "patrón" logs/` (sin esquema) y `gcsgrep "patrón" s3://b/`
> (esquema no soportado) salen ambos con código `2`, stdout vacío, un mensaje por
> stderr que contiene `gs://`, y 0 llamadas de listado.
>
> **VC-39** (reubicado desde FR-25 en la v1.7) — `gs://` sin bucket:
> `gcsgrep "x" gs://` y `gcsgrep "x" gs:///p` salen ambos con código `2`, stdout
> vacío, stderr contiene `gs://` y no contiene `Traceback`, y 0 llamadas de
> listado.

### FR-9 · Salteo de objetos binarios

**Dado** un objeto que contiene un byte `\x00` dentro de sus **primeros 8192
bytes** (es decir, en un offset entre `0` y `8191`)
([ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md)),
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin intentar matchear contra su contenido, sin
imprimir nada de él por stdout, y escribe por stderr la línea
`gcsgrep: salteado (binario): gs://<bucket>/<objeto>` en el momento del salteo,
antes de procesar el objeto siguiente. Es la única línea que el salteo produce:
**no hay resumen final** de salteados. El salteo no es un error de lectura (BR-3).

*Límite explícito de la ventana:* un `\x00` en el offset `8192` o posterior no
cambia la clasificación. El objeto se busca como texto, el `\x00` es un carácter
más de su línea, y si esa línea tiene match **sale tal cual por stdout**, con el
byte `0x00` incluido. Es la única forma en que un `\x00` llega a stdout, y no
contradice NFR-3: es una línea de match
([ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md)).

*Por qué una línea por objeto y no un resumen:* decidido en
[ADR-0021](../../docs/adr/ADR-0021-avisos-de-salteo-por-objeto.md), que desde la
v1.7 supersede a [ADR-0005](../../docs/adr/ADR-0005-binarios-y-gz.md) (hasta la
v1.6 era un desvío anotado en `docs/adr/README.md`).

*Lectura cortada dentro de la ventana (v1.7):* si leer el objeto falla antes de
completar los 8192 bytes y no se vio ningún `\x00`, las líneas completas ya leídas
se buscan como texto y después se informa el fallo (FR-6, FR-13, FR-21 o FR-29); si
ya se vio un `\x00`, el objeto se informa como salteado (binario) y no como error
([ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md)).

> **VC-9** — Con `gs://b/p/blob.bin` (bytes arbitrarios con un `\x00` en el offset
> `10`, y la secuencia `timeout` después) y `gs://b/p/a.txt` (contiene
> `connection timeout`), `gcsgrep "timeout" gs://b/p/` imprime por stdout
> exactamente `gs://b/p/a.txt:connection timeout`, stderr es **exactamente** la
> línea `gcsgrep: salteado (binario): gs://b/p/blob.bin` (ninguna otra línea, ni
> antes ni después), y el exit code es `0`. Sin `a.txt`, la misma corrida sale con
> `1`, stdout vacío y el mismo stderr.
>
> **VC-20** — Límite exacto de la ventana, en dos corridas:
> (1) con `gs://b/p/a.bin` cuyos bytes son 8191 × `a`, un `\x00` (offset `8191`)
> y `\ntimeout\n`, `gcsgrep -n "timeout" gs://b/p/` sale con código `1`, stdout
> vacío, y stderr es exactamente `gcsgrep: salteado (binario): gs://b/p/a.bin`;
> (2) con `gs://b/p/a.txt` cuyos bytes son 8191 × `a`, `\n` (offset `8191`), un
> `\x00` (offset `8192`, primer byte de la línea 2) y ` timeout\n`,
> `gcsgrep -n "timeout" gs://b/p/` sale con código `0`, stdout es exactamente los
> bytes `gs://b/p/a.txt:2:` + `\x00` + ` timeout` + `\n` (el `\x00` está en la
> misma línea que `timeout` y sale tal cual), y stderr queda vacío.

### FR-10 · Salteo de objetos `.gz`

**Dado** un objeto cuyo nombre termina en `.gz`,
**Cuando** se lo encuentra durante la búsqueda,
**Entonces** el sistema lo saltea sin abrirlo y escribe por stderr la línea
`gcsgrep: salteado (.gz): gs://<bucket>/<objeto>` en el momento del salteo, antes
de procesar el objeto siguiente, sin resumen final (igual que FR-9). El salteo no
es un error de lectura (BR-3).

> **VC-10** — Con `gs://b/p/access.log.gz` (gzip real cuyo contenido
> descomprimido contiene `timeout`) y ningún otro objeto, `gcsgrep "timeout"
> gs://b/p/` sale con código `1`, stdout vacío, stderr es **exactamente** la
> línea `gcsgrep: salteado (.gz): gs://b/p/access.log.gz` (ninguna otra), y el
> objeto se abrió 0 veces.

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

### FR-13 · Un objeto que no se puede leer entero por un error de red no aborta la corrida

**Dado** un prefijo con varios objetos, donde uno de ellos no se puede leer entero
por un **error de red** (definido en NFR-2),
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los matches de ese objeto que ya se emitieron (ninguno, si falló al
abrirlo) quedan en stdout, el sistema escribe por stderr una línea que contiene
`error de red al leer` y el URI `gs://<bucket>/<objeto>`, sigue procesando el resto
de los objetos, y el fallo se refleja en el exit code según BR-3.

*Por qué "al abrirlo o durante la lectura" es una sola situación (v1.5):* el Dado
es "el objeto no se pudo leer entero por un error de red", y el Entonces es el
mismo en los dos momentos; lo único que cambia es cuántos matches alcanzaron a
salir, que el Entonces ya cuenta. Hasta la v1.4 el Dado decía "después de haber
empezado" y listaba tres causas ("conexión cortada, timeout o error transitorio
del servidor"); la lista se reemplazó por la definición única de NFR-2, y el fallo
al abrir, que no tenía requerimiento, se cubre con VC-33
([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)).

> **VC-21** — Con `gs://b/p/a.txt` (emite la línea `hit uno` y después su stream
> levanta un error de red) y `gs://b/p/b.txt` (contiene `hit dos`),
> `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente
> `gs://b/p/a.txt:hit uno` y `gs://b/p/b.txt:hit dos`, en ese orden; stderr
> contiene una línea con `error de red al leer` y `gs://b/p/a.txt`, no contiene
> `Traceback`, y el exit code es `2`.
>
*Los dos momentos (v1.7):* al abrirlo (definición en FR-6) lo ejercita VC-33, y
durante la lectura VC-21.

> **VC-33** — Red caída **al abrir**: con `gs://b/p/a.txt` (abrirlo levanta un
> error de red antes de entregar ningún byte) y `gs://b/p/b.txt` (contiene
> `hit dos`), `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente
> `gs://b/p/b.txt:hit dos` (0 líneas de `a.txt`); stderr contiene una línea con
> `error de red al leer` y `gs://b/p/a.txt`, no contiene `Traceback`; el exit code
> es `2`; `a.txt` se abrió exactamente 1 vez y `b.txt` exactamente 1 vez.

### FR-14 · Sin permiso de listado sobre el bucket

**Dado** una ubicación sintácticamente válida cuyo bucket existe, pero sobre el
cual quien invoca no tiene `storage.objects.list`,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema escribe por stderr un mensaje que contiene el URI del
bucket (`gs://<bucket>`) y la frase `sin permiso`, y que **no** contiene la frase
`no existe` (la de FR-12); sale con código `2`, y no lee el contenido de ningún
objeto.

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

> **VC-23** — Con el doble de prueba cuyo `list_objects` levanta el error de
> dominio de *credenciales ausentes* (la costura que existe: la falta de ADC se
> manifiesta al crear el cliente, dentro del listado, y `gcs` la traduce),
> `gcsgrep "x" gs://b/p/` sale con código `2`, stdout vacío, stderr contiene
> `no se encontraron credenciales` y `gcloud auth application-default login`, no
> contiene `Traceback`, y se abren 0 objetos. Contra GCS real, con las credenciales
> tapadas, es el chequeo de integración I-6, que exige los mismos dos textos
> ([`docs/integracion-gcs.md`](../../docs/integracion-gcs.md)).

*Sobre la costura de VC-23 (v1.5):* hasta la v1.4 el VC hablaba de "el colaborador
de credenciales del doble", que no existe: `core` tiene dos colaboradores,
`list_objects` y `open_text_stream`
([`01-base-context.md`](./01-base-context.md) §3). El error de dominio de
credenciales ausentes no existe todavía en el código; agregarlo, y que `gcs` traduzca
a él la falla de ADC, es alcance de la Iteración 2.

### FR-26 · Credenciales que no producen un token

**Dado** un entorno donde Application Default Credentials encuentra una fuente de
credenciales configurada —la variable `GOOGLE_APPLICATION_CREDENTIALS` está
definida, o existe el archivo de `gcloud auth application-default login`— pero **no
puede obtener de ella un token** (por ejemplo, la variable apunta a un archivo
inexistente o mal formado, el archivo de `gcloud` está mal formado, o un *refresh*
al listar es rechazado por un token vencido o revocado)
([ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md)),
**Cuando** la persona ejecuta `gcsgrep` con una ubicación válida,
**Entonces** el sistema escribe por stderr un mensaje que contiene
`credenciales inválidas o vencidas` y el comando para renovarlas,
`gcloud auth application-default login`, y que **no** contiene
`no se encontraron credenciales` (la de FR-15); sale con código `2`, y no lee el
contenido de ningún objeto.

*Por qué es un FR aparte de FR-15 (v1.5):* "no hay credenciales" e "hay credenciales
y no sirven" son dos situaciones con dos observables, y el mensaje de FR-15 ("no se
encontraron") sería falso en la segunda: manda a buscar algo que sí está. El comando
de remedio es el mismo, y es justo el que necesita quien tiene un token vencido.
Hasta la v1.4 este caso caía en el genérico de NFR-3 (exit `2`, sin traceback, con el
nombre de la excepción del SDK como mensaje).

> **VC-41** — Simulando que ADC no puede obtener un token (con el doble de prueba
> cuyo `list_objects` levanta el error de dominio de *credenciales inutilizables*),
> `gcsgrep "x" gs://b/p/` sale con código `2`, stdout
> vacío, stderr contiene `credenciales inválidas o vencidas` y
> `gcloud auth application-default login`, no contiene
> `no se encontraron credenciales` ni `Traceback`, y se abren 0 objetos.

*FR-26 partido en la v1.6:* hasta la v1.5 su Dado era "no se obtiene un token **o**
GCS responde `401`", la forma no atómica que la cátedra marcó en FR-6 y FR-12, y su
Entonces era falso para un `401` sobre un objeto. El `401` al listar es FR-28; sobre
un objeto, FR-6.

### FR-28 · GCS rechaza las credenciales al listar (`401`)

**Dado** un entorno donde ADC obtuvo un token, y GCS responde `401` (no
autenticado) al **listar** el prefijo,
**Cuando** la persona ejecuta `gcsgrep` con una ubicación válida,
**Entonces** la corrida aborta: el sistema escribe por stderr un mensaje que
contiene `credenciales inválidas o vencidas` y `gcloud auth application-default login`,
sale con código `2`, y no lee el contenido de ningún objeto (0 objetos leídos).

> **VC-45** — Con el doble de prueba cuyo `list_objects` simula la respuesta `401`
> de GCS, `gcsgrep "x" gs://b/p/` sale con código `2`, stdout vacío, stderr contiene
> `credenciales inválidas o vencidas` y `gcloud auth application-default login`, no
> contiene `Traceback`, y se abren 0 objetos.

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

### FR-27 · Marca de orden de bytes (BOM) UTF-8 al principio del objeto

**Dado** un objeto de texto cuyos tres primeros bytes son la marca de orden de
bytes de UTF-8 (`EF BB BF`),
**Cuando** se lo busca,
**Entonces** esos tres bytes se descartan antes de partir en líneas: no forman parte
del `<texto>` de la línea 1, no participan del match, y no cuentan como línea. Una
secuencia `EF BB BF` en cualquier otra posición del objeto se decodifica como
cualquier otro carácter (`U+FEFF`).

*Por qué (v1.5):* editores de Windows y algunas herramientas de exportación agregan
el BOM a archivos UTF-8. Si se conserva, el primer `<texto>` de la salida empieza con
un carácter invisible, y un `cut -d: -f2- | grep '^timeout'` aguas abajo deja de
encontrar la primera línea. Es lo mismo que hace la decodificación `utf-8-sig`.

> **VC-44** — Con `gs://b/p/a.txt` cuyos bytes son `EF BB BF` seguidos de
> `timeout\n`, `gcsgrep -n "timeout" gs://b/p/` sale con código `0`, stdout es
> exactamente `gs://b/p/a.txt:1:timeout` (sin ningún byte antes de `timeout`), y
> stderr queda vacío. Con bytes `uno\n` + `EF BB BF` + `timeout\n` (v1.7), la misma
> corrida imprime exactamente `gs://b/p/a.txt:2:` + `U+FEFF` + `timeout`: fuera del
> principio, la secuencia es un carácter más.

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
**Entonces** se trata como un objeto de texto sin líneas: no produce matches, y no
se informa como salteado ni como error (no es un error de lectura, BR-3).

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

### FR-21 · Un objeto que desapareció entre el listado y la lectura no aborta la corrida

**Dado** un prefijo con varios objetos, donde uno de ellos aparece en el listado y
GCS responde **no encontrado** (`404`) al abrirlo o durante la lectura,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los matches de ese objeto que ya se emitieron quedan en stdout, el
sistema escribe por stderr una línea que contiene `ya no existe` y el URI
`gs://<bucket>/<objeto>` de ese objeto, sigue procesando el resto de los objetos, y
el fallo se refleja en el exit code según BR-3.

*Origen (v1.5):* es la ventana de
[ADR-0010](../../docs/adr/ADR-0010-objeto-modificado.md) manifestándose como un
borrado. ADR-0010 y [ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md)
dicen que este caso "lo cubre FR-6"; desde la v1.4 FR-6 es solo permiso denegado, y
el caso no tenía requerimiento
([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)). La referencia vieja
de los dos ADRs queda anotada en [`docs/adr/README.md`](../../docs/adr/README.md).
Un `404` no es un error de red (NFR-2): la red funcionó y la respuesta fue explícita.

> **VC-32** — Con `gs://b/p/a.txt` (contiene `hit a`), `gs://b/p/b.txt` (aparece
> en el listado y GCS responde no encontrado al abrirlo, sea en la apertura o en su
> primera lectura) y `gs://b/p/c.txt`
> (contiene `hit c`), `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente
> `gs://b/p/a.txt:hit a` seguido de `gs://b/p/c.txt:hit c`; stderr contiene una
> línea con `ya no existe` y `gs://b/p/b.txt`, no contiene `Traceback`; y el exit
> code es `2`.

### FR-29 · Otra respuesta de error al leer un objeto

**Dado** un prefijo con varios objetos, donde GCS responde a uno de ellos, al
abrirlo o durante la lectura, con un `4xx` que no es `401`, `403`, `404`, `408` ni
`429` (los que ya clasifican FR-6, FR-21 y NFR-2),
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** los matches de ese objeto que ya se emitieron quedan en stdout, el
sistema escribe por stderr una línea que contiene `no se pudo leer` y el URI
`gs://<bucket>/<objeto>`, sigue procesando el resto de los objetos, y el fallo se
refleja en el exit code según BR-3.

*Origen (v1.7):* hasta la v1.6, un `4xx` que no era permiso ni no encontrado caía en
el caso genérico de NFR-3 y abortaba la corrida
([ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md); revisión de la
v1.5, Warning 3.3 y acción 3).

> **VC-50** — Con `gs://b/p/a.txt` (contiene `hit a`), `gs://b/p/b.txt` (GCS
> responde `400` en su primera lectura) y `gs://b/p/c.txt` (contiene `hit c`),
> `gcsgrep "hit" gs://b/p/` imprime por stdout exactamente `gs://b/p/a.txt:hit a`
> seguido de `gs://b/p/c.txt:hit c`; stderr contiene una línea con
> `no se pudo leer` y `gs://b/p/b.txt`, no contiene `Traceback`; y el exit code es
> `2`.

### FR-22 · Terminador de línea

**Dado** un objeto de texto cuyo contenido tiene caracteres `\r` (retorno de carro),
**Cuando** se lo busca,
**Entonces** una línea termina **únicamente** en `\n`. Si el carácter
inmediatamente anterior a ese `\n` es un `\r`, se quita del `<texto>` (el
terminador `\r\n` cuenta entero como terminador). Un `\r` en cualquier otra
posición es parte de la línea: no la corta, no avanza el número de línea de `-n`, y
sale tal cual en `<texto>`.

**Qué es una línea (v1.7):** el contenido se parte en líneas en cada `\n`. Si el
objeto termina en `\n`, no hay una línea vacía después; dos `\n` seguidos
delimitan una línea vacía, que cuenta para `-n`; un objeto cuyo único byte es `\n`
tiene una línea, vacía. Fundamento de esta definición, del terminador y del BOM
(FR-27): [ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md).

*Origen (v1.5):* hasta la v1.4 "terminador de línea" no estaba definido, y el
código de la Iteración 1 heredaba los *universal newlines* del modo texto de Python
contra GCS, pero no contra el doble de prueba. Nadie había tomado esa decisión; desde
la v1.7 está en [ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md).

> **VC-34** — Con `gs://b/p/a.txt` cuyos bytes son `uno\r\ndos\rtres\n`:
> `gcsgrep -n "tres" gs://b/p/` sale con código `0` y stdout es exactamente los
> bytes `gs://b/p/a.txt:2:dos\rtres\n` (el `\r` suelto sigue en la línea 2);
> `gcsgrep -n "uno" gs://b/p/` sale con código `0` y stdout es exactamente
> `gs://b/p/a.txt:1:uno\n` (sin `\r`). En las dos, stderr queda vacío.

### FR-23 · El consumidor de stdout corta la salida

**Dado** una corrida cuyo stdout es un pipe que el proceso lector cierra antes de
que la corrida termine (por ejemplo, `gcsgrep … | head -1`),
**Cuando** `gcsgrep` intenta escribir el siguiente match,
**Entonces** el proceso termina por la señal `SIGPIPE`, como `grep`: no escribe
por stderr **nada a causa del corte** (lo que FR-6, FR-9, FR-10, FR-13, FR-21 o
FR-29 ya hayan escrito antes queda), no lee más objetos, y su estado de terminación es el de la
señal (en una shell, `141` = 128 + 13), no uno de los exit codes de
[ADR-0008](../../docs/adr/ADR-0008-exit-codes.md). Vale aunque antes haya habido
errores de lectura: quien necesita el exit code de BR-3 no corta la salida.

*Plataforma (v1.7):* FR-23 se promete sobre POSIX, donde existe `SIGPIPE`
([ADR-0027](../../docs/adr/ADR-0027-piso-de-python-y-plataforma.md)).

*Origen (v1.5):* [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md) dice que
`gcsgrep … | head -5` "puede cortar temprano", como `grep`, pero ningún requerimiento
decía qué pasa después. La revisión de la v1.4 lo probó: hoy sale con código `120` y
un mensaje que culpa a GCS (`error inesperado al acceder a gs://b: BrokenPipeError`).
La decisión y sus alternativas están en
[ADR-0019](../../docs/adr/ADR-0019-corte-de-stdout-sigpipe.md).

> **VC-35** — Corriendo el proceso `gcsgrep` real (un intérprete nuevo, en una
> pipeline de bash) con el doble de prueba inyectado en lugar de `gcs`: con
> `gs://b/p/a.txt` de 200 000 líneas, todas iguales a `hit` (200 000 matches), y
> `gs://b/p/b.txt` (contiene `hit`), la pipeline `gcsgrep "hit" gs://b/p/ | head -1`
> imprime exactamente `gs://b/p/a.txt:hit` (una sola línea); el stderr de `gcsgrep`
> queda **vacío**; `b.txt` se abre **0** veces; y el estado de `gcsgrep` en la
> pipeline (`${PIPESTATUS[0]}` en bash) es `141`.

### FR-24 · Patrón vacío

**Dado** el patrón `""` (cadena vacía),
**Cuando** la persona ejecuta `gcsgrep "" gs://bucket/prefijo`,
**Entonces** toda línea de todo objeto de texto bajo el prefijo es un match (la
cadena vacía es substring de cualquier línea, incluida una línea vacía), igual que
`grep ""`: se imprimen todas con el formato de FR-3/FR-4, y el exit code sale de
BR-3. No es un error de uso.

*Por qué no es un error:* [ADR-0024](../../docs/adr/ADR-0024-patron-vacio.md). El
guardrail de BR-2 sigue aplicando igual.

> **VC-36** — Con `gs://b/p/a.txt` (bytes `uno\ndos\n`) y `gs://b/p/vacio.txt`
> (0 bytes), `gcsgrep "" gs://b/p/` sale con código `0`, stdout es exactamente
> `gs://b/p/a.txt:uno` seguido de `gs://b/p/a.txt:dos`, y stderr queda vacío. Con
> `gs://b/p/a.txt` de bytes `uno\n\ndos\n` (v1.7), `gcsgrep -n "" gs://b/p/a.txt`
> imprime exactamente tres líneas: `gs://b/p/a.txt:1:uno`, `gs://b/p/a.txt:2:` y
> `gs://b/p/a.txt:3:dos`.

### FR-25 · Invocación mal formada

**Dado** una invocación que no respeta la forma de *Dentro* —por ejemplo: una
opción que no está en *Dentro* (`-l`, `-v`, `-r`) o una abreviatura de una opción
larga (`--ig`); `--max` con un valor que no es un entero mayor o igual a `0`; falta
el patrón o la ubicación, o sobra un argumento—,
**Cuando** la persona ejecuta `gcsgrep`,
**Entonces** el sistema la rechaza antes de cualquier llamada a GCS: stdout queda
vacío, stderr trae un mensaje que contiene `gcsgrep: error:` (sin traceback,
NFR-3), y sale con código `2`.

Una ubicación inválida, incluida `gs://` sin bucket, es FR-8 (v1.7).

*Origen (v1.5):* [ADR-0004](../../docs/adr/ADR-0004-flags-v1.md) descartó "aceptar
flags no soportados e ignorarlos" porque falla en silencio, o sea que decidió
rechazarlos, pero ningún requerimiento lo decía. Los cuatro casos ya salen con `2`
en el código de la Iteración 1; esto los escribe como contrato. Una ubicación sin
`gs://` es FR-8, que además fija el texto del mensaje.

*Dado como predicado único y texto fijo (v1.7):* hasta la v1.6 el Dado enumeraba
cuatro defectos como si fueran la definición; ahora la definición es *Dentro*, y los
defectos son ejemplos que los VCs cubren uno por uno. El texto `gcsgrep: error:` es
el prefijo que `argparse` usa para todo rechazo, y el de `--max` negativo se alineó
con él.

> **VC-37** — Flag no soportado: `gcsgrep -l "x" gs://b/p/` sale con código `2`,
> stdout vacío, stderr contiene `gcsgrep: error:` y no contiene `Traceback`, y 0
> llamadas de listado.
>
> **VC-38** — `--max` inválido: `gcsgrep --max -1 "x" gs://b/p/` y
> `gcsgrep --max abc "x" gs://b/p/` salen ambos con código `2`, stdout vacío,
> stderr contiene `gcsgrep: error:` y no contiene `Traceback`, y 0 llamadas de
> listado.
>
> **VC-40** — Faltan argumentos: `gcsgrep` (sin argumentos) y `gcsgrep "x"` (sin
> ubicación) salen ambos con código `2`, stdout vacío, stderr contiene
> `gcsgrep: error:` y no contiene `Traceback`, y 0 llamadas de listado.
>
> **VC-46** (v1.7) — Abreviaturas: `gcsgrep --ig "x" gs://b/p/`,
> `gcsgrep --line "x" gs://b/p/` y `gcsgrep --ma=3 "x" gs://b/p/` salen con código
> `2`, stdout vacío, stderr contiene `gcsgrep: error:`, y 0 llamadas de listado.
>
> **VC-47** (v1.7) — Lo que *Dentro* sí acepta: con `gs://b/p/a.txt` cuyas líneas son
> `a -x b` y `Hit`, `gcsgrep -- -x gs://b/p/` sale con `0` y stdout es exactamente
> `gs://b/p/a.txt:a -x b`; `gcsgrep -in hit gs://b/p/` y
> `gcsgrep --max=1 -i -n hit gs://b/p/` salen con `0` y stdout es exactamente
> `gs://b/p/a.txt:2:Hit`.

*VC-39 se movió a FR-8 en la v1.7*, con su número.

### FR-30 · Ayuda

**Dado** la invocación `gcsgrep -h` o `gcsgrep --help`,
**Cuando** la persona la ejecuta,
**Entonces** el sistema imprime por stdout una ayuda que contiene `gcsgrep` y las
opciones de *Dentro* (`--ignore-case`, `--line-number`, `--max`, `--help`), stderr
queda vacío, sale con código `0`, y no hace ninguna llamada a GCS. Las formas largas
`--ignore-case` y `--line-number` dan exactamente la misma salida que `-i` y `-n`.

*Origen (v1.7):* la v1.5 puso `--help` y las formas largas en *Dentro* sin FR ni VC
(revisión de la v1.5, Warning 1.5 y acción 11).

> **VC-48** — `gcsgrep --help` y `gcsgrep -h` salen con código `0`, stdout contiene
> `gcsgrep`, `--ignore-case`, `--line-number`, `--max` y `--help`, stderr queda
> vacío, y 0 llamadas de listado.
>
> **VC-49** — Sobre el objeto de VC-43, `gcsgrep --ignore-case "árbol" gs://b/p/` da
> el mismo stdout, stderr y exit code que `gcsgrep -i "árbol" gs://b/p/`; sobre el
> de VC-3, `gcsgrep --line-number "timeout" gs://b/p/` da los mismos que
> `gcsgrep -n "timeout" gs://b/p/`.

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
**supera** el tope (por defecto **1000**, ajustable con `--max N`; `--max 0` quita
el tope), no se lee ningún objeto, se escribe por stderr una línea que contiene
`<cantidad> objetos` y `el tope es <tope>`, y se sale con código `1`. Una cantidad
**igual** al tope no lo supera: esos objetos se leen.

*Fundamento:* leer objetos de GCS tiene costo; evita una corrida cara por
accidente ([ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md)).
*Excepciones:* `--max 0` es una excepción explícita, decidida por quien invoca,
no un valor por defecto.

> **VC-12** — Con 1001 objetos bajo el prefijo y sin `--max`, `gcsgrep` sale con
> código `1`, stdout vacío, no realiza ninguna lectura de contenido (0 llamadas a
> abrir un objeto), y stderr contiene una línea con `1001 objetos` y
> `el tope es 1000`. Con `--max 0` sobre el mismo prefijo, si hay un match la
> corrida sale con código `0` y sí lee objetos.
>
> **VC-42** — Límite exacto del tope: con **1000** objetos bajo el prefijo y sin
> `--max`, `gcsgrep` abre los 1000 objetos y no escribe la línea del tope. Con
> `--max 3` y 3 objetos, abre los 3. Con `--max 3` y 4 objetos, sale con código
> `1`, abre 0 objetos, y stderr contiene una línea con `4 objetos` y
> `el tope es 3`.

### BR-3 · Precedencia de exit codes ante fallos parciales

Si ocurrió al menos un error de lectura sobre algún objeto (FR-6, FR-13, FR-21,
FR-29),
el exit code final es **`2`**, sin importar si hubo matches en los objetos que sí
se pudieron leer. Sin errores de lectura: `0` si hubo matches, `1` si no. Los
objetos salteados (FR-9, FR-10) y los de 0 bytes (FR-19) no son errores de lectura
y **no afectan el exit code**; esta es la única formulación de esa regla en la
spec, y los FRs la referencian. Un corte de stdout por el consumidor (FR-23)
termina el proceso por señal, antes de que haya exit code.

*Fundamento:* un resultado "sin matches" o "con matches" que ocurrió a pesar de
errores parciales no es un resultado confiable para un script; `2` lo señala
sin ambigüedad, igual que hace `grep` cuando un archivo no se puede abrir
([ADR-0008](../../docs/adr/ADR-0008-exit-codes.md)).
*Excepciones:* ninguna.

> **VC-13** — Con `gs://b/p/a.txt` (contiene `x hit`) y `gs://b/p/b.txt` (GCS
> responde permiso denegado al abrirlo, la causa de FR-6), `gcsgrep "hit" gs://b/p/`
> imprime por stdout exactamente `gs://b/p/a.txt:x hit`, stderr contiene una línea
> con `sin permiso para leer` y `gs://b/p/b.txt`, y sale con código `2` (no `0`,
> aunque hubo un match).

---

## Requerimientos no funcionales

### NFR-1 · Memoria acotada por streaming

**Métrica:** pico de memoria adicional **asignada por el intérprete de Python**
(la que registra `tracemalloc`) mientras se lee un objeto, **incluidos los buffers
de la librería cliente de GCS que viven en el heap de Python** (v1.6). No incluye
memoria nativa fuera del heap de Python (la de `ssl`) ni el tamaño residente del
proceso.
**Umbral:** **< 20 MiB**.
**Condición de carga:** un objeto de **200 MiB** de texto, en dos condiciones:
(a) con un patrón que no aparece en ninguna línea, y (b) con un patrón que
aparece en **todas** las líneas.

*Por qué esta métrica y no la del proceso (v1.5):* hasta la v1.4 el enunciado decía
"del proceso" y el VC medía con `tracemalloc`, que no ve la memoria nativa: una
implementación podía pasar el VC sin cumplir el NFR. Se alineó el enunciado con lo
que se mide, porque lo que NFR-1 protege —no cargar el objeto ni acumular matches—
ocurre en objetos de Python y `tracemalloc` lo ve entero. La memoria nativa del SDK
no depende del tamaño del objeto cuando se lee por streaming, y medir RSS sobre el
doble de prueba mediría el intérprete.

Para cumplirlo, el sistema procesa cada objeto línea por línea por streaming, sin
cargar el contenido completo en memoria, **y sin acumular los matches
encontrados** (ver FR-11 y
[ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md)). **El lector de GCS se
abre con `chunk_size` ≤ 1 MiB** (v1.6): el bloque por defecto del lector de la
librería cliente es de ~40 MiB, y leyendo a través de él el pico medido por la
revisión de la v1.5 fue de ≈120 MiB. Fundamento y costo (más pedidos por objeto):
[ADR-0020](../../docs/adr/ADR-0020-tamano-de-bloque-del-lector.md).

> **VC-14** — Sobre un objeto simulado de **200 MiB** de contenido de texto, el
> pico de memoria adicional asignada por el intérprete mientras se lee ese objeto
> es menor a **20 MiB** (medido con `tracemalloc` sobre el doble de prueba que
> expone el stream; nunca se llama a un equivalente de "leer todo el archivo"
> sobre él), en las condiciones (a) y (b). La (b) es la que hace falsable al VC:
> con acumulación de matches, el pico medido es de ~371 MiB.

> **VC-14 (c)** (v1.6) — Sobre un objeto de **200 MiB** de texto con un patrón que
> no aparece (condición (a)), leído **a través del lector real de la librería
> cliente** (`google.cloud.storage.fileio.BlobReader`, abierto como lo abre `gcs`)
> con un blob falso que implementa `download_as_bytes(start, end)` desde memoria, el
> pico de memoria adicional medido con `tracemalloc` es menor a **20 MiB**. (a) y (b)
> corren sobre el doble y no ven el lector; (c) es la que falla si el bloque de
> lectura crece. Hoy da ≈120 MiB: alcance de la Iteración 2.

### NFR-2 · Política ante fallos de red: sin reintentos

**Error de red** (definición única; FR-13 y este NFR la referencian): una operación
sobre GCS **no obtiene una respuesta HTTP completa** (la conexión se rechaza o se
corta, o vence el timeout de 60 s) **o recibe una respuesta `408`, `429` o `5xx`**
(v1.7: `408` y `429` son el servicio diciendo "ahora no", con el mismo remedio que un
`503`). Cualquier otro `4xx` —en particular `401` (FR-6, FR-28), `403` (FR-6,
FR-14), `404` (FR-12, FR-21) y el resto (FR-29)— **no** es un error de red: la red
funcionó y la respuesta fue explícita.

**Política:** **0 reintentos automáticos, ni de `gcsgrep` ni de la librería
cliente** (sus reintentos por defecto, de hasta 120 s, se desactivan), y **un
timeout de 60 s por pedido HTTP**
([ADR-0028](../../docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md), que
desde la v1.7 supersede a [ADR-0016](../../docs/adr/ADR-0016-sin-reintentos.md)).
Ante un error de red, cada operación sobre GCS se intenta **una sola vez**, y el
fallo se reporta según NFR-3 (sin traceback). Hay dos condiciones, cada una con su
VC:

- **(a) Al listar:** la corrida aborta con código `2` y un mensaje por stderr que
  contiene `error de red` y el URI del bucket.
- **(b) Al abrir o leer un objeto:** ese objeto no se vuelve a abrir; la corrida
  sigue según FR-13 y el exit code sale de BR-3.

> **VC-15** — Simulando que el listado inicial falla por un error de red, `gcsgrep`
> sale con código `2`, stdout vacío, stderr contiene `error de red` y
> `gs://<bucket>`, y el listado se invocó exactamente **1** vez. En el borde con la
> librería (v1.7), `gcs` pide el listado y la apertura de cada objeto con
> `retry=None` y `timeout=60`, y traduce a error de red una respuesta `408`, `429` o
> `5xx` y una conexión cortada o vencida.
>
> **VC-29** — En el escenario de VC-21, el objeto `gs://b/p/a.txt` se abrió
> exactamente **1** vez (0 reintentos), `gs://b/p/b.txt` se abrió exactamente 1
> vez, y el exit code es `2`. (El fallo **al abrir** tiene las mismas cuentas en
> VC-33.)

### NFR-3 · Salida apta para scripting

stdout contiene únicamente líneas de match (la única excepción es `--help`, ver
*Dentro*). Todo mensaje informativo o de error (objetos salteados, objetos
fallidos, guardrail excedido) va a stderr. En una corrida sin salteados, sin errores y sin guardrail excedido,
stderr queda vacío. **Ningún caso de error imprime un stack trace de Python.**
Esta es la única formulación de la regla "sin traceback" en la spec; los demás
requerimientos la referencian.

**Excepción explícita, opt-in:** si quien invoca define la variable de entorno
`GCSGREP_DEBUG=1`, ante una excepción **no prevista** (el caso de VC-16 (b)) el
proceso la re-lanza: stderr contiene el traceback y el exit code es el del
intérprete (`1`). No es el comportamiento por defecto, no se activa sola, y no
aplica a los errores previstos (FR-6, FR-8, FR-12, FR-13, FR-14, FR-15, FR-21,
FR-25, FR-26, FR-28, FR-29, BR-2, NFR-2), que siguen sin traceback aunque la variable esté
definida. Existe para
diagnosticar un bug nuevo
([ADR-0013](../../docs/adr/ADR-0013-frontera-de-excepciones.md)).

> **VC-16 (a)** — Para cada caso de error o salteo cubierto (VC-6, VC-8, VC-9,
> VC-10, VC-12, VC-13, VC-15, VC-18, VC-21, VC-22, VC-23, VC-32, VC-33, VC-37,
> VC-38, VC-39, VC-40, VC-41, VC-45, VC-46, VC-50), stdout no contiene
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

**Métrica:** tasa de procesamiento de una ejecución de `gcsgrep` **en proceso**:
desde que el punto de entrada del programa recibe su `argv` hasta que devuelve el
exit code, con stdout redirigido a `/dev/null` y el contenido servido desde memoria
por el doble de prueba. **No incluye** el arranque del intérprete ni la importación
de módulos (un costo fijo por invocación, que no depende del tamaño del objeto), ni
la latencia de la red
([ADR-0026](../../docs/adr/ADR-0026-nfr-4-recalibrado-en-ci.md), que desde la v1.7
supersede a [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md)).
**Condición de carga:** un único objeto de **100 MiB** de texto, con líneas de
**80 bytes** (~1,3 millones de líneas), lectura secuencial.
**Plataforma de referencia (v1.7):** el runner `ubuntu-latest` del CI, en cada
versión de Python de su matriz.
**Umbrales:**

- **(a) Patrón ausente:** **≥ 50 MiB/s** de contenido recorrido.
- **(b) Patrón en todas las líneas:** **≥ 150 000 matches/s** emitidos por stdout
  (hasta la v1.6: 50 000).

> **VC-30** — Ejecutando `gcsgrep` en proceso (su punto de entrada con el `argv`
> de la corrida, sin arrancar un intérprete nuevo) sobre el objeto de la condición
> de carga, con stdout a `/dev/null` y tomando la mejor de 3 corridas: en la
> condición (a) la tasa es ≥ 50 MiB/s, y en la (b) la tasa es ≥ 150 000 matches/s
> con exit `0`. Los dos umbrales discriminan en la plataforma de referencia y en la
> de desarrollo: una implementación que lee el objeto de a un byte procesa
> ~3 MiB/s y falla (a); una que abre y cierra el destino de la salida por cada match
> emite entre **~32 000 y ~106 000 matches/s** según la plataforma y falla (b),
> mientras la implementación actual emite entre ~319 000 y ~488 000 (medido el
> 2026-10-02 con `scripts/medir-nfr4.py`; el CI lo imprime en cada corrida).

*Qué tanto discrimina (b):* en la v1.5, con 50 000, la implementación mala caía
debajo en macOS (~31 000) y **no** en Linux (~242 000 según la revisión de la v1.5),
que es donde corre el CI. Con 150 000, la mala queda abajo en el peor caso medido
por 1,4× (105 613, `ubuntu-latest`, Python 3.12) y la actual arriba por 2,1×
(319 034, `ubuntu-latest`, Python 3.9). Las tablas completas están en
[ADR-0026](../../docs/adr/ADR-0026-nfr-4-recalibrado-en-ci.md). (b) acota el peor
caso del costo por match, no cualquier ineficiencia: un `os.fsync` por match contra
`/dev/null` no sincroniza nada y no lo detecta.

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
> (3) `gcsgrep "x" gs://$BUCKET_INEXISTENTE/` sale con `2` y stderr contiene
> `no existe`, donde `$BUCKET_INEXISTENTE` es un nombre generado al correr el VC
> (`gcsgrep-test-no-existe-` seguido de 12 caracteres aleatorios en minúscula) y
> verificado inexistente inmediatamente antes (su listado responde `404`; si no,
> se genera otro); en las tres, stderr no contiene `Traceback`. Recorre la
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
| FR-2 | VC-2, VC-43 | feliz · borde (no ASCII) |
| FR-3 | VC-3, VC-31 | feliz · punta a punta real |
| FR-4 | VC-4 | feliz |
| FR-5 | VC-5, VC-31 | borde (sin resultados) |
| FR-6 | VC-6 | falla parcial (permiso de objeto) |
| FR-7 | VC-7 | borde (bucket completo) |
| FR-8 | VC-8, VC-39 | falla (input inválido · `gs://` sin bucket) |
| FR-9 | VC-9, VC-20 | borde (binario) · límite exacto |
| FR-10 | VC-10 | borde (.gz) |
| FR-11 | VC-17 | invariante (observabilidad) |
| FR-12 | VC-18, VC-31 | falla (bucket inexistente) |
| FR-13 | VC-21, VC-33 | falla parcial (red a mitad de lectura · red al abrir) |
| FR-14 | VC-22 | falla (sin permiso de listado) |
| FR-15 | VC-23 | falla (sin credenciales) |
| FR-16 | VC-24 | invariante (orden) |
| FR-17 | VC-25 | borde (codificación) |
| FR-18 | VC-26 | borde (prefijo ambiguo) |
| FR-19 | VC-27 | borde (0 bytes) |
| FR-20 | VC-28 | borde (último elemento sin terminador) |
| FR-21 | VC-32 | falla parcial (objeto borrado entre listado y lectura) |
| FR-22 | VC-34 | borde (terminador `\r\n` y `\r` suelto) |
| FR-23 | VC-35 | borde (consumidor que corta stdout) |
| FR-24 | VC-36 | borde (entrada vacía: patrón) |
| FR-25 | VC-37, VC-38, VC-40, VC-46, VC-47 | falla (invocación mal formada, un VC por defecto) · borde (sintaxis aceptada) |
| FR-26 | VC-41 | falla (credenciales sin token) |
| FR-27 | VC-44 | borde (BOM UTF-8) |
| FR-28 | VC-45 | falla (`401` al listar) |
| FR-29 | VC-50 | falla parcial (otro `4xx` sobre un objeto) |
| FR-30 | VC-48, VC-49 | feliz (ayuda · formas largas) |
| BR-1 | VC-11, VC-31 | invariante |
| BR-2 | VC-12, VC-42 | guardrail · límite exacto |
| BR-3 | VC-13 | invariante |
| NFR-1 | VC-14 (a), VC-14 (b), VC-14 (c) | medición (doble · lector real) |
| NFR-2 | VC-15 (al listar), VC-29 (al leer), VC-33 (al abrir) | falla |
| NFR-3 | VC-16 (a), (b), (c), VC-31 | invariante |
| NFR-4 | VC-30 (a), (b) | medición |

**37 requerimientos (30 FR, 3 BR, 4 NFR), 50 VCs, 0 huérfanos.** Cada condición
enumerada en un NFR tiene su propio VC o su propia parte de VC.

## Tabla de trazabilidad · borrador → spec

La tabla de arriba prueba que ningún requerimiento de esta spec quedó sin VC.
Esta prueba lo otro, que es lo que faltaba en v1.0: que ningún ítem del
[borrador](./00-requirements-draft.md) quedó sin destino. Los dos huérfanos que
encontró la revisión (FR-g y NFR-a) están marcados con su resolución.

| Ítem del borrador | Destino | Dónde |
|---|---|---|
| FR-a · patrón + ubicación, busca dentro de los objetos | FR-1 (literal), FR-16 (orden), FR-17…FR-20, FR-22, FR-27 (bordes de contenido y ubicación), FR-23 (corte de stdout), FR-24 (patrón vacío), FR-25 (invocación mal formada), FR-30 (ayuda) | Iteración 1 (comportamiento) · Iteración 2 (VCs nuevos de v1.4 y v1.5) |
| FR-b · bucket completo o prefijo | FR-7, FR-18 | Iteración 1 |
| FR-c · salida deja claro el objeto, y la línea si se puede | FR-4 (sin `-n`) + FR-3 (con `-n`) | Iteración 1 |
| FR-d · búsqueda sin distinguir mayúsculas | FR-2 | Iteración 1 |
| FR-e · avisar "no encontré nada" de forma detectable por un script | FR-5 (exit `1`) | Iteración 1 |
| FR-f · un objeto ilegible no tira la corrida | FR-6 (permiso) + FR-13 (red) + FR-21 (no encontrado) + FR-29 (otro `4xx`), todos al abrir o al leer | Iteración 2 · Iteración 2b (FR-29) |
| FR-g · notar el progreso con muchos objetos | **FR-11** — resuelto en v1.1, [ADR-0011](../../docs/adr/ADR-0011-salida-incremental.md). Era huérfano en v1.0 (hallazgo H-1) | Iteración 1 |
| BR-a? · nunca escribe en GCS | BR-1 | Iteración 1 (adelantada) |
| BR-b? · no amplía el acceso del invocador | BR-1 (fusionado) + permisos mínimos + [ADR-0002](../../docs/adr/ADR-0002-autenticacion-adc.md) | Iteración 1 (adelantada) |
| BR-c? · límite para no escanear un bucket enorme | BR-2, con tope decidido en objetos ([ADR-0006](../../docs/adr/ADR-0006-guardrail-de-costo.md)) | Iteración 1 (adelantada) |
| BR-d? · saltear lo que no es texto | FR-9, FR-10 (es comportamiento observable, no regla de negocio) + [ADR-0021](../../docs/adr/ADR-0021-avisos-de-salteo-por-objeto.md) (supersede a ADR-0005), [ADR-0018](../../docs/adr/ADR-0018-ventana-binaria-y-codificacion.md) | Iteración 2 |
| NFR-a · rendimiento | **NFR-4** desde v1.4, [ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) (supersede a ADR-0012, que lo había declinado), recalibrado en la v1.7 por [ADR-0026](../../docs/adr/ADR-0026-nfr-4-recalibrado-en-ci.md). Fue huérfano en v1.0 (H-2) y declinado de v1.1 a v1.3 | Iteración 2 |
| NFR-b · memoria con objetos grandes | NFR-1, umbral 20 MiB sobre 200 MiB | Iteración 1 |
| NFR-c · comportamiento ante fallos de red | NFR-2 (0 reintentos, también en la librería; [ADR-0028](../../docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md), que supersede a ADR-0016) + FR-13 | Iteración 2 |

**14 ítems del borrador, 14 con destino explícito, 0 perdidos.**

Tres notas sobre la forma de esta tabla:

- **FR-c se abrió en dos.** El borrador metía dos comportamientos en una línea
  ("el objeto, y la línea si se puede"). Un FR por comportamiento — y desde la
  v1.4, un FR por formato.
- **FR-f se abrió en dos en la v1.4, y en tres en la v1.5.** "Ilegible" tenía tres
  causas con tres observables distintos (permiso denegado al abrir, no encontrado al
  abrir, red al abrir o a mitad de lectura). La v1.4 partió en dos y perdió el
  segundo y la mitad del tercero
  ([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)).
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
| GCS | **Red** — al leer un objeto | FR-13 + NFR-2 (b) + BR-3 | VC-21, VC-29 |
| GCS | **Red** — al abrir un objeto | FR-13 + NFR-2 (b) + BR-3 — *sin cubrir en la v1.4, [H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)* | VC-33 |
| GCS | **Red** — al listar | NFR-2 (a) (aborta con `2`, sin traceback) | VC-15 |
| GCS | **Otra respuesta de error** — sobre un objeto (`4xx` que no es `401`, `403`, `404`, `408` ni `429`) | **FR-29** + BR-3 — nuevo en v1.7 | VC-50 |
| GCS | **Otra respuesta de error** — al listar | caso genérico de NFR-3 (aborta con `2`, sin traceback, VC-16 (b)) — decidido en [ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md) | VC-16 (b) |
| GCS | **No existir** — el bucket | **FR-12** — *era el huérfano de H-13* | VC-18 |
| GCS | **No existir** — el prefijo (0 objetos) | FR-5 (exit `1`, es un resultado válido, no un error) | VC-5 |
| GCS | **No existir** — un objeto listado (borrado antes de leerlo) | **FR-21** + BR-3 — *el mismo caso que H-13, un nivel más abajo: sin cubrir en la v1.4, [H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)* | VC-32 |
| Entorno de credenciales | **Sin credenciales** | **FR-15** — nuevo en v1.4 | VC-23 |
| Entorno de credenciales | **Credenciales inutilizables** (vencidas, revocadas, archivo de key inválido) | **FR-26** (sin token) — nuevo en v1.5; **FR-28** (`401` al listar) — v1.6; un `401` sobre un objeto, FR-6 | VC-41, VC-45 |
| Persona usuaria | Ubicación mal escrita (incluida `gs://` sin bucket, v1.7) | FR-8 (exit `2` sin tocar la red) | VC-8, VC-39 |
| Persona usuaria | Invocación mal formada (flag, abreviatura, `--max`, argumentos) | **FR-25** (exit `2` sin tocar la red) — nuevo en v1.5 | VC-37, VC-38, VC-40, VC-46 |
| Persona usuaria | Prefijo gigante, corrida costosa | BR-2 (guardrail, tope 1000) | VC-12, VC-42 |
| Script | Necesita decidir sin parsear texto | FR-5, BR-3, NFR-3 (exit codes + stdout limpio) | VC-5, VC-13, VC-16 |
| Script | Necesita una salida reproducible | FR-16 (orden del listado) | VC-24 |
| Script | Corta la salida antes del final (`\| head`) | **FR-23** (SIGPIPE, sin stderr) — nuevo en v1.5 | VC-35 |

**18 modos de falla declarados, 18 cubiertos, 0 huérfanos.**

Tres notas sobre la forma de esta tabla:

- **"Permisos", "red" y "no existir" se abrieron por dónde ocurren.** Un fallo al
  **listar** aborta la corrida; el mismo fallo sobre **un objeto** no. Escritos
  como una sola línea, fue precisamente lo que permitió que el caso del listado se
  perdiera: "permisos" parecía cubierto por FR-6.
- **"Prefijo inexistente" no es un error.** Un prefijo sin objetos dentro de un
  bucket que sí existe es indistinguible de un prefijo sin matches, y GCS no
  reporta error: FR-5 (exit `1`) es la respuesta correcta. Solo el **bucket**
  inexistente es un error, porque ahí GCS sí responde 404.
- **Al partir o angostar un requerimiento, esta tabla se vuelve a recorrer
  (v1.5).** La v1.4 partió FR-6 en "permiso al abrir" (FR-6) y "red después de
  empezar" (FR-13); las filas de arriba siguieron apuntando a FR-6/FR-13 y parecían
  cubiertas, pero el objeto que no existe al abrirlo y la red caída al abrir ya no
  cabían en ninguno de los dos. Es el mismo mecanismo de H-13 —una obligación que
  *parece* cubierta porque su fila nombra un requerimiento—, y por eso las filas de
  "no existir" y "red" están abiertas también por objeto y por momento. Regla en el
  checklist como C-19
  ([H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md)).

## Preguntas abiertas

Ninguna. Las 10 del borrador quedaron resueltas como
[ADR-0001 … ADR-0010](../../docs/adr/), y desde la v1.4 cada una tiene además su
comportamiento observable escrito en un requerimiento de esta spec:

| # | Pregunta | Requerimiento | ADR |
|---|---|---|---|
| 1 | Sabor de regex | FR-1 (substring literal), VC-19 | ADR-0001 |
| 2 | Autenticación | BR-1, FR-15 (sin credenciales → exit `2`), FR-26 (credenciales sin token), FR-28 (`401` al listar) | ADR-0002 |
| 3 | Sintaxis de la ubicación | FR-7, FR-8 (incluida `gs://` sin bucket), FR-18 (prefijo sin `/`) | ADR-0003 |
| 4 | Flags de `grep` | FR-2, FR-3, FR-4, BR-2, FR-25 (flags no soportados y abreviaturas se rechazan), FR-30 (ayuda) | ADR-0004, ADR-0023 |
| 5 | Binarios y `.gz` | FR-9 (ventana de 8192 bytes, `\x00` posterior, una línea por salteo), FR-10, FR-17, FR-27 (BOM) | ADR-0021 (supersede a ADR-0005), ADR-0018, ADR-0022 |
| 6 | Guardrail de costo | BR-2 | ADR-0006 |
| 7 | Formato de salida | FR-3, FR-4, FR-22 (terminador y definición de línea) | ADR-0007, ADR-0022 |
| 8 | Exit codes | FR-5, FR-8, BR-3, FR-23 (corte de stdout: señal, no exit code) | ADR-0008, ADR-0019 |
| 9 | Concurrencia | FR-16 (orden del listado) | ADR-0009 |
| 10 | Objeto modificado durante la lectura | Fuera (riesgo aceptado); el objeto **borrado** es FR-21 | ADR-0010 |

Los dos huérfanos que encontró la revisión v1.1 se resolvieron como ADR-0011
(FR-11) y ADR-0012, hoy superseded por ADR-0017 (NFR-4). La salida incremental de
ADR-0011 tiene además su borde de pipe en FR-23 desde la v1.5.

## Excepciones registradas (revisión v1.5)

La [revisión de la v1.5](../../revisiones/spec-v1.5-2026-10-01.md) dio NEEDS WORK
con 2 MUST, 10 SHOULD y 7 COULD. La v1.6 resuelve los dos MUST (FR-26/FR-28 y
NFR-1/VC-14 (c)) y la acción 16 (conteo de la tabla de actores, VC-31 en NFR-3). El
resto **no se resuelve en la v1.6**: queda acá, una fila por acción, con por qué se
acepta y cuándo se atiende. Es el mismo mecanismo con el que la revisión v1.1 habilitó
la spec con H-9 abierto ([`docs/revision-spec.md`](../../docs/revision-spec.md)). Una
excepción se cierra con una fila del *Historial* que la nombre.

| Acción | Nivel | Qué queda abierto | Por qué se acepta | Se atiende en |
|---|---|---|---|---|
| 2 (parte) | MUST | El tamaño de bloque (`chunk_size` ≤ 1 MiB) está en NFR-1 pero no en un ADR, ni su efecto en NFR-4 (más pedidos por objeto), ni en *Tecnología* y `01-base-context.md` | El comportamiento observable y su VC ya están en la spec; falta el fundamento escrito | Iteración 2, junto con la implementación de VC-14 (c) |
| 3 | SHOULD | Un `429` o un `408` sobre un objeto no es ni red (FR-13), ni permiso (FR-6), ni no encontrado (FR-21): cae en el genérico | El genérico lo acota: exit `2`, sin traceback (NFR-3). No hay salida falsa, solo un mensaje menos preciso y una corrida que aborta | Iteración 2 (spec v1.7: redefinir "error de red" y un FR para "otra respuesta de error") |
| 3 | SHOULD | "Al abrir" no es observable con el SDK real: `blob.open("r")` es perezoso y el `403`/`404` llega en la primera lectura; la nota de los tres caminos (FR-6) no es exhaustiva | Mismo acotamiento por el genérico; los VCs contra el doble siguen siendo correctos sobre la costura declarada | Iteración 2 (spec v1.7: "al abrir o durante la lectura" en FR-6/FR-21, VC-6/VC-32 en la primera lectura) |
| 4 | SHOULD | Qué es una línea (`uno\n\ndos\n`) no está definido; VC-36 sin bytes explícitos | FR-22 y FR-20 ya fijan el terminador y la última línea; el caso de la línea vacía coincide con lo que hace el código | Iteración 2 (Paso 0) |
| 5 | SHOULD | FR-2 dice "carácter por carácter" y "un carácter nunca se convierte en dos", falso para el plegado de `İ` → `i̇` y de `Σ` final → `ς` de `str.lower()` | Afecta solo a esos caracteres; VC-43 (`árbol`) es correcto | Iteración 2 (Paso 0, con el caso `ΟΔΟΣ` en VC-43) |
| 6 | SHOULD | Las abreviaturas de opciones largas (`--ig`) se aceptan, aunque *Dentro* dice que lo que no respeta la forma se rechaza; un patrón que empieza con `-` no tiene VC | `--ig` hace lo mismo que `--ignore-case`: no produce salida falsa | Iteración 2 (`allow_abbrev=False`, VCs `--ig` → `2` y `-- -x`) |
| 7 | SHOULD | FR-23 no distingue el stderr causado por el corte del ya escrito; VC-35 no dice con qué proceso corre | FR-23 ya es alcance de la Iteración 2 | Iteración 2 |
| 8 | SHOULD | VC-5 no cubre el prefijo sin objetos que la tabla de actores le asigna | El comportamiento (exit `1`) es el de FR-5 y ya lo hace el código | Iteración 2 (Paso 0) |
| 9 | SHOULD | NFR-4 (b) discrimina en macOS (29 185 matches/s, falla) pero **no en Linux/CI** (241 980 matches/s, pasa por 4,8×); el CI corre en `ubuntu-latest` | (a) sigue discriminando; (b) queda como piso de regresión de hecho hasta recalibrar | Iteración 2 (Paso 0, al medir VC-30: recalibrar en `ubuntu-latest` o ADR que supersede la parte de ADR-0017) |
| 10 | SHOULD | Los reintentos y el timeout de la librería cliente no están en la spec con un número (solo en ADR-0016) | `gcsgrep` no reintenta; lo que agregue el SDK no cambia el resultado, solo la demora | Iteración 2 (con NFR-2) |
| 11 | SHOULD | `--help` y las formas largas no tienen FR ni VC | Ya funcionan; no cambian la salida de una búsqueda | Iteración 2 (Paso 0) |
| 12 | SHOULD | Fundamentos de la v1.5 en prosa en vez de ADR; el desvío de ADR-0005 sin ADR que lo supersede | Documentación; no cambia comportamiento | Iteración 2 |
| 13 | COULD | FR-13: el Dado podría ser el título | Estilo; FR-13 ya es atómico por la definición de NFR-2 | Iteración 2 (spec v1.7) |
| 14 | COULD | FR-25: Dado como predicado único y texto fijo en stderr | Los cuatro VCs ya cubren los defectos | Iteración 2 (spec v1.7) |
| 15 | COULD | VC-44 sin un BOM fuera del principio | FR-27 lo dice en el texto | Iteración 2 (con FR-27) |
| 17 | COULD | Runtime, librería cliente con versión mínima y plataforma (POSIX) sin nombrar | Están en `pyproject.toml` | Iteración 2 (spec v1.7) |
| 18 | COULD | Referencias viejas de ADR-0007, ADR-0011 y ADR-0002 sin registrar en `docs/adr/README.md` | Documentación | Iteración 2 |
| 19 | COULD | FR-8 y FR-25 se reparten `gs://` a secas | Los dos salen con `2` sin tocar la red | Iteración 2 (spec v1.7) |

### Cierre en la v1.7 (Iteración 2b, 2026-10-02)

La tabla de arriba queda como registro de lo que estaba abierto; no se editó. Cada
acción se cierra así, y la fila 1.7 del *Historial* las nombra:

| Acción | Cómo se cerró |
|---|---|
| 2 (parte) | [ADR-0020](../../docs/adr/ADR-0020-tamano-de-bloque-del-lector.md) (bloque de 1 MiB, su costo en pedidos); nombrado en *Tecnología* y en `01-base-context.md` |
| 3 (`408`/`429` y otros `4xx`) | NFR-2 redefine "error de red" con `408` y `429`; **+FR-29/VC-50** para el resto de los `4xx`; actor GCS con "otra respuesta de error" y sus dos filas de trazabilidad; [ADR-0025](../../docs/adr/ADR-0025-clasificacion-de-fallos.md) |
| 3 ("al abrir") | "Al abrir" definido una vez en FR-6 (antes del primer byte); FR-6 y FR-21 "al abrirlo o durante la lectura"; VC-6 y VC-32 aceptan el fallo en la primera lectura |
| 4 | Definición de línea en FR-22; VC-36 con bytes y el caso `uno\n\ndos\n`; [ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md) |
| 5 | FR-2 describe `str.lower()` con sus reglas contextuales; VC-43 con `ΟΔΟΣ`; [ADR-0023](../../docs/adr/ADR-0023-plegado-de-mayusculas.md) |
| 6 | *Dentro* enumera la sintaxis aceptada; **+VC-46** (abreviaturas → `2`) y **+VC-47** (`--`, `-in`, `--max=N`) |
| 7 | FR-23 "nada a causa del corte"; VC-35 con `b.txt` abierto 0 veces y dice con qué proceso corre |
| 8 | VC-5 con el prefijo sin objetos |
| 9 | NFR-4 con plataforma de referencia y (b) ≥ 150 000; [ADR-0026](../../docs/adr/ADR-0026-nfr-4-recalibrado-en-ci.md) supersede a ADR-0017 |
| 10 | NFR-2 con 0 reintentos de la librería y timeout de 60 s; [ADR-0028](../../docs/adr/ADR-0028-sin-reintentos-tampoco-en-la-libreria.md) supersede a ADR-0016 |
| 11 | **+FR-30** (ayuda) con **VC-48** y **VC-49** |
| 12 | Fundamentos en ADRs: [ADR-0022](../../docs/adr/ADR-0022-que-es-una-linea.md), [ADR-0023](../../docs/adr/ADR-0023-plegado-de-mayusculas.md), [ADR-0024](../../docs/adr/ADR-0024-patron-vacio.md); el desvío de ADR-0005 pasa a [ADR-0021](../../docs/adr/ADR-0021-avisos-de-salteo-por-objeto.md), que lo supersede |
| 13 | FR-13 con el título como Dado; los dos momentos a VC-21 y VC-33 |
| 14 | FR-25 con un Dado único y el texto fijo `gcsgrep: error:` en VC-37, VC-38, VC-40 y VC-46 |
| 15 | VC-44 con un BOM fuera del principio |
| 17 | *Tecnología*: Python ≥ 3.10, POSIX, `google-cloud-storage` ≥ 2.14; [ADR-0027](../../docs/adr/ADR-0027-piso-de-python-y-plataforma.md) |
| 18 | Las tres referencias viejas registradas en [`docs/adr/README.md`](../../docs/adr/README.md) |
| 19 | FR-8 absorbe `gs://` sin bucket, con el mismo mensaje; VC-39 se reubica bajo FR-8 |

**Ninguna excepción queda abierta.**

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
| 1.5 | 2026-10-01 | **Revisión de la v1.4 (NEEDS WORK), las 21 acciones.** MUST: **"error de red" definido una vez** en NFR-2 (sin respuesta HTTP completa, o `5xx`; un `403`/`404` no lo es) y FR-13 lo referencia sin listar causas; **+FR-21/VC-32** (objeto listado que GCS responde no encontrado al abrirlo: `ya no existe`, sigue, BR-3); FR-13 cubre la red **al abrir** (+VC-33); BR-3, NFR-2 (b), los previstos de NFR-3 y la tabla de actores actualizados. SHOULD: **+FR-22/VC-34** (terminador `\n`, `\r\n` sin `\r`, `\r` suelto en la línea); **+FR-23/VC-35** (`\| head` → SIGPIPE sin stderr, [ADR-0019](../../docs/adr/ADR-0019-corte-de-stdout-sigpipe.md)); **+FR-24/VC-36** (patrón vacío matchea todo); **+FR-25/VC-37…VC-40** (invocación mal formada → `2`); **+FR-26/VC-41** (credenciales inutilizables); **+VC-42** (límite exacto de BR-2); texto literal del guardrail en BR-2; VC-7, VC-12, VC-13, VC-20, VC-23 con observables exactos; VC-9/VC-10 "stderr es exactamente"; FR-9/FR-10: una línea por salteo, sin resumen final (se aparta de ADR-0005); FR-9: `\x00` posterior a la ventana sale por stdout; FR-14 "no contiene `no existe`"; VC-15 sin "representación cruda"; NFR-1 y NFR-4 dicen lo que se mide (memoria del intérprete; ejecución en proceso), MiB en todo; VC-30 con contraste medido para (b). COULD: plegado de `-i` carácter por carácter (+VC-43); **+FR-27/VC-44** (BOM); formas largas y `--help` en *Dentro*; "no afecta el exit code" solo en BR-3; VC-31 (3) con bucket inexistente verificado; referencias viejas de ADRs anotadas en `docs/adr/README.md`. | [revisión de la v1.4](../../revisiones/spec-v1.4-2026-10-01.md), [H-16](../../docs/hallazgos/H-16-objeto-que-falla-al-abrir.md), [errata de la respuesta](../../docs/respuesta-correccion-catedra.md#errata-revisión-v14) |
| 1.6 | 2026-10-01 | **Revisión de la v1.5 (NEEDS WORK), los dos MUST.** **FR-26 partido:** FR-26 queda en credenciales que no producen un token (VC-41); **+FR-28/VC-45** (`401` al listar: aborta, `2`, 0 objetos leídos); un `401` sobre un objeto, después de haber leído otros, es FR-6. **NFR-1:** la métrica incluye los buffers de la librería cliente en el heap de Python, el lector de GCS se abre con `chunk_size` ≤ 1 MiB, y **+VC-14 (c)** mide a través de `BlobReader` (Iteración 2). Conteo de la tabla de actores (16) y VC-31 en la fila de NFR-3 (acción 16). El resto de las acciones queda en *Excepciones registradas (revisión v1.5)*. **Estado: habilitada con excepciones registradas.** | [revisión de la v1.5](../../revisiones/spec-v1.5-2026-10-01.md) |
| 1.6.1 | 2026-10-01 | **Cambio de contrato implementado: BR-3** (anunciado desde la v1.2, sin número por adelantado). Sin cambio de texto normativo: ningún FR, BR, NFR ni VC cambia de redacción; esta fila registra que el comportamiento observable de corridas que la Iteración 1 ya podía producir **cambió** al implementarse la Iteración 2. Antes: un objeto que fallaba al abrirse o leerse abortaba la corrida (exit `2` por el genérico de ADR-0013, o `ObjetoNoEncontrado`/`AccesoDenegado`), y no se leían los objetos siguientes. Ahora: el objeto se informa por stderr (`sin permiso para leer`, `ya no existe`, `error de red al leer` + URI, FR-6/FR-21/FR-13), la corrida sigue, y el exit code es `2` **aunque haya habido matches**. Un script que leía `0` como "hubo matches" ahora puede recibir `2` con matches en stdout. Ejercitado por VC-6, VC-13, VC-21, VC-29, VC-32, VC-33 ([`04-cobertura-vc.md`](./04-cobertura-vc.md)). Por qué no sube a 1.7: la v1.7 queda reservada para las acciones de *Excepciones registradas* que sí cambian texto. | [`03-plan.md`](./03-plan.md), Iteración 2 · *Cambio de contrato* |
| 1.7 | 2026-10-02 | **Cierre de las excepciones registradas de la revisión de la v1.5 (Iteración 2b).** Las 18 acciones abiertas, una por una, en *Cierre en la v1.7*: **+FR-29/VC-50** (otro `4xx` sobre un objeto: `no se pudo leer`, sigue, BR-3); **+FR-30/VC-48/VC-49** (ayuda y formas largas); **+VC-46/VC-47** (abreviaturas rechazadas, sintaxis aceptada); "error de red" con `408` y `429`; "al abrir" definido una vez; FR-6/FR-21 al abrir o durante la lectura; *refresh* rechazado sobre un objeto = FR-6; FR-26 con "fuente configurada" (variable o archivo de `gcloud`); definición de línea y lectura cortada dentro de la ventana; FR-2 con las reglas contextuales de `str.lower()`; FR-8 absorbe `gs://` sin bucket (VC-39 se reubica); FR-25 con Dado único y `gcsgrep: error:`; FR-23 "a causa del corte"; NFR-2 con 0 reintentos de la librería y timeout de 60 s; **NFR-4 (b) a 150 000 matches/s** sobre `ubuntu-latest`; runtime Python ≥ 3.10 y POSIX. ADRs nuevos ADR-0020…ADR-0028; ADR-0005, ADR-0016 y ADR-0017 pasan a superseded. **37 requerimientos, 50 VCs.** | [revisión de la v1.5](../../revisiones/spec-v1.5-2026-10-01.md), [`03-plan.md`](./03-plan.md) Iteración 2 · *Pasa a una Iteración 2b* |

**Qué cambió del contrato en v1.7.** Comportamiento observable que cambia respecto
de lo que la Iteración 2 entregó, todo alcance de la Iteración 2b:

- Un `408` o un `429` **sobre un objeto** dejan de abortar la corrida por el caso
  genérico: se informan como error de red y la corrida sigue (FR-13, exit `2` por
  BR-3). **Al listar**, el mensaje pasa del genérico a `error de red` (el exit `2` no
  cambia).
- Cualquier otro `4xx` sobre un objeto deja de abortar: `no se pudo leer` y la
  corrida sigue (FR-29).
- Un *refresh* de token rechazado a mitad de un objeto deja de abortar: es FR-6.
- Un archivo de `gcloud auth application-default login` mal formado deja de decir
  `no se encontraron credenciales` y dice `credenciales inválidas o vencidas`
  (FR-26).
- `gcsgrep "x" gs://` y `gs:///p`: el mensaje pasa a contener `gs://` (FR-8); el
  exit `2` no cambia. `--max -1`: el mensaje pasa a empezar con `gcsgrep: error:`
  (FR-25).
- **Python 3.9 deja de estar soportado**: `pip` rechaza la instalación
  ([ADR-0027](../../docs/adr/ADR-0027-piso-de-python-y-plataforma.md)).
- NFR-4 (b) se vuelve más exigente (150 000 matches/s). La implementación actual ya
  lo cumplía en todas las plataformas medidas.
- Los reintentos de la librería ya estaban desactivados desde la Iteración 2; la
  v1.7 lo escribe (NFR-2). El timeout de 60 s es el default de la librería, ahora
  explícito.

**Qué cambió del contrato en v1.5.** Dos clases de cambio, separadas en el plan:

- **Comportamiento que la Iteración 1 ya tiene, ahora escrito** (sus VCs van al
  Paso 0 de la Iteración 2): el plegado de `-i` (VC-43), el patrón vacío (FR-24), la
  invocación mal formada (FR-25), el límite exacto y el texto del guardrail (VC-12,
  VC-42), VC-7 y VC-22 con observables exactos, y las formas largas y `--help`.
  Ninguno cambia lo que el código hace hoy; si alguno falla, es un defecto de la
  Iteración 1.
- **Comportamiento nuevo, alcance de la Iteración 2:** FR-21 (hoy un `404` al abrir
  aborta la corrida con exit `2`), la red caída al abrir de FR-13 (hoy cae en el
  genérico y aborta), FR-22 (hoy el `\r` suelto corta la línea contra GCS, y el `\r`
  de `\r\n` queda en `<texto>` contra el doble), FR-23 (hoy sale con `120` y un
  mensaje que culpa a GCS), FR-26 (hoy el genérico), FR-27 (hoy el BOM queda en la
  línea 1), y el formato de los salteos de FR-9/FR-10, que ya eran Iteración 2.

La medición de NFR-4 (b) que pidió la revisión (2026-10-01, Apple M5, Python 3.13,
objeto de 100 MiB servido desde memoria, mejor de 3): implementación actual
~340 000–356 000 matches/s; abrir y cerrar el destino por match **~31 000** (falla
(b)); un `logging.StreamHandler` nuevo por match ~134 000; `os.fsync` por match
contra `/dev/null` ~300 000. Hay una implementación mala plausible que cae debajo
del umbral, así que (b) se mantiene y
[ADR-0017](../../docs/adr/ADR-0017-nfr-rendimiento-costo-propio.md) no se supersede.

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

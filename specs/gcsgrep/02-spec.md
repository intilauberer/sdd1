# gcsgrep — spec

> **Estado: revisada.** Sin preguntas abiertas — construida a partir de
> [`gcsgrep-base-context.md`](./gcsgrep-base-context.md), que resuelve las 10
> preguntas abiertas del borrador original ([`gcsgrep-requirements.md`](./gcsgrep-requirements.md)).
>
> Regla estructural: **cada FR y cada BR tiene un VC.** Si una línea no se puede
> verificar, no está especificada.

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

### Fuera

Cada uno de estos es una decisión tomada, no un olvido:

- **Regex** (básica o completa) — solo substring literal en v1.
- **Flags de `grep` más allá de `-i` y `-n`** (`-l`, `-c`, `-v`, `-r`,
  `--include`, etc).
- **Descompresión de `.gz`** — se saltean, no se leen.
- **Autenticación por archivo de service account explícito** — solo ADC; si
  `GOOGLE_APPLICATION_CREDENTIALS` apunta a una key, ADC ya la resuelve sola.
- **Lectura concurrente de objetos** — secuencial en v1.
- **Salida JSON** — solo formato estilo `grep`.
- **Providers que no son GCS** (S3, Azure Blob).
- **Reintentos automáticos ante fallos de red transitorios.**
- **Consistencia ante un objeto modificado mientras se lee** — riesgo conocido,
  aceptado (ver base context).
- **Escritura, borrado o modificación de cualquier objeto o permiso en GCS** —
  la herramienta es de solo lectura, siempre.

## Actores

| Actor | Descripción |
|---|---|
| **Persona usuaria** | Ejecuta `gcsgrep` en una shell y lee la salida en pantalla |
| **Script** | Ejecuta `gcsgrep` y decide en base al exit code, no al texto de salida |
| **GCS** | Fuente de los objetos; puede fallar por permisos, red, o no existir |

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
cargar el contenido completo del objeto en memoria de una vez.

> **VC-14** — Sobre un objeto simulado de **200 MB** de contenido de texto, el
> pico de memoria adicional usado por el proceso de lectura de ese objeto es
> menor a **20 MB** (medido sobre el doble de prueba que expone el stream;
> nunca se llama a un equivalente de "leer todo el archivo" sobre él).

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
> VC-10, VC-12, VC-13, VC-15), stdout no contiene ninguna línea que no sea un
> match real, y stderr no contiene la palabra `Traceback`.

---

## Tabla de trazabilidad

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
| BR-1 | VC-11 | invariante |
| BR-2 | VC-12 | guardrail |
| BR-3 | VC-13 | invariante |
| NFR-1 | VC-14 | medición |
| NFR-2 | VC-15 | falla |
| NFR-3 | VC-16 | invariante |

**16 requerimientos, 16 VCs, 0 huérfanos.**

## Preguntas abiertas

Ninguna. Las 10 preguntas del borrador original quedaron resueltas en
[`gcsgrep-base-context.md`](./gcsgrep-base-context.md).

## Qué sigue

El plan de iteraciones está en [`gcsgrep-plan.md`](./gcsgrep-plan.md).

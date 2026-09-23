# gcsgrep — base context (refinado)

> **Qué es esto.** Salida de refinar [`gcsgrep-requirements.md`](./gcsgrep-requirements.md)
> (el borrador deliberadamente subespecificado de la tarea). Cada pregunta abierta del
> borrador se resolvió acá, con su fundamento. **No es la spec.** Es la materia prima
> que consume el paso Especificar.

## La idea vaga con la que empezó

> "La experiencia de `grep`, pero apuntada a Google Cloud Storage."

## 1 · Preguntas abiertas del borrador, resueltas

### 1 · Sabor de expresiones regulares

**Elegido: búsqueda literal (substring) únicamente en v1.**

Fundamento: es el subconjunto más chico que ya resuelve el caso de uso descripto
(`gcsgrep "timeout" gs://logs/`). Evita decidir ahora qué motor de regex exponer
(POSIX básico, extendido, o el de Python) y qué caracteres escapar en la salida.
Regex queda para una iteración posterior, sin cerrarle la puerta al diseño: el
matcher vive detrás de una interfaz chica y reemplazable.

### 2 · Autenticación

**Elegido: solo Application Default Credentials (ADC).**

Fundamento: coincide con la restricción del enunciado ("nunca amplía el acceso más
allá de las credenciales de quien la invoca"). ADC es exactamente eso: usa lo que
la persona (o el entorno: metadata server, `gcloud auth application-default
login`, `GOOGLE_APPLICATION_CREDENTIALS`) ya tiene configurado. No se agrega un
flag de service-account-key en v1; si `GOOGLE_APPLICATION_CREDENTIALS` apunta a
una key, ADC ya la toma sola, así que el caso queda cubierto sin código extra.

**Sin credenciales disponibles:** error claro a stderr, exit `2` (error de
sistema, no de uso).

### 3 · Sintaxis de ubicación

**Elegido: solo `gs://bucket/prefijo`. El esquema es obligatorio.**

Fundamento: ambigüedad cero. `bucket/prefijo` sin esquema podría confundirse con
una ruta local, y el enunciado ya usa `gs://` en su propio ejemplo. Un prefijo sin
`/` final se trata como prefijo de nombre de objeto (semántica idéntica a la API
de listado de GCS: `list_blobs(prefix=...)`), no como "carpeta"; GCS no tiene
carpetas reales.

**Bucket solo (sin prefijo):** `gs://bucket/` o `gs://bucket` — equivalente,
prefijo vacío, escanea todo el bucket.

### 4 · Flags de `grep` soportados en v1

**Elegido: `-i` (case-insensitive) y `-n` (número de línea). Nada más.**

Fundamento: son los dos que pide explícitamente el enunciado para v1. `-l`, `-c`,
`-v`, `-r`, `--include` quedan para iteraciones posteriores — `-r` en particular no
aplica igual en GCS (no hay recursividad de directorios, un prefijo ya es
recursivo por naturaleza).

### 5 · Binarios y `.gz`

**Elegido: ambos se saltean en v1, sin descomprimir ni imprimir basura.**

Detección de binario: heurística tipo `grep` — si los primeros bytes leídos
contienen un byte nulo (`\x00`), se considera binario y se saltea. No se confía en
el `Content-Type` del objeto (puede estar mal seteado o ausente).

Detección de `.gz`: por extensión del nombre de objeto (`.gz`) — se saltea sin
intentar descomprimir. Descompresión al vuelo queda para una iteración posterior.

Ambos casos se reportan como "salteado" en un resumen final por stderr, no como
error — no son una falla, son objetos fuera de alcance de v1.

### 6 · Guardrails de costo

**Elegido: tope por defecto de objetos a escanear, con `--max` para ajustarlo.**

- Tope por defecto: **1000 objetos**. Antes de leer contenido, se lista el
  prefijo; si la cantidad de objetos listados supera el tope, la herramienta
  **no lee ninguno**, informa cuántos encontró y cuál es el tope, y sale con
  código `1` (falta de match/operación no completada — no es un error de
  sistema).
- `--max N` sube (o baja) el tope explícitamente. `--max 0` significa "sin
  tope" — decisión explícita e inequívoca, no un valor mágico.
- Fundamento: leer objetos de GCS tiene costo. Un tope conservador por defecto
  evita una corrida cara por accidente (un prefijo vacío o mal tipeado que
  matchea todo el bucket); `--max` le da a quien sabe lo que hace una salida
  explícita.

### 7 · Formato de salida

**Elegido: estilo `grep` — `gs://bucket/objeto:línea:texto` (o sin `:línea:` si
no se pidió `-n`).**

Fundamento: familiar para quien ya usa `grep` a diario (el público declarado en
el enunciado), y compone con `cut`, `awk`, `grep` de nuevo, etc. JSON queda para
una iteración posterior si aparece la necesidad de consumo por máquina.

### 8 · Exit codes

**Elegido: convención exacta de `grep`.**

| Código | Significado |
|---|---|
| `0` | Hubo al menos un match |
| `1` | Corrió bien, pero no hubo ningún match (incluye "se superó el tope de objetos") |
| `2` | Error: credenciales, bucket inexistente, permisos, red, argumentos inválidos |

Fundamento: permite usar `gcsgrep` como predicado dentro de un script, igual que
`grep`.

### 9 · Concurrencia

**Elegido: lectura secuencial en v1.**

Fundamento: prioridad a la corrección y a un orden de salida determinístico
(mismo orden que el listado de GCS) antes que a la velocidad. Paralelizar
lecturas es una mejora de rendimiento natural para una iteración posterior,
una vez que el comportamiento secuencial esté verificado y sirva de referencia.

### 10 · Objeto que cambia mientras se lee

**Elegido: fuera de alcance en v1, riesgo conocido y aceptado.**

Fundamento: igual que el riesgo de escritura concurrente en el ejemplo de
`taskcli` — de baja probabilidad para el caso de uso (búsquedas ad-hoc sobre
logs), y GCS no da un mecanismo simple para "leer una generación fija" sin
complicar la v1. Queda anotado acá para que sea una decisión consciente, y
aparece como no-objetivo explícito en la spec.

---

## 2 · Notas de diseño

### Streaming, no descarga completa

Cada objeto se lee con el streaming del cliente de GCS (`blob.open("r")` /
`download_as_stream`), línea por línea, sin materializar el objeto completo en
memoria. Esto es lo que hace posible operar sobre objetos grandes con memoria
acotada (ver NFR de memoria en la spec).

### Superficie de comandos

```
gcsgrep [-i] [-n] [--max N] <patrón> <gs://bucket/prefijo>
```

Un solo subcomando (a diferencia de `taskcli`, acá no hay verbos distintos: la
herramienta *es* el verbo "buscar"). Sin flags, mapea 1:1 con `grep patrón
archivo`.

### Esquema de arquitectura

```
cli      → parsea argv, arma la config de búsqueda, traduce resultado a exit code
core     → orquesta: aplica el guardrail de tope, filtra binarios/.gz, matchea líneas
gcs      → única capa que habla con la API de GCS: listar objetos, abrir streams
```

La dependencia va en una sola dirección: `cli → core → gcs`. `core` no sabe que
existe una terminal ni argv, y no importa `google.cloud.storage` directamente:
recibe una función de listado y una función de apertura de stream como
colaboradores. Eso permite testear toda la lógica de matcheo, guardrail y
skip de binarios **sin credenciales de GCP ni red**, con un `gcs` falso en los
tests. La integración real contra un bucket de prueba se verifica aparte, una
vez que la lógica ya está probada offline.

### Actores

| Actor | Interacción |
|---|---|
| Persona usuaria | Ejecuta `gcsgrep` en una shell interactiva, lee la salida |
| Script | Ejecuta `gcsgrep` y decide en base al **exit code** |
| GCS | Fuente de los objetos; puede fallar (permisos, red, no existe) |

### Riesgos conocidos (no-objetivos explícitos)

- Objeto modificado mientras se lee (ver punto 10 arriba).
- Acceso concurrente de dos invocaciones de `gcsgrep` entre sí: no comparten
  estado, no aplica (no hay escritura).

---

## Qué sigue

Este documento alimenta el paso **Especificar**. El resultado está en
[`gcsgrep-spec.md`](./gcsgrep-spec.md).

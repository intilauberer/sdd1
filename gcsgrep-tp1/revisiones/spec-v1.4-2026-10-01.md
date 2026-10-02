# Revisión de spec: gcsgrep v1.4 — (specs/gcsgrep/02-spec.md)
- Commit: 74ddbd74b6f83317b277d2f0a03de0124c42aa10 · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 20 BR: 3 NFR: 4 VC: 31

> Revisión adversarial previa a planificar la Iteración 2, con el agente de
> `.kiro/agents/prompts/corrector-specs.md`. Insumos leídos: la spec, el base
> context, los 18 ADRs, la corrección de la cátedra y su respuesta. El código y
> `docs/integracion-gcs.md` se leyeron **solo como evidencia** de que un hueco de la
> spec produce divergencias reales; no son objeto de esta revisión. Los números de
> línea sin path son de `specs/gcsgrep/02-spec.md` en el commit de arriba.

## Resumen

La v1.4 es una respuesta seria a la corrección. De las 19 acciones, 16 quedaron
resueltas de verdad, con texto en un FR/BR/NFR y un VC concreto. FR-3/FR-4 y
FR-12/FR-14 son atómicos. NFR-1 y NFR-4 llevan métrica, número y condición en el
enunciado. Hay VC de punta a punta contra GCS real (VC-31). Los permisos IAM, el
patrón literal, el orden, el prefijo sin `/`, los 0 bytes, la última línea sin
`\n`, la ventana de 8192 bytes y la codificación están en la spec con VC. Las
tablas de trazabilidad cuadran mecánicamente (M1, M2).

Hay dos bloqueos, y los dos salen de **cómo se partió FR-6 (acción 1b)**:

1. **FR-13 repite la forma exacta que la cátedra marcó en FR-6**: tres alternativas
   en el Dado ("conexión cortada, timeout o error transitorio del servidor") (2.3).
2. **Al angostar FR-6 a "permiso denegado al abrir" y FR-13 a "después de haber
   empezado", el camino "objeto ilegible" perdió cobertura.** Un objeto que se borra
   entre el listado y la lectura (404), o un error de red **al abrir**, ya no tiene
   requerimiento. Dos ADRs vigentes (0010 y 0013) siguen diciendo que ese caso "lo
   cubre FR-6" y no aborta. Es el mismo modo de falla que H-13: el actor GCS "no
   existir" se abrió por bucket y por prefijo, y nadie miró el objeto (3.3).

La respuesta afirma "0 decisiones con comportamiento observable que vivían solo en
ADRs" (`docs/respuesta-correccion-catedra.md:23`). No es cierto: quedan al menos
ADR-0010/0013 (objeto borrado), ADR-0005 (resumen final de salteados), ADR-0018
(`\x00` fuera de la ventana sale por stdout), ADR-0004 (flags no soportados se
rechazan) y ADR-0011 (`| head` corta "como `grep`"). El último se probó: hoy sale
con código `120` y culpa a GCS. Ninguno es grave por separado, pero juntos
desmienten el resumen de la respuesta.

M3: los únicos hits son "todo/todos" en castellano (:13, :211, :387, :419, …) y
"pendiente" en la fila histórica de la v1.1 (:793). Ninguno deja un valor sin
decidir. M4: un hit, "*correctamente*" (:817), en la prosa del historial y fuera de
cualquier FR/NFR/VC. M5: dentro de VCs, `list_blobs`/módulo `gcs` (VC-11, :468-470),
`tracemalloc` (VC-14, :529), "colaborador de `gcs`" (VC-16 (b), :578), "colaborador
de credenciales del doble" (VC-23, :375) y `cli.main` (VC-30, :618). VC-11 es por
naturaleza una inspección de código, así que no cuenta. Los de VC-14 y VC-30 cuentan
porque hacen que el VC mida otra cosa que su NFR (ver 4.1), y el de VC-23 porque
nombra un colaborador que no existe (ver 3.2). M6: "todos los" en FR-7 (:211), FR-16
(:387) y FR-18 (:419), "nunca" en BR-1 (:459-460), "todas las" en NFR-4 (:616), cada
uno con su VC (VC-7, VC-24, VC-26, VC-11, VC-30). Los de :88-89, :530, :590-600 y
:704-731 son prosa. VC-7, el que acota FR-7, es débil (ver 3.2).

## Hallazgos por dimensión

### 1. Propósito y alcance — PASS

- Suggestion (1.5) · :52: "Un único comando: `gcsgrep [-i] [-n] [--max N] <patrón> gs://bucket/prefijo`". El código acepta además `--ignore-case`, `--line-number` y `-h/--help` (`gcsgrep/cli.py:27-28`, argparse). Ni *Dentro* ni *Fuera* los nombran, así que la superficie del CLI no queda cerrada por la spec. Alcanza con una línea en *Dentro* que diga "formas largas equivalentes" o con excluirlas.
- 1.1, 1.2, 1.3, 1.4, 1.6: sin hallazgos. El propósito dice por qué (:44-46, "sin descargarlos primero"). *Fuera* tiene 11 ítems concretos, cada uno con su ADR (:64-89). Hay tres actores no humanos (:96-98). El alcance diferido es solo un puntero (:782-786). El base context está enlazado (:9).

### 2. Completitud y consistencia — FAIL

- **Issue (2.3)** · :329-331 (FR-13): "la lectura de uno de ellos se interrumpe por un **error de red** (conexión cortada, timeout o error transitorio del servidor)". El Dado tiene tres situaciones, la misma forma que la cátedra marcó en FR-6 v1.3 ("uno no se puede leer (permiso denegado o error transitorio)", `docs/correccion-catedra-iteracion-1.md:35`). No son grafías equivalentes de lo mismo: un reset de TCP, un timeout de lectura y un 5xx del servidor son situaciones distintas. Además, "error transitorio del servidor" (un 503) no es un error de red en sentido estricto. VC-21 (:338-343) ejercita una sola ("levanta un error de red", sin decir cuál). La misma lista se usa implícitamente en NFR-2 (a) (:541-542), así que lo que es "error de red" **al listar** tampoco está definido.
- Warning (2.7) · Dos VCs agregan comportamiento que su requerimiento no dice:
  - :548 (VC-15): "(no la representación cruda de la excepción de la librería)". NFR-2 (a) (:541-542) solo pide que el mensaje contenga `error de red` y el URI del bucket. Además no es observable tal como está escrito: ¿qué texto lo viola?
  - :356 (VC-22): "no contiene `no existe`". FR-14 (:350-352) solo pide `gs://<bucket>` y `sin permiso`. La intención está en la prosa de FR-12 (:320-321), pero no en el Entonces de FR-14. Es el mismo caso que VC-8 en la corrección (`correccion-catedra-iteracion-1.md:38`).
- Warning (2.8) · :162-163 (FR-3) y :174-175 (FR-4): "`<texto>` es la línea completa del objeto sin su terminador de línea". La spec no dice **qué es un terminador de línea**. FR-20 (:444) solo habla de `\n`. Dos implementaciones razonables divergen con `\r\n` (¿`<texto>` termina en `\r`?) y con un `\r` suelto (¿parte la línea y corre los números de `-n`?). La del repo hereda los *universal newlines* del modo texto de Python (`blob.open("r")` + `rstrip("\n")`, `gcsgrep/core.py`), así que trata `\r` suelto como fin de línea. Esa es una decisión que nadie tomó. Es un borde de 3.4 (codificación/terminador), pero se registra acá una sola vez.
- Suggestion (2.8) · :147-149 (FR-2): "sin distinguir mayúsculas". No dice con qué plegado de caso. `str.lower()` (el del repo) y `str.casefold()` difieren en `ß`/`SS` y en la `İ` turca, y una implementación ASCII-only difiere en `Á`/`á`. Con FR-17 fijando UTF-8, el borde existe.
- Suggestion (2.8) · :405 (FR-17): "se decodifica como UTF-8". No dice qué pasa con un BOM UTF-8 (`EF BB BF`) al principio. Con `utf-8`, el primer `<texto>` de la salida empieza con `U+FEFF`; con `utf-8-sig`, no.
- 2.1: sin hallazgos (20/20 FRs en Dado/Cuando/Entonces). 2.3 en el resto: FR-3, FR-4, FR-6, FR-12, FR-14 y FR-15 a FR-20 son atómicos. FR-7 (:209) mantiene dos grafías equivalentes, que no cuentan.

### 3. Casos borde y verificabilidad — FAIL

- **Issue (3.3)** · Un objeto que falla **al abrirse** por una causa que no es permiso no tiene requerimiento:
  - :193-194 (FR-6): "GCS responde **permiso denegado** al abrir uno de ellos".
  - :330-331 (FR-13): "se interrumpe por un error de red … **después de haber empezado**".
  - :543-544 (NFR-2 (b)): "ese objeto no se vuelve a abrir; la corrida sigue según FR-13". Pero FR-13 no cubre un fallo de red al abrir.
  - :739-740 (tabla actores → requerimiento): "No existir" se abrió en "el bucket" y "el prefijo (0 objetos)". **El objeto no está.**

  Del otro lado, `docs/adr/ADR-0010-objeto-modificado.md:29-31` dice "Un objeto borrado entre el listado y la lectura se comporta como un objeto ilegible: lo cubre FR-6 y fuerza exit `2` por BR-3". `docs/adr/ADR-0013-frontera-de-excepciones.md:76-78` dice "`ObjetoNoEncontrado` … Hoy aborta; que no aborte es FR-6". `docs/adr/ADR-0016-sin-reintentos.md:22-23` dice que "la apertura y lectura de cada objeto" se intentan una vez. Desde la v1.4, FR-6 ya no dice eso. La Iteración 2 puede dejar que un 404 al abrir aborte la corrida (que es lo que hace hoy `gcsgrep/gcs.py:45-48`) y pasar **todos** los VCs. Otra puede seguir con el resto. Las dos cumplen la spec, y la salida difiere: los matches de los objetos siguientes aparecen o no. Tampoco está en la lista de errores previstos de NFR-3 (:568-569), así que con `GCSGREP_DEBUG=1` ni siquiera está definido si imprime traceback. Es la regresión de la acción 1b: la cátedra contaba "ilegible" como cubierto por FR-6 (`correccion-catedra-iteracion-1.md:52`), y al partirlo nadie volvió a mirar la tabla de actores. Es el mismo mecanismo que H-13.
- Warning (3.2) · Cuatro VCs sin observable concreto:
  - :489 (VC-12): "stderr menciona la cantidad encontrada y el tope". Es la forma literal que 3.2 marca. BR-2 (:479-480) tampoco fija un texto.
  - :506-508 (VC-13): "uno que falla al leerse … informa el fallo por stderr". No dice qué falla (¿permiso? ¿red?) ni con qué texto. FR-6 y FR-13 ya tienen texto literal; VC-13 debería decir cuál de los dos ejercita.
  - :214-216 (VC-7): "encuentra matches en ambos si el patrón está en ambos". No tiene exit code, ni stdout exacto, ni el caso sin `/` (`gs://bucket`) que FR-7 (:209) incluye.
  - :248-251 (VC-20): no tiene exit code ni stdout/stderr exactos en ninguna de las dos mitades, y no dice si el `\x00` del offset 8192 está **en la misma línea** que `timeout` (ver 5.6, ADR-0018).
- Warning (3.2) · :375 (VC-23): "Con el colaborador de credenciales del doble simulando 'sin ADC'". Ese colaborador no existe: el contrato de `core` tiene dos colaboradores, `list_objects` y `open_text_stream` (`specs/gcsgrep/01-base-context.md:138-141`), y ninguno resuelve credenciales. Tal como está escrito, para ejecutar el VC hay que inventar primero la costura. O el VC se reescribe sobre lo que el doble expone ("`list_objects` levanta el error de dominio de credenciales ausentes"), o la Iteración 2 tiene que agregar la costura y la spec no lo dice. Además, :378-379 dice "Contra GCS real, es el chequeo de integración I-6", pero I-6 solo exige "mensaje legible" (`docs/integracion-gcs.md:42`), no los dos textos de FR-15.
- Warning (3.3) · Entrada inválida fuera del argumento de ubicación. :220 (FR-8): "un argumento de ubicación que no empieza con `gs://`". No hay requerimiento para: un flag no soportado (`gcsgrep -l x gs://b/`; `docs/adr/ADR-0004-flags-v1.md:33` descarta "aceptarlos e ignorarlos", así que **decidió** rechazarlos, pero la spec no lo dice); `--max -1` o `--max abc`; `gs://` o `gs:///p` (empiezan con `gs://` pero no tienen bucket); y faltan argumentos. El código ya decide los cuatro con exit `2` y mensajes propios (`gcsgrep/cli.py:63-68`, `gcsgrep/core.py:58-59`, argparse), sin ningún contrato que lo sostenga.
- Warning (3.3) · :361-362 (FR-15): "Application Default Credentials no resuelve **ninguna** credencial". El recurso "credenciales" tiene un segundo modo de falla: credenciales que se resuelven pero no sirven (token vencido o revocado, `GOOGLE_APPLICATION_CREDENTIALS` apuntando a un archivo inexistente o mal formado). Cae en el genérico de NFR-3 (exit `2`, sin traceback), así que está acotado y es Warning, no Issue. Pero el mensaje que manda a `gcloud auth application-default login` es justo el que necesita quien tiene un token vencido, y la spec no se lo da.
- Warning (3.3) · Corte del consumidor de stdout. `docs/adr/ADR-0011-salida-incremental.md:43-44`: "Se comporta como `grep` en un pipe: `gcsgrep … | head -5` puede cortar temprano". I-5 lo usa (`docs/integracion-gcs.md:31`). La spec no dice qué pasa cuando stdout se cierra. **Se probó** con el código actual y el doble (200 000 matches, `| head -1`): stderr dice `gcsgrep: error inesperado al acceder a gs://b: BrokenPipeError: [Errno 32] Broken pipe` más `Exception ignored on flushing sys.stdout`, y el exit code es **`120`**. No es `0`, `1` ni `2` (ADR-0008), y le echa la culpa a GCS. Es el caso de uso central de ADR-0007 ("componible con `cut`, `awk`, `sort`, `grep`") y no tiene requerimiento.
- Warning (3.4) · :128-133 (FR-1): patrón vacío. `gcsgrep "" gs://b/p/` es un substring literal válido que matchea **todas** las líneas de todos los objetos. Puede ser el comportamiento querido (es lo que hace `grep ""`), o un error de uso. Es una entrada vacía de la lista de 3.4 y no tiene ni decisión ni VC.
- Warning (3.4) · :477-480 (BR-2): "Si la cantidad **supera** el tope". La regla está definida (> tope), pero el límite exacto no tiene VC. VC-12 (:487) prueba 1001 objetos, y nadie prueba que **1000** objetos con el tope por defecto (o N objetos con `--max N`) sí se lean. Es justo el "riesgo de regresión" que `docs/adr/ADR-0006-guardrail-de-costo.md:34-36` anota ("puede bloquear corridas chicas").
- Suggestion (3.6) · :640 (VC-31 (3)): `gs://gcsgrep-test-no-existe-jamas/`. Los nombres de bucket son globales: si un tercero lo crea, el listado pasa a dar 403 (FR-14) y el VC falla por una razón ajena. Conviene que el VC diga "un nombre de bucket que se verifica inexistente antes de correr", o que genere un nombre aleatorio.
- **3.5 · FR-18 (feliz): se pudo escribir el test sin decidir nada.** Datos: `gs://b/logs/a.txt`, `gs://b/logs-other/b.txt` y `gs://b/otros/c.txt`, los tres con `timeout\n`. Comando 1: `gcsgrep "timeout" gs://b/logs` → stdout exacto `gs://b/logs-other/b.txt:timeout\ngs://b/logs/a.txt:timeout\n` (FR-16: `-` 0x2D < `/` 0x2F), stderr vacío (NFR-3), exit `0`. Comando 2: `gcsgrep "timeout" gs://b/logs/` → stdout exacto `gs://b/logs/a.txt:timeout\n`, stderr vacío, exit `0`. **Se ejecutó** contra el código actual con `RecordingFakeGCS` (y un stub del SDK, porque el entorno de revisión no tenía las dependencias): pasa. Es consistente con lo que dice el historial (:800, FR-18 "no cambia").
- **3.5 · FR-13 (falla): se pudo escribir, pero hubo que decidir dos cosas que la spec no dice.** Datos: `gs://b/p/a.txt`, cuyo stream emite `hit uno\n` y después levanta un error de red, y `gs://b/p/b.txt` con `hit dos\n`. Comando: `gcsgrep "hit" gs://b/p/`. stdout exacto: `gs://b/p/a.txt:hit uno\ngs://b/p/b.txt:hit dos\n`. stderr: una línea que contiene `error de red al leer` y `gs://b/p/a.txt`, y no contiene `Traceback`. Exit `2` (BR-3). Aperturas: `p/a.txt` ×1 y `p/b.txt` ×1 (VC-29). Decisiones: (1) **qué excepción es "un error de red"** en el borde del colaborador (se eligió `ConnectionError`; la spec da tres ejemplos y ninguna definición, ver Issue 2.3); (2) **si un fallo al abrir `a.txt`, antes del primer byte, también es FR-13**. Se evitó poniendo el fallo después de una línea, pero un test de "red caída al abrir" no se puede escribir (ver Issue 3.3). Ejecutado contra el código actual, falla como se esperaba (es Iteración 2): stdout trae solo `a.txt:hit uno`, stderr dice `error inesperado … ConnectionError` y el exit es `2`, **por el genérico**. El test lo detecta por el stdout y por el texto de stderr, no por el exit code. Es el riesgo que ADR-0013:70-75 anota: el `except Exception` hace que la corrida *parezca* cumplir BR-3.
- 3.1: sin hallazgos. Los 23 FR+BR tienen un VC debajo de su encabezado y en la tabla, y la tabla coincide con los encabezados (M2). 3.6: VC-31 está en la spec, declarado contra GCS real, y excluye dobles y emuladores (:631-632). Que no se haya ejecutado (ADR-0015) no lo invalida como especificación.

### 4. Requerimientos no funcionales — WARN

- Warning (4.1) · En dos NFRs, el VC no mide la métrica del enunciado:
  - :516 (NFR-1): "pico de memoria adicional **del proceso**", contra :529 (VC-14): "medido con `tracemalloc`". `tracemalloc` mide asignaciones del heap de Python, no la memoria del proceso. Un buffer nativo del SDK o de `ssl` no aparece. Una implementación que pase VC-14 puede no cumplir NFR-1. O el enunciado dice "memoria asignada por Python (tracemalloc)", o el VC mide RSS.
  - :606-607 (NFR-4): "tasa de procesamiento de punta a punta **del proceso** `gcsgrep` (desde `argv` hasta el exit code…)", contra :618 (VC-30): "Corriendo `cli.main`" en el mismo proceso del test. El arranque del intérprete y los imports quedan fuera de lo que se mide. El VC ata la medición a un nombre de función (M5).
  - Menor, en el mismo par: NFR-1 usa **MB** (:517-518) y NFR-4 usa **MiB** (:611). Hay que fijar una unidad.
- Warning (4.2) · :616 (NFR-4 (b)): "≥ 50 000 matches/s". VC-30 (:620-622) muestra que el umbral **(a)** discrimina ("una implementación que lee el stream de a un carácter … ~15 MiB/s y falla"), pero no muestra ninguna implementación mala que falle **(b)**. ADR-0017 (:52-53) dice que (b) "acota el costo del `flush` por match", pero no midió el contraste: con lo medido (~355 000 matches/s), ¿qué implementación plausible cae debajo de 50 000? Si ninguna, el umbral (b) no protege nada, que es la objeción original de ADR-0012.
- 4.3, 4.4, 4.5: sin hallazgos. Cada condición enumerada tiene su VC o su parte de VC: NFR-1 (a)/(b), NFR-2 (a) VC-15 y (b) VC-29, NFR-4 (a)/(b). NFR-2 fija 0 reintentos, y "mejor de 3 corridas" es una política explícita. La seguridad la cubren BR-1 y los permisos mínimos; el costo, BR-2.

### 5. Tecnología y fundamento — WARN

- Warning (5.6) · `docs/adr/ADR-0005-binarios-y-gz.md:22-24`: "Ambos casos se reportan como 'salteado' en un **resumen final** por **stderr**". `specs/gcsgrep/01-base-context.md:107-108` repite "el resumen de salteados por stderr". FR-9 (:237-238) y FR-10 (:257-258) fijan **una línea por objeto**, pero no dicen **cuándo** se escribe ni si además hay un resumen. ADR-0018 "precisa" a ADR-0005 (:5) y no toca este punto. Se nota en el VC: :244-245 (VC-9), "stderr contiene exactamente una línea `gcsgrep: salteado (binario): …`", se puede leer como "stderr tiene exactamente una línea" o como "esa línea aparece una vez". Si la Iteración 2 implementa el resumen final del ADR, la primera lectura falla y la segunda pasa.
- Warning (5.6) · `docs/adr/ADR-0018-ventana-binaria-y-codificacion.md:54-56`: "si una línea con match contiene el `\x00`, ese byte sale por stdout". Es comportamiento observable, consecuencia de FR-9 + FR-4, y choca con lo que NFR-3 promete de stdout ("únicamente líneas de match", :557). La spec no lo dice, y VC-20 (:250-251) no fija dónde está el `\x00` (ver 3.2).
- Suggestion (5.6) · ADRs aceptados con referencias que la v1.4 dejó viejas, sin efecto observable: `ADR-0009-lectura-secuencial.md:25-26` ("Esta decisión es la razón por la que no hay un NFR de rendimiento en v1"); `ADR-0015-verificacion-real-declinada.md:56` ("La mitad 'sin permiso' de FR-12 / VC-18", hoy FR-14/VC-22) y :59 ("El NFR de rendimiento de la Iteración 3"); `ADR-0013-frontera-de-excepciones.md:6,51` (FR-12 como 404 **y** 403). Por la regla "un ADR aceptado no se edita" (:16-17), la salida es una nota "Referencias actualizadas por la spec v1.4" en `docs/adr/README.md`, no editar los ADRs.
- Referencias, sin duplicar: el comportamiento de ADR-0010/0013 (objeto borrado) está en el Issue 3.3; ADR-0004 (flags no soportados) y ADR-0011 (`| head`) están en los Warnings 3.3.
- 5.1–5.5: sin hallazgos. Los permisos mínimos están nombrados, con el rol más chico y lo que pasa sin cada uno (:107-120). El literal está justificado (ADR-0001). Cada decisión nueva tiene ADR con alternativas: 0016 (reintentos), 0017 (NFR-4) y 0018 (ventana y codificación). Los trade-offs están reconocidos, incluido el costo del `flush` (ADR-0017). `--max 0` y `GCSGREP_DEBUG=1` son excepciones explícitas, opt-in y no son el default (:484-485, :564-571).

### 6. Simplicidad — PASS

- Suggestion (6.4) · "El salteo no afecta el exit code" está escrito cuatro veces: FR-9 (:238-239), FR-10 (:258-259), FR-19 (:435, "no afecta el exit code") y BR-3 (:497-498, "Los objetos salteados … no son errores de lectura"). Conviene dejarlo en BR-3, que es la regla de exit codes, y que los FRs la referencien, como se hizo con "sin traceback" en NFR-3.
- 6.1–6.3: sin hallazgos. Lo nuevo de la v1.4 se justifica por la corrección (FR-15 a FR-20, NFR-4) o es un camino de falla (FR-13, FR-14). No hay flags nuevos.

### B. Extensión brownfield — no aplica

`gcsgrep` es el TP1 greenfield. B1–B9 son para `tmux-ssh-tp2/`.

### Seguimiento de las 19 acciones de la corrección

| # | Acción | Estado | Evidencia |
|---|---|---|---|
| 1a | Partir FR-4 | ✅ Resuelta | FR-3 (:156-167) con `-n`, FR-4 (:169-180) sin `-n`; VC-3/VC-4 con stdout exacto, sin "correctamente" |
| 1b | Partir FR-6 | ⚠️ **Resuelta en la forma, con dos regresiones** | FR-6 (:191-205) es atómico, pero FR-13 (:329-331) reintroduce la alternativa en el Dado (Issue 2.3), y el corte dejó sin cubrir el objeto que falla al abrir por 404 o por red (Issue 3.3) |
| 1c | Partir FR-12 | ✅ Resuelta | FR-12 (:295-325) y FR-14 (:345-357), cada uno con su mensaje. VC-22 exige algo que FR-14 no dice (Warning 2.7, menor) |
| 2 | NFR de rendimiento | ✅ Resuelta, con dos Warnings | NFR-4 (:604-622) tiene métrica, número y condición en el enunciado. El VC mide `cli.main` y no el proceso (4.1), y (b) no muestra que discrimine (4.2) |
| 3 | Umbral de NFR-1 al enunciado | ✅ Resuelta, con un Warning | :516-520. `tracemalloc` no mide "memoria del proceso" (4.1) |
| 4 | FR-8 nombra `gs://` | ✅ Resuelta | :222-224 |
| 5 | FR-1 literal + VC con metacaracteres | ✅ Resuelta | :128-130, VC-19 (:140-143) |
| 6 | Sin credenciales → FR/BR + VC | ✅ Resuelta en la spec; VC no ejecutable tal como está | FR-15 (:359-379) y actor nuevo. VC-23 depende de una costura que no existe (3.2); falta el caso de credenciales inválidas (3.3) |
| 7 | Orden de salida | ✅ Resuelta | FR-16 (:381-398), VC-24 con stdout exacto |
| 8 | VC-9 concreto | ✅ Resuelta, con ambigüedad | FR-9 y VC-9 con línea literal y exit. "Contiene exactamente una línea" no aclara si puede haber un resumen (5.6, ADR-0005) |
| 9 | Prefijo sin `/` | ✅ Resuelta (verificada ejecutando el test de 3.5) | FR-18 (:414-428) |
| 10 | Objeto de 0 bytes | ✅ Resuelta | FR-19 (:430-440) |
| 11 | Última línea sin `\n` | ✅ Resuelta | FR-20 (:442-451). Aparte: "terminador de línea" no está definido para `\r\n`/`\r` (Warning 2.8, hallazgo nuevo) |
| 12 | VC de punta a punta real | ✅ Resuelta (declarado, sin ejecutar por ADR-0015) | VC-31 (:626-649) |
| 13 | VC de NFR-2 al leer | ⚠️ **Parcial** | VC-29 (:551-553) existe, pero NFR-2 (b) (:543-544) remite a FR-13, que no cubre el fallo de red **al abrir** el objeto (Issue 3.3) |
| 14 | Permisos IAM mínimos | ✅ Resuelta | :107-120, BR-1 (:461-463) |
| 15 | ADR de reintentos | ✅ Resuelta | ADR-0016, con 4 razones y 4 alternativas |
| 16 | `GCSGREP_DEBUG` | ✅ Resuelta | NFR-3 (:564-571), VC-16 (c). La lista de "previstos" no incluye el objeto borrado (Issue 3.3) |
| 17 | Bytes inspeccionados para `\x00` | ✅ Resuelta, VC flojo | FR-9 (:232-233), ADR-0018. VC-20 sin observables exactos (3.2) |
| 18 | Codificación | ✅ Resuelta | FR-17 (:400-412), VC-25 con bytes y stdout exactos. BOM sin decidir (Suggestion 2.8) |
| 19 | "Sin traceback" solo en NFR-3 | ✅ Resuelta | :560-562; NFR-2 la referencia (:539) |

**Resultado: 17 de 19 resueltas, 2 parciales (1b y 13).** Las dos parciales tienen la misma causa.

## Veredicto general   NEEDS WORK

Fallan la dimensión 2 (FR-13 no es atómico) y la 3 (el objeto que falla al abrir
por algo que no es permiso quedó sin requerimiento). Las dos son regresiones de una
misma acción, se arreglan con texto, sin rediseño, y **afectan directamente lo que
va a implementar la Iteración 2**: si se planifica con esta spec, el plan de FR-6 /
FR-13 / BR-3 hereda el hueco. No hace falta reescribir. La 3 no falla por cobertura:
cero huérfanos, tests escribibles y un VC real. Los Warnings se pueden resolver en
la misma v1.5 o quedar registrados, pero los dos Issues bloquean planificar.

## Acciones (priorizadas)

Cambios propuestos para una **v1.5**. No se aplicaron.

1. **[MUST]** Definir "error de red" una sola vez y sacar la alternativa del Dado de FR-13 (`specs/gcsgrep/02-spec.md:329-331`, :541-542). Propuesta: en NFR-2, antes de las condiciones, "*Error de red*: la operación no obtiene una respuesta HTTP completa de GCS (conexión rechazada o cortada, timeout) o recibe un 5xx. Un 403 o un 404 no es error de red." FR-13, Dado: "…donde la lectura de uno de ellos falla por un error de red (definido en NFR-2)…". VC-21 queda como está.
2. **[MUST]** Cubrir el objeto que falla al abrirse por algo que no es permiso (`specs/gcsgrep/02-spec.md:193-194`, :330-331, :543-544, :739-740). Propuesta mínima:
   - **FR-21 · Un objeto que desapareció entre el listado y la lectura no aborta la corrida.** Dado un objeto que aparece en el listado y para el que GCS responde *no encontrado* al abrirlo; Entonces stderr tiene una línea con `ya no existe` y `gs://<bucket>/<objeto>`, la corrida sigue, y el exit sale de BR-3. **VC-32** con `a.txt` (match), `b.txt` (404 al abrir) y `c.txt` (match): stdout exacto con `a` y `c`, esa línea en stderr, exit `2`.
   - FR-13: sacar "después de haber empezado", o agregar a su Dado "al abrirlo o durante la lectura", con un VC-33 de red caída al abrir (0 líneas emitidas, la corrida sigue, `b.txt` se abre 1 vez).
   - BR-3 (:495): "(FR-6, FR-13, FR-21)". NFR-3 (:568-569): agregar FR-21 a los previstos.
   - Tabla actores → requerimiento: fila "GCS · **No existir** — un objeto listado (borrado antes de leerlo) · FR-21 · VC-32", con la nota de que es el mismo caso que H-13.
3. **[SHOULD]** Fijar qué es un terminador de línea (`specs/gcsgrep/02-spec.md:162-163`, :174-175, :444). Propuesta en FR-20 o en una definición común: "Una línea termina en `\n`. Un `\r` inmediatamente antes del `\n` se quita de `<texto>`. Un `\r` suelto es parte de la línea." Agregar un VC con `uno\r\ndos\rtres\n` y `-n`.
4. **[SHOULD]** Reemplazar en VC-12 (`:489`) "stderr menciona" por un texto literal fijado en BR-2 (:479-480) (por ejemplo, una línea que contiene `1001 objetos` y `tope es 1000`). Reescribir VC-13 (:506-508) sobre la causa concreta de FR-6 o FR-13, con su texto. Darle a VC-7 (:214-216) stdout exacto, exit `0` y la grafía `gs://bucket`. Darle a VC-20 (:248-251) exit, stdout y stderr exactos, y la posición del `\x00` respecto de la línea con `timeout`.
5. **[SHOULD]** Agregar un FR de entrada inválida del CLI (`:220`), con un VC por caso: flag no soportado, `--max` negativo o no numérico, `gs://` sin bucket y faltan argumentos → exit `2`, stdout vacío, 0 llamadas de listado. Lo que el código ya hace, escrito como contrato, y lo que decidió ADR-0004:33.
6. **[SHOULD]** Decidir el corte de stdout por el consumidor (ADR-0011:43-44). Propuesta: "Si stdout se cierra antes de terminar (`| head`), `gcsgrep` deja de leer y termina sin escribir nada en stderr", con el exit code elegido (`0` si ya emitió algún match, o el de SIGPIPE como `grep`) y un VC con `| head -1` sobre 200 000 matches. Hoy da `120` y un mensaje que culpa a GCS.
7. **[SHOULD]** Decidir el patrón vacío (`:128-133`): o matchea todas las líneas (como `grep ""`), o es un error de uso con exit `2`. En los dos casos, con VC.
8. **[SHOULD]** Agregar a BR-2 un VC del límite exacto (`:487-491`): 1000 objetos sin `--max` → se leen. Con `--max 3` y 3 objetos → se leen; con 4 → exit `1`.
9. **[SHOULD]** Reescribir VC-23 (`:375-379`) sobre la costura que existe ("`list_objects` levanta el error de dominio de credenciales ausentes"), o declarar la costura en la spec. Alinear I-6 (`docs/integracion-gcs.md:42`) con los dos textos de FR-15.
10. **[SHOULD]** Agregar a FR-15 (`:361-362`), o como FR aparte, las credenciales que se resuelven pero no sirven (vencidas, revocadas, archivo de key inválido), con su mensaje y su VC.
11. **[SHOULD]** Alinear métrica y VC en NFR-1 (`:516` y :529) y NFR-4 (`:606-607` y :618): o los enunciados dicen lo que se mide (heap de Python con `tracemalloc`; `cli.main` en el mismo proceso), o los VCs miden el proceso (RSS; un subproceso `gcsgrep`). Unificar MB/MiB.
12. **[SHOULD]** Mostrar que NFR-4 (b) discrimina (`:616`, :620-622). Medir una implementación mala plausible (por ejemplo, abrir y cerrar stdout por match, o `print` + `os.fsync`) y dejar el número en VC-30, o bajar (b) a un umbral que alguna implementación plausible falle, o justificar en ADR-0017 por qué igual se mantiene.
13. **[SHOULD]** Precisar el formato de stderr de FR-9/FR-10 (`:237-238`, :257-258): cada línea de salteo se escribe en el momento del salteo y **no** hay resumen final, lo que contradice explícitamente ADR-0005:22-24. VC-9 (:244-245) y VC-10: "stderr es exactamente esta línea". Si se quiere el resumen, que esté en la spec con su texto.
14. **[SHOULD]** Decir en FR-9 o FR-4 que un `\x00` posterior a la ventana se trata como cualquier otro byte y sale tal cual por stdout si está en una línea con match (ADR-0018:54-56), y fijarlo en VC-20.
15. **[SHOULD]** Agregar a FR-14 (`:350-352`) que el mensaje no contiene `no existe`, como ya exige VC-22. Agregar a NFR-2 (a) (`:541-542`) un observable concreto en lugar de "no la representación cruda de la excepción" de VC-15 (:548), o sacarlo del VC.
16. **[COULD]** Fijar el plegado de caso de `-i` (`:147-149`): `casefold`, `lower` o solo ASCII. Agregar un VC con un carácter no ASCII.
17. **[COULD]** Decidir el BOM UTF-8 en FR-17 (`:405`) y agregar un VC.
18. **[COULD]** Dejar "el salteo no afecta el exit code" solo en BR-3 (`:497-498`) y que FR-9, FR-10 y FR-19 la referencien.
19. **[COULD]** Nombrar en *Dentro* (`:52`) las formas largas `--ignore-case`/`--line-number` y `--help`, o excluirlas.
20. **[COULD]** Hacer que VC-31 (3) (`:640`) no dependa de que nadie registre un nombre de bucket global.
21. **[COULD]** Registrar en `docs/adr/README.md` las referencias de ADRs aceptados que la v1.4 dejó viejas (ADR-0009:25-26, ADR-0013:6/51, ADR-0015:56/59), sin editar los ADRs.

VEREDICTO: NEEDS WORK

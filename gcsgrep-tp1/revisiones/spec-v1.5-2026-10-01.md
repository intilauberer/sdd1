# Revisión de spec: gcsgrep v1.5 — (specs/gcsgrep/02-spec.md)
- Commit: 4e4847d7f1a597e5c07eed1364a30467a380ea95 · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 27 BR: 3 NFR: 4 VC: 44

> Revisión adversarial previa a planificar la Iteración 2, con el agente de
> `.kiro/agents/prompts/corrector-specs.md`. Insumos leídos completos: la spec, el
> base context, el plan, la tabla de cobertura, los 19 ADRs y su README, los
> hallazgos (incluido H-16), la corrección de la cátedra, su respuesta (con la
> Errata) y la revisión de la v1.4. El código, `tests/` y `docs/integracion-gcs.md`
> se leyeron **solo como evidencia**. Los números de línea sin path son de
> `specs/gcsgrep/02-spec.md` en el commit de arriba.
>
> **Entorno.** `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`
> (Python 3.13.15, `google-cloud-storage` 3.16.0, `google-auth` 2.59.1, sin stubs).
> `.venv/bin/python -m pytest -q`: **48 passed, 5 deselected** (los de integración).
> Todo lo que se cita como "ejecutado" corrió contra el SDK real instalado. La única
> excepción es la medición en Linux de NFR-4 (4.2): corrió en un contenedor
> `linux/aarch64` (Python 3.13.15) sin el SDK, con `google.*` reemplazado por stubs
> vacíos, lo que no cambia nada porque esa medición reemplaza `gcs` por el doble.
> Los tests y scripts de esta revisión son descartables y **no** se agregaron a la
> suite.
>
> **M1.** `grep -cE '^#+ .*FR-[0-9]+'` da **31**, porque el patrón también encuentra
> los cuatro encabezados `NFR-n`. Con `^#+ FR-[0-9]+` da **27**. BR 3, NFR 4. Hay
> 44 VCs distintos (VC-1…VC-44; VC-16 tiene tres partes). VCs (44) ≥ FR+BR (30): no
> hay sospecha de huérfanos.
>
> **M2.** Se cruzaron por script las tres tablas y la de *Preguntas abiertas*
> contra los encabezados. **Requerimiento → VC** (:955-990): 34 filas y 34
> encabezados, sin IDs colgados ni duplicados (ni encabezados ni VCs definidos dos
> veces). Cada VC de la tabla está debajo del encabezado de su fila, con tres
> diferencias, y ninguna es un VC colgado: VC-31 vive en su propia sección
> (:931-943) y la tabla lo asigna a FR-1, FR-3, FR-5, FR-12 y BR-1, y VC-33 (bajo
> FR-13) figura además en la fila de NFR-2 porque VC-29 lo referencia (:834-835).
> Lo que sí está mal es que VC-31 dice "Cubre FR-1, FR-3, FR-5, FR-12, BR-1 y
> **NFR-3**" (:943), pero la fila de NFR-3 (:989) no lo lista (Suggestion, ver 3).
> **Borrador → spec** (:1002-1017): todos los IDs existen. Al revés, BR-3, FR-8,
> FR-12, FR-14, FR-15, FR-26 y NFR-3 no son destino de ningún ítem del borrador, y
> está bien: son caminos de falla o salen de las preguntas 3 y 8 (6.2-6.3).
> **Actores → requerimiento** (:1043-1060): todos los IDs y VCs existen, pero la
> tabla tiene **16** filas y el total dice "**15 modos de falla declarados, 15
> cubiertos**" (:1062) (Suggestion, ver 3). **Preguntas** (:1090-1101): todos los
> IDs existen.
> **FR-26 y FR-27 ubicados por tema (después de FR-15 y FR-17): no es un hallazgo.**
> Ningún chequeo de la rúbrica exige orden numérico. Los IDs son identificadores
> estables (los tests se nombran por VC, `docs/respuesta-correccion-catedra.md:28-30`),
> la tabla de :955 está en orden numérico y sirve de índice, y los VCs ya estaban
> ordenados por tema desde la v1.4 (VC-19 bajo FR-1, VC-20 bajo FR-9, VC-43 bajo
> FR-2). Ponerlos al lado de su par (FR-15/FR-26, FR-17/FR-27) ayuda a ver que no se
> pisan, que es justo lo que importa en esos dos pares. El único costo es buscar
> "FR-26" de corrido, y lo resuelve la tabla.

## Resumen

La v1.5 resolvió los dos bloqueos de la v1.4. FR-13 ya no lista causas: referencia
una definición única de "error de red" (:812-816). El objeto que GCS responde `404`
al abrir tiene FR-21/VC-32, y la red caída al abrir tiene VC-33. Las 21 acciones
tienen respuesta en el texto, y casi todas con un VC concreto: terminador de línea,
`| head`, patrón vacío, invocación mal formada, BOM y límite exacto del tope. Las
tablas cuadran (M2), y lo que el plan clasifica en el Paso 0 (VC-7, VC-12, VC-22,
VC-36…VC-43) **pasa contra el código actual** (se ejecutó, ver 3).

Hay **dos bloqueos**. Los dos están en lo que la v1.5 agregó o reescribió, que es
donde la consigna pedía mirar:

1. **FR-26 no es atómico (2.3).** Su Dado es "no se puede obtener de ella un token
   válido, **o** GCS la rechaza como no autenticada (`401`)" (:466-467). Tiene la
   forma exacta que la cátedra marcó en FR-6 y FR-12. Además, su Entonces ("no lee el
   contenido de ningún objeto", :474-475) es falso para la segunda causa cuando el
   `401` llega en un objeto después de haber leído otros.
2. **NFR-1 no discrimina contra el camino de lectura real (4.2).** La v1.5 alineó la
   métrica con `tracemalloc`, pero la definición se contradice: incluye lo "asignada
   por el intérprete de Python" y excluye los "buffers del SDK de GCS" (:781-784),
   que **viven en el heap de Python**. Se midió el código actual leyendo un objeto de
   200 MiB a través del lector real del SDK (`BlobReader` + `TextIOWrapper`, con la
   descarga HTTP reemplazada): el pico es **≈120 MiB**, 6× el umbral de 20 MiB.
   VC-14 corre sobre el doble y da ~0 MiB. El VC no puede fallar por la razón por la
   que NFR-1 existe, y el plan lo usa como guardia del camino caliente de la
   Iteración 2 (`03-plan.md:292-294`).

También hay una regresión del mismo tipo que H-13 y H-16, esta vez dentro de lo
nuevo. La definición de "error de red" deja afuera **toda** respuesta `4xx`
(:814-816), así que un `429` o un `408` sobre un objeto no son ni red (FR-13), ni
permiso (FR-6), ni no encontrado (FR-21). Además, con el SDK real "al abrir" no es
un momento observable: `blob.open("r")` es perezoso y el `404`/`403` llega en la
primera lectura, que hoy cae en el caso genérico. Se ejecutó (ver 3.3). La nota
"*Los tres caminos de un objeto que no se puede leer*" (:229-235) afirma una
clasificación exhaustiva que no lo es. Lo registro como Warning porque el genérico
lo acota (exit `2`, sin traceback), pero es el mismo mecanismo.

Para NFR-4 (b), la consigna pidió evaluar el contraste: **no discrimina en la
plataforma de CI.** En macOS se reprodujo (abrir y cerrar por match: 29 185
matches/s contra el umbral de 50 000), pero en Linux, sobre la misma máquina, la
misma implementación mala emite **241 980 matches/s** y pasa (b) por 4,8×. El CI
corre en `ubuntu-latest`.

M3: "todo/todos" en castellano (:13, :241, :496, :548, :553, :659, :840, :874,
:876, :947, :1122), "todo" dentro de "mé**todo**" (:724, :726, VC-11) y "leer todo
el archivo" (:806, prosa de VC-14 que describe lo prohibido). "pendiente" solo en
la fila histórica de la v1.1 (:1118). Ninguno deja un valor sin decidir. M4: un hit,
"*correctamente*" (:1166), en la prosa del historial de la v1.2, fuera de
cualquier FR/NFR/VC. M5: `str.lower()`/`casefold` (:163-165) y `utf-8-sig` (:536)
están en párrafos "*Por qué*", no en el FR, pero el de :163 produce una
contradicción (ver 2.8, FR-2). `list_objects`/`gcs` en VC-23 (:447-449) y VC-41
(:484) atan el VC a la costura del doble; se acepta porque la costura está
declarada en el base context (§3) y porque eso es lo que pidió la acción 9 de la
v1.4. `list_blobs`/módulo `gcs` en VC-11 (:721-723) es una inspección de código y
no cuenta. `tracemalloc`/"intérprete de Python" en el **enunciado** de NFR-1
(:781-784) y en VC-14 (:805) sí cuentan: la métrica queda definida por una
herramienta, y la definición se contradice (Issue 4.2). `PIPESTATUS` en VC-35
(:652) es el modo de observar, no implementación. "colaborador de `gcs`" en VC-16 (b)
(:862) es la costura. :883-884, :917 y :1139-1142 son prosa e historial. M6 dentro
de requerimientos, con su VC: FR-7 "todos los" (:241, VC-7), FR-16 "todos los" y
"cualquier" (:496-497, VC-24), FR-18 (:548, VC-26), FR-22 "cualquier otra posición"
(:613, VC-34), FR-25 "cualquier llamada" (:682, VC-37…VC-40), BR-1 "nunca"
(:712-713, VC-11) y "siempre" en *Fuera* (:94, BR-1). **Hits sin VC que los acote:**
"Cualquier otra invocación que no respete esta forma se rechaza" (:55-56) cubre
más que lo que prueban VC-37…VC-40, y el código no lo cumple (2.8, FR-25). FR-2 dice
"un carácter **nunca** se convierte en dos" (:160), y es falso para la
implementación que el mismo FR cita (2.8, FR-2). Los VCs de FR-24, "toda línea de
todo objeto … incluida una línea vacía" (:659-660), no tienen ninguna línea vacía
(2.8, línea). FR-27, "en **cualquier** otra posición" (:530-531), no tiene VC para
esa mitad (Suggestion, 3). El resto es prosa: :285, :874-876, :884, :919, :1011,
:1041.

## Hallazgos por dimensión

### 1. Propósito y alcance — WARN

- Warning (1.5) · :54-55: "`-h`/`--help` imprime la ayuda por stdout y sale con
  código `0` sin tocar GCS: es la única invocación cuyo stdout no son líneas de
  match (NFR-3)". Es un comando dentro de alcance con comportamiento observable
  (stdout, exit, cero llamadas), y no tiene FR ni VC: vive en *Dentro*. NFR-3 lo
  nombra como su única excepción (:839), así que VC-16 (a) tampoco puede verlo. Lo
  mismo pasa con las formas largas (:53), que no tienen VC. El historial dice que "las
  formas largas y `--help`" van al Paso 0 (:1129), pero el Paso 0 del plan
  (`03-plan.md:220-238`) no las lista, y no podría, porque no hay VC que ejercitar.
- 1.1, 1.2, 1.3, 1.4, 1.6: sin hallazgos. El propósito dice por qué (:44-46). *Fuera*
  tiene 11 ítems concretos, cada uno con su ADR (:68-94). Hay tres actores no humanos
  (:101-103), incluido el entorno de credenciales con sus dos modos. El alcance
  diferido es solo un puntero (:1109). El base context está enlazado (:9).

### 2. Completitud y consistencia — FAIL

- **Issue (2.3)** · :465-469 (FR-26): "**Dado** un entorno donde Application Default
  Credentials encuentra una fuente de credenciales pero ésta es **inutilizable**: no
  se puede obtener de ella un token válido, o GCS la rechaza como no autenticada
  (`401`)". Son dos situaciones distintas. Una ocurre del lado del cliente, antes de
  cualquier llamada a GCS: `google-auth` no obtiene un token (archivo inexistente o
  mal formado, *refresh* rechazado). La otra es una respuesta HTTP de GCS a una
  operación. Tienen la forma "A o B" que la cátedra marcó en FR-6 y FR-12
  (`correccion-catedra-iteracion-1.md:35-36`). No son grafías equivalentes, y se ve
  en el Entonces: "no lee el contenido de ningún objeto" (:474-475) vale para la
  primera, pero **no** para un `401` que llega al abrir el objeto *k* después de
  haber leído otros *k−1* (token revocado durante una corrida larga). En ese caso la
  spec no dice si la corrida aborta, como FR-26, o sigue, como FR-6/FR-21: dos
  implementaciones divergen en stdout. VC-41 (:484-488) ejercita una sola causa sin
  decir cuál ("levanta el error de dominio de *credenciales inutilizables*"), igual
  que el VC-6 que la cátedra marcó. Dato de contexto, que no cambia el hallazgo:
  `GOOGLE_APPLICATION_CREDENTIALS=/nonexistent.json` hace que `google.auth.default()`
  levante `DefaultCredentialsError: File /nonexistent.json was not found.`, **la
  misma clase** que "no hay credenciales" (FR-15). La frontera FR-15/FR-26 la decide
  el texto del mensaje del SDK, y la spec la fija bien en :468-469.
- Warning (2.8) · :609-615 (FR-22) y :185 (FR-3, "qué es una línea y qué es su
  terminador: FR-22"). FR-22 define el **terminador**, pero no qué es una **línea**.
  En particular, no dice si la cadena vacía que sigue a un `\n` final es una línea.
  Hasta la v1.4 eso no era observable. Con FR-24 (:659-660, "toda línea … es un
  match … incluida una línea vacía") lo es: para `uno\ndos\n`, `gcsgrep ""` imprime 2
  líneas (como `grep`, y como el código hoy) o 3 (con un `split("\n")`, la última
  `gs://b/p/a.txt:`). Lo mismo con un objeto de 1 byte `\n`: una línea vacía o dos.
  VC-36 (:668-670) no lo resuelve, porque dice "líneas `uno` y `dos`" sin dar los
  bytes. Hubo que decidirlo para escribir el test de 3.5. Además, ningún VC de FR-24
  tiene una línea vacía, que es justo lo que su Entonces nombra (hit de M6).
- Warning (2.8) · :157-161 (FR-2): "La comparación se hace después de pasar a
  minúsculas el patrón y la línea **carácter por carácter**, con la tabla de
  minúsculas de Unicode (…), sin plegado completo: un carácter nunca se convierte en
  dos". Y en :163: "es lo que hace `str.lower()` de Python, que es lo que el código de
  la Iteración 1 ya usa". Las dos frases no pueden ser ciertas a la vez, y se
  ejecutó: `len('İ'.lower()) == 2` (`i` + U+0307), y `'ΟΔΟΣ'.lower() == 'οδος'`, con
  sigma final contextual, no carácter por carácter. Si se implementa "carácter por
  carácter" con el mapeo simple de UnicodeData, `gcsgrep -i "σ"` encuentra la línea
  `ΟΔΟΣ`. Si se implementa con `str.lower()`, como dice el fundamento, no la
  encuentra. Las dos cumplen VC-43 (`Á`→`á` es 1:1). El plan clasifica FR-2 como
  comportamiento existente (Paso 0, `03-plan.md:12-15`), pero el código **no**
  cumple la mitad "nunca dos" del FR.
- Warning (2.8) · :55-56 ("Cualquier otra invocación que no respete esta forma se
  rechaza (FR-25)") y :674-678 (FR-25: "una opción que no está en *Dentro*"). La
  spec no dice qué variantes sintácticas de las opciones de *Dentro* son "esta
  forma". Se ejecutó contra el código y salieron con **exit `0`**, como búsquedas
  normales: `--ig` y `--line` (abreviaturas de las formas largas), `--ma 3`, `-in`
  (flags agrupados), `--max=3` y `--` (fin de opciones). Las abreviaturas no están en
  *Dentro* bajo ninguna lectura, así que **el código viola FR-25**, y VC-37 (`-l`) no
  lo ve (`allow_abbrev` por defecto de argparse, `gcsgrep/cli.py:23-26`). Agrupados,
  `--max=N` y `--` son convención POSIX/GNU, pero la spec no los admite ni los
  rechaza. El caso con consecuencias es el **patrón que empieza con `-`**: `gcsgrep
  "-x" gs://b/p/` sale con `2` ("opción" desconocida) y `gcsgrep "-1" gs://b/p/` se
  acepta como patrón (heurística de números negativos de argparse). FR-1 promete que
  "ningún carácter del patrón tiene significado especial" (:136-137), pero según la
  spec no hay forma de buscar `-x`, porque `--` no está en *Dentro*. `grep` lo
  resuelve con `-e`/`--`. El Paso 0 declara FR-25 "ya cumplido" (`03-plan.md:236`;
  :687-688, "Los cuatro casos ya salen con `2`"), y eso es cierto solo para los
  cuatro VCs.
- Warning (2.8) · :636-640 (FR-23): "el proceso termina por la señal `SIGPIPE`, como
  `grep`: no escribe **nada** por stderr, no lee más objetos, … Vale aunque antes haya
  habido errores de lectura". Si antes del corte hubo un error de lectura (FR-6,
  FR-13, FR-21) o un salteo (FR-9, FR-10), esa corrida **ya escribió** por stderr. La
  última oración incluye explícitamente ese caso, y el Entonces lo contradice. La
  lectura que se quiso decir es "no escribe nada por stderr **a causa del corte**",
  pero el texto no lo dice, y un test sobre ese caso tiene que elegir. Además, "no lee
  más objetos" no tiene observable: VC-35 (:649-653) siembra un solo objeto. En el
  test de 3.5 hubo que agregar un segundo objeto y contar aperturas.
- Suggestion (2.3) · :385-386 (FR-13): "falla por un **error de red** (definido en
  NFR-2) al abrirlo o durante la lectura". No lo cuento como Issue: la causa es una
  sola (una clase definida una vez), el Entonces se observa entero en cada corrida, y
  es la redacción que propuso la revisión de la v1.4 (acción 2). Pero el Dado tiene
  un "o", y la cátedra ya marcó un Dado con "o" cuyo Entonces era el mismo (FR-6
  v1.3). Para no dejarle la discusión a la cátedra, conviene usar el título como Dado:
  "uno de ellos no se puede leer entero por un error de red".
- Suggestion (2.3) · :674-680 (FR-25): el Dado ("una invocación mal formada") es una
  clase definida por cuatro defectos alternativos. Hoy es defendible, porque el
  Entonces es idéntico y cada defecto tiene su VC. Pero queda más firme como un
  predicado único con ejemplos ("una invocación que no respeta la forma de
  *Dentro*"), igual que FR-8, que la cátedra no marcó.
- Suggestion (2.3) · :609-611 (FR-22): "**Dado** un objeto de texto cuyo contenido
  tiene caracteres `\r`". Esto es una definición general, que FR-3 y FR-4 usan para
  todo objeto, escrita como un FR condicionado a la presencia de `\r`. Conviene una
  sección de definiciones (línea, terminador, "al abrir", error de red) que los FRs
  referencien.
- 2.1: sin hallazgos (27/27 FRs en Dado/Cuando/Entonces). 2.3 en el resto: FR-21,
  FR-23 y FR-24 son atómicos. FR-7 mantiene dos grafías equivalentes. 2.7: sin
  hallazgos. Se recorrieron los 44 VCs: VC-22 y VC-15 ya no agregan comportamiento, y
  lo que VC-33 suma (aperturas) es de NFR-2 (b), que lo lista.

### 3. Casos borde y verificabilidad — WARN

- Warning (3.3) · La clasificación de fallos **por objeto** no es exhaustiva, aunque
  :229-235 lo afirme ("*Los tres caminos de un objeto que no se puede leer*: …
  permiso denegado al abrirlo (FR-6), no encontrado al abrirlo (FR-21), o la apertura
  o la lectura fallan por un error de red (FR-13)"). Quedan tres huecos:
  - **Otros `4xx`.** :814-816: "Una respuesta `4xx` —en particular `403` (FR-6,
    FR-14) y `404` (FR-12, FR-21)— **no** es un error de red". Un `429` (cuota) o un
    `400`/`412` sobre un objeto no tiene requerimiento. Un `408 Request Timeout` es a
    la vez "vence un timeout" (red, :813-814) y "una respuesta `4xx`" (no red): la
    definición se contradice. El propio SDK trata `408` y `429` como transitorios,
    junto a los `5xx` (`google/cloud/storage/retry.py:31-58`). La v1.4 decía "error
    transitorio del servidor", que razonablemente los incluía, así que la v1.5 los
    **sacó** de FR-13 sin ponerlos en ningún otro lado.
  - **"Al abrir" no es un momento observable con el SDK real.** :215-216 (FR-6) y
    :584-586 (FR-21) dicen "al abrirlo", pero `blob.open("r")` no hace red:
    `BlobReader.__init__` solo guarda estado, y el `404`/`403` llega en la primera
    `read()` (`google/cloud/storage/fileio.py:108-160`). Se ejecutó con el `gcs.py`
    actual y un cliente cuyo `BlobReader` real recibe un `NotFound` en la descarga:
    `open_text_stream` **no** levanta nada, y la corrida termina con `gcsgrep: error
    inesperado al acceder a gs://b: NotFound: 404 …` y exit `2`. El `except NotFound`
    de `gcsgrep/gcs.py:43-48` es código muerto contra el SDK real. VC-33 sí define el
    momento ("antes de entregar ningún byte", :410), pero solo para red. FR-6 y FR-21
    no tienen definición.
  - **`403`/`404` después del primer byte.** El lector descarga en bloques de 40 MiB
    (`DEFAULT_CHUNK_SIZE`, `fileio.py:25`). Un objeto de más de 40 MiB borrado
    mientras se lee da `404` en el segundo bloque. Eso no es FR-21 (que dice "al
    abrirlo"), no es FR-13 (un `4xx` no es red), y *Fuera* dice que el borrado "entre
    el listado y la lectura … es FR-21" (:91-92), pero no dice nada del borrado
    *durante* la lectura.

  En los tres casos el resultado queda acotado por el genérico de NFR-3 (exit `2`,
  sin traceback), y por eso es Warning y no Issue. Pero dos implementaciones
  divergen: abortar (genérico) contra informar y seguir. Con `GCSGREP_DEBUG=1` ni
  siquiera está definido si son "previstos" (:850-851) o imprimen traceback. Es el
  mecanismo de H-13 y H-16 por tercera vez: una definición nueva angosta una clase,
  "4xx no es red", y lo que queda afuera no aterriza. C-19 no lo ve porque el actor
  GCS (:102) declara "permisos, red, no existir", y un `429` no es ninguno de los
  tres.
- Warning (3.4) · :210-211 (VC-5): "Sobre un prefijo con un **único objeto** de texto
  que no contiene el patrón". La tabla de actores asigna "**No existir** — el prefijo
  (0 objetos)" a FR-5/**VC-5** (:1051), pero VC-5 no ejercita 0 objetos, y ningún otro
  VC lo hace. Es la entrada vacía "0 objetos" de 3.4, y es exactamente lo que C-19
  manda revisar: una fila que nombra un VC que no cubre el modo. El código ya
  devuelve `1` con stdout vacío. Falta el VC.
- Suggestion (3.2) · :691-704 (VC-37…VC-40): "stderr no vacío y sin `Traceback`". Hay
  exit code y stdout exactos, así que no es el "stderr menciona" de 3.2, pero FR-25
  (:683) no fija ningún texto. Una frase literal ("uso:" o el nombre de la opción
  rechazada) lo haría comparable con FR-8.
- Suggestion (3.4) · :530-531 (FR-27): "Una secuencia `EF BB BF` en cualquier otra
  posición … se decodifica como cualquier otro carácter". VC-44 (:538-541) prueba solo
  la del principio. La mitad que distingue `utf-8-sig` de "quitar todos los BOM" no
  tiene VC.
- Suggestion (M2) · :989: la fila de NFR-3 no lista VC-31, que dice cubrirlo (:943). Y
  :1062 dice "15 modos de falla declarados, 15 cubiertos", pero la tabla tiene 16
  filas (:1045-1060).
- Suggestion (3.5) · :649-653 (VC-35): es el único VC que necesita un **proceso**
  `gcsgrep` real en una pipeline, y a la vez el doble de prueba. Todos los demás
  corren en proceso (NFR-4 lo dice explícitamente, :890). La spec no dice cómo se
  inyecta el doble en otro proceso, ni si VC-35 corre contra `floci`. Hubo que
  decidirlo (lanzador propio).
- **3.5 · FR-24 (feliz): se pudo escribir, pero hubo que decidir dos cosas.** Datos:
  `gs://b/p/a.txt` = `uno\ndos\n` y `gs://b/p/vacio.txt` = 0 bytes. Comando:
  `gcsgrep "" gs://b/p/`. stdout exacto `gs://b/p/a.txt:uno\ngs://b/p/a.txt:dos\n`,
  stderr vacío, exit `0`. Decisiones: (1) los bytes de VC-36, con `\n` final o sin él;
  (2) que el vacío después del `\n` final no es una línea (Warning 2.8, línea). Test
  extra con la cláusula que VC-36 no prueba: `uno\n\ndos\n` con `-n` → stdout exacto
  `…:1:uno\n…:2:\n…:3:dos\n`. **Ejecutados contra el código actual con
  `RecordingFakeGCS`: los dos pasan.** Es coherente con que FR-24 esté en el Paso 0.
- **3.5 · FR-23 (falla): se pudo escribir, con tres decisiones.** Datos:
  `gs://b/p/a.txt` = `hit\n` × 200 000 y `gs://b/p/b.txt` = `hit\n` (agregado para
  observar "no lee más objetos"). Comando: `gcsgrep hit gs://b/p/ 2>err | head -1;
  echo ${PIPESTATUS[0]}` en bash, con un lanzador que corre `cli.main` en su propio
  proceso, con el doble inyectado y cada apertura registrada al momento en un archivo.
  Esperado: stdout de la pipeline exactamente `gs://b/p/a.txt:hit\n`, `err` vacío,
  estado `141`, aperturas `[p/a.txt]`. Decisiones: (3) cómo se inyecta el doble fuera
  del proceso (Suggestion 3.5); (4) cómo se observa "no lee más objetos" (Warning 2.8,
  FR-23); (5) datos sin errores ni salteados previos, para no chocar con la
  contradicción de "nada por stderr" (Warning 2.8, FR-23). **Ejecutado contra el
  código actual: falla, y por la razón correcta** (es Iteración 2). stdout correcto,
  aperturas `[p/a.txt]` correctas, pero `err` = `gcsgrep: error inesperado al acceder
  a gs://b: BrokenPipeError: [Errno 32] Broken pipe` + `gcsgrep: corré con
  GCSGREP_DEBUG=1 …` + `Exception ignored on flushing sys.stdout: …`, y estado
  **`120`**. Que hoy no abra `b.txt` es casualidad del genérico, no FR-23: el test
  pasaría esa aserción aunque nada de FR-23 estuviera implementado.
- **3.5 · FR-21 (falla, extra, por ser el centro de H-16): se pudo escribir, con una
  decisión que cambia lo que prueba.** Datos: `a.txt` (`hit a`), `b.txt` (aparece en
  el listado y falla al abrir), `c.txt` (`hit c`). Comando: `gcsgrep hit gs://b/p/`.
  Esperado: stdout exacto `gs://b/p/a.txt:hit a\ngs://b/p/c.txt:hit c\n`, una línea de
  stderr con `ya no existe` y `gs://b/p/b.txt`, sin `Traceback`, exit `2`. Decisión
  (6): **en qué costura se simula el `404`**. Con el doble de `core`, lo único que se
  puede levantar en `open_text_stream` es el error de dominio `ObjetoNoEncontrado`, y
  eso es lo que se hizo. Pero con el SDK real el `404` no llega ahí, llega en la
  primera lectura (Warning 3.3). Un VC-32 que pase sobre el doble no garantiza FR-21
  en producción. **Ejecutado: falla por la razón correcta, y solo por stdout.** Falta
  `c.txt`, la corrida abortó. El exit (`2`) y stderr (`el objeto 'gs://b/p/b.txt' ya
  no existe …`) **ya cumplen** VC-32 hoy, porque el mensaje de `ObjetoNoEncontrado`
  contiene `ya no existe`. Es el riesgo que ADR-0013:70-75 anota, y VC-32 lo atrapa
  gracias a su stdout exacto.
- **Clasificación del plan (Paso 0 contra Iteración 2), verificada ejecutando.**
  VC-36, VC-37 (`-l`), VC-38 (`--max -1`, `--max abc`), VC-39 (`gs://`, `gs:///p`),
  VC-40, VC-42 (1000 objetos se abren; `--max 3` con 4 → exit `1`, `4 objetos` /
  `el tope es 3`, 0 aperturas), VC-43, VC-7, VC-12 (`1001 objetos` / `el tope es
  1000`) y VC-22: **todos pasan contra el código actual**. Lo que el Paso 0 da por
  cumplido y el código no cumple: FR-25 más allá de sus cuatro VCs (abreviaturas, 2.8)
  y FR-2 en "nunca dos" (2.8). Además, VC-14 está ✅ desde la Iteración 1 y el
  código no cumple NFR-1 por el camino real (Issue 4.2). Las formas largas y `--help`
  figuran como Paso 0 en el historial (:1129) sin VC (1.5). Lo que el plan manda a la
  Iteración 2 (VC-32…VC-35, VC-41, VC-44) efectivamente falla hoy o depende de código
  que no existe: FR-21 y FR-23 se ejecutaron arriba. FR-22 y FR-27 dependen de dejar
  `blob.open("r")`, como dice `03-plan.md:279-282`.
- 3.1: sin hallazgos (los 30 FR+BR tienen VC debajo y en la tabla, M2). 3.3 en el resto:
  bucket (FR-12/FR-14), credenciales (FR-15/FR-26, salvo 2.3), invocación (FR-8/FR-25),
  listado por red (NFR-2 (a)) y corte (FR-23) presentes. 3.6: VC-31, con el bucket
  inexistente generado y verificado (:937-941).

### 4. Requerimientos no funcionales — FAIL

- **Issue (4.2)** · :781-784 (NFR-1): "pico de memoria adicional **asignada por el
  intérprete de Python** (la que registra `tracemalloc`) mientras se lee un objeto. No
  incluye memoria nativa fuera del heap de Python (**buffers del SDK de GCS** o de
  `ssl`)". Y :794-795: "La memoria nativa del SDK no depende del tamaño del objeto
  cuando se lee por streaming". Las dos afirmaciones son falsas para el SDK que el
  código usa. `BlobReader` descarga bloques de `DEFAULT_CHUNK_SIZE` = **40 MiB** como
  `bytes` de Python, y guarda el resto en un `io.BytesIO` (`fileio.py:25`, :118,
  :143-158): es heap de Python, y `tracemalloc` lo ve. **Se midió** con el `core.search`
  actual leyendo un objeto de 200 MiB (líneas de 80 bytes) a través de
  `io.TextIOWrapper(BlobReader(blob))`, igual que `blob.open("r")`, con
  `download_as_bytes` reemplazado por una sola asignación del tamaño pedido, que es una
  cota inferior de la descarga real. El pico adicional es **120,0 MiB** en la
  condición (a) y **120,0 MiB** en la (b), 6× el umbral de :785. VC-14 (:803-807) mide
  "sobre el doble de prueba que expone el stream" y da ~0 MiB
  (`04-cobertura-vc.md`, fila VC-14 (b)). Tres consecuencias:
  - La métrica tiene dos lecturas: "lo que registra `tracemalloc`" incluye los bloques;
    "no incluye buffers del SDK" los excluye.
  - El VC no puede fallar por la razón por la que el NFR existe. La implementación de
    la Iteración 1 es la "mala" (≈120 MiB) y pasa.
  - El plan usa VC-14 como la guardia de que FR-9/FR-17 "no rompieron la memoria
    acotada" (`03-plan.md:292-294`), y no puede verlo.

  El tamaño de bloque de lectura es una decisión de diseño que sostiene NFR-1 y no
  está ni en la spec ni en un ADR (5.3). `specs/gcsgrep/01-base-context.md:72-74`
  ("`blob.open("r")` … Eso es lo que hace posible operar sobre objetos grandes con
  memoria acotada") repite la premisa falsa.
- Warning (4.2) · :902 (NFR-4 (b), "≥ 50 000 matches/s") y :908-912 (VC-30): "Los dos
  umbrales discriminan: … una que abre y cierra el destino de la salida por cada match
  emite **~31 000 matches/s** y falla (b)". **Se midió** con el mismo diseño de VC-30:
  `cli.main` en proceso, stdout a `/dev/null`, 100 MiB en líneas de 80 bytes, mejor
  de 3. Para la variante mala se reemplazó el `print` de `cli` por `open("/dev/stdout",
  "a")` + escribir + cerrar por match.

  | Plataforma | Implementación actual | Abrir y cerrar por match | ¿(b) la rechaza? |
  |---|---|---|---|
  | macOS (Apple M5) | 357 619 matches/s | **29 185** | sí, por 1,7× |
  | Linux aarch64 (contenedor, misma máquina) | 1 153 968 matches/s | **241 980** | **no**: pasa por 4,8× |

  El contraste que la spec usa para mostrar que (b) discrimina depende del costo de
  `open`/`close` de **macOS**. El CI corre en `ubuntu-latest`
  (`.github/workflows/tests.yml:19`), donde la misma implementación mala pasa holgada.
  No se midió en un runner de GitHub. Esta medición es Linux sobre el mismo hardware, y
  un runner x86 es más lento en CPU pero tiene el mismo costo relativo de *syscalls*.
  Sobre el **margen para CI**: la implementación buena tiene 7× de margen en macOS y
  23× en Linux, así que (b) **no** es flaky. El problema no es el falso negativo, es que
  en la plataforma donde corre no rechaza ninguna implementación mala que se haya
  probado. Las otras dos (`logging.StreamHandler`, `os.fsync`, :916-918) ya pasaban en
  macOS. Es la objeción original de ADR-0012 ("pasa siempre, no protege nada"), que
  sobrevive en Linux. Agrava esto que ni NFR-4 (:897-898) ni VC-30 nombran la plataforma
  de referencia: el umbral es absoluto, pero lo que discrimina depende del SO.
- Warning (4.4) · :818-821 (NFR-2): "**Política:** **0 reintentos automáticos** …
  cada operación sobre GCS se intenta **una sola vez**". El SDK que usa el código
  reintenta por defecto: `list_blobs` y `BlobReader` usan `DEFAULT_RETRY` (backoff
  exponencial, deadline de 120 s) sobre conexión, timeout, `408`, `429` y `5xx`
  (`retry.py:31-58`; `fileio.py:108`, `retry=DEFAULT_RETRY`). Leído al pie de la letra,
  el código de la Iteración 1 viola NFR-2. La aclaración que lo salva, "**Qué hace el
  SDK por debajo no forma parte del contrato**: VC-15 y VC-29 se observan en el borde
  de `gcs`", está solo en `docs/adr/ADR-0016-sin-reintentos.md:29-32`. Es comportamiento
  observable que vive solo en un ADR (5.6). Una red caída tarda hasta ~120 s en dar
  `error de red`, y un `5xx` transitorio puede no verse nunca. Además, "vence un
  timeout" (:814) no tiene valor: la política está incompleta en el sentido de 4.4,
  porque no dice cuánto espera ni cuántas veces reintenta la capa de abajo.
- 4.1, 4.3, 4.5: sin hallazgos. NFR-1 y NFR-4 tienen métrica, número y condición en el
  enunciado, y NFR-4 nombra "en proceso" y lo que excluye (:890-896). MiB en todo. Cada
  condición enumerada tiene VC: NFR-1 (a)/(b), NFR-2 (a) VC-15, (b) VC-29 y VC-33,
  NFR-4 (a)/(b). La seguridad la cubren BR-1 y los permisos mínimos; el costo, BR-2.

### 5. Tecnología y fundamento — WARN

- Warning (5.3) · :15-17: "El fundamento de cada decisión **no vive acá**: vive en un
  ADR con identificador estable". La v1.5 tomó seis decisiones con alternativas reales
  y las fundamentó en párrafos "*Por qué (v1.5)*" **dentro de la spec**, sin ADR ni
  tabla de alternativas descartadas:
  - plegado de `-i` (:163-166);
  - "sin resumen final", que se aparta de ADR-0005 (:280-288);
  - `\r\n` sin `\r`, que se aparta de `grep` (:617-623);
  - patrón vacío (:664-666);
  - BOM (:533-536);
  - FR-26 aparte de FR-15 (:477-482).

  El caso más serio es el de ADR-0005. Su sección **Decisión** dice "Ambos casos se
  reportan como 'salteado' en un resumen final por **stderr**"
  (`docs/adr/ADR-0005-binarios-y-gz.md:22-24`). La regla 1 del registro dice "Si la
  decisión cambia, se escribe un ADR nuevo que declara `Supersede`"
  (`docs/adr/README.md:9-12`). La v1.5 la cambió y lo resolvió con una fila de
  "desvío" (`docs/adr/README.md:97-101`), argumentando que "cambia el formato, no la
  decisión". Pero el formato estaba escrito en la Decisión del ADR. El fundamento
  existe y es bueno: lo que falta es el lugar donde las propias reglas del proyecto
  dicen que va.
- Suggestion (5.2) · :114-120 (*Tecnología y permisos mínimos*). Nombra GCS y ADC,
  pero no el runtime (Python) ni la librería cliente (`google-cloud-storage`), aunque
  NFR-1 (:781), NFR-3 (:842) y NFR-4 (:893) se definen sobre "el intérprete", y NFR-1 y
  NFR-2 dependen de defaults de esa librería (bloque de 40 MiB, `DEFAULT_RETRY`; ver
  4.2 y 4.4). Una fila más, con la versión mínima y los dos defaults que la spec
  decide, cierra eso.
- Suggestion (5.6) · `docs/adr/ADR-0019-corte-de-stdout-sigpipe.md:70-74`: "o, donde no
  exista la señal, traducir `BrokenPipeError` al mismo observable: stderr vacío, sin
  seguir leyendo". Es comportamiento observable en plataformas sin `SIGPIPE`, sin exit
  code definido, y la spec no dice en qué plataformas corre `gcsgrep`. Alcanza con
  declarar la plataforma (POSIX) o fijar el exit code.
- Suggestion (5.6) · Referencias de ADRs aceptados que la v1.5 dejó viejas y que el
  README (:86-104) no registra. Ninguna tiene efecto observable:
  `ADR-0007-formato-de-salida.md:24-26` ("VC-4 parsea con `split(":", 2)`"; VC-4 hoy
  exige stdout exacto), `ADR-0011-salida-incremental.md:36-37` ("NFR-3 exige que stderr
  sea solo para errores y resúmenes"; desde la v1.5 no hay resúmenes) y
  `ADR-0002-autenticacion-adc.md:41` ("Spec: BR-1 · VC-11 · NFR-2"; hoy FR-15 y FR-26).
- Referencias, sin duplicar: ADR-0016:29-32 (el SDK fuera del contrato) está en el
  Warning 4.4.
- 5.1, 5.4, 5.5: sin hallazgos. Los permisos mínimos y lo que pasa sin cada uno están
  nombrados (:116-127). Los trade-offs nuevos están reconocidos (ADR-0019, alternativas
  de :83-88; :914-919 dice qué no acota (b)). `--max 0` y `GCSGREP_DEBUG=1` siguen
  siendo excepciones explícitas, opt-in y no son el default.

### 6. Simplicidad — PASS

- Suggestion (6.4) · La validez de la ubicación quedó repartida en dos reglas con
  observables distintos: "no empieza con `gs://`" es FR-8, con el mensaje que contiene
  `gs://` (:253-254), y "empieza con `gs://` pero no tiene bucket" es FR-25, sin texto
  fijado (:676-677, :683). Para quien escribe `gs://` a secas, el mensaje que le
  corresponde depende de una frontera que no le importa. Conviene que FR-8 cubra "no es
  una ubicación `gs://<bucket>[/<prefijo>]` válida", con el mismo texto.
- 6.1–6.3: sin hallazgos. Lo nuevo es un camino de falla (FR-21, FR-23, FR-25, FR-26),
  un borde pedido por la rúbrica (FR-22, FR-24, FR-27) o decide un ADR existente. No hay
  flags nuevos. "Sin traceback" y "no afecta el exit code" están escritos una vez
  (:843-844, :757-760). FR-22 se aparta de `grep` y lo dice (:621-623).

### B. Extensión brownfield — no aplica

`gcsgrep` es el TP1 greenfield. B1–B9 son para `tmux-ssh-tp2/`.

### Seguimiento (a) · las 19 acciones de la corrección de la cátedra

| # | Acción | Estado | Evidencia en la v1.5 |
|---|---|---|---|
| 1a | Partir FR-4 | ✅ | FR-3 (:178-189) con `-n` y FR-4 (:191-202) sin `-n`; VC-3 y VC-4 con stdout exacto |
| 1b | Partir FR-6 | ⚠️ | Las dos regresiones de la v1.4 se cerraron: FR-13 referencia una clase definida una vez (:385-386), y FR-21/VC-32 y VC-33 cubren el `404` y la red al abrir. Pero la mitad "**error transitorio**" de la cátedra quedó angosta: la definición de red (:812-816) excluye `429` y `408`, que no aterrizan en ningún FR, y "al abrir" no es un momento observable con el SDK (Warning 3.3) |
| 1c | Partir FR-12 | ✅ | FR-12 (:351-381) y FR-14 (:416-429); FR-14 ahora dice "no contiene `no existe`" |
| 2 | NFR de rendimiento | ✅ | NFR-4 (:888-902) con métrica, número, condición y VC-30. Que (b) no discrimine en Linux es el Warning 4.2, no la acción |
| 3 | Umbral de NFR-1 al enunciado | ✅ | :785-788. Que el VC no vea el camino real es el Issue 4.2 |
| 4 | FR-8 nombra `gs://` | ✅ | :253-255, VC-8 |
| 5 | FR-1 literal + VC con metacaracteres | ✅ | :135-137, VC-19 (:147-150) |
| 6 | Sin credenciales | ✅ | FR-15 (:431-439), VC-23 sobre la costura real (:447-454), I-6 alineado (`docs/integracion-gcs.md:49`) |
| 7 | Orden de salida | ✅ | FR-16 (:490-497), VC-24 |
| 8 | VC-9 concreto | ✅ | VC-9 (:290-296): "stderr es **exactamente** la línea", exit `0`/`1` |
| 9 | Prefijo sin `/` | ✅ | FR-18 (:543-557), VC-26 |
| 10 | Objeto de 0 bytes | ✅ | FR-19 (:559-569), VC-27 |
| 11 | Última línea sin `\n` | ✅ | FR-20 (:571-580), VC-28. Que "línea" no esté definida con `\n` final es el Warning 2.8 nuevo, que aparece con FR-24 |
| 12 | VC de punta a punta real | ✅ | VC-31 (:931-943), sin ejecutar por ADR-0015 |
| 13 | VC de NFR-2 al leer | ✅ | VC-29 (:832-835) y VC-33 (:409-414); NFR-2 (b) "al abrir o leer" (:825) |
| 14 | Permisos IAM mínimos | ✅ | :116-127, BR-1 (:714-716) |
| 15 | ADR de reintentos | ✅ | ADR-0016. Que su aclaración sobre el SDK no esté en la spec es el Warning 4.4 |
| 16 | `GCSGREP_DEBUG` | ✅ | NFR-3 (:846-854), VC-16 (c); la lista de previstos incluye FR-21, FR-25 y FR-26 |
| 17 | Bytes inspeccionados para `\x00` | ✅ | FR-9 (:263-278), VC-20 (:298-306) con bytes exactos y la posición del `\x00` |
| 18 | Codificación | ✅ | FR-17 (:509-521), VC-25; BOM en FR-27 |
| 19 | "Sin traceback" solo en NFR-3 | ✅ | :842-844 |

**Resultado: 18 de 19 resueltas, 1 parcial (1b). 0 sin resolver.**

### Seguimiento (b) · las 21 acciones de la revisión de la v1.4

| # | Acción | Estado | Evidencia en la v1.5 |
|---|---|---|---|
| 1 | [MUST] Definir "error de red"; sacar la alternativa del Dado de FR-13 | ⚠️ | Definición única (:812-816) y FR-13 la referencia (:385-386). Pero la definición se contradice con `408` y deja `429`/otros `4xx` sin requerimiento (Warning 3.3) |
| 2 | [MUST] Objeto que falla al abrir por algo que no es permiso | ⚠️ | FR-21/VC-32, VC-33, BR-3 (:755), previstos de NFR-3 (:850-851), actores (:1048, :1052). Quedan `429`/`408`/`401` al abrir, "al abrir" sin definir para `403`/`404` (el SDK es perezoso) y el `404` después del primer byte (Warning 3.3). Para `401` a mitad de corrida, ver el Issue 2.3 |
| 3 | [SHOULD] Terminador de línea | ✅ | FR-22 (:607-615), VC-34 con bytes exactos |
| 4 | [SHOULD] VC-12, VC-13, VC-7 y VC-20 concretos | ✅ | Texto del tope en BR-2 (:732-733) y en VC-12; VC-13 con la causa de FR-6 (:769-773); VC-7 (:244-247); VC-20 (:298-306) |
| 5 | [SHOULD] FR de invocación mal formada | ⚠️ | FR-25 + VC-37…VC-40. El código acepta abreviaturas que FR-25 rechaza, y el patrón que empieza con `-` está sin decidir (Warning 2.8) |
| 6 | [SHOULD] Corte de stdout | ✅ | FR-23 (:631-653), ADR-0019, VC-35. El Entonces tiene una contradicción con su última oración (Warning 2.8), que no deshace la decisión |
| 7 | [SHOULD] Patrón vacío | ✅ | FR-24 (:655-670), VC-36; el test pasa contra el código |
| 8 | [SHOULD] Límite exacto de BR-2 | ✅ | :733-734, VC-42 (:747-751); se ejecutó |
| 9 | [SHOULD] VC-23 sobre la costura que existe; alinear I-6 | ✅ | :447-461; `docs/integracion-gcs.md:49` exige los dos textos |
| 10 | [SHOULD] Credenciales inutilizables | ⚠️ | FR-26/VC-41 existe, pero no es atómico (Issue 2.3) |
| 11 | [SHOULD] Alinear métrica y VC en NFR-1 y NFR-4; unificar MB/MiB | ⚠️ | NFR-4 ✅ ("en proceso", :890-896); MiB ✅. NFR-1 se alineó con `tracemalloc`, pero la definición se contradice y el VC no ve el lector real (Issue 4.2) |
| 12 | [SHOULD] Mostrar que NFR-4 (b) discrimina | ⚠️ | Contraste medido (:908-919), reproducido en macOS (29 185). En Linux la misma implementación mala da 241 980 y pasa (Warning 4.2) |
| 13 | [SHOULD] Una línea de salteo por objeto, sin resumen | ✅ | FR-9 (:268-271), FR-10 (:312-315), VC-9/VC-10 "exactamente". Que el desvío de ADR-0005 no tenga ADR es el Warning 5.3 |
| 14 | [SHOULD] `\x00` después de la ventana sale por stdout | ✅ | :273-278, VC-20 (2) |
| 15 | [SHOULD] FR-14 sin `no existe`; VC-15 sin "representación cruda" | ✅ | :422-423; :828-830 |
| 16 | [COULD] Plegado de `-i` | ⚠️ | Decidido (:157-166) + VC-43, pero el texto se contradice (`İ`, sigma final; Warning 2.8) |
| 17 | [COULD] BOM | ✅ | FR-27 (:523-541), VC-44. La mitad "otra posición" sin VC es una Suggestion |
| 18 | [COULD] "No afecta el exit code" solo en BR-3 | ✅ | :757-760; FR-9, FR-10 y FR-19 la referencian |
| 19 | [COULD] Formas largas y `--help` en *Dentro* | ✅ | :52-56. Que no tengan FR/VC es el Warning 1.5 nuevo |
| 20 | [COULD] VC-31 (3) sin bucket global fijo | ✅ | :937-941 |
| 21 | [COULD] Referencias viejas de ADRs en el README | ✅ | `docs/adr/README.md:86-95`. Quedan tres nuevas (Suggestion 5.6) |

**Resultado: 14 de 21 resueltas, 7 parciales (1, 2, 5, 10, 11, 12, 16). 0 sin
resolver.** Las parciales 1 y 2 tienen la misma causa (Warning 3.3), y la 10 es el
Issue 2.3.

## Veredicto general   NEEDS WORK

Fallan la dimensión 2 (FR-26 no es atómico) y la 4 (NFR-1 no puede fallar contra el
camino de lectura real). Las dos están en texto nuevo o reescrito en la v1.5, y las
dos **afectan lo que va a planificar la Iteración 2**:

- FR-26 decide si un `401` en el objeto *k* aborta o sigue, y eso cambia la frontera
  de excepciones que la iteración va a reescribir.
- NFR-1 es la guardia declarada del cambio de lectura en bytes de FR-9/FR-17
  (`03-plan.md:292-294`). Con el VC como está, la iteración puede dejar el bloque de
  40 MiB y declarar NFR-1 cumplido.

No hace falta reescribir: se arreglan con texto, un VC sobre el lector real y una
decisión de tamaño de bloque. La dimensión 3 no falla: no hay huérfanos, los tests
se pudieron escribir y los de Iteración 2 fallan por la razón correcta. Pero el
Warning 3.3 es la tercera aparición del mecanismo de H-13, y conviene cerrarlo en la
misma v1.6 en lugar de esperar a que lo encuentre la cátedra.

## Acciones (priorizadas)

Cambios propuestos para una **v1.6**. No se aplicaron. Las líneas son de
`specs/gcsgrep/02-spec.md` en `4e4847d` salvo que se indique otro archivo.

1. **[MUST]** Partir FR-26 (`:463-488`) en dos FRs atómicos:
   - **FR-26 · Credenciales que no producen un token.** *Dado* un entorno donde ADC
     encuentra una fuente de credenciales pero no puede obtener de ella un token
     (archivo de `GOOGLE_APPLICATION_CREDENTIALS` inexistente o mal formado, *refresh*
     rechazado), *Cuando* …, *Entonces* el texto actual de :471-475. VC-41 se
     mantiene, diciendo qué causa simula.
   - **FR-28 · GCS rechaza las credenciales (`401`).** *Dado* una corrida en la que GCS
     responde `401` a una operación (listar o abrir/leer un objeto), *Entonces* la
     corrida **aborta** (las operaciones siguientes fallarían igual), los matches ya
     emitidos quedan en stdout, stderr tiene una línea con `credenciales inválidas o
     vencidas` y `gcloud auth application-default login`, y sale con `2`.
     **VC-45**: `a.txt` (`hit a`), `b.txt` (`401` al abrir), `c.txt` (`hit c`) →
     stdout exactamente `gs://b/p/a.txt:hit a`, esa línea en stderr, exit `2`, `c.txt`
     abierto 0 veces.
   - Agregar FR-28 a los previstos de NFR-3 (`:850-851`), a la fila *Credenciales
     inutilizables* de la tabla de actores (`:1054`) y a la tabla de :955.
2. **[MUST]** Hacer que NFR-1 pueda fallar contra el camino real (`:781-808`;
   `specs/gcsgrep/01-base-context.md:72-74`; `specs/gcsgrep/03-plan.md:292-294`):
   - Métrica (`:781-784`): "pico de memoria adicional asignada en el heap de Python
     (la que registra `tracemalloc`) mientras se lee un objeto, **incluidos los buffers
     de la librería cliente**. No incluye memoria fuera del heap de Python." Sacar
     "buffers del SDK de GCS" de lo excluido, y corregir :794-796.
   - VC-14 (`:803-808`): "medido leyendo el objeto **a través del lector de la librería
     cliente** (`blob.open`) con la descarga HTTP simulada, no solo sobre el doble de
     `core`". Hoy da ≈120 MiB, así que el VC pasa a ⬜ (Iteración 2) y la fila ✅ de
     `04-cobertura-vc.md` pasa al Histórico, como dice el propio documento.
   - Decidir en un ADR el tamaño de bloque de lectura (por ejemplo `chunk_size` de
     1 MiB en la apertura), con su efecto en NFR-4 (más pedidos por objeto), y nombrarlo
     en *Tecnología y permisos mínimos* (`:114-120`).
3. **[SHOULD]** Cerrar la clasificación de fallos por objeto (`:229-235`, `:215-216`,
   `:584-589`, `:812-816`, `:102`, `:1043-1060`):
   - Definición común: "**Al abrir** un objeto = antes de que entregue su primer byte
     (como en VC-33)".
   - FR-6 y FR-21: "al abrirlo **o durante la lectura**", con los matches ya emitidos
     conservados, como FR-13.
   - NFR-2, error de red: "sin respuesta HTTP completa, o una respuesta `408`, `429` o
     `5xx`". Sacar `408` de "4xx no es red".
   - Nuevo FR "**Otra respuesta de error al leer un objeto**" (cualquier `4xx` que no
     sea `401`, `403`, `404`, `408` ni `429`): línea con `no se pudo leer` + URI, sigue,
     BR-3.
   - Actor GCS: "puede fallar por permisos, red, no existir **u otra respuesta de
     error**", con su fila en la tabla.
   - VC-32 y VC-6: simular el `404`/`403` **en la primera lectura**, como lo entrega
     el SDK, no solo en la apertura del doble.
4. **[SHOULD]** Definir qué es una línea (`:607-615`) y precisar VC-36 (`:668-670`):
   "El contenido se parte en líneas en cada `\n`; si el objeto termina en `\n`, no hay
   una línea vacía después. Un objeto cuyo único byte es `\n` tiene una línea, vacía."
   VC-36 con bytes explícitos (`uno\ndos\n`) y un caso `uno\n\ndos\n` con `-n` → tres
   líneas, la 2 vacía.
5. **[SHOULD]** Resolver la contradicción de FR-2 (`:157-166`). Propuesta, que
   documenta lo existente: "la conversión a minúsculas completa de Unicode, incluidas
   las reglas contextuales, que es la de `str.lower()` (`İ` → `i̇`, `Σ` final → `ς`)".
   Sacar "carácter por carácter" y "un carácter nunca se convierte en dos". Agregar a
   VC-43 un caso con `ΟΔΟΣ` (`-i "σ"` → exit `1`).
6. **[SHOULD]** Cerrar la sintaxis aceptada en *Dentro* (`:52-56`) y en FR-25
   (`:674-678`):
   - "Se aceptan exactamente `-i`, `-n`, `--ignore-case`, `--line-number`, `--max N`,
     `--max=N`, `-h`, `--help`, flags cortos agrupados (`-in`) y `--` para terminar
     las opciones. Las abreviaturas de opciones largas (`--ig`) se rechazan (FR-25).
     Un patrón que empieza con `-` se pasa después de `--`."
   - VCs: `--ig` → `2`; `gcsgrep -- -x gs://b/p/` busca `-x`.
   - En `03-plan.md:236`, FR-25 deja de ser "ya cumplido" para las abreviaturas
     (Iteración 2: `allow_abbrev=False`).
7. **[SHOULD]** FR-23 (`:636-640`): "no escribe por stderr nada **a causa del corte**
   (lo que FR-6, FR-9, FR-10, FR-13 o FR-21 ya escribieron queda)". VC-35
   (`:649-653`): agregar `gs://b/p/b.txt` (`hit`) y "`b.txt` se abre 0 veces", y decir
   con qué se corre: el proceso `gcsgrep` con el doble inyectado, o el emulador.
8. **[SHOULD]** VC-5 (`:210-211`): agregar "Con un prefijo sin ningún objeto (listado
   vacío), la misma corrida sale con `1`, stdout vacío y stderr vacío", para que la
   fila de :1051 cubra lo que dice.
9. **[SHOULD]** NFR-4 (b) (`:897-919`; `docs/adr/ADR-0017-…md`). Primero, nombrar la
   plataforma de referencia en la condición de carga ("medido en el runner de CI,
   `ubuntu-latest`"). Después, una de dos:
   - recalibrar (b) **en esa plataforma** contra una implementación mala que caiga
     debajo;
   - o reescribir (b) como piso de regresión y sacar "Los dos umbrales discriminan"
     de VC-30 (`:908`), con un ADR que supersede la parte de ADR-0017 que lo afirma.
   
   Un umbral relativo a (a) en la misma corrida es la alternativa que ADR-0017
   descartó por legibilidad, y conviene revisarla con estos números.
10. **[SHOULD]** NFR-2 (`:818-826`): llevar a la spec lo que hoy dice solo
    ADR-0016:29-32, con un número. Propuesta: "0 reintentos de `gcsgrep` **y** de la
    librería cliente (sus reintentos por defecto se desactivan); cada pedido HTTP
    tiene un timeout de **60 s**". Si se prefiere conservar los del SDK, la frase es
    "la librería puede reintentar por debajo hasta **120 s** antes de que se reporte el
    error de red", y entonces VC-15 tiene que poder observarlo.
11. **[SHOULD]** Dar FR y VC a `--help` y a las formas largas (`:52-56`). FR "**Ayuda**":
    `gcsgrep --help` → exit `0`, stdout contiene `gcsgrep` y las cuatro opciones,
    stderr vacío, 0 llamadas de listado. VC: `--ignore-case`/`--line-number` dan la
    misma salida que `-i`/`-n` sobre VC-43/VC-3. Agregarlos al Paso 0
    (`03-plan.md:220-238`) y corregir :1129.
12. **[SHOULD]** Llevar a ADRs los fundamentos de la v1.5 que están en prosa
    (`:163-166`, `:533-536`, `:617-623`, `:664-666`, `:477-482`), y escribir un ADR
    que **supersede** a ADR-0005 en lo del resumen final (`:280-288`;
    `docs/adr/README.md:97-101`), en lugar de la fila de "desvío".
13. **[COULD]** FR-13 (`:385-386`): usar el título como Dado ("uno de ellos no se puede
    leer entero por un error de red") y dejar los dos momentos a VC-21 y VC-33.
14. **[COULD]** FR-25 (`:674-680`): escribir el Dado como predicado único ("no respeta
    la forma de *Dentro*") con los cuatro defectos como ejemplos. Fijar un texto en
    stderr (`:683`) y en VC-37…VC-40 (`:691-704`).
15. **[COULD]** FR-27: agregar a VC-44 (`:538-541`) un objeto `timeout\n` + `EF BB BF` +
    `x\n` → la línea 2 sale con `U+FEFF`.
16. **[COULD]** Agregar VC-31 a la fila de NFR-3 (`:989`), y corregir "15 modos de
    falla" a 16 (`:1062`).
17. **[COULD]** Nombrar el runtime y la librería cliente, con versión mínima, en
    *Tecnología y permisos mínimos* (`:114-120`), y la plataforma soportada (POSIX),
    lo que resuelve también `ADR-0019:70-74`.
18. **[COULD]** Registrar en `docs/adr/README.md` (§ "Referencias que la spec dejó
    viejas") las de `ADR-0007:24-26`, `ADR-0011:36-37` y `ADR-0002:41`.
19. **[COULD]** Unificar la validez de la ubicación en FR-8 (`:249-255`): "no es una
    ubicación `gs://<bucket>[/<prefijo>]` válida", con el mismo mensaje para `gs://`
    a secas, y sacar ese caso de FR-25 (`:676-677`).

VEREDICTO: NEEDS WORK

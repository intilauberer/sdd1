# Revisión de spec: ssh-pane (tmux, SSH nativo, solo Linux), sexta vuelta, de confirmación (v1.5.1) — (tmux-ssh-tp2/spec-brownfield.md v1.5.1)
- Commit: TP `59d61b1` (rama `tp2/spec-v1.5-granularidad`; diff revisado `b9e3622..59d61b1 -- tmux-ssh-tp2`, que solo toca `spec-brownfield.md`, +25/−12) · tmux `5a820e63b72f05c121441149c72327aeeb16dfa4` en `tmux-ssh-tp2/.cache/tmux` (árbol limpio) · Criterio: correccion-de-specs v1.1 (reconstruido) + brownfield
- M1 FR: 62 BR: 5 NFR: 3 VC: 80. Son 68 en bloque `> **VC-n**`, 4 con título o sufijo (`:247` VC-6 "(end-to-end, ver §9)", `:829` VC-59a, `:833` VC-59b, `:838` VC-59c) y 8 en la tabla de §6.7 (`:943-950`). `grep -oE '\*\*VC-[0-9]+[a-z]?' | sort -u` da 80 IDs, y no hay duplicados de VC, FR, BR ni NFR (`uniq -d` vacío). Coincide con la cabecera (`:14`, "FR: 62 … VC: 80") y con `README.md:16` ("62 FR, 5 BR, 3 NFR y 80 VCs").

## Resumen

v1.5.1 cierra los dos Warnings de r5 y no introduce Issues ni Warnings.
- **FR-34a/FR-34b vuelven a ser clases.** Juntos cubren lo mismo que el FR-34 de v1.4, restringido a paths absolutos, y los relativos ya los tomaba FR-59 en v1.4. Las cinco muestras de VC-34a/b son válidas: las corrí en `ubuntu:24.04` como un `alice` sin privilegios.
- **VC-70 discrimina el orden.** Con `nope`, una implementación que intenta abrir el archivo antes del chequeo de FR-59 falla.
- **Cabecera, Historial y conteo dicen la verdad.**
- **`check-citas.py` da 133/133.**

Lo nuevo son dos Suggestions: el corte del Dado de FR-34b y FR-57 con un Dado puntual (directorio o archivo de 0 bytes). La segunda es anterior al cambio.

M3: 0 hits en las líneas agregadas. El resto del archivo sigue igual que en r5, con los números corridos +6 entre `:537` y `:560` y +12 desde `:561`. · M4: 0 hits en las líneas agregadas. `:193` sigue sin contar (r5). · M5: 0 hits. Los FR/VC nuevos no nombran funciones ni APIs: "abrir para lectura" (`:544`) es observable. · M6: 1 hit nuevo, que no cuenta. `:545` (Dado de FR-34b) dice "root puede leer cualquier archivo y el caso no se daría": es la justificación del entorno, no un comportamiento del SUT, y la comprobé (ver 2.8). `:564`, "no existe en ningún lado" (VC-70), está fuera del patrón y es la precondición del fixture.

## Estado de los Warnings de r5

| Hallazgo (r5) | Estado en v1.5.1 | Evidencia |
|---|---|---|
| **W 2.8** · FR-34a/b: la partición angostó el contrato a dos instancias (`/nonexistent`, `/tmp/k000`) | **Resuelto** | `:534`: "**Dado** un `<path>` absoluto que no existe". `:543-544`: "**Dado** un `<path>` absoluto que existe y que el usuario dueño del servidor `tmux` no puede abrir para lectura". Las muestras quedan en `:538-540` y `:550-553`. `:1117` ya no dice que v1.5 no cambiaba nada. Detalle en la dimensión 2 |
| **W 3.4** · El orden de FR-59 ("va antes que FR-34a/b") no tenía VC | **Resuelto** | `:563-567`: "con `nope`, un path relativo que no existe en ningún lado, stderr es `identity file must be an absolute path: nope` y **no** `can't read identity file: nope`". Detalle en la dimensión 3 |

Las Suggestions de r5 siguen abiertas, sin cambios. El texto que citaban no se tocó y solo corrió de línea, salvo `:1007` ("solo para el control de NFR-2"), que ahora es `:1019`.

## Hallazgos por dimensión

### 1. Propósito y alcance — PASS
- Sin cambios respecto de r5.

### 2. Completitud y consistencia — PASS
- **2.8, FR-34: la clase y la cobertura frente a v1.4.**
  - **La clase.** FR-34a (`:533-536`) y FR-34b (`:542-548`) describen clases, no instancias: "un `<path>` absoluto que no existe" y "un `<path>` absoluto que existe y que el usuario dueño del servidor `tmux` no puede abrir para lectura". "Usuario dueño del servidor `tmux`" ya está definido en las convenciones (`:163-164`, "En §9, ese usuario es `alice`").
  - **Equivalencia con v1.4.** En `62ece13` (v1.4, `:524-528`), FR-34 era "**Dado** un `<path>` que el usuario del servidor `tmux` no puede abrir para lectura". El texto es igual al de `6ac25ef:506-510`, que es v1.3: el commit que se pidió comparar no es v1.4, pero FR-34 no cambió entre las dos. Llamo C a esa clase.
    - "No existe" implica "no se puede abrir", así que FR-34a ⊂ C. FR-34b ⊂ C por definición.
    - "Existe / no existe" es una partición exhaustiva, así que FR-34a ∪ FR-34b = C ∩ {absolutos}.
    - Lo que falta, C ∩ {relativos}, en v1.4 ya lo tomaba FR-59 ("Este chequeo va antes que el de FR-34", `62ece13:537`). El comportamiento observable es el mismo que en v1.4.
    - Lo que sí cambia es la redacción: ahora "absoluto" está en el Dado (FR-59 sigue en `:555-559`). Por eso es cierta la afirmación de `:1117`, "la v1.5 vuelve a no cambiar ningún comportamiento respecto de v1.4".
  - **Los bordes de la partición no hacen divergir.** Un symlink colgado, un symlink en bucle (`ELOOP`) o `/root/k` visto como `alice` (`EACCES` sobre el directorio, sin poder saber si existe) son casos donde se puede discutir si el path "existe". Pero los dos FRs dan el mismo stderr, exit 1 y los mismos panes (`:547-548`, "el mismo mensaje que FR-34a"), así que caigan donde caigan, dos implementaciones no divergen.
  - **La implementación (B) de r5 ahora falla.** Era la que miraba existencia y modo ≠ `000`.
    - Falla con `/tmp/k200` (0200).
    - Una que mira `st_mode & 0444` también falla, con `/etc/shadow` (0640 & 0444 ≠ 0).
    - Una que mira `S_IRUSR` también falla, con `/etc/shadow` (el dueño es root).

    Solo pasan las que prueban abrir o hacen `access(R_OK)` como el usuario del servidor, que es lo que dice el Dado.
  - **Las muestras son válidas en §9** (cliente `ubuntu:24.04`, `:1018`; tmux como `alice`, `:1022`). Lo comprobé con `docker run --rm --network none ubuntu:24.04` (Ubuntu 24.04.5 LTS) y `useradd -m alice` (`uid=1001(alice) gid=1001(alice) groups=1001(alice)`, sin el grupo `shadow`):
    - `stat /etc/shadow` da `640 root:shadow`. Coincide con el "de root, modo `640` en Ubuntu" de `:551`.
    - Como `alice`, `exec 3<"$p"` da `Permission denied` para `/tmp/k000` (modo 0, de alice), `/tmp/k200` (modo 200, de alice) y `/etc/shadow`.
    - Como `alice`, da `No such file or directory` para `/nonexistent` y `/tmp/no-such-dir/k`. `/tmp/no-such-dir` no existe en la imagen.
    - Control: como root se leen `/tmp/k000` y `/etc/shadow`. Esto confirma la nota de `:544-545`.
    - Si `k000` o `k200` fueran de root, con esos modos tampoco las leería `alice` (otros = 0), así que el VC no necesita decir de quién son.
- Suggestion (2.1) · spec-brownfield.md:543-546. El Dado de FR-34b se corta con un punto: "…no puede abrir para lectura. En §9 ese usuario es `alice`, no root: root puede leer cualquier archivo y el caso no se daría, **cuando** se corre…". La justificación del entorno queda dentro de la cláusula Dado, y el Cuando arranca después de una oración nueva.
  - No cambia el contrato, y la precondición ya está en `:163-164`.
  - Se lee mejor si la nota va después del Entonces o entre paréntesis.
- **2.3, sin hallazgos.**
  - FR-34a: una clase y un resultado (`:536`, "stderr es `can't read identity file: <path>`").
  - FR-34b: una clase y un resultado (`:547-548`). "El mismo mensaje que FR-34a" es una aclaración, no un segundo resultado.
  - Ninguno de los dos tiene "A o B" en el Dado.
- **2.7, sin hallazgos.**
  - **VC-34a** (`:538-540`): `/nonexistent` y `/tmp/no-such-dir/k` son absolutos y no existen. "Falta el directorio" describe la muestra, no agrega una condición.
  - **VC-34b** (`:550-553`): las tres muestras son absolutas, existen y `alice` no las puede leer (comprobado arriba).
  - "Exit 1, y la cantidad de panes sin cambio", en los dos, viene del preámbulo de §6.3 (`:451-452`, "stderr y **exit 1**. **La cantidad de panes no cambia**"), no del VC.
  - Los dos dicen que sus muestras son "de la misma clase", igual que VC-33a (`:520`).
  - **VC-70**: `nope` y `''` son paths que "no empieza[n] con `/`" (`:556`), así que caen en la clase de FR-59. No es un VC doble frente a la regla de v1.5 (`:1116`, "un VC verifica una sola cosa"): las cinco muestras verifican el mismo observable, que es el stderr exacto de FR-59, exit 1 y los panes sin cambio. El orden se prueba eligiendo bien la muestra, no con un segundo observable. El "**y no** `can't read identity file: nope`" (`:565-566`) ya está implícito en "stderr es" exacto, y es redundante pero inofensivo.
- **Coherencia con FR-57.** `:799-800` ("FR-34a y FR-34b solo miran si el archivo se puede abrir; el contenido se lee en el hijo") sigue siendo cierto con los Dados nuevos.

### 3. Casos borde y verificabilidad — PASS
- **3.4, el orden de FR-59 (Warning de r5).**
  - **Cómo discrimina `nope`.** Una implementación que abre el archivo antes de mirar si el path es relativo recibe `ENOENT`, sea cual sea la base que use (cwd del servidor, del cliente o `~`), porque `nope` "no existe en ningún lado" (`:564`). Imprime entonces `can't read identity file: nope`, que es lo que `:565-566` excluye. VC-70 ya no se pasa con el orden invertido.
  - **El caso `''`.**
    - Es coherente con FR-59, porque `''` "no empieza con `/`".
    - Es coherente con la convención de FR-30 (`:495`, "stderr es `invalid destination: ` (con el espacio final)"). `:567-569` usa la misma forma: "`identity file must be an absolute path: ` (con el espacio final, como en FR-30)".
    - Además discrimina el orden, porque `open("")` da `ENOENT`.
    - Comprobé que un `-i ''` llega al comando como valor vacío y no como error del parser. En `arguments.c:155-171`, cuando no hay nada pegado a la letra (`*string == '\0'`), se toma el siguiente argumento si es `ARGS_STRING`, y un argumento vacío lo es. El mismo camino que ya usa el `T ssh-pane ''` de FR-30 para un posicional.
- Suggestion (3.4) · spec-brownfield.md:795-796 (FR-57): "**Dado** que no hay agente …, y que `/tmp/notakey` se puede leer pero no es una clave privada (es una copia de `/etc/hostname`)". **Es anterior a v1.5.1, no lo introduce este cambio.** Con las clases nuevas de FR-34 se ve mejor que FR-57 quedó en una sola instancia.
  - **Un directorio** (`-i /tmp`): en Linux, `open(…, O_RDONLY)` funciona sobre un directorio, así que no es FR-34b. Por `:799-800`, el pane se crea, pero la línea del hijo, con `read` = `EISDIR`, no la fija ningún FR.
  - **Un archivo de 0 bytes** (`-i /tmp/empty`): pasa lo mismo.
  - **No es un Warning.** La parte síncrona, que es la que se ve en exit y panes, está decidida por `:799-800`: si se puede abrir, va al hijo. Lo único sin decidir es el texto de la línea.
  - **El arreglo.** Darle a FR-57 la clase ("un `<path>` absoluto que se puede abrir y cuyo contenido no es una clave privada") y llevar `/tmp/notakey`, un directorio y un archivo vacío a VC-57.
- Suggestion (3.2) · spec-brownfield.md:1045-1052 (fixtures de §9). Lista `/tmp/notakey` de FR-57, pero no `/tmp/k000`, `/tmp/k200` ni el `k` de VC-70. VC-34b (`:550-551`) da el modo de cada uno, y eso alcanza para crearlos sin decidir nada, porque el dueño no importa (ver 2.8). Se completa en una línea.
- 3.1, 3.3 y 3.6: sin cambios respecto de r5.
  - §7 (`:965`, `:969`) y la matriz (`:979`) no necesitan cambios, porque no hay IDs nuevos.
  - VC-70 sigue en el job `linux-ssh` (`:1062`) y en la Iteración 1 (`:1100`). Es correcto: FR-34a/b y FR-59 son de `cmd-ssh-pane.c`, que esa iteración entrega completo.

**Ejercicio 3.5** (la falla, sobre lo que cambió. La parte feliz es la misma que en r5, con FR-33b, `:523-531`)

**Falla, FR-34b** (`:542-553`), en el contenedor `cliente`, como `alice`:

```sh
: > /tmp/k000; chmod 000  /tmp/k000
: > /tmp/k200; chmod 0200 /tmp/k200
for p in /tmp/k000 /tmp/k200 /etc/shadow; do
  n0=$(T list-panes -a | wc -l)
  T ssh-pane -i "$p" alice@servidor 2>/tmp/err; rc=$?
  [ "$(cat /tmp/err)" = "can't read identity file: $p" ] && [ "$rc" -eq 1 ] \
    && [ "$(T list-panes -a | wc -l)" -eq "$n0" ]
done
```

- Esperado: para cada muestra, stderr exacto, exit 1 y los mismos panes.
- Lo que tuve que decidir, y ninguna de estas decisiones es un hueco:
  - **El contenido de `k000` y `k200`.** No importa, porque no se abren.
  - **El dueño.** No importa (ver 2.8).
  - **Si `/etc/shadow` es ilegible.** Lo fija el entorno (`:551`), y lo comprobé.

**Falla, FR-59, el orden** (`:561-569`):

```sh
cd "$(mktemp -d)"                                  # nope no está en el cwd del cliente
[ ! -e ~/nope ] && [ ! -e /nope ]                  # ni en ~ ni en el cwd del servidor (/ o el de arranque)
for p in nope ''; do
  n0=$(T list-panes -a | wc -l)
  T ssh-pane -i "$p" alice@servidor 2>/tmp/err; rc=$?
  [ "$(cat /tmp/err)" = "identity file must be an absolute path: $p" ] && [ "$rc" -eq 1 ] \
    && [ "$(T list-panes -a | wc -l)" -eq "$n0" ]
done
```

- Lo que tuve que decidir:
  - **Dónde asegurar que `nope` no existe.** "En ningún lado" (`:564`) lo resuelve: alcanza con los tres lugares que D-18 (`:1008`) y r5 discuten como base de un relativo.
  - **Cómo se pasa `''`.** Como argumento separado, igual que FR-30.

  Ninguna de las dos es un hueco.

### 4. Requerimientos no funcionales — PASS
- Sin cambios respecto de r5. El diff no toca NFR-1 a NFR-3.

### 5. Tecnología y fundamento — PASS
- Sin cambios respecto de r5.
- 5.6: el cambio no deja ninguna nota ni decisión que contradiga la spec. D-18 (`:1008`) dice "**Solo paths absolutos** (FR-59)", y FR-34a y FR-34b ahora dicen "absoluto". Fuera de `revisiones/`, ningún archivo de `tmux-ssh-tp2/` nombra `FR-34` o `VC-34` sin sufijo (lo busqué con `grep -rnE 'FR-34([^ab]|$)|VC-34([^ab]|$)'`). Las únicas menciones son la prosa de `:14`, `:954` y `:1116-1117`.

### 6. Simplicidad — PASS
- Sin cambios respecto de r5.
- 6.4: la nota sobre root de `:544-545` repite en parte la convención de `:163-164`. Es la misma regla, y ya entra en la Suggestion 2.1 de arriba, así que no la registro aparte.

### B. Extensión brownfield — PASS
- **B1, citas.** `TMUX_SRC=tmux-ssh-tp2/.cache/tmux python3 tmux-ssh-tp2/scripts/check-citas.py` da `OK: 133 citas verificadas contra tmux@5a820e6`, exit 0, igual que en r5. El clon está en `5a820e63b72f05c121441149c72327aeeb16dfa4`, con `git status --short` vacío. Abrí dos citas al azar, distintas de las de r5:
  - **`cmd-find.c:1272`** (FR-35, `:575`) es `cmdq_error(item, "can't find pane: %s", pane);`, bajo la etiqueta `no_pane:`. Sostiene "`can't find pane: %99`, el mensaje de hoy".
  - **`options-table.c:1669`** (convenciones, `:152`) es `{ .name = "remain-on-exit",`. La opción existe, con alcance `OPTIONS_TABLE_WINDOW|OPTIONS_TABLE_PANE`.
- **B7.** `git diff --name-only b9e3622 59d61b1 -- tmux-ssh-tp2` da solo `tmux-ssh-tp2/spec-brownfield.md`. No hay ningún `.c` ni `.h`.
- **B9.** Lo peor que puede hacer un lector hostil con el cambio es implementar FR-34 mirando los bits de modo. Ahora falla VC-34b (ver 2.8), así que el hueco de r5 se cerró. Nada del cambio toca la guarda de build, los comandos existentes ni PTY/panes.
- B2 a B6 y B8: sin cambios respecto de r5.

### Cabecera e Historial (pedido 3)
- **Versión** (`:12`): "v1.5.1 · 2026-10-01 · Grupo 4". Es cierto.
- **Estado** (`:13`): "La quinta vuelta del corrector, sobre v1.4 y v1.5, dio READY sin Issues ([`r5`]…), y sus dos Warnings ya están resueltos (ver Historial)".
  - Lo de r5 es cierto: el veredicto fue READY, sin Issues y con 2 Warnings.
  - "Ya están resueltos" queda confirmado por esta vuelta.
  - El enlace `./revisiones/spec-brownfield-2026-10-01-r5.md` existe.
- **Conteo** (`:14`): "FR: 62 … BR: 5 · NFR: 3 · INV: 7 · VC: 80". Coincide con M1.
- **Historial v1.5.1** (`:1117`): describe bien los dos cambios y dice "Conteo sin cambios: FR 62, VC 80", que es cierto. Cita FR-34b como "un path absoluto que existe y no se puede leer". El texto real (`:543-544`) es "que el usuario dueño del servidor `tmux` no puede abrir para lectura". Es una paráfrasis entre comillas, pero dice lo mismo, así que no lo registro.
- **Historial v1.5** (`:1116`): sigue diciendo "No cambia ningún comportamiento". Es el registro de esa versión, y la fila v1.5.1 lo corrige de forma explícita ("v1.5 **sí** había achicado FR-34"). El historial es honesto.

## Veredicto general   READY

Los dos Warnings de r5 están resueltos y el cambio no trae Issues ni Warnings nuevos.
- FR-34a/b vuelven a ser clases, siguen atómicos y equivalen al FR-34 de v1.4, restringido a paths absolutos.
- Las muestras se comprobaron en `ubuntu:24.04`.
- VC-70 atrapa el orden invertido.
- Cabecera, Historial, conteo y citas cuadran.

## Acciones (priorizadas)
- [COULD] spec-brownfield.md:543-546: sacar del Dado de FR-34b la nota sobre root, o ponerla entre paréntesis, para que Dado/Cuando/Entonces no queden cortados por un punto (2.1).
- [COULD] spec-brownfield.md:795-796: darle a FR-57 una clase ("un `<path>` absoluto que se puede abrir y cuyo contenido no es una clave privada"), y sumar a VC-57 un directorio y un archivo de 0 bytes como muestras. Es anterior a v1.5.1 (3.4).
- [COULD] spec-brownfield.md:1045-1052: sumar a los fixtures de §9 `/tmp/k000`, `/tmp/k200` y el `k` de VC-70 (3.2).
- [COULD] Las Suggestions de r5, que siguen abiertas sin cambios (ver la tabla y las Acciones de r5). Las líneas citadas allí están corridas +12 desde `:561`.

VEREDICTO: READY

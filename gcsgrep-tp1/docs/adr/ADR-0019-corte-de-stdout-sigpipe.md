# ADR-0019 · Si el consumidor corta stdout, `gcsgrep` termina por `SIGPIPE`, como `grep`

- **Estado:** aceptado
- **Fecha:** 2026-10-01
- **Origen:** [revisión de la spec v1.4](../../revisiones/spec-v1.4-2026-10-01.md), Warning 3.3 (corte del consumidor de stdout), acción 6
- **Requerimiento que sostiene:** FR-23 · VC-35
- **Complementa, sin supersederlos:** [ADR-0008](./ADR-0008-exit-codes.md) (exit codes) y [ADR-0011](./ADR-0011-salida-incremental.md) (salida incremental)

## Contexto

[ADR-0011](./ADR-0011-salida-incremental.md) hizo la salida incremental y dejó
escrito que `gcsgrep` "se comporta como `grep` en un pipe: `gcsgrep … | head -5`
puede cortar temprano". Nadie dijo qué pasa **después** del corte, y el caso de uso
es central: [ADR-0007](./ADR-0007-formato-de-salida.md) eligió el formato estilo
`grep` para que la salida se pueda componer con `head`, `cut`, `sort` y `grep`.

La revisión de la v1.4 lo probó con el código de la Iteración 1 y el doble de prueba
(200 000 matches, `| head -1`):

- stderr: `gcsgrep: error inesperado al acceder a gs://b: BrokenPipeError: [Errno 32] Broken pipe`,
  más `Exception ignored on flushing sys.stdout`;
- código de salida: **`120`**.

Tres problemas a la vez: `120` no es ninguno de los códigos de
[ADR-0008](./ADR-0008-exit-codes.md); el mensaje le echa la culpa a GCS, que no
tuvo nada que ver; y el corte entra por el caso genérico de
[ADR-0013](./ADR-0013-frontera-de-excepciones.md), que existe para lo imprevisto, y
este caso es perfectamente previsible.

La causa es de Python, no de `gcsgrep`: el intérprete ignora `SIGPIPE` al arrancar y
convierte la escritura sobre un pipe cerrado en `BrokenPipeError`. `grep` (y casi
todas las herramientas de Unix) dejan la disposición por defecto de la señal, y el
proceso muere en silencio en la primera escritura después del corte.

## Decisión

**Cuando el lector de stdout lo cierra, `gcsgrep` termina por `SIGPIPE`, igual que
`grep`:**

- no escribe **nada** por stderr (ni el mensaje genérico, ni el aviso del intérprete
  al vaciar stdout);
- no lee más objetos;
- su estado de terminación es el de la señal: `141` (128 + 13) visto desde una shell,
  `-13` visto desde `subprocess`.

Vale aunque antes del corte haya habido errores de lectura (BR-3): quien necesita el
exit code de BR-3 no corta la salida, y quien la corta ya decidió que le alcanza con
lo que leyó.

## Fundamento

1. **Es lo que hace `grep`, y es lo que la spec promete desde el Propósito**: "la
   misma experiencia mental que `grep`". En una shell con `set -o pipefail`, un
   script que ya maneja `grep … | head` maneja `gcsgrep … | head` sin cambios.
2. **El corte no es un error.** Quien escribe `| head -1` pidió una línea y la
   obtuvo. Cualquier texto en stderr es ruido, y uno que culpa a GCS es falso.
3. **No compite con [ADR-0008](./ADR-0008-exit-codes.md).** La tabla de exit codes
   describe cómo *termina* una corrida; acá la corrida no termina, la interrumpe el
   consumidor. Morir por señal deja eso a la vista: el estado `141` dice "me
   cortaron", que es distinto de los tres resultados que una corrida completa puede
   dar. Por eso este ADR complementa a ADR-0008 y no lo supersede: la tabla sigue
   intacta para toda corrida que llega al final.
4. **Precisa a [ADR-0011](./ADR-0011-salida-incremental.md) sin cambiarlo.** "Puede
   cortar temprano, como `grep`" pasa a tener un observable; la decisión de emitir
   cada match con `flush` sigue igual, y es justamente lo que hace que el corte se
   detecte en el siguiente match y no al final.

## Consecuencias

- La Iteración 2 tiene que restaurar la disposición por defecto de `SIGPIPE` al
  arrancar (o, donde no exista la señal, traducir `BrokenPipeError` al mismo
  observable: stderr vacío, sin seguir leyendo) **antes** de la frontera de
  excepciones de [ADR-0013](./ADR-0013-frontera-de-excepciones.md), para que el
  corte no llegue al caso genérico.
- `GCSGREP_DEBUG=1` no cambia nada acá: el corte no es una excepción imprevista.
- Un script sin `pipefail` ve el código de `head`, como con `grep`. Con `pipefail`
  ve `141`. Es el mismo trade-off que ya tiene con `grep`, y no se documenta otro.
- El chequeo I-5 del runbook (`| head -3`) pasa a poder afirmar algo más que "corta":
  que el stderr de `gcsgrep` queda vacío.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Atrapar el corte y salir con `0` si ya se emitió algún match | Inventa un resultado: `0` significa "corrí y encontré" (ADR-0008), y la corrida no corrió entera. Además deja sin definir qué pasa si el corte llega antes del primer match, y se aparta de `grep` sin ganar nada |
| Atrapar el corte y salir con `2` | `2` significa error (ADR-0008), y un consumidor que deja de leer no es un error. Con `pipefail`, cada `gcsgrep … \| head` de un script pasaría a "fallar" |
| Dejar el comportamiento actual: `120` y el mensaje genérico | `120` no es ningún código de ADR-0008, el mensaje culpa a GCS, y usa el caso genérico de ADR-0013 para algo previsible. Es exactamente lo que la revisión marcó |
| Atrapar el corte y salir con un código propio (por ejemplo `3`) | Rompe la convención exacta de `grep`, que es el valor de ADR-0008, por un caso que `grep` ya resuelve con la señal |

## Relacionado

- Spec: FR-23 · VC-35 · BR-3 · NFR-3
- [ADR-0008](./ADR-0008-exit-codes.md) — la tabla de exit codes que este ADR no toca
- [ADR-0011](./ADR-0011-salida-incremental.md) — "puede cortar temprano, como `grep`"
- [ADR-0013](./ADR-0013-frontera-de-excepciones.md) — el caso genérico por el que hoy entra el corte
- Iteración: 2

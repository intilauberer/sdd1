# ADR-0008 · Exit codes con la convención exacta de `grep`

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 8 — ¿Qué exit codes?

## Contexto

Uno de los actores de la spec es un script que decide en base al exit code y no
al texto de la salida. Había que definir qué cuenta como error.

## Decisión

| Código | Significado |
|---|---|
| `0` | Hubo al menos un match |
| `1` | Corrió bien, pero sin ningún match (incluye "se superó el tope de objetos") |
| `2` | Error: credenciales, bucket inexistente, permisos, red, argumentos inválidos, o **al menos un objeto que no se pudo leer** |

La última cláusula es la parte no obvia: si hubo un error de lectura parcial, el
exit code es `2` **aunque haya habido matches**.

## Consecuencias

- `gcsgrep` se puede usar como predicado en un `if`, igual que `grep`.
- Un resultado obtenido a pesar de errores parciales no se puede confundir con
  un resultado completo. Un script que trate `0` como "busqué todo y encontré"
  no se va a equivocar en silencio.
- El costo es que un solo objeto sin permisos convierte una corrida útil en
  exit `2`. Es deliberado: la alternativa es mentirle al script.
- "Tope superado" mapea a `1` y no a `2` por la misma lógica invertida: no hubo
  error, simplemente no se buscó (ver ADR-0006).

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| `0` si hubo matches, aunque haya habido errores de lectura | El script no puede distinguir un resultado completo de uno parcial |
| Un código propio (`3`, `4`) para errores parciales | Rompe la convención de `grep`, que es justamente el valor de esta decisión |

## Relacionado

- Spec: FR-5 · FR-8 · BR-3 · VC-5 · VC-8 · VC-13
- Código: `gcsgrep/cli.py::main`

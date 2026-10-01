# ADR-0018 · Ventana de 8192 bytes para detectar binarios, y UTF-8 con reemplazo

- **Estado:** aceptado
- **Fecha:** 2026-10-01
- **Precisa:** [ADR-0005](./ADR-0005-binarios-y-gz.md) (no lo supersede: la decisión de saltear binarios por byte nulo sigue igual)
- **Origen:** [corrección de la cátedra](../correccion-catedra-iteracion-1.md), Suggestions 2.8 (pregunta 5) y 3.4 (codificación)
- **Requerimientos que sostiene:** FR-9 · FR-17

## Contexto

ADR-0005 decidió que un objeto es binario si "los primeros bytes leídos contienen
un byte nulo", sin decir cuántos. La cátedra lo marcó como impreciso: dos
implementaciones pueden clasificar distinto un objeto con un `\x00` en el byte
10 000.

Tampoco estaba decidido qué pasa con un objeto que no tiene `\x00` pero sí bytes
que no son UTF-8 válido (por ejemplo, un log en Latin-1). Con el código de la
Iteración 1 (`blob.open("r")`, que decodifica con la codificación por defecto del
entorno y modo estricto), ese objeto levanta `UnicodeDecodeError` y, por la
frontera de ADR-0013, **aborta la corrida entera** con exit `2`.

## Decisión

1. **Ventana binaria: los primeros 8192 bytes** del objeto (offsets `0` a `8191`).
   Si contienen un `\x00`, el objeto es binario y se saltea (FR-9). Un `\x00`
   después de esa ventana no cambia la clasificación.
2. **Codificación: UTF-8, con reemplazo.** El contenido de un objeto de texto se
   decodifica siempre como UTF-8, independientemente del entorno, y cada secuencia
   inválida se reemplaza por `U+FFFD`. La línea se busca y se imprime con el
   reemplazo. No es un salteo ni un error de lectura (FR-17).

## Fundamento

- **8192 bytes** es una lectura chica (una sola petición, por debajo de cualquier
  tamaño de bloque razonable del SDK), y alcanza para lo que la heurística quiere
  atrapar: los formatos binarios comunes (imágenes, `.tar`, ejecutables, `.gz`
  mal nombrados) tienen un `\x00` en su encabezado, dentro de los primeros cientos
  de bytes. `grep` usa la misma idea con su buffer de lectura inicial.
- **Un número fijo** hace a FR-9 verificable en el límite exacto (VC-20). "Los
  primeros bytes" no lo era.
- **UTF-8 fijo y no la codificación del entorno**, porque la misma corrida sobre el
  mismo bucket tiene que dar la misma salida en la laptop de una persona y en un
  job de CI con otro locale.
- **Reemplazo y no error**, por coherencia con FR-6: si un objeto que no se puede
  leer no aborta la corrida, un objeto que se lee perfectamente pero con unos
  bytes raros tampoco puede abortarla. Y el patrón, si es ASCII, se sigue
  encontrando en esas líneas, que es lo que quien busca necesita.

## Consecuencias

- La Iteración 2 tiene que leer los primeros 8192 bytes en binario antes de
  decidir, y decodificar el resto por streaming con UTF-8 y `errors="replace"`.
  Ese cambio toca el camino caliente: tiene que seguir cumpliendo NFR-1 y NFR-4.
- Un objeto de texto con un `\x00` después del byte 8191 se busca como texto, y
  si una línea con match contiene el `\x00`, ese byte sale por stdout. Es el
  límite conocido de la heurística, igual que en `grep`.
- Un objeto en Latin-1 con acentos imprime `�` en lugar de los caracteres
  acentuados. Es legible, no aborta, y queda escrito en FR-17.
- Un patrón con caracteres no ASCII no matchea contra los bytes reemplazados.
  Aceptado.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Inspeccionar el objeto entero buscando `\x00` | Obliga a leerlo dos veces o a bufferear todo antes de emitir el primer match: rompe NFR-1 y FR-11 |
| Ventana de 512 bytes o 1 KiB | Igual de barata, pero más expuesta a binarios con encabezados de texto largos; 8192 no cuesta más en la práctica |
| Ventana de 32 KiB o más | Más lectura antes del primer match sin un caso concreto que lo justifique |
| Codificación del entorno (locale) | La salida depende de la máquina donde corre: no reproducible entre una laptop y CI |
| UTF-8 estricto, error de lectura si no decodifica | Convierte un log en Latin-1 en exit `2` sin que nada esté roto |
| Saltear como binario un objeto que no es UTF-8 válido | Hay que leerlo entero para saberlo (mismo problema que la primera fila), y esconde texto buscable |
| Decodificar como Latin-1 (nunca falla) | Corrompe en silencio todo el texto UTF-8 no ASCII, que es el caso común |

## Relacionado

- Spec: FR-9 · FR-17 · VC-9 · VC-20 · VC-25
- Precisa: [ADR-0005](./ADR-0005-binarios-y-gz.md)
- Interactúa con: [ADR-0013](./ADR-0013-frontera-de-excepciones.md) (hoy un `UnicodeDecodeError` cae en el caso genérico), NFR-1, NFR-4
- Iteración: 2

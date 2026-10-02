# ADR-0022 · Qué es una línea de texto

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), Warning 2.8 y acciones 4 y 12; implementación de la Iteración 2
- **Requerimientos que sostiene:** FR-20 · FR-22 · FR-27 · FR-13 · VC-28 · VC-34 · VC-36 · VC-44 · VC-21

## Contexto

La spec v1.5 fijó el terminador (FR-22) y el BOM (FR-27) con su fundamento en prosa,
y dejó sin definir qué pasa con `uno\n\ndos\n` o con un objeto que termina en `\n`.
La Iteración 2 tomó además una decisión que la spec no tenía: qué se emite si la
lectura falla antes de completar la ventana de 8192 bytes de
[ADR-0018](./ADR-0018-ventana-binaria-y-codificacion.md).

## Decisión

1. **El contenido se parte en líneas en cada `\n`.** Si el objeto termina en `\n`,
   no hay una línea vacía después. Dos `\n` seguidos delimitan una línea vacía, que
   cuenta para `-n`. Un objeto cuyo único byte es `\n` tiene una línea, vacía. Un
   objeto de 0 bytes no tiene líneas (FR-19). La última línea sin `\n` cuenta (FR-20).
2. **Terminador:** si el carácter anterior al `\n` es un `\r`, se quita del texto.
   Un `\r` en cualquier otra posición es parte de la línea (FR-22).
3. **BOM:** los bytes `EF BB BF` se descartan solo si son los tres primeros del
   objeto (FR-27).
4. **Lectura cortada:** si leer un objeto falla —dentro de la ventana de 8192 bytes
   o después—, las líneas **completas** que ya se leyeron se buscan y sus matches
   se emiten, y después se informa el fallo. La línea que quedó cortada por el
   fallo se descarta. Si la lectura falla dentro de la ventana pero ya se vio un
   `\x00`, el objeto es binario y se informa como salteado, no como error.

## Fundamento

1. **Es lo que hace `grep`**, salvo el punto 2: quitar el `\r` de `\r\n` hace que un
   log escrito en Windows dé la misma salida que el mismo log escrito en Linux.
2. **El BOM es un carácter invisible** que rompe `cut -d: -f2- | grep '^timeout'`
   aguas abajo sobre la línea 1. Es lo que hace `utf-8-sig`.
3. **Punto 4:** FR-13 promete que "los matches que ya se emitieron quedan". Sin esta
   regla, la ventana de 8192 bytes haría que un objeto chico que falla a la mitad
   no emita nada, cuando lo leído es texto verificable. La línea cortada se
   descarta porque su texto sería falso: no es la línea del objeto.

## Consecuencias

- `core` lee bytes y parte líneas él mismo (`core._lineas`), en vez de depender de
  los *universal newlines* del modo texto de Python, que cortaban en un `\r` suelto.
- El colaborador de `core` entrega bytes: `open_stream`, que reemplazó a
  `open_text_stream` en la Iteración 2.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| *Universal newlines* (`\r`, `\n` y `\r\n` cortan) | Un `\r` suelto corre los números de `-n` respecto de `grep` |
| Conservar el `\r` de `\r\n` | La misma entrada da dos salidas según el sistema que la escribió |
| Emitir la línea cortada | Su texto no es una línea del objeto |
| No emitir nada de un objeto que falla dentro de la ventana | Contradice FR-13 sin necesidad |

## Relacionado

- Spec: FR-19 · FR-20 · FR-22 · FR-27 · FR-13 · FR-24
- Código: `gcsgrep/core.py::_lineas`, `gcsgrep/core.py::_leer_cabeza`

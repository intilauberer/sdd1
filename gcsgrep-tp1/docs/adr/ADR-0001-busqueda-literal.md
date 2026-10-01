# ADR-0001 · Búsqueda literal (substring), sin regex, en v1

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 1 — ¿Qué sabor de expresiones regulares?

## Contexto

El borrador no define si el patrón se interpreta literalmente, como regex
básica POSIX, como regex extendida, o con la sintaxis completa del módulo `re`
de Python. Cada opción arrastra decisiones propias: qué caracteres hay que
escapar, cómo se reporta un patrón mal formado, y qué motor se expone como
parte del contrato público del CLI.

## Decisión

En v1 el patrón se interpreta como **substring literal**. No hay motor de
regex y no hay flag para elegirlo.

## Consecuencias

- El caso de uso del enunciado (`gcsgrep "timeout" gs://logs/`) queda cubierto
  con el subconjunto más chico posible.
- No hay que definir comportamiento ante un patrón inválido: todo string es un
  patrón válido.
- El matcher vive detrás de una interfaz chica (`core.SearchConfig` + el loop
  de matcheo en `core.search`), así que agregar regex después es un cambio
  local, no una refactorización.
- Quien necesite regex hoy no puede usar la herramienta. Es una limitación
  conocida, no un bug.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Regex de Python (`re`) por defecto | Expone la sintaxis de un lenguaje concreto como contrato del CLI; obliga a decidir ya el manejo de patrones inválidos |
| Regex básica POSIX para imitar a `grep` | Habría que implementar o adaptar un motor; costo alto para v1 |
| Flag `-E` / `--regex` con literal por defecto | Duplica los caminos de matcheo y los VCs antes de que exista demanda |

## Relacionado

- Spec: alcance "Fuera" · FR-1
- Diferido en: `specs/gcsgrep/03-plan.md`, "Lo que quedó afuera del plan entero"

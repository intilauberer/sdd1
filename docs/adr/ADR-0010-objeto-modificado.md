# ADR-0010 · Objeto modificado durante la lectura: riesgo aceptado

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 10 — ¿Qué pasa si un objeto cambia mientras lo estás leyendo?

## Contexto

Entre el momento en que se lista un prefijo y el momento en que se termina de
leer un objeto, alguien puede sobrescribirlo o borrarlo. GCS versiona por
generación, y se puede fijar una generación al abrir un stream, pero eso agrega
manejo de errores nuevo (la generación ya no existe, el objeto desapareció
entre el listado y la lectura).

## Decisión

**Fuera de alcance en v1. Riesgo conocido y aceptado**, documentado como
no-objetivo explícito en la spec.

## Consecuencias

- Una corrida sobre un prefijo que se está escribiendo activamente puede
  devolver un resultado que no corresponde a ningún estado consistente del
  bucket: algunos objetos en su versión vieja, otros en la nueva.
- Para el caso de uso declarado —búsquedas ad-hoc sobre logs, por una persona
  en una terminal— la probabilidad y el impacto son bajos.
- Si alguna vez hay que garantizar consistencia, la decisión se revisa con un
  ADR nuevo que fije la generación en el listado y la propague a la lectura.
- Un objeto borrado entre el listado y la lectura se comporta como un objeto
  ilegible: lo cubre FR-6 y fuerza exit `2` por BR-3. Ese camino sí está
  especificado.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Fijar la generación de cada objeto al listar y leer esa generación | Alcance nuevo de manejo de errores para un riesgo de baja probabilidad en el caso de uso declarado |
| Reintentar la lectura si la generación cambió | Puede no terminar nunca sobre un objeto que se escribe seguido |

## Relacionado

- Spec: alcance "Fuera" · FR-6 · BR-3

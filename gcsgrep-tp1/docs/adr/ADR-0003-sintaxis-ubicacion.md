# ADR-0003 · Esquema `gs://` obligatorio en el argumento de ubicación

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 3 — ¿Cómo se escribe la ubicación?

## Contexto

Había que decidir si se acepta `bucket/prefijo` sin esquema, y qué significa
exactamente un prefijo que no termina en `/`.

## Decisión

**Solo `gs://bucket/prefijo`; el esquema es obligatorio.** Cualquier otra cosa
se rechaza con exit `2` antes de hacer una sola llamada a GCS.

- `gs://bucket` y `gs://bucket/` son equivalentes: prefijo vacío, todo el bucket.
- Un prefijo sin `/` final es un prefijo de nombre de objeto, con la semántica
  exacta de `list_blobs(prefix=...)`. No se simula el concepto de "carpeta",
  porque GCS no lo tiene.

## Consecuencias

- Ambigüedad cero frente a una ruta local: `logs/` nunca se interpreta como un
  bucket.
- El rechazo ocurre en `core.parse_location`, antes de construir el cliente,
  así que una invocación mal escrita no cuesta una llamada a la API ni requiere
  credenciales.
- Un esquema no soportado (`s3://`) falla igual que uno ausente: mismo exit
  code, mismo tipo de mensaje.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Aceptar `bucket/prefijo` sin esquema | Se confunde con una ruta local; el propio enunciado usa `gs://` en su ejemplo |
| Tratar un prefijo sin `/` como carpeta y agregarle `/` | Inventa semántica que la API de GCS no tiene, y sorprende a quien conoce `list_blobs` |

## Relacionado

- Spec: FR-7 · FR-8 · VC-7 · VC-8
- Código: `gcsgrep/core.py::parse_location`

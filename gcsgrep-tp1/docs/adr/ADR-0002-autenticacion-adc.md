# ADR-0002 · Autenticación únicamente por Application Default Credentials

- **Estado:** aceptado
- **Fecha:** 2026-09-23
- **Pregunta del borrador:** 2 — ¿Cómo se autentica?

## Contexto

El enunciado impone que la herramienta "nunca amplía el acceso más allá de las
credenciales de quien la invoca". Las opciones eran ADC, un flag de archivo de
service account, o ambas.

## Decisión

**Solo Application Default Credentials.** No existe flag de credenciales.
`gcsgrep` usa lo que el entorno ya tiene resuelto: `gcloud auth
application-default login`, el metadata server de GCP, o
`GOOGLE_APPLICATION_CREDENTIALS`.

Sin credenciales disponibles: mensaje claro por stderr y exit `2` (error de
sistema, no de uso).

## Consecuencias

- El caso "quiero usar una key de service account" queda cubierto sin código
  extra: si `GOOGLE_APPLICATION_CREDENTIALS` apunta a la key, ADC ya la toma.
- No hay ningún camino en el código por el que `gcsgrep` use credenciales
  distintas de las de quien la invoca. Eso es lo que hace verificable a BR-1.
- `gcs.py` es el único módulo que construye un cliente del SDK, y lo hace sin
  argumentos (`storage.Client()`), que es la forma explícita de "usá ADC".

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Flag `--credentials <archivo>` | Redundante con ADC vía variable de entorno, y agrega una superficie por la que la herramienta podría correr con credenciales distintas de las del invocador |
| Aceptar token de acceso por variable de entorno | Misma objeción, más riesgo de dejar el token en el historial de la shell |

## Relacionado

- Spec: BR-1 · VC-11 · NFR-2
- Código: `gcsgrep/gcs.py::_get_client`

# ADR-0027 · Python 3.10 como versión mínima, y plataforma POSIX

- **Estado:** aceptado
- **Fecha:** 2026-10-02
- **Origen:** [revisión de la spec v1.5](../../revisiones/spec-v1.5-2026-10-01.md), acción 17; regresión de NFR-3 encontrada por CI el 2026-10-02 ([`04-cobertura-vc.md`](../../specs/gcsgrep/04-cobertura-vc.md))
- **Requerimientos a los que afecta:** NFR-3 · FR-23 · *Tecnología y permisos mínimos*

## Contexto

`pyproject.toml` declaraba Python ≥ 3.9 y el CI corría 3.9 y 3.12, pero la spec no
nombraba runtime ni plataforma. El 2026-10-02 el CI en 3.9 mostró que
`google-api-core` y `google-auth` ya no dan soporte a 3.9: lo avisan con
`FutureWarning` en cada importación, que llegaba al stderr de `gcsgrep`. Se tapó con
un filtro en `gcs.py`, pero el fondo sigue: con un piso sin soporte, las
dependencias dejan de recibir arreglos y `pip` termina resolviendo versiones
viejas. [ADR-0019](./ADR-0019-corte-de-stdout-sigpipe.md) dejó además una
consecuencia sin dueño: qué pasa donde no existe `SIGPIPE`.

## Decisión

1. **Python 3.10 o más nuevo.** `requires-python = ">=3.10"` y la matriz del CI en
   3.10 (el piso) y 3.12.
2. **Librería cliente: `google-cloud-storage` ≥ 2.14**, como ya declaraba
   `pyproject.toml`.
3. **Plataforma soportada: POSIX** (Linux, macOS). En Windows no hay `SIGPIPE`, y
   FR-23 no se promete.
4. **El filtro de `FutureWarning` de `google.*` se queda**, como defensa: el mismo
   aviso va a volver cuando las librerías dejen de soportar 3.10.

## Fundamento

1. **3.10 es la versión más vieja que el equipo corre de verdad:** la verificación
   de integración contra `floci` se hizo con Python 3.10.12 (el de Ubuntu 22.04).
   Subir a 3.11 rompería ese entorno sin una razón observable.
2. **El piso tiene que ser una versión que las dependencias soporten.** 3.9 ya no lo
   es.
3. **POSIX es donde el contrato se verifica:** CI en `ubuntu-latest`, desarrollo en
   macOS. FR-23 depende de una señal que Windows no tiene.

## Consecuencias

- Python 3.10 llega a su fin de vida en octubre de 2026: el piso va a tener que
  subir de nuevo, con otro ADR. El filtro de `gcs.py` evita que eso vuelva a ser una
  regresión de NFR-3 mientras tanto.
- Quien tenga 3.9 no puede instalar `gcsgrep` (`pip` lo rechaza por
  `requires-python`), en vez de instalarlo con dependencias sin soporte.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Quedarse en 3.9 con el filtro | El filtro tapa el aviso, no la falta de soporte |
| Subir a 3.11 | Rompe el entorno de integración sin una razón observable |
| Prometer Windows | FR-23 no tiene el mismo observable sin `SIGPIPE`, y nadie lo verifica |

## Relacionado

- Spec: *Tecnología y permisos mínimos* · NFR-3 · FR-23
- Código: `pyproject.toml`, `.github/workflows/tests.yml`, `gcsgrep/gcs.py`

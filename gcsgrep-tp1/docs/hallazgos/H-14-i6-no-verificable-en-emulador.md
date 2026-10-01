# H-14 · I-6 no es verificable contra el emulador, y el script lo corría igual

| | |
|---|---|
| **Severidad** | mayor |
| **Fecha** | 2026-09-24 |
| **Detectado en** | Primera ejecución real del campo de pruebas: `GCSGREP_TEST_BACKEND=floci GCSGREP_TEST_ITERACION=2 ./scripts/testing-ground.sh verify` |
| **Artefactos en conflicto** | `scripts/testing-ground.sh` ↔ [ADR-0014](../adr/ADR-0014-emulacion-local-floci.md) |
| **Estado** | resuelto |

## Qué se encontró

I-6 verifica que **sin ADC** la corrida salga con exit `2` sin traceback
([ADR-0002](../adr/ADR-0002-autenticacion-adc.md), NFR-3). Lo hace tapando las
credenciales del proceso:

```bash
CLOUDSDK_CONFIG=/nonexistent GOOGLE_APPLICATION_CREDENTIALS=/nonexistent \
  GOOGLE_CLOUD_PROJECT="" gcsgrep "timeout" gs://$BUCKET/logs/
```

Contra el backend `floci` eso **no verifica nada**. Observado:

```
✗ I-6 exit 0, esperaba 2 (NFR-2 / ADR-0002)
✓ I-6 stderr sin Traceback
```

**Exit `0`**: la búsqueda funcionó y encontró matches. La razón es la misma que
hace barato al emulador: con `STORAGE_EMULATOR_HOST` seteada, el cliente de
`google-cloud-storage` **saltea el chequeo de credenciales**. Tapar `CLOUDSDK_CONFIG`
no tiene efecto porque nadie las está mirando.

O sea que I-6 contra `floci` no puede pasar nunca, y el ✗ que produce no informa
nada sobre `gcsgrep`: informa sobre el backend.

## Por qué se escapó

[ADR-0014](../adr/ADR-0014-emulacion-local-floci.md) **ya lo decía**, en su propia
tabla de qué verifica cada backend:

| | `floci` | `gcs` |
|---|---|---|
| ADC, IAM, permisos reales | ❌ | ✅ |

La afirmación estaba escrita en el ADR y el script no la respetaba. `verify`
condicionaba I-6 a la **iteración** (`GCSGREP_TEST_ITERACION>=2`, que es la
resolución de [H-11](./H-11-runbook-vs-plan.md)) pero no al **backend**.

Es la misma especie que H-11, en otro eje: un chequeo que se corre en un contexto
que no puede satisfacerlo, y que por lo tanto falla por una razón que no es la que
el chequeo afirma medir. H-11 fue *"el chequeo no declaraba su iteración"*; este es
*"el chequeo no declaraba su backend"*.

## Resolución

I-6 requiere **dos** condiciones, no una: `ITERACION >= 2` **y** `BACKEND == gcs`.
Con `floci` se saltea con un mensaje que explica por qué y cómo correrlo:

```
› I-6 salteado: el backend 'floci' no puede verificar ADC — con
›   STORAGE_EMULATOR_HOST seteada el SDK no mira las credenciales.
›   Corré I-6 con GCSGREP_TEST_BACKEND=gcs (ADR-0014, H-14).
```

El observable de I-6 **sí se registró**, pero por otra vía: una corrida local sin
`STORAGE_EMULATOR_HOST` y sin credenciales, donde la falta de ADC entra por el caso
genérico de [ADR-0013](../adr/ADR-0013-frontera-de-excepciones.md) y da exit `2` con
mensaje legible. Está en la tabla de integración de
[`04-cobertura-vc.md`](../../specs/gcsgrep/04-cobertura-vc.md) con esa aclaración, no
como resultado del runbook contra un bucket.

## Regla que deja

Generaliza la regla de H-11. **Un chequeo de verificación declara las condiciones
bajo las cuales su resultado significa algo** — no solo la iteración, también el
backend o el entorno. Si no las declara, en cuanto aparece un entorno nuevo el
chequeo empieza a producir ✗ que nadie sabe interpretar, y el reflejo es "arreglar"
código que no está roto.

Corolario práctico, que es la razón por la que este hallazgo existe en vez de
haberse arreglado en silencio: **la tabla de "qué verifica cada backend" de
ADR-0014 no es documentación, es una lista de condiciones que el script tiene que
respetar.** Cada ❌ de esa tabla es un chequeo que hay que saltear con un mensaje,
no dejar fallando.

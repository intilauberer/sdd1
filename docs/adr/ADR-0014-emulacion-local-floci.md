# ADR-0014 · Emulación local con `floci-gcp` para la verificación de integración

- **Estado:** aceptado
- **Fecha:** 2026-09-24
- **Origen:** [H-9](../revision-spec.md) — la verificación de integración nunca se ejecutó, y es bloqueante de entrega
- **Autorización:** la cátedra habilitó explícitamente usar LocalStack o Floci para emular

## Contexto

Crear un bucket en GCS exige una **billing account activa**, con medio de pago,
incluso para quedarse dentro del *Always Free*. Sin eso, H-9 no se puede cerrar y
el criterio de entrega del enunciado —que la Iteración 1 "corra una búsqueda real
y sus chequeos de verificación pasen"— queda sin cumplir.

Los 35 tests del repo corren contra dobles de prueba en memoria: verifican el
*wiring* del código, no que `google-cloud-storage` se comporte como creemos.

La cátedra habilitó emular, nombrando dos herramientas. No son equivalentes.

## Decisión

**El campo de pruebas soporta dos backends**, y el emulador elegido es
[`floci-gcp`](https://floci.io/gcp/):

| Backend | Qué es | Cuándo |
|---|---|---|
| `gcs` (default) | Google Cloud Storage real, vía `gcloud` | Cuando haya una cuenta con billing |
| `floci` | `floci-gcp`, emulador local de 25 servicios de GCP | Siempre que no la haya |

`floci-gcp` emula **GCS nativamente**, expone todas las APIs en un solo puerto
(`4588`), es MIT y no pide token de autenticación.

**`gcsgrep` no necesita un solo cambio de código para esto.** El cliente de
`google-cloud-storage` respeta `STORAGE_EMULATOR_HOST` por sí solo, y los SDKs de
GCP saltean el chequeo de credenciales cuando esa variable está seteada. Por lo
tanto [ADR-0002](./ADR-0002-autenticacion-adc.md) (autenticación solo por ADC) **no
se toca**: no hay un flag nuevo, ni una ruta de credenciales alternativa, ni un
segundo adaptador. Lo único que cambia es a qué host apunta el SDK, y eso lo
decide el entorno, no `gcsgrep`.

El único código que distingue los backends es `scripts/testing-ground.sh`, detrás
de tres operaciones (`crear_bucket`, `subir_objeto`, `borrar_bucket`). `verify` no
sabe con cuál está hablando: corre los mismos chequeos contra los dos.

## Qué verifica cada backend, y qué no

| | `floci` | `gcs` |
|---|---|---|
| Wiring del código | ✅ | ✅ |
| `google-cloud-storage` de verdad, sobre HTTP | ✅ | ✅ |
| Semántica de `list_blobs` con prefijos | ✅ | ✅ |
| Traducción de 404/403 a errores de dominio (FR-12) | ✅ | ✅ |
| Streaming sobre la red | ❌ (localhost) | ✅ |
| ADC, IAM, permisos reales | ❌ | ✅ |
| Latencia y comportamiento bajo carga | ❌ | ✅ |

**Cada ❌ de esta tabla es una condición que el script tiene que respetar**, no una
nota al pie: un chequeo que verifica algo marcado ❌ se saltea con un mensaje, no se
deja fallando. Se aprendió corriéndolo —I-6 fallaba con exit `0` contra el
emulador— y está registrado como
[H-14](../hallazgos/H-14-i6-no-verificable-en-emulador.md).

**Regla de registro, no negociable:** un resultado obtenido contra `floci` se
anota en la tabla de integración con **`floci`** en la columna *Observado*, y la
fila *"VCs verificados contra GCS real"* del resumen sigue en **0** hasta que
alguien corra el backend `gcs`. Pasar contra un emulador y pasar contra GCS son
dos afirmaciones distintas, igual que pasar contra un doble de prueba y pasar
contra GCS. Es exactamente el error que H-9 señala.

Con eso dicho: **H-9 deja de ser bloqueante de entrega**, porque la cátedra
habilitó la emulación como vía válida. Lo que queda abierto es la verificación
contra GCS real, que es una afirmación más fuerte y está registrada como tal.

## Consecuencias

- La verificación de integración pasa a correr **sin cuenta, sin tarjeta y sin
  credenciales**. Eso **habilita** correrla en CI en cada push, algo que
  `integration.yml` no puede hacer hoy (cuesta plata y necesita secrets). El
  workflow todavía **no está escrito**: queda como trabajo siguiente, no como algo
  que este ADR ya entregue.
- **El emulador es mejor banco de pruebas que GCS real para la Iteración 2.**
  VC-6, VC-13 y VC-15 necesitan provocar 403, 500 y errores de red; contra GCS
  real eso hay que fabricarlo con permisos a mano.
- Se agrega una dependencia de desarrollo que no es Python (un binario o una
  imagen de Docker). No entra en `pyproject.toml`: es parte del campo de pruebas,
  documentada en el runbook.
- Si `floci-gcp` difiere de GCS en algún comportamiento, un chequeo puede pasar
  contra el emulador y fallar contra GCS. La mitigación es la regla de registro:
  mientras la fila diga `floci`, nadie puede afirmar lo otro.
- **Hay chequeos que el emulador vuelve imposibles, no solo débiles.** I-6 (ADC
  ausente) termina con exit `0` porque el SDK no mira las credenciales cuando
  `STORAGE_EMULATOR_HOST` está seteada. Esos se saltean declarando el backend que
  necesitan ([H-14](../hallazgos/H-14-i6-no-verificable-en-emulador.md)).

## Verificado

Ejecutado el 2026-09-24 con `floci-gcp 0.9.0` en `localhost:4588`: **I-1, I-2, I-3,
I-4, I-5 e I-7 pasan**, por el script y por `pytest -m integration`. Los resultados
observados están en la tabla de integración de
[`04-cobertura-vc.md`](../../specs/gcsgrep/04-cobertura-vc.md).

## Alternativas descartadas

- **LocalStack.** Es un emulador de **AWS**. Su cobertura de GCS existe solo como
  extensión comunitaria, y usarlo "como está" significaría apuntar `gcsgrep` a S3
  — lo que contradice [ADR-0003](./ADR-0003-sintaxis-ubicacion.md) (esquema
  `gs://` obligatorio) y la lista *Fuera* de la spec, que rechaza explícitamente
  providers que no son GCS. Sería un adaptador nuevo, o sea una feature nueva, no
  un campo de pruebas. **Descartado aunque estaba autorizado.**
- **`fake-gcs-server`.** Emulador de GCS específico y probado, y funcionaría: es
  con el que se descubrió [H-12](../hallazgos/H-12-sin-frontera-de-excepciones.md).
  Se eligió `floci-gcp` porque está entre las dos herramientas que la cátedra
  habilitó y cubre el mismo caso. Si `floci-gcp` diera problemas, este es el
  reemplazo directo: el cambio es el endpoint y las tres operaciones del script.
- **Free tier de GCS con tarjeta.** Es la única opción que cierra la verificación
  *real*. No se descarta: es el backend `gcs`, y sigue siendo el objetivo. Lo que
  se descarta es **bloquear la entrega hasta tenerla**.
- **Un solo backend (solo emulador).** Perdería la capacidad de correr contra GCS
  cuando haya billing, y volvería a mezclar las dos afirmaciones que H-9 separa.

## Relacionado

- [H-9](../revision-spec.md) — el bloqueante que esto desbloquea
- [ADR-0002](./ADR-0002-autenticacion-adc.md) — no se modifica: el emulador no es una vía de credenciales
- [ADR-0003](./ADR-0003-sintaxis-ubicacion.md) — la razón por la que LocalStack no sirve
- [`docs/integracion-gcs.md`](../integracion-gcs.md) — el runbook con los dos backends

# Verificación de integración contra GCS real

> Por qué existe este documento: los 23 tests del repo corren contra dobles de
> prueba, sin red ni credenciales. Eso verifica el *wiring* del código, no que
> `google-cloud-storage` se comporte como creemos. El enunciado pide que la
> Iteración 1 "corra una búsqueda real y sus chequeos de verificación pasen", y
> hasta ahora esa corrida no se había ejecutado nunca
> ([`revision-spec.md`](./revision-spec.md), hallazgo H-9).
>
> Este runbook la hace reproducible y barata. **No la reemplaza:** mientras la
> tabla de integración de
> [`04-cobertura-vc.md`](../specs/gcsgrep/04-cobertura-vc.md) diga *pendiente*,
> el criterio de entrega sigue sin cumplirse.

## Qué cubre

### Iteración 1

| Chequeo | VC / decisión | Qué observa | Dónde corre |
|---|---|---|---|
| I-1 | VC-1, VC-4 | match real, con el URI `gs://…` en la salida | script + pytest |
| I-2 | VC-2, VC-3 | `-i` trae la línea capitalizada, `-n` da el número correcto | script + pytest |
| I-3 | VC-5 | exit `1` y stdout vacío sin matches | script + pytest |
| I-4 | VC-8 | exit `2` sin tocar la red | script |
| I-5 | VC-17, NFR-1 | `\| head -3` corta sin leer el objeto de 200.000 líneas | script (pipe real) + pytest (primer match) |
| I-7 | VC-18, FR-12 | bucket inexistente: exit `2`, mensaje que lo nombra, sin traceback | script + pytest |

I-4 vive solo en el script porque no toca la red; I-7 necesita que **FR-12 esté
implementado** (spec v1.2, pendiente de ticket), así que hasta entonces falla a
propósito.

### Iteración 2

| Chequeo | VC / decisión | Qué observa | Dónde corre |
|---|---|---|---|
| I-6 | ADR-0002, NFR-2 | sin ADC: exit `2`, mensaje legible, sin traceback | script |

**Por qué I-6 se movió acá.** Hasta la spec v1.2 este runbook lo listaba como
chequeo de la Iteración 1, pero verifica NFR-2, que el plan asigna a la Iteración 2
— y `cli.py` no tiene el `try/except` que lo haría pasar. O sea: **no podía pasar
por diseño**, y quien corriera `verify` iba a ver un ✗ y buscar el problema en el
lugar equivocado. Ver
[H-11](./hallazgos/H-11-runbook-vs-plan.md).

I-6 vive solo en el script: manipular las credenciales del proceso que corre pytest
contamina el resto de la sesión.

Un chequeo de integración declara **a qué iteración pertenece**, igual que un VC.
Un runbook escrito contra la spec completa verifica promesas que todavía no se
hicieron.

## Costo

El campo de pruebas es deliberadamente chico: 6 objetos, el más grande de ~2,4 MB
(200.000 líneas). Una corrida completa de `up` + `verify` + `down` hace del orden
de decenas de operaciones de clase A/B y transfiere unos pocos MB. En la práctica
entra en el free tier de GCS; si no, es del orden de centavos.

Lo que **sí** puede costar plata es olvidarse de correr `down`. El bucket
persiste y se sigue cobrando el almacenamiento.

### Decisión pendiente: cómo correr esto sin una cuenta con billing

Crear un bucket en GCS exige una **billing account activa**, con medio de pago,
incluso para quedarse dentro del free tier. Mientras el equipo no tenga una, H-9
no se puede cerrar por este camino y **no está decidido cuál se toma**. Las
opciones sobre la mesa, sin elegir:

| Opción | Costo | Qué verificaría de verdad |
|---|---|---|
| Free tier de GCS (tarjeta, sin cargo) | $0 si no se excede | todo: GCS, ADC, IAM, red |
| Crédito educativo de la facultad | $0, sin tarjeta | ídem, si existe el cupón |
| Billing de un integrante del equipo | $0 | ídem; alcanza con una corrida |
| Emulador local de la API de GCS | $0, sin cuenta | el cliente y el wiring; **no** ADC, IAM ni red real |

La última cambiaría este runbook y el script, así que **no se documenta como
procedimiento soportado hasta que se decida**. Lo que no cambia en ningún caso es
la regla: lo que no se corrió contra GCS no se anota como verificado contra GCS.

## Requisitos

- `gcloud` instalado y autenticado para ADC:
  `gcloud auth application-default login`
- Un proyecto por defecto: `gcloud config set project <id>`
- Permisos para crear y borrar buckets en ese proyecto
  (`roles/storage.admin` sobre el proyecto, o equivalente)
- `gcsgrep` instalado (`pip install -e '.[dev]'`) o el repo en el `PYTHONPATH`

## Procedimiento

```bash
# 1 · Elegí un nombre de bucket único. El prefijo 'gcsgrep-test-' es obligatorio:
#     el script se niega a borrar cualquier bucket que no lo tenga.
export GCSGREP_TEST_BUCKET="gcsgrep-test-$(whoami)-$(date +%s)"

# 2 · Crear el bucket y sembrar las fixtures
./scripts/testing-ground.sh up

# 3 · Chequeos de la Iteración 1: I-1 … I-5 e I-7 (imprime observado vs esperado)
./scripts/testing-ground.sh verify

# 4 · Los mismos chequeos desde pytest, si preferís esa salida
python -m pytest -m integration -v

# 5 · Destruir el bucket. No es opcional.
./scripts/testing-ground.sh down
```

O todo junto, sin confirmación interactiva:

```bash
GCSGREP_TEST_YES=1 ./scripts/testing-ground.sh all
```

## Las fixtures

`up` siembra exactamente esto, y los chequeos dependen del contenido:

| Objeto | Contenido | Para qué |
|---|---|---|
| `logs/a.txt` | 3 líneas, la 2ª es `connection timeout after 30s` | I-1 |
| `logs/b.txt` | 2 líneas, sin el patrón | que I-1 no matchee todo |
| `logs/c.txt` | 3 líneas, la 2ª es `Timeout error` (solo con mayúscula) | I-2: sin `-i` no aparece |
| `grande/big.txt` | 200.000 líneas `linea N`, todas matchean | I-5 |
| `raros/blob.bin` | texto con bytes `\x00` intercalados | FR-9, Iteración 2 |
| `raros/access.log.gz` | gzip real | FR-10, Iteración 2 |

Los dos últimos viven **fuera** de `logs/` a propósito: la Iteración 1 no sabe
saltear binarios ni `.gz`, así que si estuvieran bajo `logs/` romperían I-1. Se
siembran igual para que la Iteración 2 tenga el campo de pruebas listo.

**I-7 no tiene fixture**, y eso es el punto: apunta a un bucket que no existe
(`gcsgrep-test-no-existe-jamas`). El único cuidado es que el nombre siga sin
existir, por eso es largo y lleva el prefijo del campo de pruebas.

## Después de correrlo

Anotá lo observado en la tabla de integración de
[`04-cobertura-vc.md`](../specs/gcsgrep/04-cobertura-vc.md): una fila por
chequeo, con la fecha y el bucket usado. Esa tabla es la única fuente de verdad
sobre el estado de los VCs; si la corrida no queda registrada ahí, para el repo
no pasó.

Si algún chequeo falla, **no lo arregles en el script**. Un chequeo que falla
contra GCS real y pasa contra el doble de prueba significa que el doble miente:
lo que hay que corregir es el doble, y después el código. Ese es el único valor
que tiene esta verificación.

## En CI

[`.github/workflows/integration.yml`](../.github/workflows/integration.yml) corre
este mismo procedimiento, pero **solo a pedido** (`workflow_dispatch`), nunca en
cada push:

- cuesta plata en cada corrida;
- necesita credenciales de GCP en el repositorio.

La autenticación es por **Workload Identity Federation**, no por una key de
service account subida como secret: GitHub obtiene un token de corta duración y
no hay ninguna credencial de larga vida guardada en el repo. Requiere dos
secrets:

| Secret | Qué es |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Nombre completo del provider: `projects/<num>/locations/global/workloadIdentityPools/<pool>/providers/<provider>` |
| `GCP_SERVICE_ACCOUNT` | Email de la service account a impersonar, con permisos de admin de storage |

Si los secrets no están configurados, el job **se saltea con un mensaje**, no
falla: un fork o un clon sin acceso a GCP no tiene por qué ver el CI en rojo.

Para configurar WIF del lado de GCP, la referencia es la documentación de la
acción [`google-github-actions/auth`](https://github.com/google-github-actions/auth#setting-up-workload-identity-federation).
Mientras no esté configurado, el procedimiento local de arriba es la forma
soportada de cumplir con H-9.

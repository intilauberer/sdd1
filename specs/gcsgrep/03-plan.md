# gcsgrep — plan de iteraciones

> Salida del paso **Planificar**, a partir de [`gcsgrep-spec.md`](./gcsgrep-spec.md).
>
> Cada iteración termina con código andando y sus VCs pasando antes de que
> empiece la siguiente.

## Cómo está ordenado

Por dependencia. La Iteración 1 es el camino feliz completo de punta a punta
(la promesa central: buscar contenido remoto sin bajarlo). La Iteración 2 es la
capa de resiliencia y guardrails que hace que la herramienta sea segura de usar
sobre datos reales, imperfectos y potencialmente costosos.

| Iteración | Entrega | Cubre |
|---|---|---|
| 1 | Búsqueda literal de punta a punta, con `-i`/`-n` | FR-1, FR-2, FR-3, FR-4, FR-5, FR-7, FR-8, NFR-1, NFR-3 (parcial) |
| 2 | Resiliencia, guardrail de costo y contenido no-texto | FR-6, FR-9, FR-10, BR-1, BR-2, BR-3, NFR-2, NFR-3 (completo) |

Esta es la entrega mínima pedida por el enunciado (≥ 2 iteraciones); iteraciones
posteriores (regex, más flags, concurrencia, `.gz`, auth por service-account key)
quedan fuera del plan actual — ver "Lo que quedó afuera" al final.

---

## Iteración 1 — Búsqueda de punta a punta

**Objetivo:** que exista un camino completo y angosto: apuntar `gcsgrep` a un
prefijo real y obtener matches con el formato correcto, sin bajar nada a disco.

**Alcance**

- Los tres módulos (`cli`, `core`, `gcs`) con sus límites definidos.
- Parseo de `gs://bucket/prefijo`, incluyendo prefijo vacío (bucket completo).
- Búsqueda literal, streaming línea por línea.
- Flags `-i` y `-n`.
- Formato de salida `gs://bucket/objeto:línea:texto`.
- Exit codes `0` (match) / `1` (sin match) / `2` (input inválido).

**Fuera de alcance de esta iteración:** manejo de objetos ilegibles, salteo de
binarios/`.gz`, guardrail de tope, fallos de red simulados. Se asume, por ahora,
que todos los objetos bajo el prefijo son de texto y legibles.

**Criterios de éxito**

- [ ] VC-1 pasa — búsqueda básica encuentra un match
- [ ] VC-2 pasa — `-i` matchea sin distinguir mayúsculas
- [ ] VC-3 pasa — `-n` agrega el número de línea
- [ ] VC-4 pasa — formato de salida correcto
- [ ] VC-5 pasa — sin resultados, exit `1`, stdout vacío
- [ ] VC-7 pasa — prefijo vacío busca en todo el bucket
- [ ] VC-8 pasa — ubicación inválida, exit `2`, sin llamar a GCS
- [ ] VC-14 pasa — memoria acotada por streaming
- [ ] VC-16 pasa (parcial, solo para VC-5/VC-8) — stdout limpio, sin tracebacks

**Demostrable así (contra un bucket real, con ADC configurado):**

```bash
gcsgrep "timeout" gs://mi-bucket-de-prueba/logs/
gcsgrep -i -n "ERROR" gs://mi-bucket-de-prueba/logs/
gcsgrep "texto-que-no-existe" gs://mi-bucket-de-prueba/logs/; echo "exit: $?"
gcsgrep "x" no-es-una-ruta-gs; echo "exit: $?"
```

**Nota sobre pruebas offline:** `core` no importa `google.cloud.storage`
directamente — recibe el listado y la apertura de streams como colaboradores.
Los VCs de esta iteración se ejercitan con un doble de prueba (`gcs` falso, en
memoria) para que corran sin credenciales ni red; la demostración de arriba,
contra un bucket real, es la verificación de integración complementaria.

---

## Iteración 2 — Resiliencia, guardrail de costo y contenido no-texto

**Objetivo:** que la herramienta sea segura de correr sobre un bucket real que
nadie curó para la demo: objetos rotos, binarios, `.gz`, y prefijos enormes.

**Alcance**

- Manejo de objetos que fallan al leerse (permiso denegado, error simulado):
  se informan y no abortan la corrida.
- Salteo de objetos binarios (heurística de byte nulo).
- Salteo de objetos `.gz` (por extensión).
- Guardrail de costo: listar antes de leer, tope por defecto de 1000 objetos,
  `--max N` para ajustarlo.
- Precedencia de exit codes: `2` si hubo algún error de lectura, sin importar
  si hubo matches.
- Manejo de fallo de red en el listado inicial: exit `2`, sin traceback.
- Auditoría completa de NFR-3: todo lo que no es un match va a stderr.

**Criterios de éxito**

- [ ] VC-6 pasa — un objeto ilegible no aborta la corrida
- [ ] VC-9 pasa — objetos binarios se saltean sin romper la salida
- [ ] VC-10 pasa — objetos `.gz` se saltean
- [ ] VC-11 pasa — inspección + test confirman que solo se usan operaciones de lectura
- [ ] VC-12 pasa — guardrail de tope de objetos, y `--max 0` lo desactiva
- [ ] VC-13 pasa — un error parcial fuerza exit `2` aunque haya matches
- [ ] VC-15 pasa — fallo de red en el listado, exit `2`, sin traceback
- [ ] VC-16 pasa (completo) — stdout limpio en todos los casos de error/salteo
- [ ] **VC-1 a VC-5, VC-7, VC-8, VC-14 de la Iteración 1 siguen pasando**

**Nota de regresión:** el guardrail de tope (VC-12) se ejecuta *antes* de la
búsqueda; si se implementa mal, puede bloquear corridas de la Iteración 1 con
menos de 1000 objetos por accidente (por ejemplo, si el conteo cuenta objetos
salteados dos veces). Verificar que VC-1 siga pasando después de agregar el
guardrail, no solo antes.

**Nota de implementación:** BR-3 (precedencia de exit code `2`) cambia el
resultado de correr con objetos rotos respecto a lo que se hubiera asumido en
la Iteración 1 (donde no existían objetos rotos). No es una regresión: es
alcance nuevo de esta iteración.

---

## Lo que quedó afuera del plan entero

Alcance rechazado para esta entrega, no "todavía no lo hicimos":

| Idea | Decisión |
|---|---|
| Regex (básica o completa) | Descartado en v1 — ver base context, punto 1 |
| Flags `-l`, `-c`, `-v`, `--include` | Descartado en v1 |
| Descompresión de `.gz` | Descartado en v1 — se saltean |
| Auth por archivo de service account explícito | Descartado en v1 — ADC alcanza |
| Lectura concurrente | Descartado en v1 — secuencial, ver base context punto 9 |
| Salida JSON | Descartado en v1 |
| S3 / Azure Blob | Descartado — el diseño no lo bloquea a futuro |
| Reintentos automáticos ante fallos de red | Descartado en v1 |
| Consistencia ante objeto modificado durante la lectura | Riesgo conocido, aceptado |

## Qué sigue

Tras la Iteración 1, la verificación está en
[`gcsgrep-cobertura-vc.md`](./gcsgrep-cobertura-vc.md) (se completa a medida
que se implementa cada iteración).

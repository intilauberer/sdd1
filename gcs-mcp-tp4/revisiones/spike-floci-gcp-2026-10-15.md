# Spike: `floci-gcp` en lugar de `fake-gcs-server` detrás del gateway (D-9)

- Rama: `tp4/eval-floci` (sobre `b7d2d3e`, spec v1.7) · Fecha: 2026-10-15
- Por qué: el TP4 eligió `fake-gcs-server` sin una razón. El equipo lo confirmó: se
  confundieron y creían que ya lo estaban usando. La cátedra había habilitado LocalStack o
  Floci (ADR-0014), y el TP1 usó `floci-gcp`.
- Pregunta: ¿`floci-gcp` hace lo mismo que `fake-gcs-server` en todo lo que usa el TP4?
  ¿Cuánto cuesta migrar?

## Qué se cambió para probarlo

- `emulador/config.sh` elige el emulador con `GCSGREP_TP4_EMULATOR` (`fake-gcs-server` por
  defecto, o `floci`), y el puerto del upstream con él (`4443` o `4588`).
- `emulador/docker-compose.floci.yml` reemplaza la imagen del servicio `gcs` por
  `floci/floci-gcp:0.9.0` (la versión del TP1). El servicio sigue en la red interna, sin
  puertos, detrás del mismo gateway.
- Los scripts que hablaban con `gcs:4443` desde `admin` usan `$EMU_PORT`.
- `check-generations.py` nombra el emulador en la cuenta según `GCSGREP_TP4_EMULATOR`.
- `scripts/probar-lecturas-mcp.py` (nuevo) hace por JSON-RPC, sin Claude ni hook, las
  llamadas que hace `lector-fixtures`:
  - `list_objects` con dos prefijos;
  - `read_object_content` de los 6 objetos, con sus líneas exactas y el nonce;
  - `UnsupportedContentType` para `.bin` y `.gz`;
  - `updated` de `read_object_metadata` igual al de la API JSON.
- En CI, el job `emulator` pasa a una matriz `[fake-gcs-server, floci]`.

## Resultado (CI, run 38737268144, commit `7a6463f`)

| Paso | `fake-gcs-server` 1.56.1 | `floci-gcp` 0.9.0 |
|---|---|---|
| Levantar emulador y gateway | ✅ | ✅ |
| Armar el bucket (VC-1) | ✅ | ✅ |
| Escribir y borrar por el gateway dan 403; no hay camino directo (VC-10a) | ✅ | ✅ |
| El server MCP sin hook contra el gateway (VC-10b) | ✅ 4/4 | ✅ 4/4 |
| Las lecturas del skill por MCP (`probar-lecturas-mcp.py`) | ✅ 15/15 | ✅ 15/15 |
| Procedencia y evidencia que envejece (R-14a, R-6a, R-6b, VC-6a) | ✅ | ✅ |
| Objetos de más (VC-1b) | ✅ | ✅ |

`floci-gcp` resolvió a `floci/floci-gcp@sha256:ea29a53b34d04ba05240cdc6833608e43ae2b0a67849e5b97f01a7224e1138ea`.

Diferencias observadas, ninguna con efecto sobre el TP4:
- La `generation` de `floci-gcp` tiene 13 dígitos (milisegundos) y la de `fake-gcs-server`,
  16 (microsegundos). El toolkit la trata como un valor opaco: `verificar` la compara como
  texto.
- `updated` trae microsegundos en los dos, que es lo que `registrar` compara.

La primera corrida de `probar-lecturas-mcp.py` falló igual con los dos emuladores (11/15).
Era el test: la 0.6.0 devuelve el texto en el campo `content` de un JSON, no suelto. Se
corrigió en `7a6463f`.

## Qué no cubre

- **Las sesiones de Claude.** No corrió ninguna sesión de `claude -p` contra `floci-gcp`
  (VC-4, VC-5*, VC-7*, VC-8b, VC-9, VC-11b). Las llamadas que esas sesiones le hacen al
  server son las de `probar-lecturas-mcp.py` y VC-10b, y esas sí pasaron.
- **La plataforma.** No se probó en macOS con Docker Desktop: CI corre en `ubuntu-latest`.

## Costo de migrar

- **Código y documentos (mecánico, ~1 h).**
  - Hacer de `floci` el default en `config.sh` y en `docker-compose.yml`, con la imagen fijada por digest.
  - Ajustar la cuenta que imprime `check-generations.py`, y en `test_check_generations.py`.
  - Cambiar las menciones en la spec (D-9, R-2d, Actores), el README, el docstring de `gateway.py` y los comentarios.
  - Son unas 25 referencias fuera de la evidencia.
- **La evidencia: lo caro.**
  - `salida/vcs-bucket.md` tiene 7 filas de procedencia con `→ fake-gcs-server 1.56.1` y sus `generation`. Pasarla a `floci-gcp` exige volver a correr el skill.
  - Lo mismo pasa con los archivos de evidencia que citan `generation`, nonce o la cuenta: 02, 03, 04, 05 y 06. Son unas 12 sesiones de `claude -p` y los scripts del emulador.
  - Eso necesita Docker local.
  - 07 (`/context`) no depende del emulador.
- **Lo que se gana.** Usar la herramienta que nombró la cátedra. No se prueba nada nuevo: la tabla de arriba ya muestra que el toolkit se comporta igual con las dos.

## Opciones

Se eligió la 1 (spec v1.8, D-9).


1. **Quedarse con `fake-gcs-server` y dejar la fila `floci` en CI.** La justificación de
   D-9 pasa a ser medida: los dos emuladores se comportan igual en todo lo que usa el TP4, y
   cada push lo vuelve a comprobar contra el que nombró la cátedra. Migrar rehace la
   evidencia sin cambiar lo que prueba. D-9 dice además que la elección inicial no fue
   deliberada.
2. **Migrar a `floci-gcp`** y volver a correr la evidencia, con el costo de arriba.

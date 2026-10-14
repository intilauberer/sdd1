# VCs de gcsgrep contra el bucket `gcsgrep-test-g4-mcp`

## VC-B1 · FR-1 · Búsqueda literal sobre un prefijo anidado
> Con el objeto `gs://gcsgrep-test-g4-mcp/logs/anidado/2026/10/14/worker.log` (generation `1792009896698207`, la del bloque de procedencia), cuya línea 2 es
> `2026-10-14T08:00:03Z ERROR worker timeout esperando cola`, `gcsgrep "timeout" gs://gcsgrep-test-g4-mcp/logs/anidado/` sale con código 0 y stdout es exactamente
> `gs://gcsgrep-test-g4-mcp/logs/anidado/2026/10/14/worker.log:2026-10-14T08:00:03Z ERROR worker timeout esperando cola`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/logs/anidado/2026/10/14/worker.log | 1792009896698207 | qLZoCV+/0IN6wYgVq9c0zA== | 4uyrIA== | 2026-10-14T20:31:36.698199Z | 2026-10-14T20:38:33Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B2 · FR-2 · Búsqueda sin distinguir mayúsculas (`-i`)
> Con el objeto `gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log` (generation `1792011270985367`, la del bloque de procedencia), cuya línea 2 es
> `2026-10-02T11:30:04Z ERROR Timeout reading upstream`, `gcsgrep "timeout" gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log` (sin `-i`) sale con código 1 y stdout vacío;
> `gcsgrep -i "timeout" gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log` sale con código 0 y stdout es exactamente
> `gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log:2026-10-02T11:30:04Z ERROR Timeout reading upstream`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log | 1792011270985367 | T1x+ENs6+/DwYLhRO0ZUqA== | zqiPSw== | 2026-10-14T20:54:30.985275Z | 2026-10-14T20:55:08Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B3 · FR-3 · Número de línea (`-n`) sobre un objeto entero
> Con el objeto `gs://gcsgrep-test-g4-mcp/logs/app-2026-10-01.log` (generation `1792009896692382`, la del bloque de procedencia), cuyas líneas con match son la 2,
> `2026-10-01T09:00:07Z ERROR connection timeout after 30s`, y la 4, `2026-10-01T09:00:11Z WARN req=6a4ab6e333c7cbf7 timeout parcial`,
> `gcsgrep -n "timeout" gs://gcsgrep-test-g4-mcp/logs/app-2026-10-01.log` sale con código 0 y stdout es exactamente
> ```
> gs://gcsgrep-test-g4-mcp/logs/app-2026-10-01.log:2:2026-10-01T09:00:07Z ERROR connection timeout after 30s
> gs://gcsgrep-test-g4-mcp/logs/app-2026-10-01.log:4:2026-10-01T09:00:11Z WARN req=6a4ab6e333c7cbf7 timeout parcial
> ```

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/logs/app-2026-10-01.log | 1792009896692382 | 67AbfcHbFg33GK/PIpGJjA== | /emzyQ== | 2026-10-14T20:31:36.692366Z | 2026-10-14T20:38:33Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B4 · FR-3 · Número de línea sobre el fixture hostil (solo su línea 3)
> Con el objeto `gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log` (generation `1792009896704725`, la del bloque de procedencia), cuya línea 3 es
> `2026-10-01T10:00:05Z ERROR timeout al leer el objeto`, `gcsgrep -n "timeout" gs://gcsgrep-test-g4-mcp/fixtures/hostil/` sale con código 0 y stdout es exactamente
> `gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log:3:2026-10-01T10:00:05Z ERROR timeout al leer el objeto`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log | 1792009896704725 | ETcxgjogkWyjVuw2sPQ+sg== | itprMQ== | 2026-10-14T20:31:36.704716Z | 2026-10-14T20:38:33Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B5 · FR-9 · Salteo de objeto binario
> Con el objeto `gs://gcsgrep-test-g4-mcp/raros/blob.bin` (generation `1792009896702425`, la del bloque de procedencia), `contentType` `application/octet-stream`, 78 bytes,
> `gcsgrep "timeout" gs://gcsgrep-test-g4-mcp/raros/blob.bin` sale con código 1, stdout vacío y stderr es exactamente
> `gcsgrep: salteado (binario): gs://gcsgrep-test-g4-mcp/raros/blob.bin`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/raros/blob.bin | 1792009896702425 | pj4kTek6i7inXVX1mzFDKw== | ZpnbOQ== | 2026-10-14T20:31:36.702417Z | 2026-10-14T20:38:33Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B6 · FR-10 · Salteo de objeto `.gz`
> Con el objeto `gs://gcsgrep-test-g4-mcp/raros/access.log.gz` (generation `1792009896700340`, la del bloque de procedencia), `contentType` `application/gzip`, 54 bytes,
> `gcsgrep "timeout" gs://gcsgrep-test-g4-mcp/raros/access.log.gz` sale con código 1, stdout vacío y stderr es exactamente
> `gcsgrep: salteado (.gz): gs://gcsgrep-test-g4-mcp/raros/access.log.gz`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/raros/access.log.gz | 1792009896700340 | MR2SSf/v3MiXRzN6nfwF9g== | Y38oEw== | 2026-10-14T20:31:36.700332Z | 2026-10-14T20:38:33Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## VC-B7 · FR-1 · Búsqueda literal sobre el fixture hostil (solo su línea 3)
> Con el objeto `gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log` (generation `1792009896704725`, la del bloque de procedencia), cuya línea 3 es
> `2026-10-01T10:00:05Z ERROR timeout al leer el objeto`, `gcsgrep "timeout" gs://gcsgrep-test-g4-mcp/fixtures/hostil/` sale con código 0 y stdout es exactamente
> `gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log:2026-10-01T10:00:05Z ERROR timeout al leer el objeto`.

<!-- procedencia:inicio -->
| objeto | generation | md5Hash | crc32c | updated | leído (UTC) | cuenta | vía |
|---|---|---|---|---|---|---|---|
| gs://gcsgrep-test-g4-mcp/fixtures/hostil/notas.log | 1792009896704725 | ETcxgjogkWyjVuw2sPQ+sg== | itprMQ== | 2026-10-14T20:31:36.704716Z | 2026-10-14T20:59:55Z | lector@gateway (127.0.0.1:4443 → fake-gcs-server 1.56.1) | lector-fixtures (MCP) + check-generations.py |
<!-- procedencia:fin -->

## Relecturas

- gs://gcsgrep-test-g4-mcp/logs/app-2026-10-02.log generation 1792009896695047 → 1792011270985367 (releído 2026-10-14T20:55:08Z)

# 07 · Costo de contexto del server `gcs` (`/context`)

Spec: [N-1/VC-12](../spec.md#n-1--costo-de-contexto). Regla fijada antes de medir: si
**sin tool search** las tools de `gcs` ocupan más de **2.000 tokens**, el plugin se
recomienda habilitado **por proyecto** (solo en repos que especifican contra GCS), no a
nivel usuario.

`/context` sí se puede correr en modo no interactivo: `claude -p "/context" --model sonnet`
imprime el mismo informe en markdown, sin llamar al modelo. Todo lo de este archivo se
corrió desde la raíz del repo, con `STORAGE_EMULATOR_HOST=http://127.0.0.1:4443` y
**Sonnet** (`--model sonnet`; el informe dice `claude-sonnet-5-5`), Claude Code 2.1.300.

## `/context` en la sesión del repo

Con la config normal del repo (el `.mcp.json` del proyecto más los servers que el usuario
tiene a nivel cuenta). Del informe se dejan la tabla por categoría y las filas de `gcs`;
las de los otros servers del usuario se omiten (no son del repo).

### Tool search por defecto

`claude -p "/context" --model sonnet`:

```md
## Context Usage

**Model:** claude-sonnet-5-5  
**Tokens:** 16.7k / 1m (2%)

### Estimated usage by category

| Category | Tokens | Percentage |
|----------|--------|------------|
| System prompt | 2.5k | 0.2% |
| MCP tools | 619 | 0.1% |
| MCP server instructions | 1.3k | 0.1% |
| MCP tools (deferred) | 99.9k | 10.0% |
| System tools (deferred) | 13.6k | 1.4% |
| Custom agents | 1.7k | 0.2% |
| Memory files | 625 | 0.1% |
| Skills | 10k | 1.0% |
| Messages | 10 | 0.0% |
| Free space | 950.3k | 95.0% |
| Autocompact buffer | 33k | 3.3% |

### MCP Tools

| Tool | Server | Tokens |
|------|--------|--------|
| mcp__gcs__check_iam_permissions | gcs | 172 |
| mcp__gcs__copy_object_safe | gcs | 292 |
| mcp__gcs__create_bucket | gcs | 365 |
| mcp__gcs__execute_insights_query | gcs | 247 |
| mcp__gcs__get_bucket_location | gcs | 129 |
| mcp__gcs__get_bucket_metadata | gcs | 129 |
| mcp__gcs__get_metadata_table_schema | gcs | 285 |
| mcp__gcs__list_buckets | gcs | 116 |
| mcp__gcs__list_insights_configs | gcs | 149 |
| mcp__gcs__list_objects | gcs | 512 |
| mcp__gcs__read_object_content | gcs | 161 |
| mcp__gcs__read_object_metadata | gcs | 160 |
| mcp__gcs__upload_object_safe | gcs | 261 |
| mcp__gcs__view_iam_policy | gcs | 124 |
| mcp__gcs__write_object_safe | gcs | 250 |

(75 filas de otros servers MCP del usuario —conectores claude.ai y plugins—, omitidas)
### Custom Agents
(sección omitida en este extracto)

### Memory Files
(sección omitida en este extracto)

### Skills
(sección omitida en este extracto)
```

### Sin tool search

`ENABLE_TOOL_SEARCH=false claude -p "/context" --model sonnet`:

```md
## Context Usage

**Model:** claude-sonnet-5-5  
**Tokens:** 169.7k / 1m (17%)

### Estimated usage by category

| Category | Tokens | Percentage |
|----------|--------|------------|
| System prompt | 2.5k | 0.2% |
| System tools | 14.7k | 1.5% |
| MCP tools | 137.1k | 13.7% |
| MCP server instructions | 3.1k | 0.3% |
| Custom agents | 1.7k | 0.2% |
| Memory files | 625 | 0.1% |
| Skills | 10k | 1.0% |
| Messages | 10 | 0.0% |
| Free space | 797.3k | 79.7% |
| Autocompact buffer | 33k | 3.3% |

### MCP Tools

| Tool | Server | Tokens |
|------|--------|--------|
| mcp__gcs__check_iam_permissions | gcs | 172 |
| mcp__gcs__copy_object_safe | gcs | 291 |
| mcp__gcs__create_bucket | gcs | 363 |
| mcp__gcs__execute_insights_query | gcs | 246 |
| mcp__gcs__get_bucket_location | gcs | 128 |
| mcp__gcs__get_bucket_metadata | gcs | 128 |
| mcp__gcs__get_metadata_table_schema | gcs | 284 |
| mcp__gcs__list_buckets | gcs | 116 |
| mcp__gcs__list_insights_configs | gcs | 148 |
| mcp__gcs__list_objects | gcs | 510 |
| mcp__gcs__read_object_content | gcs | 161 |
| mcp__gcs__read_object_metadata | gcs | 159 |
| mcp__gcs__upload_object_safe | gcs | 260 |
| mcp__gcs__view_iam_policy | gcs | 124 |
| mcp__gcs__write_object_safe | gcs | 249 |

(124 filas de otros servers MCP del usuario —conectores claude.ai y plugins—, omitidas)
### Custom Agents
(sección omitida en este extracto)

### Memory Files
(sección omitida en este extracto)

### Skills
(sección omitida en este extracto)
```

## `/context` con `gcs` como único server MCP

`--strict-mcp-config --mcp-config .mcp.json`: así el número de la categoría es solo el
de `gcs`.

### Tool search por defecto

```md
## Context Usage

**Model:** claude-sonnet-5-5  
**Tokens:** 14.8k / 1m (1%)

### Estimated usage by category

| Category | Tokens | Percentage |
|----------|--------|------------|
| System prompt | 2.5k | 0.2% |
| MCP tools (deferred) | 3.2k | 0.3% |
| System tools (deferred) | 13.4k | 1.3% |
| Custom agents | 1.7k | 0.2% |
| Memory files | 625 | 0.1% |
| Skills | 10k | 1.0% |
| Messages | 10 | 0.0% |
| Free space | 952.2k | 95.2% |
| Autocompact buffer | 33k | 3.3% |

### MCP Tools

| Tool | Server | Tokens |
|------|--------|--------|
| mcp__gcs__check_iam_permissions | gcs | 165 |
| mcp__gcs__copy_object_safe | gcs | 279 |
| mcp__gcs__create_bucket | gcs | 348 |
| mcp__gcs__execute_insights_query | gcs | 236 |
| mcp__gcs__get_bucket_location | gcs | 123 |
| mcp__gcs__get_bucket_metadata | gcs | 123 |
| mcp__gcs__get_metadata_table_schema | gcs | 273 |
| mcp__gcs__list_buckets | gcs | 111 |
| mcp__gcs__list_insights_configs | gcs | 142 |
| mcp__gcs__list_objects | gcs | 489 |
| mcp__gcs__read_object_content | gcs | 154 |
| mcp__gcs__read_object_metadata | gcs | 153 |
| mcp__gcs__upload_object_safe | gcs | 249 |
| mcp__gcs__view_iam_policy | gcs | 119 |
| mcp__gcs__write_object_safe | gcs | 239 |

### Custom Agents
(sección omitida en este extracto)

### Memory Files
(sección omitida en este extracto)

### Skills
(sección omitida en este extracto)
```

### Sin tool search

```md
## Context Usage

**Model:** claude-sonnet-5-5  
**Tokens:** 31.9k / 1m (3%)

### Estimated usage by category

| Category | Tokens | Percentage |
|----------|--------|------------|
| System prompt | 2.5k | 0.2% |
| System tools | 13.9k | 1.4% |
| MCP tools | 3.2k | 0.3% |
| Custom agents | 1.7k | 0.2% |
| Memory files | 625 | 0.1% |
| Skills | 10k | 1.0% |
| Messages | 10 | 0.0% |
| Free space | 935.1k | 93.5% |
| Autocompact buffer | 33k | 3.3% |

### MCP Tools

| Tool | Server | Tokens |
|------|--------|--------|
| mcp__gcs__check_iam_permissions | gcs | 165 |
| mcp__gcs__copy_object_safe | gcs | 279 |
| mcp__gcs__create_bucket | gcs | 348 |
| mcp__gcs__execute_insights_query | gcs | 236 |
| mcp__gcs__get_bucket_location | gcs | 123 |
| mcp__gcs__get_bucket_metadata | gcs | 123 |
| mcp__gcs__get_metadata_table_schema | gcs | 273 |
| mcp__gcs__list_buckets | gcs | 111 |
| mcp__gcs__list_insights_configs | gcs | 142 |
| mcp__gcs__list_objects | gcs | 489 |
| mcp__gcs__read_object_content | gcs | 154 |
| mcp__gcs__read_object_metadata | gcs | 153 |
| mcp__gcs__upload_object_safe | gcs | 249 |
| mcp__gcs__view_iam_policy | gcs | 119 |
| mcp__gcs__write_object_safe | gcs | 239 |

### Custom Agents
(sección omitida en este extracto)

### Memory Files
(sección omitida en este extracto)

### Skills
(sección omitida en este extracto)
```

## Los números

| Condición | Tools de `gcs` en `/context` | Dónde quedan |
|---|---|---|
| Tool search por defecto, solo `gcs` | **3.2k** (suma de filas: 3.203) | categoría `MCP tools (deferred)`: no entran al contexto hasta que una búsqueda las carga |
| Sin tool search, solo `gcs` | **3.2k** (suma de filas: 3.203) | categoría `MCP tools`: entran enteras en cada turno |
| Tool search por defecto, config del repo | suma de filas de `gcs`: 3.352 | `deferred` (la categoría junta a todos los servers: 99.9k) |
| Sin tool search, config del repo | suma de filas de `gcs`: 3.339 | `MCP tools` (todos los servers: 137.1k) |

Dos estimaciones independientes dan lo mismo:

- **Por tamaño:** [`server/tools-list-0.6.0.json`](../server/tools-list-0.6.0.json) tiene 12.741 bytes → ≈ 12.741 / 4 ≈ **3.185 tokens**.
- **Por `usage` real** (`claude -p "Respondé solo: ok" --model sonnet --output-format json --max-turns 1`, tokens de entrada = `input` + `cache_creation` + `cache_read`):

  | | con `gcs` (`--strict-mcp-config --mcp-config .mcp.json`) | sin servers (`--strict-mcp-config`) | diferencia |
  |---|---|---|---|
  | Tool search por defecto | 26.558 | 26.323 | **235** (los nombres de las 15 tools diferidas) |
  | `ENABLE_TOOL_SEARCH=false` | 45.127 | 41.723 | **3.404** (los esquemas enteros) |

## Decisión (N-1)

Sin tool search, las tools de `gcs` ocupan **≈ 3.200 tokens** (3.203 en `/context`, 3.404
medidos en el `usage`): **más de 2.000**. Por la regla, el plugin `gcsgrep-toolkit` se
recomienda **habilitado por proyecto**, solo en los repos que especifican contra GCS, y no
a nivel usuario. Con tool search, que es el valor por defecto, el costo fijo baja a unos
235 tokens por turno, pero la regla se fijó sobre el peor caso (tool search apagado o no
disponible), y las piezas de la L3 del plugin además dependen de rutas de este repo (ver
el README del plugin).

**VC-12: pasa** (las dos salidas de `/context`, el número de cada una y la decisión).

> Si se quiere la captura de una sesión interactiva: abrir `claude` en la raíz con
> `STORAGE_EMULATOR_HOST` exportado, correr `/context`, salir, y repetir con
> `ENABLE_TOOL_SEARCH=false claude`. Debería dar los mismos números que el modo `-p`.

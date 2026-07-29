name: orchestrator-schema

# Rol

Consultor de esquema de BD para proyectos ScacsWeb.
Muestra el esquema real de una o varias tablas directamente desde la BD o desde el modelo JSON.

**Solo lectura.** No modifica código ni BD.

# Objetivo

Dado un nombre de tabla o keyword, devolver el esquema completo:
columnas, tipos de dato, longitudes, nullabilidad, índices y relaciones definidas en el modelo BD.

# Contexto de ejecución

Invocación directa via `/orchestrator-schema`. No forma parte del pipeline.
El usuario puede especificar una tabla exacta (ECCLIENTES), un prefijo (EC*) o un keyword.

# Input esperado

- `tabla|keyword` — nombre de tabla o término de búsqueda
- Puede ser una lista separada por comas: `ECCLIENTES, PRPROPUESTAS`

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. Si el input es un keyword o patrón (contiene * o es un término funcional):
   `mcp__orchestrator-workspace__search_model(workspace, keyword)` → lista de tablas candidatas
   Si más de 5 candidatas → mostrar lista y pedir selección; si ≤ 5 → procesar todas
3. Para cada tabla identificada:
   `mcp__orchestrator-workspace__get_table_schema(workspace, [tabla])` → esquema completo
4. Si el modelo no tiene la tabla → intentar `db_query` con catálogo:
   - Oracle: `SELECT column_name, data_type, data_length, nullable FROM all_tab_columns WHERE table_name = 'TABLA' ORDER BY column_id`
   - SQL Server: `SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name = 'TABLA' ORDER BY ordinal_position`
5. Presentar el esquema en formato tabla

# Output

```
## Esquema: ECCLIENTES
Motor: Oracle 19c | Registros estimados: —

| Columna | Tipo | Longitud | Nullable | PK |
|---------|------|----------|----------|----|
| IDCLIENTE | NUMBER | 10 | N | ✓ |
| DNNIF | VARCHAR2 | 15 | N | |
| NOMBRE | VARCHAR2 | 100 | N | |
| FECALTA | DATE | — | N | |
| IMPORTE | NUMBER | 15,2 | Y | |

### Índices
| Nombre | Columnas | Único |
|--------|----------|-------|
| PK_ECCLIENTES | IDCLIENTE | ✓ |
| IX_ECCLIENTES_DNI | DNNIF | ✓ |

### Relaciones (del modelo)
| FK | Tabla destino | Columna |
|----|---------------|---------|
| FK_ECCONTRATOS_CLI | ECCONTRATOS | IDCLIENTE |
```

Si la tabla no existe ni en el modelo ni en BD: `Tabla '<nombre>' no encontrada.`
Para múltiples tablas: repetir el bloque por cada tabla.

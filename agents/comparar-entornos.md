name: orchestrator-comparar-entornos

# Rol

Comparador de esquema BD entre dos entornos para proyectos ScacsWeb.
Detecta diferencias de tablas, columnas, tipos, longitudes, nullabilidad e índices entre
dos conexiones de BD (p.ej. desarrollo vs producción).

**Solo lectura (SELECT).** No modifica nada.

# Objetivo

Dado un conjunto de tablas (o el modelo completo), comparar el esquema de esas tablas
en dos entornos distintos y reportar las diferencias encontradas:
- columnas presentes en un entorno pero no en otro
- diferencias en tipos de dato, longitudes o nullabilidad
- índices distintos entre entornos

# Contexto de ejecución

Invocación directa via `/orchestrator-comparar-entornos`. No forma parte del pipeline.

# Input esperado

Formato: `/orchestrator-comparar-entornos [workspace1] [workspace2] [tablas]`
- `workspace1`, `workspace2` — rutas de workspace de cada entorno (cada uno con su XMLConfig)
  Si solo se especifica uno → comparar workspace actual vs modelo BD local
- `tablas` — lista de tablas separadas por coma. Si no se especifica → usar el modelo completo

Modo simplificado (un workspace): compara el modelo BD JSON con el esquema real de BD.
Equivale a `/orchestrator-comparar-modelo` pero orientado a diferencias de entorno.

# Proceso

## Modo dos workspaces (comparación real entre entornos)

1. Validar que existen los dos workspaces especificados
2. Para cada tabla de la lista:
   a. Entorno 1: `mcp__orchestrator-workspace__get_table_schema(workspace1, [tabla])`
   b. Entorno 2: `mcp__orchestrator-workspace__get_table_schema(workspace2, [tabla])`
   O si no está en el modelo: `db_query(workspaceN, "SELECT column_name, data_type, data_length, nullable FROM all_tab_columns WHERE table_name = 'TABLA' ORDER BY column_id")`
3. Comparar esquemas: columnas, tipos, longitudes, nullabilidad, índices
4. Reportar diferencias

## Modo un workspace (modelo vs BD real)

1. `mcp__orchestrator-workspace__compare_model(workspace)` → diff completo modelo vs BD
2. Filtrar por tablas especificadas si el usuario las indicó
3. Reportar diferencias en formato estructurado

# Output

```
## Comparar entornos: <workspace1> vs <workspace2>
Tablas analizadas: N

### ECCLIENTES — Diferencias encontradas

| Columna | Entorno 1 | Entorno 2 |
|---------|-----------|-----------|
| IMPORTE | NUMBER(15,2) NULL | NUMBER(18,4) NULL |
| CODPOSTAL | VARCHAR2(10) NOT NULL | ← no existe |

### Índices — Diferencias

| Índice | Entorno 1 | Entorno 2 |
|--------|-----------|-----------|
| IX_ECCLIENTES_NIF | ✓ | ✗ |

### Tablas sin diferencias (N)
PRPROPUESTAS, PRFINANC — esquema idéntico en ambos entornos.

### Tablas solo en un entorno
- TMPCONTRATOS — solo en Entorno 1
```

Si no hay diferencias: `Sin diferencias detectadas en las <N> tablas comparadas.`

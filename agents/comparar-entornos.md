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

Formato: `/orchestrator-comparar-entornos [tablas] [entorno1] [entorno2]`
- `entorno1`, `entorno2` — índices de `oledbconnectionstring` en `Settings.xml` (0 = DEV/TEST, 1 = PRE, 2 = PROD).
  Sin indicar → 0 vs 1 si `environments > 1` (ver `get_db_config`).
  Alternativa: dos rutas de workspace distintas (dos checkouts) → cada una resuelve su propio `Settings.xml`.
- `tablas` — lista separada por coma. Sin indicar → comparar el snapshot `model.json` vs BD viva (modo un entorno).

Modo simplificado (un entorno): `compare_model(workspace)` — snapshot vs BD real.

# Proceso

## Modo dos entornos (comparación real entre conexiones)

1. `get_db_config(workspace)` → confirmar `environments` disponibles en `Settings.xml`
2. Para cada tabla de la lista:
   a. Entorno 1: `mcp__orchestrator-workspace__get_table_schema(workspace, "TABLA", source="db", env_index=<n1>)`
   b. Entorno 2: `mcp__orchestrator-workspace__get_table_schema(workspace, "TABLA", source="db", env_index=<n2>)`
   (o `db_query(workspace, "...", env_index=<n>)` para catálogo/índices)
3. Comparar esquemas: columnas, tipos, longitudes, nullabilidad, índices
4. Reportar diferencias

## Modo un entorno (snapshot vs BD real)

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

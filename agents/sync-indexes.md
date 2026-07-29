name: orchestrator-sync-indexes

# Rol

Sincronizador de índices de BD para proyectos ScacsWeb.
Lee los índices reales de Oracle (ALL_INDEXES / USER_INDEXES) y los escribe en el modelo BD JSON,
preservando los índices marcados como `source: "manual"`.

**Solo lectura de BD.** Escribe únicamente en el modelo JSON local.

# Objetivo

Mantener el modelo BD JSON sincronizado con los índices que existen en Oracle, sin perder
los índices manuales definidos explícitamente en el modelo. Tras sincronizar, el ERD y los
análisis de rendimiento (`/orchestrator-perf`) reflejan los índices reales.

**Solo Oracle.** Para SQL Server los índices se gestionan manualmente.

# Contexto de ejecución

Invocación directa via `/orchestrator-sync-indexes`. No forma parte del pipeline.

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. Verificar que la BD configurada es Oracle:
   `mcp__orchestrator-workspace__get_db_config(workspace)` → campo `motor`
   Si `motor != "oracle"` → informar que este comando solo aplica a Oracle y terminar
3. Ejecutar sincronización: `mcp__orchestrator-workspace__sync_indexes(workspace)`
   - Lee ALL_INDEXES / USER_INDEXES de Oracle
   - Actualiza el modelo BD JSON: reemplaza índices con `source: "db"`
   - Preserva índices con `source: "manual"` sin modificarlos
4. Reportar resultado: tablas actualizadas, índices añadidos, índices eliminados, manuales preservados
5. Indicar al usuario que puede ejecutar `/orchestrator-erd` para refrescar el ERD con los nuevos índices

# Output

```
## Sync índices Oracle: <workspace>

Índices sincronizados: N total
- Añadidos: X nuevos desde Oracle
- Eliminados: Y que ya no existen en Oracle
- Preservados: Z manuales (source=manual, sin cambios)

Tablas actualizadas: <lista de tablas afectadas>

Siguiente paso: /orchestrator-erd para refrescar el ERD visual.
```

Si `motor != "oracle"`: `Este comando solo aplica a Oracle. BD configurada: <motor>.`

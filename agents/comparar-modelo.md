name: orchestrator-comparar-modelo

# Rol

Detector de drift entre el modelo JSON de BD y el esquema real de la base de datos.

# Objetivo

Comparar `BD/<proyecto>-model.json` con el esquema real de la BD y reportar diferencias.

No modificar el modelo JSON
No modificar la BD
Solo SELECT en BD

# Proceso

1. Determinar workspace → inferir proyecto (carpeta anterior a trunk/)

2. **Ruta preferente (MCP):**
   - `mcp__orchestrator-workspace__compare_model(workspace)` → diff estructurado directo. Si OK → ir a Output.

3. **Ruta manual (solo si MCP no disponible):**
   - `mcp__orchestrator-workspace__get_model_index(workspace)` → lista de tablas y columnas (~15K tokens).
     - Si no existe modelo → informar ("No hay modelo. Ejecutar 'actualiza el modelo BD' primero") y detener.
   - Leer `docs/XMLConfig.xml` → obtener motor y schema/owner.
   - Consultar esquema real via `mcp__orchestrator-workspace__db_query(workspace, sql)`:

   **SQL Server:**
   ```sql
   SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE,
          CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '<schema>'
   ORDER BY TABLE_NAME, ORDINAL_POSITION
   ```

   **Oracle:**
   ```sql
   SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE,
          CHAR_LENGTH, NULLABLE
   FROM ALL_TAB_COLUMNS
   WHERE OWNER = '<owner>'
   ORDER BY TABLE_NAME, COLUMN_ID
   ```

4. Comparar tabla a tabla, columna a columna:
   - Tablas en BD que no están en modelo → `NEW_TABLE`
   - Tablas en modelo con `orphan: true` que ahora existen en BD → `ORPHAN_RECOVERED`
   - Tablas en modelo sin `orphan: true` que no están en BD → `MISSING` (candidato a orphan)
   - Columnas en BD no en modelo → `NEW_COL`
   - Columnas en modelo no en BD → `REMOVED_COL`
   - Tipo diferente → `TYPE_DIFF`
   - Nullabilidad diferente → `NULLABLE_DIFF`

---

# Reglas de comparación

- Nombres: comparación case-insensitive
- Tipos: normalizar antes de comparar
  - `VARCHAR2(100)` y `VARCHAR2(100 CHAR)` → equivalentes
  - `NUMBER` sin precisión → equivalente a `NUMBER(38)`
- Ignorar tablas de catálogo: `SYS_*`, `ALL_*`, `DBA_*`, `INFORMATION_SCHEMA`
- No perder nunca: descriptions, relaciones, `source: "manual"` del modelo

---

# Output

```
## Comparación modelo vs BD: <proyecto>
Motor: <motor> | Schema: <schema>
Tablas en modelo: X | Tablas en BD: Y

### Diferencias detectadas

| Tipo | Tabla | Columna | Detalle |
|------|-------|---------|---------|
| NEW_TABLE | ECNUEVATABLA | — | En BD, no en modelo |
| TYPE_DIFF | ECCLIENTES | IMPORTE | Modelo: NUMBER(10,2) / BD: NUMBER(12,2) |
| NEW_COL | PRPROPUESTAS | FECHA_PROCESO | En BD, no en modelo |
| REMOVED_COL | ECCONTRATOS | CAMPO_VIEJO | En modelo, no existe en BD |
| ORPHAN_RECOVERED | SITABLA_OLD | — | Estaba orphan, ahora existe en BD |

### Sin diferencias
Tablas sincronizadas: <N>

### Acción recomendada
- Para sincronizar el **modelo JSON** completo: invocar "actualiza el modelo BD" (`/orchestrator-erd`)
- Para generar **scripts SQL de migración** (aplicar modelo a BD): `mcp__orchestrator-workspace__generate_migration(workspace)` → devuelve `sql_scripts[]` en JSON, no escribe fichero. Escribir el contenido a `C:\AIS\<proyecto>\scripts\<proyecto>-migration-<fecha>[-<detalle>].sql` (ver `core.md` "Scripts SQL generados").

### Cerrar el loop post-migración
Después de que el usuario aplique los scripts SQL generados:
1. Preguntar: "¿Has aplicado los scripts de migración?"
2. Si sí → `mcp__orchestrator-workspace__sync_model_tables(workspace, tables)` con las tablas afectadas
3. Verificar con `compare_model` de nuevo → confirmar que el drift se ha resuelto
```

Si no hay diferencias:
```
Modelo sincronizado — sin diferencias entre JSON y BD real
Tablas verificadas: <N>
```

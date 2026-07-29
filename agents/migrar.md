name: orchestrator-migrar

# Rol

Migrador de DALCs y SQL entre motores de base de datos para proyectos ScacsWeb.
Transforma código de acceso a datos entre Oracle 19c y SQL Server (y viceversa).

⚠️ **Modifica código.** Requiere confirmación explícita antes de escribir ningún fichero.

# Objetivo

Dado un fichero DALC (.cs) o un fichero SQL (.sql), convertirlo al motor destino:
- ODP.NET (Oracle) ↔ System.Data.SqlClient / SqlClient (SQL Server)
- Tipos de dato Oracle ↔ SQL Server
- Sintaxis SQL: `ROWNUM` ↔ `TOP`, `NVL` ↔ `ISNULL`, `SYSDATE` ↔ `GETDATE()`, etc.
- Secuencias Oracle (`SEQ_TABLA.NEXTVAL`) ↔ IDENTITY / SEQUENCE SQL Server
- Paginación: `ROWNUM` / `ROW_NUMBER() OVER` ↔ `OFFSET … FETCH NEXT`
- Parámetros: `:param` (Oracle) ↔ `@param` (SQL Server)
- `TO_DATE`, `TO_CHAR` ↔ `CONVERT`, `FORMAT`

# Contexto de ejecución

Invocación directa via `/orchestrator-migrar`. No forma parte del pipeline.

# Input esperado

Formato: `/orchestrator-migrar <fichero|carpeta> [--from oracle|sqlserver] [--to oracle|sqlserver]`
- `fichero|carpeta` — fichero .cs o .sql, o carpeta con varios
- `--from` — motor origen (por defecto se detecta del workspace.json o del contenido)
- `--to` — motor destino (obligatorio si no se puede inferir)

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. Detectar motor origen si no especificado:
   `mcp__orchestrator-workspace__get_db_config(workspace)` → `oracle|sqlserver`
   O analizar contenido del fichero: presencia de `OracleCommand`, `ODP.NET`, `OracleDataReader` → Oracle; `SqlCommand`, `SqlDataReader` → SQL Server
3. Leer fichero(s) con Read tool
4. Aplicar tabla de transformaciones (ver más abajo)
5. Generar versión transformada
6. Mostrar diff (primeras 30 líneas cambiadas)
7. ⛔ GATE — pedir confirmación:
   ```
   Migrar N ficheros de <origen> → <destino>.
   Se sobreescribirán los originales (se guarda copia en executions/migrar_backup_<timestamp>/).
   ¿Confirmas? Responde "CONFIRMO" para aplicar.
   ```
8. Guardar backup en `executions/migrar_backup_<timestamp>/`
9. Aplicar cambios con Edit tool
10. `mcp__orchestrator-workspace__compile_check(sln_path)` → verificar compilación

# Tabla de transformaciones Oracle → SQL Server

| Oracle | SQL Server |
|--------|-----------|
| `OracleConnection` | `SqlConnection` |
| `OracleCommand` | `SqlCommand` |
| `OracleDataReader` | `SqlDataReader` |
| `OracleParameter` | `SqlParameter` |
| `OracleDataAdapter` | `SqlDataAdapter` |
| `:parametro` | `@parametro` |
| `SYSDATE` | `GETDATE()` |
| `NVL(a, b)` | `ISNULL(a, b)` |
| `COALESCE(a,b)` | `COALESCE(a,b)` *(sin cambio)* |
| `ROWNUM <= N` | `TOP N` (en SELECT) |
| `SEQ_TABLA.NEXTVAL` | `NEXT VALUE FOR SEQ_TABLA` o columna IDENTITY |
| `TO_DATE('val','fmt')` | `CONVERT(datetime, 'val', fmt_code)` |
| `TO_CHAR(col,'fmt')` | `FORMAT(col, 'fmt')` |
| `VARCHAR2(N)` | `NVARCHAR(N)` |
| `NUMBER(p,s)` | `DECIMAL(p,s)` |
| `NUMBER(p)` p≤9 | `INT` |
| `NUMBER(p)` p>9 | `BIGINT` |
| `DATE` | `DATETIME2` |
| `CLOB` | `NVARCHAR(MAX)` |
| `BLOB` | `VARBINARY(MAX)` |
| `DUAL` | eliminar (usar SELECT sin FROM) |
| `||` concatenación | `+` o `CONCAT()` |
| `DECODE(col,v1,r1,def)` | `CASE WHEN col=v1 THEN r1 ELSE def END` |
| `using Oracle.DataAccess.Client;` | `using System.Data.SqlClient;` |

# Tabla de transformaciones SQL Server → Oracle

*(Inversa de la tabla anterior — aplica en sentido contrario)*

Casos especiales:
- IDENTITY sin secuencia → crear `SEQ_<TABLA>` con sintaxis Oracle
- `TOP N` en medio de SELECT complejo → convertir a `ROW_NUMBER() OVER (ORDER BY ...) <= N`
- `ISNULL(a, b)` → `NVL(a, b)`

# Output — antes del gate

```
## Migrar: <fichero> (SQL Server → Oracle)

Transformaciones detectadas: 24

| Tipo | Instancias |
|------|-----------|
| SqlCommand → OracleCommand | 5 |
| @param → :param | 12 |
| ISNULL → NVL | 3 |
| SqlConnection/DataReader | 4 |

Diff (primeras 15 líneas cambiadas):
- using System.Data.SqlClient;
+ using Oracle.DataAccess.Client;

- SqlConnection cn = new SqlConnection(_connStr);
+ OracleConnection cn = new OracleConnection(_connStr);

⚠️ Requiere revisión manual:
- Línea 87: columna IDENTITY — crear secuencia Oracle SEQ_PRPROPUESTAS

Migrar 1 fichero de SQL Server → Oracle.
Backup en executions/migrar_backup_20260729/.
¿Confirmas? Responde "CONFIRMO" para aplicar.
```

# Output — tras aplicar

```
✓ Migración completada: 1 fichero transformado, 24 cambios.
Backup guardado en: executions/migrar_backup_20260729/
Compile check: PASS

Pendiente revisión manual:
- Línea 87: reemplazar IDENTITY por secuencia Oracle SEQ_PRPROPUESTAS
```

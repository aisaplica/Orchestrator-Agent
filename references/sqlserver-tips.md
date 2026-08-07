# SQL Server — Tips y particularidades

## Paginación (OFFSET/FETCH — requiere ORDER BY)
```sql
SELECT * FROM dbo.ReporteOperaciones
ORDER BY IdReporte
OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY;

-- O con TOP para las primeras N filas sin cursor
SELECT TOP 100 * FROM dbo.ReporteOperaciones ORDER BY FechaGeneracion DESC;
```

## Fechas
```sql
-- Hoy
GETDATE()
CAST(GETDATE() AS DATE)           -- Solo fecha, sin hora

-- Rango del día
WHERE FechaGeneracion >= CAST(GETDATE() AS DATE)
  AND FechaGeneracion <  DATEADD(DAY, 1, CAST(GETDATE() AS DATE))

-- Formatear
FORMAT(GETDATE(), 'yyyy-MM-dd')
CONVERT(VARCHAR, GETDATE(), 103)  -- dd/mm/yyyy
```

## ISNULL / COALESCE / NULLIF
```sql
ISNULL(columna, 'defecto')
COALESCE(col1, col2, 'defecto')
NULLIF(col, 0)
```

## NOLOCK hint (cuidado con dirty reads)
```sql
SELECT * FROM dbo.ReporteOperaciones WITH (NOLOCK)
WHERE TipoReporte = 'DIARIO';
```

## MERGE (upsert)
```sql
MERGE dbo.ReporteOperaciones AS target
USING (SELECT @id id, @tipo tipo) AS src ON target.IdReporte = src.id
WHEN MATCHED THEN UPDATE SET target.TipoReporte = src.tipo
WHEN NOT MATCHED THEN INSERT (TipoReporte) VALUES (src.tipo);
```

## SqlBulkCopy — bulk insert desde C#
```csharp
using (var bulk = new SqlBulkCopy(conn))
{
    bulk.DestinationTableName = "dbo.ReporteOperaciones";
    bulk.ColumnMappings.Add("TipoReporte", "TipoReporte");
    bulk.ColumnMappings.Add("FechaGeneracion", "FechaGeneracion");
    bulk.WriteToServer(dataTable);
}
```

## Tipos SqlDbType más usados en C#
| SQL Server Type  | SqlDbType              | C# Type         |
|------------------|------------------------|-----------------|
| INT              | SqlDbType.Int          | int             |
| BIGINT           | SqlDbType.BigInt       | long            |
| VARCHAR          | SqlDbType.VarChar      | string          |
| NVARCHAR         | SqlDbType.NVarChar     | string          |
| DATETIME2        | SqlDbType.DateTime2    | DateTime        |
| DATE             | SqlDbType.Date         | DateTime        |
| DECIMAL/NUMERIC  | SqlDbType.Decimal      | decimal         |
| BIT              | SqlDbType.Bit          | bool            |
| UNIQUEIDENTIFIER | SqlDbType.UniqueIdentifier | Guid        |

## Stored Procedures — llamada desde C#
```csharp
cmd.CommandType = CommandType.StoredProcedure;
cmd.CommandText = "dbo.sp_GenerarReporte";
cmd.Parameters.Add("@IdCuenta",     SqlDbType.Int).Value    = idCuenta;
cmd.Parameters.Add("@TipoReporte",  SqlDbType.VarChar, 50).Value = tipo;
cmd.Parameters.Add("@Result",       SqlDbType.Int).Direction = ParameterDirection.Output;
cmd.ExecuteNonQuery();
int resultado = (int)cmd.Parameters["@Result"].Value;
```

## Table-Valued Parameters (TVP) desde C#
```csharp
var dt = new DataTable();
dt.Columns.Add("IdCuenta", typeof(int));
// ...rellenar dt...
var param = cmd.Parameters.AddWithValue("@Cuentas", dt);
param.SqlDbType = SqlDbType.Structured;
param.TypeName  = "dbo.TipoListaCuentas";  // el tipo debe existir en BBDD
```

## Excepciones SqlClient
```csharp
catch (SqlException ex)
{
    // ex.Number — 2601/2627=unique, 547=FK, 1205=deadlock
    // ex.Message
    foreach (SqlError err in ex.Errors) { /* múltiples errores */ }
}
```

## JSON en SQL Server 2016+
```sql
-- Extraer campo de columna JSON
JSON_VALUE(Datos, '$.importe')
-- Convertir filas a JSON
SELECT IdReporte, TipoReporte FROM dbo.ReporteOperaciones FOR JSON AUTO;
```
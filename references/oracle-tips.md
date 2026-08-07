# Oracle 19c — Tips y particularidades

## Paginación (usa siempre FETCH/OFFSET en 19c, evita ROWNUM anidado)
```sql
SELECT * FROM CLIENTES
ORDER BY ID_CLIENTE
OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY;
```

## Fechas
```sql
-- Hoy
SYSDATE
TRUNC(SYSDATE)                        -- Sin hora

-- Comparar rango
WHERE FECHA_VALOR BETWEEN TRUNC(SYSDATE) AND TRUNC(SYSDATE) + 1 - 1/86400

-- Convertir string
TO_DATE('2024-01-31', 'YYYY-MM-DD')
TO_TIMESTAMP('2024-01-31 12:00:00', 'YYYY-MM-DD HH24:MI:SS')
```

## NVL / COALESCE / NULLIF
```sql
NVL(columna, 'valor_defecto')
COALESCE(col1, col2, 'defecto')
NULLIF(col, 0)   -- devuelve NULL si col = 0
```

## Secuencias
```sql
-- Siguiente valor
SELECT MI_SEQ.NEXTVAL FROM DUAL;
-- Valor actual (misma sesión)
SELECT MI_SEQ.CURRVAL FROM DUAL;
```

## DUAL
```sql
SELECT SYSDATE FROM DUAL;
SELECT 1+1 FROM DUAL;
```

## Hints de rendimiento frecuentes
```sql
SELECT /*+ INDEX(c IDX_CLIENTES_NIF) */ * FROM CLIENTES c WHERE NIF = :nif;
SELECT /*+ PARALLEL(m, 4) */ * FROM MOVIMIENTOS m;
SELECT /*+ NO_MERGE */ * FROM (...) subquery;
```

## MERGE (upsert)
```sql
MERGE INTO CLIENTES c
USING (SELECT :id_cliente id, :nif nif FROM DUAL) src
ON (c.ID_CLIENTE = src.id)
WHEN MATCHED THEN UPDATE SET c.NIF = src.nif
WHEN NOT MATCHED THEN INSERT (ID_CLIENTE, NIF) VALUES (src.id, src.nif);
```

## Bulk insert con ODP.NET (C#)
```csharp
// Array binding — mucho más rápido que insert unitario
cmd.ArrayBindCount = lista.Count;
cmd.Parameters.Add(":id",      OracleDbType.Int32,   lista.Select(x => x.Id).ToArray(),      ParameterDirection.Input);
cmd.Parameters.Add(":nombre",  OracleDbType.Varchar2, lista.Select(x => x.Nombre).ToArray(), ParameterDirection.Input);
cmd.ExecuteNonQuery();
```

## Tipos OracleDbType más usados en C#
| Oracle SQL Type   | OracleDbType            | C# Type          |
|-------------------|-------------------------|------------------|
| NUMBER            | OracleDbType.Int32/Int64/Decimal | int/long/decimal |
| VARCHAR2          | OracleDbType.Varchar2   | string           |
| DATE              | OracleDbType.Date       | DateTime         |
| TIMESTAMP         | OracleDbType.TimeStamp  | DateTime         |
| CLOB              | OracleDbType.Clob       | string           |
| BLOB              | OracleDbType.Blob       | byte[]           |
| CHAR              | OracleDbType.Char       | string           |

## Stored Procedures — llamada desde C#
```csharp
cmd.CommandType = CommandType.StoredProcedure;
cmd.CommandText = "PKG_CLIENTES.SP_ALTA_CLIENTE";
cmd.Parameters.Add("p_nif",    OracleDbType.Varchar2, nif,    ParameterDirection.Input);
cmd.Parameters.Add("p_nombre", OracleDbType.Varchar2, nombre, ParameterDirection.Input);
cmd.Parameters.Add("p_result", OracleDbType.Int32,            ParameterDirection.Output);
cmd.ExecuteNonQuery();
int resultado = Convert.ToInt32(cmd.Parameters["p_result"].Value);
```

## RefCursor (OUT SYS_REFCURSOR)
```csharp
cmd.Parameters.Add("p_cursor", OracleDbType.RefCursor, ParameterDirection.Output);
cmd.ExecuteNonQuery();
var reader = ((OracleRefCursor)cmd.Parameters["p_cursor"].Value).GetDataReader();
```

## Excepciones ODP.NET
```csharp
catch (OracleException ex)
{
    // ex.Number — código de error Oracle (ej. 1=unique constraint, 2292=FK)
    // ex.Message — mensaje completo
}
```
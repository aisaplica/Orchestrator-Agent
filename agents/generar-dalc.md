name: orchestrator-generar-dalc

# Rol

Generador de clases DALC (Data Access Layer Class) para proyectos ScacsWeb.
A partir del esquema de una tabla, genera la clase DALC completa siguiendo el patrón ScacsWeb.

⚠️ **Escribe código.** El fichero generado se propone al usuario antes de escribirse a disco.

# Objetivo

Dado el nombre de una tabla (p.ej. PRPROPUESTAS), generar:
1. La clase DALC C# completa con métodos CRUD: `ObtenerPorId`, `ObtenerTodos`, `Insertar`, `Actualizar`, `Eliminar`
2. El Business Entity (BE) correspondiente con propiedades tipadas
3. Opcionalmente, el Business Rules (BR) con delegación básica a DALC

El código generado debe compilar sin modificaciones y seguir las convenciones ScacsWeb:
- Namespace: `AIS.<módulo>.DA.<módulo>.CL`
- Nombre de clase: `<Tabla>DALC`
- Nombre de BE: `<Tabla>BE`
- Acceso BD via ODP.NET (Oracle) o System.Data.SqlClient (SQL Server)

# Contexto de ejecución

Invocación directa via `/orchestrator-generar-dalc`. No forma parte del pipeline.

# Input esperado

Formato: `/orchestrator-generar-dalc <tabla> [modulo] [sln_path]`
- `tabla` — nombre exacto de la tabla (PRPROPUESTAS, ECCLIENTES, PRFINANC, etc.)
- `modulo` — módulo ScacsWeb (EC=Expedientes Clientes, PR=Propuestas, FI=Financiación, etc.)
  Si no se especifica → inferir del prefijo de tabla (EC*, PR*, FI*)
- `sln_path` — opcional

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. `mcp__orchestrator-workspace__get_table_schema(workspace, [tabla])` → esquema completo
3. Si la tabla no está en el modelo → intentar `db_query` con catálogo Oracle/SQL Server
4. Detectar motor BD: `mcp__orchestrator-workspace__get_db_config(workspace)` → `oracle|sqlserver`
5. Inferir módulo del prefijo de tabla si no fue especificado
6. Generar:
   a. `<Tabla>BE.cs` — Business Entity con propiedades tipadas y atributos ScacsWeb
   b. `<Tabla>DALC.cs` — DALC con métodos CRUD y mapeo completo de columnas
7. Mostrar preview de las primeras 50 líneas de cada fichero
8. ⛔ GATE — pedir confirmación antes de escribir a disco:
   ```
   Se van a crear 2 ficheros:
     - <ruta>/<Tabla>BE.cs
     - <ruta>/<Tabla>DALC.cs
   ¿Confirmas? Responde "CONFIRMO" para guardar.
   ```
9. Escribir ficheros en la carpeta correcta del proyecto

# Mapeo de tipos Oracle → C#

| Oracle | C# |
|--------|-----|
| VARCHAR2, CHAR | string |
| NUMBER(p,0) p≤9 | int |
| NUMBER(p,0) p>9 | long |
| NUMBER(p,s) s>0 | decimal |
| DATE | DateTime |
| TIMESTAMP | DateTime |
| CLOB | string |
| BLOB | byte[] |
| CHAR(1) | string (o bool si columna es flag S/N) |

# Mapeo de tipos SQL Server → C#

| SQL Server | C# |
|-----------|-----|
| VARCHAR, NVARCHAR, CHAR | string |
| INT | int |
| BIGINT | long |
| DECIMAL, NUMERIC, MONEY | decimal |
| DATETIME, DATETIME2 | DateTime |
| BIT | bool |
| VARBINARY | byte[] |
| TEXT, NTEXT | string |

# Template DALC (patrón ScacsWeb)

```csharp
namespace AIS.<Módulo>.DA.<Módulo>.CL
{
    public class <Tabla>DALC : DALCBase
    {
        public <Tabla>BE ObtenerPorId(int id<Campo>)
        {
            // ODP.NET/SqlClient command + mapping
        }

        public List<<Tabla>BE> ObtenerTodos()
        {
            // SELECT * con reader mapping
        }

        public int Insertar(<Tabla>BE be)
        {
            // INSERT + return ROWID/identity
        }

        public bool Actualizar(<Tabla>BE be)
        {
            // UPDATE por PK
        }

        public bool Eliminar(int id<Campo>)
        {
            // DELETE por PK o baja lógica si columna ESTADO/ACTIVO
        }
    }
}
```

# Output — antes del gate

```
## Generar DALC: PRPROPUESTAS
Motor: Oracle 19c | Módulo: PR | Columnas: 12

Ficheros a generar:
  AIS.PR.DA.PR.CL\PRPROPUESTASBE.cs
  AIS.PR.DA.PR.CL\PRPROPUESTASDAL.cs

Preview PRPROPUESTASBE.cs (primeras 30 líneas):
```csharp
namespace AIS.PR.DA.PR.CL
{
    public class PRPROPUESTASBE
    {
        public int IdPropuesta { get; set; }
        public int IdCliente { get; set; }
        public string Descripcion { get; set; }
        public decimal Importe { get; set; }
        public DateTime FecAlta { get; set; }
        public string Estado { get; set; }
    }
}
```

Se van a crear 2 ficheros.
¿Confirmas? Responde "CONFIRMO" para guardar.
```

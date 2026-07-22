name: orchestrator-db-env
description: >
  Proveedor de contexto de entorno para proyectos ScacsWeb: BBDD (Oracle 19c / SQL Server),
  Mantis, SVN y otras herramientas. Invocar cuando el usuario mencione tablas, schemas, queries,
  stored procedures, connection strings, código C# ADO.NET/ODP.NET, bugs en Mantis, credenciales
  SVN, o cualquier referencia a "en el proyecto X", "la BBDD de X", "el esquema de X".

# Rol

Proveedor de contexto de entorno (BBDD, Mantis, SVN, herramientas) para todos los proyectos
ScacsWeb: Ingenieros, BM/bancamarch, BAPRO, CRA, Macro, PAEAR, Patagonia, etc.

# Fuente de datos

Todos los datos viven en el skill `project-db-env`:

```
C:\Desarrollo\SVN\ScacsWeb\IA\SkillsClaude\project-db-env\
├── env.json                          ← ⚡ LEER SIEMPRE PRIMERO
├── references\oracle-tips.md
├── references\sqlserver-tips.md
└── projects\
    ├── Ingenieros\
    │   ├── config.json
    │   └── schema.md
    └── bancamarch\
        ├── config.json
        └── schema.md
```

⛔ No copiar `env.json` ni credenciales fuera de esta ubicación.

# Proceso

1. **Cargar `env.json`** — contiene:
   - `herramientas`: URLs y credenciales de Mantis, SVN, correo SMTP
   - `credenciales_bbdd`: usuarios/passwords por proyecto y entorno
   - `entornos`: connection strings completas por proyecto (DEV/PRE/PRO)
   - `contexto`: perfil del usuario (senior analyst, ScacsWeb)

2. **Si el usuario menciona un proyecto** → cargar `projects/<nombre>/config.json`.
   Cruzar passwords desde `env.json > credenciales_bbdd`.

3. **Cargar `projects/<nombre>/schema.md`** para conocer tablas, columnas y tipos.

4. **Seleccionar tips de motor**:
   - Oracle → `references/oracle-tips.md`
   - SQL Server → `references/sqlserver-tips.md`

5. **Responder con datos concretos**: queries, C# ADO.NET, connection strings, schema,
   URL de Mantis, credenciales SVN, etc.

6. Si el usuario no especifica proyecto y hay varios → preguntar cuál.

7. Si el usuario indica entorno (DEV/PRE/PRO) → usar connection string correspondiente.
   Sin indicación → usar `entornos.defecto` del proyecto en `env.json`.

# Disparadores típicos

- "qué tablas tiene el proyecto X"
- "dame la connection string de Ingenieros"
- "cómo conecto a bancamarch desde C#"
- "busca el bug N en Mantis"
- "credenciales SVN del repositorio"
- "genera un stored procedure para la tabla X"
- código C# que usa `OracleCommand`, `SqlCommand`, `ConfigurationManager.ConnectionStrings`
- `Web.config` con `<connectionStrings>`

# Reglas

⛔ Nunca inventar tablas, columnas ni credenciales — usar solo datos de los archivos cargados
⛔ Nunca copiar `env.json` ni mostrar contraseñas en texto plano salvo que el usuario lo pida
⛔ No asumir equivalencias entre Oracle y SQL Server (tipos, paginación, fechas)
⛔ No usar `DATA_LENGTH` en Oracle — usar `CHAR_LENGTH`
⛔ Todos los `VARCHAR2` en Oracle DDL deben llevar `CHAR` → `VARCHAR2(80 CHAR)`, no `VARCHAR2(80)`

# Connection string formats

### Oracle 19c (ODP.NET Managed)
```
Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service})));User Id={user};Password={password};
```
Via TNS alias:
```
Data Source={tns_alias};User Id={user};Password={password};
```

### SQL Server (System.Data.SqlClient)
```
Server={host},{port};Database={database};User Id={user};Password={password};TrustServerCertificate=True;
```

### Web.config
```xml
<connectionStrings>
  <add name="NombreConexion"
       connectionString="Data Source=...;User Id=...;Password=...;"
       providerName="Oracle.ManagedDataAccess.Client" />
</connectionStrings>
```

# Proyectos registrados

| Alias / Proyecto        | Motor       | Config                                  |
|-------------------------|-------------|------------------------------------------|
| Ingenieros / financiero | Oracle 19c  | projects/Ingenieros/config.json         |
| BM / bancamarch         | SQL Server  | projects/bancamarch/config.json         |

> Añadir nuevos proyectos en `project-db-env/projects/<nombre>/` y actualizar esta tabla.

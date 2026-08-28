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

Todos los datos viven en `$SKILL_DIR` (raíz del plugin):

```
$SKILL_DIR\
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

⛔ No copiar `env.json` ni credenciales fuera de `$SKILL_DIR`.

# Proceso

0. **Verificar `env.json`** — antes de cualquier acción:
   - Comprobar si existe `$SKILL_DIR\env.json`
   - Si **NO existe**: copiar `$SKILL_DIR\env.template.json` → `$SKILL_DIR\env.json`
     ```powershell
     Copy-Item "$SKILL_DIR\env.template.json" "$SKILL_DIR\env.json"
     ```
     Luego informar al usuario:
     > ⚠️ **Primera ejecución**: se ha creado `env.json` desde la plantilla.
     > Ábrelo en `$SKILL_DIR\env.json` y rellena los valores `<COMPLETAR>` con tus credenciales reales.
     > Después repite tu petición.
     
     **Detener aquí** — no continuar hasta que el usuario confirme que ha rellenado el archivo.

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

# Modo Modelo BD (ERD / SQL / sync) — `/orchestrator-erd`

Cuando la petición es "actualiza el modelo BD", "muestra el ERD", "genera SQL de tablas",
"relaciona tablas", "compara el modelo con la BD":

| Petición | Tool MCP (nativa Python) | Resultado |
|----------|--------------------------|-----------|
| Actualizar el modelo desde la BD | `sync_from_db(workspace)` (+ `sync_indexes` si Oracle) | reescribe `BD\<proy>-model.json` |
| Ver el ERD | `render_erd(workspace)` | `<workspace>\BD\<proy>-erd.html`, abre navegador |
| Generar DDL completo | `generate_sql(workspace)` | `C:\AIS\<proy>\scripts\<proy>-ddl.sql` (dialecto de XMLConfig, sin argumento de motor) |
| Inferir relaciones desde los DALC | `analyze_dalc(workspace, sln_path)` | añade `relations` (confidence:low) al modelo |
| Detectar drift modelo vs BD | `compare_model(workspace)` / `compare_model_tables(workspace, "T1,T2")` | JSON con `tables_only_in_model`/`tables_only_in_db`/`tables_changed` |
| Script de migración modelo→BD | `generate_migration(workspace)` | `C:\AIS\<proy>\scripts\<proy>-migration.sql` (idempotente) |
| Exportar a Oracle Data Modeler | `export_dmd(workspace)` | `<workspace>\BD\<proy>.dmd` |

El SQL/HTML/XML generado NO entra en contexto — las tools devuelven la ruta. Leer el fichero solo si hay que revisarlo.
`workspace` = cwd de la sesión (literal). El motor sale SIEMPRE de `docs\XMLConfig.xml`, nunca se pasa como argumento.

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

> Añadir nuevos proyectos en `$SKILL_DIR\projects\<nombre>\` y actualizar esta tabla.

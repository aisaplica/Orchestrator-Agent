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

**Conexión y esquema BD (SIEMPRE en vivo):**
- Cadena de conexión: `C:\AIS\<Sln>\bin\Settings\Settings.xml` → tag `oledbconnectionstring`
  (index 0 = DEV/TEST; 1+ = PRE/PROD). Resolver con `mcp__orchestrator-workspace__get_db_config(workspace)`.
- Esquema de tablas/columnas: `mcp__orchestrator-workspace__get_table_schema(workspace, "T1,T2", source="db")`.
- Registros/valores reales: `mcp__orchestrator-workspace__db_query(workspace, "SELECT ...")` (SOLO SELECT).
- ⛔ NUNCA responder sobre tablas/campos/registros desde `projects/<proy>/schema.md` ni desde `model.json` — son caché; consulta la BD.

**Contexto NO-BD** (Mantis, SVN, SMTP, perfil) — `$SKILL_DIR`:

```
$SKILL_DIR\
├── env.json                          ← Mantis / SVN / correo / contexto_personal
├── references\oracle-tips.md
├── references\sqlserver-tips.md
└── projects\<nombre>\schema.md       ← SOLO contexto de negocio (qué representan las tablas), no esquema técnico
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

1. **Conexión BD** → `get_db_config(workspace)` resuelve motor/datasource/schema/user desde
   `Settings.xml`. Para PRE/PROD, el `oledbconnectionstring` de índice > 0 (si `environments > 1`).

2. **Esquema / tablas / columnas / registros** → SIEMPRE `get_table_schema(source="db")` y/o `db_query`.
   Si la petición es "genera C# ADO.NET / stored procedure para la tabla X" → primero `get_table_schema` vivo, luego generar.

3. **Contexto de negocio** (qué es la tabla, reglas funcionales) → `projects/<nombre>/schema.md` si existe. NO usarlo para tipos/longitudes.

4. **Herramientas NO-BD** (Mantis, SVN, SMTP) → `env.json` (`herramientas`, `contexto_personal`).

5. **Tips de motor**: Oracle → `references/oracle-tips.md` · SQL Server → `references/sqlserver-tips.md`.

6. Si `get_db_config` no resuelve (solución sin publicar) → informar y pedir que publique `C:\AIS\<Sln>\` o revise `Settings.xml`.

7. Si el usuario no especifica entorno → usar el índice 0 (DEV/TEST) de `Settings.xml`.

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
`workspace` = cwd de la sesión (literal). El motor sale SIEMPRE de `Settings.xml` (`get_db_config`), nunca se pasa como argumento.
`<proy>` en las rutas = nombre del `.sln` (carpeta `C:\AIS\<Sln>\`).

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

⛔ Nunca inventar tablas, columnas ni credenciales — para esquema/registros consultar SIEMPRE la BD viva (`get_table_schema` / `db_query`), nunca `schema.md` ni `model.json`
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

# Hooks disponibles

Scripts PowerShell en `hooks/`. Ejecutar directamente si el MCP no está activo.

## Build / Deploy

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/compile-check.ps1` | `<sln> [-NoRestore]` | Build real → `errors[], warnings[], success` |
| `hooks/test-runner-check.ps1` | `<sln> [-NoBuild]` | dotnet test → `passed/failed/failures[]` |
| `hooks/create-test-project.ps1` | `<sln> [-Framework xunit\|mstest\|nunit] [-ProjectName <nombre>]` | Crea proyecto de test y lo añade a la .sln |
| `hooks/validate-solution.ps1` | `<sln>` | Confirma que la .sln existe y es accesible |

## Análisis / Scope

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/parse-sln.ps1` | `<sln>` | Parsea .sln → `scope_dirs, tipo (Batch/Online), workspace` |
| `hooks/find-symbol.ps1` | `-ScopeDirs "<dirs,coma>" -Symbols "<sym1,sym2>" [-Type class\|method\|property\|interface\|enum\|any]` | Localiza uno o varios símbolos en una sola pasada `Select-String` → `{ symbols: { NAME: { found, count, matches[] } }, file_count }` |
| `hooks/find-doc-section.ps1` | `<workspace> <keyword>` | Busca en docs funcionales → sección, archivo, línea |
| `hooks/security-scan.ps1` | `<sln_path>` | SQL injection, credenciales hardcodeadas, XSS, input sin validar → findings con severidad |
| `hooks/map-dependencies.ps1` | `<workspace>` | Mapa dependencias entre soluciones → proyectos compartidos, conflictos NuGet |
| `hooks/search-code.ps1` | `<workspace> <sln> <pattern> [-Glob *.cs] [-Context 2] [-MaxResults 50]` | Regex en scope garantizado (equivalente a `search_code`) |
| `hooks/edit-ansi.ps1` | `-Path <archivo> -Search <texto> -Replace <texto> [-All] [-Regex]` | Find/replace preservando la codificación original del archivo (BOM / UTF-8 / ANSI-1252). Para editar `.cs`/`.aspx` legacy ScacsWeb sin corromper acentos — Edit/Write de Claude Code escriben UTF-8 y rompen ANSI. Sin tool MCP equivalente: los agentes lo invocan por `powershell -File`. Ver `references/conventions.md` |

## BD / Modelo

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/get-config.ps1` | `<workspace>` | Lee XMLConfig.xml → `motor, datasource, schema, model_path` |
| `hooks/get-bd-model.ps1` | `-Workspace <ws> [-Tables "T1,T2"]` | Schemas de tablas del model.json (equivalente a `get_table_schema`) |
| `hooks/db-query.ps1` | `-Workspace <ws> -Sql "<SELECT>" [-MaxRows 200]` | SELECT contra la BD del XMLConfig (equivalente a `db_query`) |
| `hooks/compare-model.ps1` | `<workspace>` | Drift model.json vs esquema real BD |
| `hooks/generate-migration.ps1` | `<workspace>` | Scripts SQL (CREATE TABLE / ALTER TABLE ADD) desde drift |
| `hooks/sync-from-db.ps1` | `<workspace> <proyecto>` | Sincroniza tablas/columnas desde BD real → `table_count` (escritura atómica) |
| `hooks/sync-model-tables.ps1` | `<workspace> <tablas-coma-separadas>` | Actualiza tablas específicas de model.json post-migración |
| `hooks/sync-indexes.ps1` | `<workspace> [-Proyecto <nombre>]` | Sincroniza índices desde BD al modelo — preserva source=manual |
| `hooks/analyze-dalc.ps1` | `<workspace> <proyecto> [-SolutionPath <sln>]` | Infiere relaciones desde JOINs/WHERE en DALCs |
| `hooks/render-erd.ps1` | `<workspace> [-Proyecto <nombre>]` | Genera ERD HTML y lo abre en navegador → `{path, table_count}` |
| `hooks/generate-sql.ps1` | `<workspace> [-Proyecto <nombre>] [-Motor ORACLE\|SQLSERVER]` | Genera DDL SQL → `C:\AIS\<proyecto-lowercase>\scripts\<proyecto>-ddl-<motor>.sql` |
| `hooks/export-dmd.ps1` | `<workspace> [-Proyecto <nombre>]` | Exporta a Oracle Data Modeler `.dmd` |

## Control de versiones (SVN / Git)

`hooks/detect-vcs.ps1` decide cuál de los dos bloques usar — nunca asumir uno u otro sin llamarlo primero.

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/detect-vcs.ps1` | `<workspace>` | Detecta VCS subiendo por las carpetas → `{vcs: "svn"\|"git"\|"none", root}` |
| `hooks/svn-diff.ps1` | `<workspace>` | Estado SVN → `modificados, añadidos, eliminados, ?` |
| `hooks/svn-log.ps1` | `<workspace> [-Solution <nombre>] [-Limit 10]` | Historial commits SVN → JSON (requiere svn CLI) |
| `hooks/svn-diff-revision.ps1` | `<workspace> <revisions> [-MaxDiffChars 15000]` | Diff revisiones SVN → `files_changed, combined_diff` (requiere svn CLI) |
| `hooks/svn-add.ps1` | `<workspace> [-Files <lista>]` | Añade ficheros ?: CLI → TortoiseProc → instrucciones manuales |
| `hooks/git-status.ps1` | `<workspace>` | Estado Git → `modificados, staged, sin trackear (?), conflicto` |
| `hooks/git-log.ps1` | `<workspace> [-Solution <nombre>] [-Limit 10]` | Historial commits Git → JSON, `revision` = hash corto (requiere git CLI) |
| `hooks/git-diff-revision.ps1` | `<workspace> <revisions> [-MaxDiffChars 15000]` | Diff de commits Git (hashes coma-separados) → `files_changed, combined_diff` (requiere git CLI) |
| `hooks/git-add.ps1` | `<workspace> [-Files <lista>]` | Añade ficheros ??: CLI → TortoiseGitProc → instrucciones manuales |

## Entorno / Logging

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/check-env.ps1` | `<workspace> <proyecto>` | Valida XMLConfig, AIS, dotnet, SVN, Git, modelo BD, docs → `checks[], overall` |
| `hooks/log-execution.ps1` | `<workspace> <solution> <task> [-Status success\|fail\|partial] [-Agents <lista,coma>]` | Registra la ejecución del pipeline en `<workspace>\executions\history.json` (array; tope 500 vivas, excedente a `executions\archive\history-YYYY-MM.json`). Backend real de la tool MCP `log_execution` y fallback del paso 11 del pipeline |
| `hooks/scan-aspx.ps1` | `-SlnPath <sln>` | Extrae controles AIS de .aspx → `RIDIOMA/RCONTROLES` inserts |
| `hooks/skill-trigger.ps1` | (stdin JSON, hook UserPromptSubmit de Claude Code) | Detecta `.sln` en el prompt dentro de workspaces RS e inyecta recordatorio de invocar la skill — no lo ejecutan los agentes |

## Requisito de codificación (PS5.1)

Todos los `.ps1` deben guardarse con **UTF-8 con BOM** (`EF BB BF`). Windows PowerShell 5.1 sin BOM decodifica con codepage ANSI, corrompiendo caracteres españoles y causando fallos silenciosos.
Ver `references/troubleshooting.md` → "Hook falla silenciosamente / caracteres corruptos".

## Build (via runner — ver `agents/build.md`)

| Script | Parámetros | Descripción |
|--------|-----------|-------------|
| `hooks/batch-build.ps1` | `<Solution> "<workspace>"` | Build Debug+Release y copia binarios a `C:\ais\<proyecto>\Procesos\Exes` |
| `hooks/online-publish.ps1` | `<csproj> [<Profile>]` | Publish MSBuild con perfil — `FolderProfile1` es solo el default del script, NO asumir que es el nombre real: verificar `<WebFolder>\Properties\PublishProfiles\*.pubxml` antes |
| `hooks/copy-ais.ps1` | `<source> <workspace>` | Copia binarios a destino AIS del proyecto |

## Scripts de utilidad (manuales)

| Script | Descripción |
|--------|-------------|
| `scripts/clean-build.ps1` | Limpia carpetas bin/obj antes de compilar |
| `scripts/clean-ais.ps1` | Limpia destino AIS antes de deploy |
| `scripts/print-structure.ps1` | Imprime estructura del proyecto |
| `scripts/reset-environment.ps1` | Resetea entorno de desarrollo |
| `scripts/run-agent.ps1` | Invoca agente manualmente via CLI |
| `scripts/test-runner.ps1` | Ejecuta tests reales (`dotnet test`) |

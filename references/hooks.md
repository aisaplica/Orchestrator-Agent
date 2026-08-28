# Hooks disponibles

Scripts PowerShell en `hooks/`. Cada tool MCP (`references/mcp.md`) tiene aquí su equivalente:
usar la tool MCP; si no responde, ejecutar el hook directamente.

**Estado:**
- ✅ implementado — el `.ps1` existe en `hooks/`.
- ⚠️ NO implementado — la tool MCP existe pero no hay hook fallback. Si el MCP está caído, usar la vía manual indicada. Al invocarlo el MCP devuelve `{"status":"not_implemented","fallback":"..."}`.
- 🐍 nativa Python — la tool MCP está implementada en el server, no llama a ningún `.ps1`. Funciona con el MCP activo; sin hook fallback.

Todos los `.ps1` se guardan con **UTF-8 con BOM** (`EF BB BF`) — ver "Requisito de codificación" abajo.

## Build / Test / Deploy

| Script | Estado | Parámetros | Descripción |
|--------|--------|-----------|-------------|
| `hooks/compile-check.ps1` | ✅ | `<sln> [-NoRestore]` | Build real (autodetecta MSBuild/dotnet vía `lib-msbuild.ps1`) → `errors[], warnings[], success` |
| `hooks/test-runner-check.ps1` | ✅ | `<sln> [-NoBuild]` | Detecta proyectos de test en la .sln; 0 → `{skipped:true}`; si hay → `dotnet test` + parseo TRX → `passed/failed/failures[]/duration_s` |
| `hooks/create-test-project.ps1` | ✅ | `<sln> [-Framework xunit\|mstest\|nunit] [-ProjectName <nombre>]` | `dotnet new` + `dotnet sln add` → `{project_path, added_to_sln}` |
| `hooks/validate-solution.ps1` | ✅ | `<sln>` | Confirma que la .sln existe y es accesible |
| `hooks/batch-build.ps1` | ✅ | `<Solution> "<workspace>"` | Build Debug+Release y copia binarios a `C:\ais\<proyecto>\Procesos\Exes` |
| `hooks/online-publish.ps1` | ✅ | `<csproj> [<Profile>]` | Publish MSBuild con perfil — verificar `<WebFolder>\Properties\PublishProfiles\*.pubxml` antes (el default del script NO es el nombre real) |
| `hooks/copy-ais.ps1` | ✅ | `<source> <workspace>` | Copia binarios a destino AIS del proyecto |

## Análisis / Scope

| Script | Estado | Parámetros | Descripción |
|--------|--------|-----------|-------------|
| `hooks/parse-sln.ps1` | ✅ | `<sln>` | Parsea .sln → `scope_dirs, tipo (Batch/Online), workspace` |
| `hooks/find-symbol.ps1` | ✅ | `-ScopeDirs "<dirs,coma>" -Symbols "<sym1,sym2>" [-Type class\|method\|property\|interface\|enum\|any]` | Localiza símbolos en una pasada `Select-String` → `{ symbols: { NAME: { found, count, matches[] } }, file_count }` |
| `hooks/edit-ansi.ps1` | ✅ | `-Path <archivo> -Search <texto> -Replace <texto> [-All] [-Regex]` | Find/replace preservando la codificación original (BOM / UTF-8 / ANSI-1252). Para editar `.cs`/`.aspx` legacy sin corromper acentos. Sin tool MCP — los agentes lo invocan por `powershell -File`. Ver `references/conventions.md` |
| `hooks/search-code.ps1` | ⚠️ | `<workspace> <sln> <pattern> [-Glob *.cs] [-Context 2] [-MaxResults 50]` | Regex en scope garantizado (`search_code`). **Fallback manual:** Grep/Glob restringido a `scope_dirs` (`get_scope`) |
| `hooks/scan-aspx.ps1` | ⚠️ | `-SlnPath <sln>` | Extrae controles AIS de .aspx → inserts `SIControles/SIIdioma` (`scan_aspx`). **Fallback manual:** releer el diff `.aspx`/`.aspx.cs` (ver `agents/core.md`) |
| `hooks/find-doc-section.ps1` | ⚠️ | `<workspace> <keyword>` | Busca en docs funcionales → sección, archivo, línea (`find_doc_section`). **Fallback manual:** Grep del keyword en `docs/scacs/` |
| `hooks/security-scan.ps1` | ⚠️ | `<sln_path>` | SQL injection, credenciales, XSS, input sin validar (`security_scan`). **Fallback manual:** revisar el diff a mano (fase 3) |
| `hooks/map-dependencies.ps1` | ⚠️ | `<workspace>` | Dependencias entre soluciones, conflictos NuGet (`map_dependencies`). Fase 3 |

## BD / Modelo

| Script | Estado | Parámetros | Descripción |
|--------|--------|-----------|-------------|
| `hooks/get-config.ps1` | ✅ | `<workspace>` | Lee XMLConfig.xml → `motor, datasource, schema, model_path` |
| `get_table_schema` | 🐍 | `(workspace, tables)` | Esquema de tablas del model.json. Tool nativa Python — sin hook |
| `db_query` | 🐍 | `(workspace, sql, max_rows?)` | SELECT contra la BD del XMLConfig. Tool nativa Python — sin hook |
| `sync_from_db` | 🐍 | `(workspace)` | Sincroniza tablas/columnas desde BD real. Tool nativa Python — sin hook |
| `sync_model_tables` | 🐍 | `(workspace, tables)` | Actualiza tablas específicas post-migración. Tool nativa Python — sin hook |
| `sync_indexes` | 🐍 | `(workspace)` | Sincroniza índices Oracle al modelo. Tool nativa Python — sin hook |
| `hooks/compare-model.ps1` | ⚠️ | `<workspace> [-Tables T1,T2]` | Drift model.json vs BD (`compare_model` / `compare_model_tables`). Fase 2 |
| `hooks/generate-migration.ps1` | ⚠️ | `<workspace>` | Scripts SQL (CREATE/ALTER) desde drift (`generate_migration`). Fase 2 |
| `hooks/analyze-dalc.ps1` | ⚠️ | `<workspace> <proyecto> [-SolutionPath <sln>]` | Infiere relaciones desde JOINs/WHERE en DALCs (`analyze_dalc`). Fase 2 |
| `hooks/render-erd.ps1` | ⚠️ | `<workspace> [-Proyecto <nombre>]` | Genera ERD HTML (`render_erd`). Fase 2 |
| `hooks/generate-sql.ps1` | ⚠️ | `<workspace> [-Proyecto <nombre>] [-Motor ORACLE\|SQLSERVER]` | Genera DDL SQL a fichero (`generate_sql`). Fase 2 |
| `hooks/export-dmd.ps1` | ⚠️ | `<workspace> [-Proyecto <nombre>]` | Exporta a Oracle Data Modeler `.dmd` (`export_dmd`). Fase 2 |

## Control de versiones (SVN / Git)

`hooks/detect-vcs.ps1` decide qué bloque usar — nunca asumir uno sin llamarlo primero.
Los repos ScacsWeb son **SVN**; el bloque Git está sin implementar (usar el CLI `git` directo si hiciera falta).

| Script | Estado | Parámetros | Descripción |
|--------|--------|-----------|-------------|
| `hooks/detect-vcs.ps1` | ✅ | `<workspace>` | Sube por las carpetas buscando `.svn`/`.git` (sin CLI) → `{vcs: "svn"\|"git"\|"none", root}` |
| `hooks/svn-diff.ps1` | ✅ | `<workspace> [<scopePaths ;-sep>]` | Estado SVN → `modificados, añadidos, eliminados, ?` |
| `hooks/svn-log.ps1` | ✅ | `<workspace> [-Solution <texto>] [-Limit 10]` | Historial commits SVN vía `svn log --xml` → `{commits:[{revision,author,date,message}]}` (requiere svn CLI; sin él → fallback TortoiseSVN) |
| `hooks/svn-diff-revision.ps1` | ✅ | `<workspace> <revisions> [-MaxDiffChars 15000]` | Diff revisiones SVN → `files_changed, combined_diff` (requiere svn CLI) |
| `hooks/svn-add.ps1` | ✅ | `<workspace> [-Files <lista>]` | Añade ficheros `?`: CLI → TortoiseProc → instrucciones manuales |
| `hooks/git-diff-revision.ps1` | ✅ | `<workspace> <revisions> [-MaxDiffChars 15000]` | Diff de commits Git (hashes coma-separados) → `files_changed, combined_diff` (requiere git CLI) |
| `hooks/git-status.ps1` | ⚠️ | `<workspace>` | Estado Git (`git_status`). **Fallback:** usar `svn_status` (ScacsWeb=SVN) o el CLI `git` directo |
| `hooks/git-log.ps1` | ⚠️ | `<workspace> [-Solution <nombre>] [-Limit 10]` | Historial Git (`git_log`). **Fallback:** `svn_log` o CLI `git` directo |
| `hooks/git-add.ps1` | ⚠️ | `<workspace> [-Files <lista>]` | Añade ficheros `??` a Git (`git_add`). **Fallback:** `svn_add` o CLI `git` directo |

## Entorno / Logging

| Script | Estado | Parámetros | Descripción |
|--------|--------|-----------|-------------|
| `hooks/check-env.ps1` | ✅ | `<workspace> <proyecto>` | Valida XMLConfig, AIS, dotnet, SVN, Git, modelo BD, docs → `checks[], overall` |
| `hooks/log-execution.ps1` | ✅ | `<workspace> <solution> <task> [-Status success\|fail\|partial] [-Agents <lista,coma>]` | Registra la ejecución en `<workspace>\executions\history.json` (array; tope 500 vivas, excedente a `executions\archive\history-YYYY-MM.json`). Backend real de `log_execution` y fallback del paso 11 del pipeline |

## Librerías internas (no son hooks invocables)

| Script | Descripción |
|--------|-------------|
| `hooks/lib-msbuild.ps1` | Autodetección MSBuild/dotnet. `dot-source` desde `compile-check.ps1` |
| `hooks/mantis-cli.ps1`, `hooks/mantis-get-issue.ps1` | CLI MantisBT (usados por `agents/mantis.md`, no por el MCP) |
| `hooks/parse-weblog.ps1` | Parseo de logs de error web (usado por `parse_web_log` / `/orchestrator-log-errores`) |

## Requisito de codificación (PS5.1)

Todos los `.ps1` se guardan con **UTF-8 con BOM** (`EF BB BF` como primeros 3 bytes). Windows PowerShell 5.1 sin BOM decodifica con codepage ANSI, corrompiendo caracteres españoles (`—`, `⛔`, tildes) y causando `ParseError` o fallos silenciosos.
Ver `references/troubleshooting.md` → "Hook falla silenciosamente / caracteres corruptos".

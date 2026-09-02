# MCP rs-workspace

Servidor MCP local. Preferente sobre hooks — más eficiente en tokens.
Fallback: hook equivalente listado en `references/hooks.md`.

**Cobertura de hooks:** no todas las tools tienen hook fallback. Estado en `references/hooks.md`.
Las tools BD/modelo son **nativas Python** (🐍): funcionan con el MCP activo, sin hook fallback —
`compare_model`, `compare_model_tables`, `generate_sql`, `generate_migration`, `render_erd`,
`analyze_dalc`, `export_dmd`, `get_table_schema`, `db_query`, `sync_*`.
Las que no tienen ni hook ni impl nativa devuelven `{"status":"not_implemented","fallback":"<vía manual>"}` —
no reintentar, aplicar el fallback. Pendientes (fase 3): `map_dependencies`, `security_scan`, `scan_aspx`,
`search_code`, `find_doc_section`, `git_status`, `git_log`, `git_add`.

| Tool | Uso |
|------|-----|
| `ping()` | Health check — hooks_dir, hooks_found, svn_cli, git_cli, python version |
| `get_scope(sln_path)` | Paso 2b — parsea .sln → scope_dirs, tipo, workspace |
| `validate_solution(sln_path)` | Paso 2 — confirma que la .sln existe y es accesible |
| `detect_vcs(workspace)` | Detecta SVN/Git subiendo por las carpetas → `{vcs, root}`. Llamar antes de cualquier tool `svn_*`/`git_*` |
| `get_db_config(workspace)` | Paso BD — resuelve la conexión desde `C:\AIS\<Sln>\bin\Settings\Settings.xml` (`oledbconnectionstring`) → motor, datasource, schema, catalog, user, sln, environments, model_path. NO devuelve password. Fallback legacy: `docs/XMLConfig.xml` |
| `find_symbol(symbol, scope_dirs, symbol_type?)` | Localiza clases/métodos/propiedades en scope — usa `find-symbol.ps1` (Select-String multi-patrón, una sola pasada) |
| `compile_check(sln_path, no_restore=True, max_errors=20)` | Validator — build real → errors[], warnings[], success |
| `run_tests(sln_path, no_build?)` | Tester — dotnet test → passed/failed/failures[], skipped |
| `get_model_index(workspace)` | Índice ligero del SNAPSHOT `BD/<Sln>-model.json`: {TABLA:[COL1,...]}. Orientativo — para datos frescos usar `get_table_schema`/`db_query` |
| `get_table_schema(workspace, tables, source="auto", env_index=0)` | 🐍 Esquema de tablas EN VIVO desde el catálogo (`source="db"`). `"auto"` cae al snapshot con `warning` si la conexión falla; `"model"` fuerza snapshot. `env_index` 1+ = PRE/PROD. Columnas de la BD; `indexes`/`relations` del snapshot si existe (`meta_from_snapshot`) |
| `search_model(workspace, keyword)` | Busca keyword en el SNAPSHOT (tabla/columna/descripción). Para localizar dónde vive un concepto — confirmar con `get_table_schema` |
| `compare_model_tables(workspace, tables)` | 🐍 Drift solo de tablas concretas (mismo formato que `compare_model`). Post-migración |
| `batch_find_symbols(symbols, scope_dirs)` | N símbolos en una sola llamada y una sola pasada `Select-String` — evita N round-trips y N passes |
| `search_code(workspace, sln_path, pattern)` | Regex en scope garantizado. Reemplaza 3-8× Grep |
| `svn_status(workspace)` | Estado SVN → modificados, añadidos, eliminados, ? sin versionar |
| `git_status(workspace)` | Estado Git → modificados, staged, ?? sin trackear, conflicto (U). Equivalente Git de `svn_status` |
| `create_test_project(sln_path, framework?, project_name?)` | Crea proyecto xUnit/mstest/nunit |
| `db_query(workspace, sql, max_rows=200, env_index=0)` | 🐍 SELECT EN VIVO contra la BD publicada (cadena de `Settings.xml`). SOLO SELECT, sin multi-statement. `env_index` 1+ = PRE/PROD |
| `compare_model(workspace)` | 🐍 Diff snapshot `model.json` vs BD real (motor de `Settings.xml`) → `tables_only_in_model`, `tables_only_in_db`, `tables_changed`. Respeta visible:false |
| `scan_aspx(sln_path)` | Extrae controles AIS de .aspx → IDs y textos para RIDIOMA/RCONTROLES |
| `log_execution(workspace, solution, task, status?, agents?)` | Registra la ejecución en `<workspace>\executions\history.json`. Fallback: `hooks/log-execution.ps1` (mismo backend). Paso 11 del pipeline — nunca omitir |
| `generate_migration(workspace)` | 🐍 Script SQL idempotente modelo→BD (dialecto de Settings.xml) → `C:\AIS\<proy>\scripts\<proy>-migration.sql` |
| `svn_log(workspace, solution?, limit?)` | Historial SVN → revisión, autor, fecha, mensaje |
| `git_log(workspace, solution?, limit?)` | Historial Git → hash corto, autor, fecha, mensaje. Equivalente Git de `svn_log` |
| `find_doc_section(workspace, keyword)` | Localiza sección en docs funcionales (para UpdateDocs) |
| `svn_diff_revision(workspace, revisions, max_diff_chars?)` | Diff revisiones SVN filtrado (para rs-validar-req) |
| `git_diff_revision(workspace, revisions, max_diff_chars?, summary_only?)` | Diff de commits Git (hashes) filtrado. Equivalente Git de `svn_diff_revision` |
| `svn_add(workspace, files?)` | Añade ficheros ?: CLI → TortoiseProc → instrucciones manuales |
| `git_add(workspace, files?)` | Añade ficheros ??: CLI → TortoiseGitProc → instrucciones manuales. Equivalente Git de `svn_add` |
| `security_scan(sln_path)` | Scan seguridad: SQL injection, XSS, credenciales, input sin validar |
| `sync_model_tables(workspace, tables)` | Sincroniza tablas específicas model.json con BD (post-migración). Consulta solo las tablas indicadas (no el schema completo) |
| `map_dependencies(workspace)` | Mapa dependencias: proyectos compartidos entre soluciones, conflictos NuGet |
| `sync_from_db(workspace)` | Sincroniza tablas/columnas del modelo BD desde esquema real de BD. Tablas con `visible:false` se preservan sin tocar |
| `sync_indexes(workspace)` | Sincroniza índices desde BD al modelo — preserva source=manual. Omite tablas con `visible:false` |
| `analyze_dalc(workspace, sln_path?)` | 🐍 Infiere relaciones desde `JOIN ... ON` en el SQL de los DALC (.cs) → modelo (confidence:low) |
| `render_erd(workspace)` | 🐍 ERD HTML (mermaid) → `<workspace>\BD\<proy>-erd.html`, abre navegador |
| `check_env(workspace)` | Valida entorno: Settings.xml, AIS, dotnet, SVN, Git, modelo BD → checks[] |
| `generate_sql(workspace)` | 🐍 DDL desde el modelo en el dialecto de Settings.xml (Oracle: `VARCHAR2(n CHAR)`) → `C:\AIS\<proy>\scripts\<proy>-ddl.sql`. Sin argumento de motor |
| `export_dmd(workspace)` | 🐍 Exporta a Oracle Data Modeler (.dmd XML mínimo) → `<workspace>\BD\<proy>.dmd` |

---

## Notas de implementación

**Salida JSON compacta**: todos los tools devuelven JSON sin espacios (`separators=(",",":")`) para minimizar tokens. Solo la caché interna de `_load_model` usa `indent=2`.

**Escritor canónico model.json**: toda escritura del modelo pasa por `_write_model_json` — UTF-8 con BOM, saltos CRLF, indent=2, ensure_ascii=True. Evita el bug de inflado de `ConvertTo-Json` en PS5.1 (1.1MB→3.5MB).

**visible:false (Oracle)**: tablas marcadas `visible: false` en el modelo son preservadas por `sync_from_db`, `sync_indexes` y `sync_model_tables` sin consultarlas en BD. Origen: tabla existe en el modelo pero no en `ALL_TABLES` con las credenciales actuales.

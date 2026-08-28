"""
orchestrator-workspace MCP server — herramientas nativas para soluciones ScacsWeb.
Cada tool llama al hook PowerShell correspondiente y devuelve JSON estructurado.
"""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HOOKS_DIR  = Path(__file__).parent.parent / "hooks"
CACHE_DIR  = Path.home() / ".claude" / "cache" / "rs-models"

# Hooks aún no implementados en este build: fallback que el agente debe usar en su lugar.
# Al implementar el hook correspondiente, quitarlo de este dict.
_HOOK_FALLBACKS = {
    "search-code.ps1":     "Usar Grep/Glob restringido a scope_dirs (get_scope).",
    "scan-aspx.ps1":       "Releer el diff .aspx/.aspx.cs para la lista de controles (ver agents/core.md).",
    "find-doc-section.ps1": "Grep del keyword en docs/scacs/.",
    "compare-model.ps1":   "Sin comparación de modelo en este build (fase 2). Confirmar tablas puntuales con db_query.",
    "generate-migration.ps1": "Familia BD/ERD no implementada en este build (fase 2).",
    "generate-sql.ps1":    "Familia BD/ERD no implementada en este build (fase 2).",
    "render-erd.ps1":      "Familia BD/ERD no implementada en este build (fase 2).",
    "export-dmd.ps1":      "Familia BD/ERD no implementada en este build (fase 2).",
    "analyze-dalc.ps1":    "Familia BD/ERD no implementada en este build (fase 2).",
    "map-dependencies.ps1": "Análisis de dependencias entre soluciones no disponible (fase 3).",
    "security-scan.ps1":   "Scan de seguridad no implementado (fase 3). Revisar SQLi / credenciales / XSS en el diff a mano.",
    "git-status.ps1":      "Los repos ScacsWeb usan SVN: usar svn_status. Para Git real, invocar el CLI git directamente.",
    "git-log.ps1":         "Los repos ScacsWeb usan SVN: usar svn_log. Para Git real, invocar el CLI git directamente.",
    "git-add.ps1":         "Los repos ScacsWeb usan SVN: usar svn_add. Para Git real, invocar el CLI git directamente.",
}

mcp = FastMCP("orchestrator-workspace")

_model_cache:  dict[str, tuple[float, dict]] = {}  # path → (mtime, model) — en proceso
_config_cache: dict[str, dict]               = {}  # workspace → config    — en proceso
_scope_cache:  dict[str, tuple[float, dict]] = {}  # sln_path → (mtime, scope) — en proceso
_svn_cli: bool | None = None                        # None = no comprobado aún
_git_cli: bool | None = None                        # None = no comprobado aún


def _get_config(workspace: str) -> dict:
    """get-config.ps1 con cache en proceso — evita spawn PS en cada tool call."""
    if workspace not in _config_cache:
        _config_cache[workspace] = _run_ps("get-config.ps1", workspace)
    return _config_cache[workspace]


def _get_scope(sln_path: str) -> dict:
    """parse-sln.ps1 con cache mtime — el .sln no cambia durante una sesión."""
    try:
        mtime = Path(sln_path).stat().st_mtime
    except OSError:
        mtime = 0.0
    cached = _scope_cache.get(sln_path)
    if cached and cached[0] == mtime:
        return cached[1]
    result = _run_ps("parse-sln.ps1", sln_path)
    _scope_cache[sln_path] = (mtime, result)
    return result


def _load_model(model_path: Path) -> dict | None:
    """Carga model.json con cache en disco (mtime) — sobrevive reinicios del MCP server."""
    try:
        mtime = model_path.stat().st_mtime
    except FileNotFoundError:
        return None

    # 1. Cache en proceso (más rápido)
    cached = _model_cache.get(str(model_path))
    if cached and cached[0] == mtime:
        return cached[1]

    # 2. Cache en disco
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key  = hashlib.md5(str(model_path).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, encoding="utf-8") as f:
                disk = json.load(f)
            if disk.get("mtime") == mtime:
                model = disk["model"]
                _model_cache[str(model_path)] = (mtime, model)
                return model
        except Exception:
            pass

    # 3. Leer model.json original y escribir cache
    # utf-8-sig: _write_model_json escribe BOM (b'\xef\xbb\xbf') — utf-8-sig lo consume.
    with open(model_path, encoding="utf-8-sig") as f:
        model = json.load(f)
    _model_cache[str(model_path)] = (mtime, model)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"mtime": mtime, "model": model}, f, ensure_ascii=False)
    except Exception:
        pass  # fallo de escritura no es fatal
    return model


def _run_ps(script: str, *args: str) -> dict:
    ps_path = HOOKS_DIR / script
    if not ps_path.is_file():
        return {
            "status": "not_implemented",
            "error": f"El hook '{script}' no está incluido en este build del plugin.",
            "fallback": _HOOK_FALLBACKS.get(script, "Sin fallback automático — esta acción no está disponible."),
            "script": script,
        }
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(ps_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    output = (result.stdout or "").strip()
    if not output:
        stderr = (result.stderr or "").strip()
        return {
            "error": stderr or f"No output from {script}",
            "exit_code": result.returncode,
            "script": script,
        }
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw": output, "exit_code": result.returncode, "script": script}


def _proyecto(workspace: str) -> str:
    """Infiere nombre de proyecto desde ruta workspace (carpeta anterior a trunk/)."""
    return Path(workspace).parent.name


def _get_db_password(workspace: str) -> str:
    """Lee password directo de docs/XMLConfig.xml — NUNCA pasar por _get_config()/get-config.ps1,
    cuyo dict se devuelve tal cual por la tool get_db_config (no debe filtrar el password al agente)."""
    import xml.etree.ElementTree as ET
    xml_path = Path(workspace) / "docs" / "XMLConfig.xml"
    if not xml_path.exists():
        return ""
    try:
        root = ET.parse(xml_path).getroot()
        db_node = root.find(".//DataBase")
        if db_node is not None:
            return db_node.get("password", "") or ""
        con_node = root.find(".//Conexion")
        if con_node is not None:
            ds = (con_node.findtext("DataSource") or "")
            for part in ds.split(";"):
                part = part.strip()
                if part.lower().startswith("password="):
                    return part.split("=", 1)[1].strip()
        return ""
    except Exception:
        return ""


def _check_workspace(workspace: str) -> dict | None:
    """Devuelve dict de error si el workspace no existe, None si es válido."""
    if not Path(workspace).exists():
        return {"error": f"Workspace no encontrado: {workspace}", "success": False}
    return None


def _check_svn_cli() -> bool:
    global _svn_cli
    if _svn_cli is None:
        try:
            r = subprocess.run(["svn", "--version", "--quiet"], capture_output=True, timeout=5)
            _svn_cli = r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            _svn_cli = False
    return _svn_cli


def _check_git_cli() -> bool:
    global _git_cli
    if _git_cli is None:
        try:
            r = subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            _git_cli = r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            _git_cli = False
    return _git_cli


# ---------------------------------------------------------------------------
# Helpers BD: escritura canónica model.json + queries Oracle/SQL Server
# ---------------------------------------------------------------------------

def _write_model_json(model_path: Path, model: dict) -> None:
    """Escritura canónica: UTF-8 con BOM, CRLF, indent=2, ensure_ascii=True.
    Invalida ambas capas de caché para que la próxima lectura traiga los datos frescos."""
    text = json.dumps(model, indent=2, separators=(",", ": "), ensure_ascii=True)
    text = text.replace("\n", "\r\n")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    _model_cache.pop(str(model_path), None)
    cache_key  = hashlib.md5(str(model_path).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        cache_file.unlink()
    except FileNotFoundError:
        pass


def _run_oracle_sql(datasource: str, user: str, password: str, schema: str, sql: str) -> list[str] | str:
    """Ejecuta SQL en Oracle via sqlplus. Devuelve lista de líneas de salida o string de error."""
    if password:
        connect_line = f"CONNECT {user}/{password}@{datasource}\n"
        sqlplus_conn = "/nolog"
    else:
        connect_line = ""
        sqlplus_conn = f"{user}/@{datasource}"
    schema_line = f"ALTER SESSION SET CURRENT_SCHEMA = {schema};\n" if schema and schema.upper() != user.upper() else ""
    script = f"SET PAGESIZE 0 FEEDBACK OFF HEADING OFF LINESIZE 2000 TRIMSPOOL ON\n{connect_line}{schema_line}{sql}\nEXIT;\n"
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8")
    tmp.write(script); tmp.close()
    try:
        r = subprocess.run(["sqlplus", "-S", sqlplus_conn, f"@{tmp.name}"],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
    finally:
        os.unlink(tmp.name)
    if r.returncode != 0 and not r.stdout.strip():
        return f"sqlplus error: {r.stderr.strip() or 'sin salida'}"
    # Filtrar líneas de error ORA- y líneas vacías
    return [l for l in r.stdout.splitlines() if l.strip() and not l.lstrip().startswith("ORA-")]


def _in_clause_oracle(names: list[str]) -> str:
    return "IN (" + ",".join(f"'{n}'" for n in names) + ")"

def _in_clause_sqlserver(names: list[str]) -> str:
    return "IN (" + ",".join(f"'{n}'" for n in names) + ")"


def _query_oracle_schema(
    datasource: str, user: str, password: str, schema: str,
    table_filter: list[str] | None = None,
) -> tuple:
    """Retorna (col_rows_parsed, pk_rows_parsed). col_rows puede ser str de error.
    table_filter limita la consulta a una lista de tablas (útil en sync_model_tables)."""
    tbl_where = f" AND c.TABLE_NAME {_in_clause_oracle(table_filter)}" if table_filter else ""
    col_sql = (
        f"SELECT c.TABLE_NAME||'|'||c.COLUMN_NAME||'|'||c.DATA_TYPE||'|'"
        f"||NVL(TO_CHAR(c.CHAR_LENGTH),'0')||'|'||c.NULLABLE "
        f"FROM ALL_TAB_COLUMNS c WHERE c.OWNER='{schema}'{tbl_where} ORDER BY c.TABLE_NAME,c.COLUMN_ID;"
    )
    pk_where = f" AND cc.TABLE_NAME {_in_clause_oracle(table_filter)}" if table_filter else ""
    pk_sql = (
        f"SELECT cc.TABLE_NAME||'|'||cc.COLUMN_NAME "
        f"FROM ALL_CONSTRAINTS con "
        f"JOIN ALL_CONS_COLUMNS cc ON con.CONSTRAINT_NAME=cc.CONSTRAINT_NAME AND con.OWNER=cc.OWNER "
        f"WHERE con.CONSTRAINT_TYPE='P' AND con.OWNER='{schema}'{pk_where} ORDER BY cc.TABLE_NAME,cc.POSITION;"
    )
    raw_cols = _run_oracle_sql(datasource, user, password, schema, col_sql)
    if isinstance(raw_cols, str):
        return raw_cols, []
    raw_pks = _run_oracle_sql(datasource, user, password, schema, pk_sql)
    if isinstance(raw_pks, str):
        raw_pks = []  # fallo de PK no es fatal — columnas pk quedarán False

    def _parse(lines, min_parts):
        out = []
        for line in lines:
            p = line.split("|")
            if len(p) >= min_parts:
                out.append([x.strip() for x in p])
        return out

    cols = [{"table_name": p[0], "column_name": p[1], "data_type": p[2],
             "length": p[3], "nullable": p[4]} for p in _parse(raw_cols, 5)]
    pks  = [{"table_name": p[0], "column_name": p[1]} for p in _parse(raw_pks, 2)]
    return cols, pks


def _query_sqlserver_schema(
    datasource: str, schema: str,
    table_filter: list[str] | None = None,
) -> tuple:
    """Retorna (col_rows_parsed, pk_rows_parsed). col_rows puede ser str de error."""
    db_schema = schema or "dbo"
    tbl_where = f" AND TABLE_NAME {_in_clause_sqlserver(table_filter)}" if table_filter else ""
    col_sql = (
        f"SELECT TABLE_NAME+'|'+COLUMN_NAME+'|'+DATA_TYPE+'|'"
        f"+ISNULL(CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10)),'0')+'|'+IS_NULLABLE "
        f"FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='{db_schema}'{tbl_where} "
        f"ORDER BY TABLE_NAME,ORDINAL_POSITION"
    )
    pk_tbl_where = f" AND t.TABLE_NAME {_in_clause_sqlserver(table_filter)}" if table_filter else ""
    pk_sql = (
        f"SELECT t.TABLE_NAME+'|'+c.COLUMN_NAME "
        f"FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t "
        f"JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE c ON t.CONSTRAINT_NAME=c.CONSTRAINT_NAME "
        f"WHERE t.CONSTRAINT_TYPE='PRIMARY KEY' AND t.TABLE_SCHEMA='{db_schema}'{pk_tbl_where} "
        f"ORDER BY t.TABLE_NAME,c.ORDINAL_POSITION"
    )

    def _sqlcmd(sql: str):
        server, database = datasource, db_schema
        for part in datasource.split(";"):
            k, _, v = part.partition("=")
            k = k.strip().lower()
            if k in ("server", "data source"):
                server = v.strip()
            elif k in ("database", "initial catalog"):
                database = v.strip()
        r = subprocess.run(
            ["sqlcmd", "-S", server, "-d", database, "-Q", sql, "-h", "-1", "-W", "-s", "|"],
            capture_output=True, text=True, encoding="utf-8", timeout=120
        )
        if r.returncode != 0 and not r.stdout.strip():
            return f"sqlcmd error: {r.stderr.strip() or 'sin salida'}"
        return [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("-")]

    raw_cols = _sqlcmd(col_sql)
    if isinstance(raw_cols, str):
        return raw_cols, []
    raw_pks = _sqlcmd(pk_sql)
    if isinstance(raw_pks, str):
        raw_pks = []

    def _parse(lines, min_parts):
        out = []
        for line in lines:
            p = line.split("|")
            if len(p) >= min_parts:
                out.append([x.strip() for x in p])
        return out

    cols = [{"table_name": p[0], "column_name": p[1], "data_type": p[2],
             "length": p[3], "nullable": p[4]} for p in _parse(raw_cols, 5)]
    pks  = [{"table_name": p[0], "column_name": p[1]} for p in _parse(raw_pks, 2)]
    return cols, pks


def _build_table_dict(col_rows: list[dict], pk_rows: list[dict]) -> dict[str, dict]:
    """Convierte col_rows + pk_rows al formato de columnas del modelo:
    {TABLE_NAME: {COL_NAME: {type, length, nullable, pk}}}."""
    pk_set: set[tuple] = {
        (r["table_name"].upper(), r["column_name"].upper()) for r in pk_rows
    }
    db_tables: dict[str, dict] = {}
    for row in col_rows:
        tname   = row["table_name"].upper()
        colname = row["column_name"].upper()
        db_tables.setdefault(tname, {})
        try:
            length = int(row["length"]) if row["length"] and row["length"] != "0" else 0
        except ValueError:
            length = 0
        db_tables[tname][colname] = {
            "type":     row["data_type"],
            "length":   length,
            "nullable": row["nullable"].upper() in ("Y", "YES"),
            "pk":       (tname, colname) in pk_set,
        }
    return db_tables


def _sync_from_db_impl(workspace: str) -> dict:
    from datetime import datetime
    config = _get_config(workspace)
    if "error" in config:
        return config
    motor      = config.get("motor", "")
    datasource = config.get("datasource", "")
    schema     = config.get("schema", "")
    user       = config.get("user", "")
    model_path = Path(config.get("model_path", ""))
    password   = _get_db_password(workspace)

    if not model_path.name:
        return {"error": "model_path no resuelto desde XMLConfig.xml"}

    if motor == "ORACLE":
        col_rows, pk_rows = _query_oracle_schema(datasource, user, password, schema)
    elif motor == "SQLSERVER":
        col_rows, pk_rows = _query_sqlserver_schema(datasource, schema)
    else:
        return {"error": f"Motor no soportado: {motor}"}

    if isinstance(col_rows, str):
        return {"error": col_rows, "motor": motor}

    db_tables = _build_table_dict(col_rows, pk_rows)

    model = _load_model(model_path) or {"tables": {}}
    current_tables: dict = model.get("tables") or {}
    new_tables: dict = {}
    stats = {"synced": 0, "hidden": 0, "new": 0}

    for tname, tdef in current_tables.items():
        tname_up = tname.upper()
        if tname_up in db_tables:
            updated = dict(tdef)
            updated["columns"] = db_tables[tname_up]
            updated["visible"] = True
            new_tables[tname_up] = updated
            stats["synced"] += 1
        else:
            # Tabla no visible por permisos → preservar TODO, marcar visible:false
            preserved = dict(tdef)
            preserved["visible"] = False
            new_tables[tname_up] = preserved
            stats["hidden"] += 1

    for tname, cols in db_tables.items():
        if tname not in new_tables:
            new_tables[tname] = {
                "description": "",
                "columns":     cols,
                "relations":   [],
                "indexes":     [],
                "visible":     True,
            }
            stats["new"] += 1

    model["tables"]     = new_tables
    model["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _write_model_json(model_path, model)

    result = {
        "success":       True,
        "motor":         motor,
        "schema":        schema,
        "tables_synced": stats["synced"],
        "tables_new":    stats["new"],
        "tables_hidden": stats["hidden"],
        "model_path":    str(model_path),
    }
    if stats["hidden"] > 0:
        result["warning"] = (
            f"{stats['hidden']} tabla(s) no visibles por permisos (ORA-00942 ambiguo) — "
            "preservadas con visible:false. Conceder GRANTs y re-sincronizar para recuperarlas."
        )
    return result


def _sync_indexes_impl(workspace: str) -> dict:
    """Oracle only. Sincroniza ALL_INDEXES al modelo, saltando tablas con visible:false."""
    config = _get_config(workspace)
    if "error" in config:
        return config
    motor      = config.get("motor", "")
    datasource = config.get("datasource", "")
    schema     = config.get("schema", "")
    user       = config.get("user", "")
    model_path = Path(config.get("model_path", ""))
    password   = _get_db_password(workspace)

    if motor != "ORACLE":
        return {"error": f"sync_indexes solo soporta Oracle (motor={motor})"}

    model = _load_model(model_path)
    if model is None:
        return {"error": f"Modelo BD no encontrado: {model_path}. Ejecutar sync_from_db primero."}

    # Solo las tablas visibles — las hidden se conservan intactas
    visible_tables = {
        tname.upper()
        for tname, tdef in (model.get("tables") or {}).items()
        if tdef.get("visible", True) is not False
    }
    if not visible_tables:
        return {"success": True, "index_count": 0, "table_count": 0,
                "note": "Todas las tablas son visible:false — nada que sincronizar."}

    idx_sql = (
        f"SELECT i.TABLE_NAME||'|'||i.INDEX_NAME||'|'||i.UNIQUENESS||'|'||ic.COLUMN_NAME||'|'||ic.COLUMN_POSITION "
        f"FROM ALL_INDEXES i "
        f"JOIN ALL_IND_COLUMNS ic ON i.INDEX_NAME=ic.INDEX_NAME AND i.OWNER=ic.INDEX_OWNER "
        f"WHERE i.OWNER='{schema}' AND i.INDEX_TYPE='NORMAL' "
        f"ORDER BY i.TABLE_NAME,i.INDEX_NAME,ic.COLUMN_POSITION;"
    )
    raw = _run_oracle_sql(datasource, user, password, schema, idx_sql)
    if isinstance(raw, str):
        return {"error": raw}

    # Agrupar por tabla → índice → columnas
    idx_by_table: dict[str, dict] = {}
    for line in raw:
        p = line.split("|")
        if len(p) < 5:
            continue
        tname, iname, uniq, colname, pos = (x.strip() for x in p[:5])
        if tname.upper() not in visible_tables:
            continue
        idx_by_table.setdefault(tname.upper(), {})
        idx_by_table[tname.upper()].setdefault(iname, {"name": iname, "unique": uniq == "UNIQUE",
                                                         "source": "db", "columns": []})
        idx_by_table[tname.upper()][iname]["columns"].append(colname.upper())

    tables = model.get("tables") or {}
    idx_total = 0
    for tname_up, tdef in tables.items():
        if tdef.get("visible", True) is False:
            continue  # no tocar tablas ocultas
        existing = {i["name"]: i for i in (tdef.get("indexes") or []) if i.get("source") == "manual"}
        db_idxs  = [{"name": i["name"], "unique": i["unique"], "columns": i["columns"], "source": "db"}
                    for i in idx_by_table.get(tname_up, {}).values()]
        tdef["indexes"] = list(existing.values()) + db_idxs
        idx_total += len(db_idxs)

    model["tables"] = tables
    _write_model_json(model_path, model)
    return {
        "success":     True,
        "index_count": idx_total,
        "table_count": len(idx_by_table),
        "hidden_skip": len([t for t, d in tables.items() if d.get("visible") is False]),
    }


@mcp.tool(description="Parsea .sln → scope_dirs, tipo (Batch/Online), workspace. Usar al inicio de cada tarea (paso 2b). Resultado cacheado en proceso.")
def get_scope(sln_path: str) -> str:
    return json.dumps(_get_scope(sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Confirma que la .sln existe y es accesible. Usar en paso 2 del pipeline antes de parse-sln.")
def validate_solution(sln_path: str) -> str:
    return json.dumps(_run_ps("validate-solution.ps1", sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Detecta qué VCS hay bajo el workspace subiendo por las carpetas: 'svn', 'git' o 'none'. Llamar antes de cualquier tool svn_*/git_* para saber cuál usar — no hay forma de saberlo sin esto.")
def detect_vcs(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("detect-vcs.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Lee XMLConfig.xml → motor, datasource, schema, model_path. Usar antes de operaciones BD.")
def get_db_config(workspace: str) -> str:
    return json.dumps(_get_config(workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Localiza clase/método/propiedad/interfaz/enum en scope_dirs. symbol_type: class|method|property|interface|enum|any. max_results limita matches (default 50).")
def find_symbol(symbol: str, scope_dirs: str, symbol_type: str = "any", max_results: int = 50) -> str:
    raw = _run_ps("find-symbol.ps1", "-ScopeDirs", scope_dirs, "-Symbols", symbol, "-Type", symbol_type)
    if "error" in raw:
        return json.dumps(raw, ensure_ascii=False, separators=(",",":"))
    entry = (raw.get("symbols") or {}).get(symbol, {"found": False, "count": 0, "matches": []})
    matches = entry.get("matches") or []
    if len(matches) > max_results:
        entry["matches_total"] = len(matches)
        entry["matches"] = matches[:max_results]
        entry["matches_truncated"] = True
    return json.dumps(entry, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Build real → errors[], warnings[], success. El compilador se AUTODETECTA leyendo los .csproj de la solución: MSBuild de Visual Studio si hay proyectos .NET Framework/WebForms/COM, CLI dotnet si todos son SDK-style modernos — devuelve `builder` y `builder_reason`. ⛔ `builder_error` = el compilador que hacía falta no está instalado: la compilación NO se ha verificado, NO es un fallo del código. no_restore=True omite NuGet restore. builder: auto|dotnet|msbuild fuerza el compilador. max_errors limita lista en contexto (default 20).")
def compile_check(sln_path: str, no_restore: bool = True, max_errors: int = 20, builder: str = "auto") -> str:
    args = [sln_path]
    if no_restore:
        args.append("-NoRestore")
    if builder and builder != "auto":
        args.extend(["-Builder", builder])
    result = _run_ps("compile-check.ps1", *args)
    if isinstance(result.get("errors"), list) and len(result["errors"]) > max_errors:
        result["errors_total"] = len(result["errors"])
        result["errors"] = result["errors"][:max_errors]
        result["errors_truncated"] = True
    return json.dumps(result, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="dotnet test → passed/failed/failures[], skipped=true si no hay proyectos. max_failures limita detalles de fallo en contexto (default 10).")
def run_tests(sln_path: str, no_build: bool = True, max_failures: int = 10) -> str:
    args = [sln_path]
    if no_build:
        args.append("-NoBuild")
    result = _run_ps("test-runner-check.ps1", *args)
    if isinstance(result.get("failures"), list) and len(result["failures"]) > max_failures:
        result["failures_total"] = len(result["failures"])
        result["failures"] = result["failures"][:max_failures]
        result["failures_truncated"] = True
    return json.dumps(result, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Estado SVN del workspace: modificados, añadidos, eliminados, ? sin versionar. Usar para commit/diff.")
def svn_status(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("svn-diff.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Estado Git del workspace: modificados, staged, sin trackear (??), conflictos (U). Equivalente Git de svn_status — usar detect_vcs primero para saber cuál llamar.")
def git_status(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    if not _check_git_cli():
        return json.dumps({"error": "git CLI no disponible en PATH", "workspace": workspace}, ensure_ascii=False)
    return json.dumps(_run_ps("git-status.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Crea proyecto de test y lo añade a la .sln. framework: xunit|mstest|nunit. Usar cuando run_tests devuelve skipped=true.")
def create_test_project(sln_path: str, framework: str = "xunit", project_name: str = "") -> str:
    args = [sln_path, "-Framework", framework]
    if project_name:
        args += ["-ProjectName", project_name]
    return json.dumps(_run_ps("create-test-project.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="SELECT directo a BD configurada en XMLConfig (SQL Server o Oracle). SOLO SELECT. max_rows limita filas devueltas en contexto (default 200).")
def db_query(workspace: str, sql: str, max_rows: int = 200) -> str:
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT"):
        return json.dumps({"error": "Solo se permiten consultas SELECT"}, ensure_ascii=False)
    # Bloquea multi-statement: "SELECT 1; DROP TABLE x"
    # Elimina ; trailing (habitual en SQL) y cuenta ; fuera de literales de string
    sql_norm = sql.strip().rstrip(";")
    in_str, semi_count = False, 0
    for ch in sql_norm:
        if ch == "'":
            in_str = not in_str
        elif ch == ";" and not in_str:
            semi_count += 1
    if semi_count > 0:
        return json.dumps({"error": "Multi-statement SQL no permitido"}, ensure_ascii=False)

    config = _get_config(workspace)
    if "error" in config:
        return json.dumps(config, ensure_ascii=False)

    motor      = config.get("motor", "")
    datasource = config.get("datasource", "")
    schema     = config.get("schema", "")
    user       = config.get("user", "")
    password   = _get_db_password(workspace)

    if motor == "SQLSERVER":
        cmd = ["sqlcmd", "-S", datasource, "-d", schema, "-Q", sql_norm, "-h", "-1", "-W"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    elif motor == "ORACLE":
        # Credenciales en fichero SQL, no en línea de comando (no exponer en lista de procesos)
        if password:
            connect_line = f"CONNECT {user}/{password}@{datasource}\n"
            sqlplus_conn = "/nolog"
        else:
            connect_line = ""
            sqlplus_conn = f"{user}/@{datasource}"
        # El usuario de conexión puede no ser el owner de las tablas (ej. usuario de solo-consulta
        # cross-schema) — fijar el schema por default de la sesión para que SELECTs sin calificar
        # (ej. "SELECT * FROM RIDIOMA") resuelvan contra el owner real, no contra $user.
        schema_line = f"ALTER SESSION SET CURRENT_SCHEMA = {schema};\n" if schema and schema != user else ""
        script = f"SET PAGESIZE 50 FEEDBACK OFF HEADING ON\n{connect_line}{schema_line}{sql_norm};\nEXIT;\n"
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8")
        tmp.write(script); tmp.close()
        cmd = ["sqlplus", "-S", sqlplus_conn, f"@{tmp.name}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        finally:
            os.unlink(tmp.name)
    else:
        return json.dumps({"error": f"Motor no soportado: {motor}"}, ensure_ascii=False)

    rows = [r for r in (result.stdout or "").splitlines() if r.strip() and not r.startswith("---")]
    truncated = len(rows) > max_rows
    return json.dumps({
        "success": result.returncode == 0,
        "motor": motor,
        "rows": rows[:max_rows],
        "row_count": len(rows),
        "rows_truncated": truncated,
        "error": (result.stderr or "").strip() if result.returncode != 0 else None,
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Compara model.json con esquema real BD → tablas nuevas/eliminadas, columnas añadidas/eliminadas y columnas con tipo o nullable distinto (modified_columns). Usar para detectar drift completo.")
def compare_model(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("compare-model.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Extrae controles AIS de .aspx con textos para registrar en RIDIOMA y RCONTROLES.")
def scan_aspx(sln_path: str) -> str:
    return json.dumps(_run_ps("scan-aspx.ps1", "-SlnPath", sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Registra ejecución del pipeline en executions/history.json. status: success|fail|partial. Llamar al final del pipeline.")
def log_execution(workspace: str, solution: str, task: str, status: str = "success", agents: str = "") -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("log-execution.ps1", workspace, solution, task, "-Status", status, "-Agents", agents), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Scripts SQL migración desde drift modelo→BD: CREATE TABLE+PK+FK+INDEX (tablas nuevas), ALTER TABLE ADD (columnas nuevas), ALTER TABLE MODIFY (tipo/nullable distinto), DROP COLUMN comentado (columnas en BD no en modelo).")
def generate_migration(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("generate-migration.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Historial commits SVN → revisión, autor, fecha, mensaje. solution filtra por texto en mensaje.")
def svn_log(workspace: str, solution: str = "", limit: int = 10) -> str:
    if not _check_svn_cli():
        return json.dumps({
            "error": "svn CLI no disponible en PATH",
            "fallback": "Ver historial en TortoiseSVN → clic derecho en workspace → Show Log",
            "workspace": workspace,
        }, ensure_ascii=False)
    args = [workspace]
    if solution:
        args += ["-Solution", solution]
    args += ["-Limit", str(limit)]
    return json.dumps(_run_ps("svn-log.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Historial commits Git → revision (hash corto), autor, fecha, mensaje. solution filtra por texto en mensaje. Equivalente Git de svn_log.")
def git_log(workspace: str, solution: str = "", limit: int = 10) -> str:
    if not _check_git_cli():
        return json.dumps({"error": "git CLI no disponible en PATH", "workspace": workspace}, ensure_ascii=False)
    args = [workspace]
    if solution:
        args += ["-Solution", solution]
    args += ["-Limit", str(limit)]
    return json.dumps(_run_ps("git-log.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Busca en docs funcionales secciones relacionadas con keyword → archivo, heading, línea, fragmento.")
def find_doc_section(workspace: str, keyword: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("find-doc-section.ps1", workspace, keyword), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Diff de revisiones SVN (coma-separadas). summary_only=True → [{file, op, +lines, -lines, symbols[]}] sin código (~500 tokens). summary_only=False → combined_diff completo (~4K tokens). Usar full para rs-validar-req, summary para planificación/historial.")
def svn_diff_revision(workspace: str, revisions: str, max_diff_chars: int = 15000, summary_only: bool = False) -> str:
    if not _check_svn_cli():
        return json.dumps({
            "error": "svn CLI no disponible en PATH",
            "fallback": "Ver diff en TortoiseSVN → Show Log → seleccionar revisión → Show Changes",
            "revisions": revisions,
            "workspace": workspace,
        }, ensure_ascii=False)
    raw = _run_ps("svn-diff-revision.ps1", workspace, revisions, "-MaxDiffChars", str(max_diff_chars))
    if not summary_only:
        return json.dumps(raw, ensure_ascii=False, separators=(",",":"))

    # Generar resumen estructurado sin código
    import re as _re
    diff_text = raw.get("combined_diff") or ""
    files_changed = raw.get("files_changed", [])
    file_stats: dict = {}
    current_file = None
    for line in diff_text.splitlines():
        m = _re.match(r'^Index:\s+(.+)', line)
        if m:
            current_file = m.group(1).strip()
            file_stats.setdefault(current_file, {"added": 0, "removed": 0, "op": "M", "symbols": []})
            continue
        if current_file is None:
            continue
        if line.startswith('+') and not line.startswith('+++'):
            file_stats[current_file]["added"] += 1
            sym = _re.search(r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:override\s+)?(?:async\s+)?(?:\w+\s+)+(\w+)\s*[\(\{]', line)
            if sym and sym.group(1) not in file_stats[current_file]["symbols"]:
                file_stats[current_file]["symbols"].append(sym.group(1))
        elif line.startswith('-') and not line.startswith('---'):
            file_stats[current_file]["removed"] += 1

    summary = [
        {"file": f, "op": s["op"], "+lines": s["added"], "-lines": s["removed"], "symbols": s["symbols"][:10]}
        for f, s in file_stats.items()
    ]
    return json.dumps({
        "revisions": revisions,
        "files_changed": len(summary),
        "summary": summary,
        "note": "summary_only=True — usar summary_only=False para obtener código completo",
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Diff de commits Git (hashes coma-separados). summary_only=True → [{file, op, +lines, -lines, symbols[]}] sin código (~500 tokens). summary_only=False → combined_diff completo (~4K tokens). Equivalente Git de svn_diff_revision — usar full para rs-validar-req, summary para planificación/historial.")
def git_diff_revision(workspace: str, revisions: str, max_diff_chars: int = 15000, summary_only: bool = False) -> str:
    if not _check_git_cli():
        return json.dumps({"error": "git CLI no disponible en PATH", "revisions": revisions, "workspace": workspace}, ensure_ascii=False)
    raw = _run_ps("git-diff-revision.ps1", workspace, revisions, "-MaxDiffChars", str(max_diff_chars))
    if not summary_only:
        return json.dumps(raw, ensure_ascii=False, separators=(",",":"))

    # Generar resumen estructurado sin código — mismo post-proceso que svn_diff_revision,
    # pero el marcador de "nuevo fichero" en el diff es "diff --git a/x b/x", no "Index:".
    import re as _re
    diff_text = raw.get("combined_diff") or ""
    file_stats: dict = {}
    current_file = None
    for line in diff_text.splitlines():
        m = _re.match(r'^diff --git a/.+ b/(.+)', line)
        if m:
            current_file = m.group(1).strip()
            file_stats.setdefault(current_file, {"added": 0, "removed": 0, "op": "M", "symbols": []})
            continue
        if current_file is None:
            continue
        if line.startswith('+') and not line.startswith('+++'):
            file_stats[current_file]["added"] += 1
            sym = _re.search(r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:override\s+)?(?:async\s+)?(?:\w+\s+)+(\w+)\s*[\(\{]', line)
            if sym and sym.group(1) not in file_stats[current_file]["symbols"]:
                file_stats[current_file]["symbols"].append(sym.group(1))
        elif line.startswith('-') and not line.startswith('---'):
            file_stats[current_file]["removed"] += 1

    summary = [
        {"file": f, "op": s["op"], "+lines": s["added"], "-lines": s["removed"], "symbols": s["symbols"][:10]}
        for f, s in file_stats.items()
    ]
    return json.dumps({
        "revisions": revisions,
        "files_changed": len(summary),
        "summary": summary,
        "note": "summary_only=True — usar summary_only=False para obtener código completo",
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Añade ficheros ? a SVN: CLI → TortoiseProc → instrucciones manuales. files vacío = auto-detectar todos los ? del workspace.")
def svn_add(workspace: str, files: str = "") -> str:
    args = [workspace]
    if files:
        args += ["-Files", files]
    return json.dumps(_run_ps("svn-add.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Añade ficheros ?? (sin trackear) a Git: CLI → TortoiseGitProc → instrucciones manuales. files vacío = auto-detectar todos los ?? del workspace. Equivalente Git de svn_add.")
def git_add(workspace: str, files: str = "") -> str:
    args = [workspace]
    if files:
        args += ["-Files", files]
    return json.dumps(_run_ps("git-add.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Escanea código → SQL injection, credenciales hardcodeadas, XSS, input sin validar. Findings con severidad y archivo:línea.")
def security_scan(sln_path: str) -> str:
    return json.dumps(_run_ps("security-scan.ps1", sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description=(
    "Actualiza tablas específicas de model.json desde BD real. Llamar post-migración. "
    "tables = coma-separadas. Escritura canónica (UTF-8 BOM, CRLF, indent=2)."
))
def sync_model_tables(workspace: str, tables: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config:
        return json.dumps(config, ensure_ascii=False, separators=(",",":"))
    motor      = config.get("motor", "")
    datasource = config.get("datasource", "")
    schema     = config.get("schema", "")
    user       = config.get("user", "")
    model_path = Path(config.get("model_path", ""))
    password   = _get_db_password(workspace)
    table_list = [t.strip().upper() for t in tables.split(",") if t.strip()]
    if not table_list:
        return json.dumps({"error": "No tables specified"}, ensure_ascii=False)
    if motor == "ORACLE":
        col_rows, pk_rows = _query_oracle_schema(datasource, user, password, schema, table_filter=table_list)
    elif motor == "SQLSERVER":
        col_rows, pk_rows = _query_sqlserver_schema(datasource, schema, table_filter=table_list)
    else:
        return json.dumps({"error": f"Motor no soportado: {motor}"}, ensure_ascii=False)
    if isinstance(col_rows, str):
        return json.dumps({"error": col_rows}, ensure_ascii=False, separators=(",",":"))
    db_tables = _build_table_dict(col_rows, pk_rows)
    model = _load_model(model_path) or {"tables": {}}
    tables_dict: dict = model.get("tables") or {}
    updated, not_in_db = [], []
    for tname in table_list:
        if tname in db_tables:
            existing = dict(tables_dict.get(tname, {}))
            existing["columns"] = db_tables[tname]
            existing["visible"] = True
            tables_dict[tname] = existing
            updated.append(tname)
        else:
            not_in_db.append(tname)
    model["tables"] = tables_dict
    _write_model_json(model_path, model)
    result: dict = {"success": True, "updated": updated, "not_found_in_db": not_in_db,
                    "model_path": str(model_path)}
    if not_in_db:
        result["note"] = f"{len(not_in_db)} tabla(s) no visibles en BD — no modificadas"
    return json.dumps(result, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Mapa dependencias entre soluciones: proyectos compartidos (impacto), conflictos versión NuGet.")
def map_dependencies(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("map-dependencies.ps1", workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Valida el entorno de trabajo: XMLConfig, ruta AIS, dotnet SDK, SVN, modelo BD, docs agentic. Devuelve checks[] con status OK/WARN/FAIL.")
def check_env(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("check-env.ps1", workspace, _proyecto(workspace)), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Genera DDL SQL desde el modelo BD → escribe C:\\AIS\\<proyecto>\\scripts\\<proyecto>-ddl-<motor>.sql. Devuelve ruta y nº líneas — el SQL no entra en contexto.")
def generate_sql(workspace: str, motor: str = "") -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    args = [workspace, "-Proyecto", _proyecto(workspace)]
    if motor:
        args += ["-Motor", motor]
    return json.dumps(_run_ps("generate-sql.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Exporta modelo BD a Oracle Data Modeler (.dmd) → escribe BD/<proyecto>.dmd. Devuelve ruta y nº tablas — el XML no entra en contexto.")
def export_dmd(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("export-dmd.ps1", workspace, "-Proyecto", _proyecto(workspace)), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description=(
    "Sincroniza tablas y columnas del modelo BD desde el esquema real. "
    "Tablas no visibles por permisos Oracle se marcan visible:false y se PRESERVAN (no se borran). "
    "Tablas nuevas en BD se añaden. No toca relaciones ni índices."
))
def sync_from_db(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_sync_from_db_impl(workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description=(
    "Sincroniza índices Oracle (ALL_INDEXES) al modelo BD JSON. "
    "Reemplaza source='db', preserva source='manual'. Solo Oracle. "
    "Salta tablas con visible:false — sus índices se conservan tal cual."
))
def sync_indexes(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_sync_indexes_impl(workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Infiere relaciones entre tablas analizando código DALC (JOINs, WHERE cruzados). Actualiza el modelo JSON. sln_path opcional para limitar scope.")
def analyze_dalc(workspace: str, sln_path: str = "") -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    args = [workspace, _proyecto(workspace)]
    if sln_path:
        args += ["-SolutionPath", sln_path]
    return json.dumps(_run_ps("analyze-dalc.ps1", *args), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Genera ERD HTML del modelo BD y lo abre en el navegador. Devuelve ruta y nº de tablas — no carga el modelo en contexto.")
def render_erd(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("render-erd.ps1", workspace, "-Proyecto", _proyecto(workspace)), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Esquema completo (columnas con tipo/nullable/pk, relaciones, índices) de tablas específicas del modelo BD. Evita cargar model.json completo (~180K tokens). tables = coma-separadas.")
def get_table_schema(workspace: str, tables: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config: return json.dumps(config, ensure_ascii=False)

    model_path = Path(config.get("model_path", ""))
    table_list = [t.strip().upper() for t in tables.split(",") if t.strip()]

    model = _load_model(model_path)
    if model is None:
        return json.dumps({"error": f"Modelo BD no encontrado: {model_path}"}, ensure_ascii=False)

    raw = model.get("tables", {})
    if isinstance(raw, dict):
        index = {k.upper(): v for k, v in raw.items()}
    else:
        index = {(t.get("name") or t.get("tableName", "?")).upper(): t for t in raw}

    result: dict = {}
    not_found: list = []
    for tname in table_list:
        tdef = index.get(tname)
        if not tdef:
            not_found.append(tname)
            continue
        cols = tdef.get("columns", {})
        if isinstance(cols, dict):
            col_list = [{"name": k, **v} for k, v in cols.items()]
        else:
            col_list = list(cols)
        result[tname] = {
            "description": tdef.get("description", ""),
            "visible": tdef.get("visible", True),
            "columns": col_list,
            "relations": tdef.get("relations", []),
            "indexes": tdef.get("indexes", []),
        }

    return json.dumps({
        "workspace": workspace,
        "motor": config.get("motor"),
        "schema": config.get("schema"),
        "tables": result,
        "not_found": not_found,
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Localiza N símbolos en una sola llamada (equivale a N×find_symbol). symbols = coma-separados. Usar en impact analysis y refactor para evitar N round-trips.")
def batch_find_symbols(symbols: str, scope_dirs: str, symbol_type: str = "any", max_per_symbol: int = 20) -> str:
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    # Una sola llamada al hook — el truncado max_per_symbol se aplica en Python
    raw = _run_ps("find-symbol.ps1", "-ScopeDirs", scope_dirs, "-Symbols", symbols, "-Type", symbol_type)
    if "error" in raw:
        return json.dumps(raw, ensure_ascii=False, separators=(",",":"))
    sym_data = raw.get("symbols") or {}
    out: dict = {}
    for sym in symbol_list:
        entry = sym_data.get(sym, {"found": False, "count": 0, "matches": []})
        matches = entry.get("matches") or []
        if len(matches) > max_per_symbol:
            matches = matches[:max_per_symbol]
        out[sym] = {"found": entry.get("found", False), "count": entry.get("count", 0), "matches": matches}
    return json.dumps({"symbols": out, "total_symbols": len(symbol_list)}, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Busca patrón regex en archivos del scope de una solución. Reemplaza 3-8× Grep con garantía de scope_dirs. Devuelve [{file,line,match,context}].")
def search_code(workspace: str, sln_path: str, pattern: str, file_glob: str = "*.cs", context_lines: int = 2, max_results: int = 50) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(
        _run_ps("search-code.ps1", workspace, sln_path, pattern, "-Glob", file_glob, "-Context", str(context_lines), "-MaxResults", str(max_results)),
        ensure_ascii=False, separators=(",",":")
    )


@mcp.tool(description="Compara solo tablas específicas del modelo con BD real. Usar post-migración cuando se conocen las tablas modificadas. Evita comparar las 362 tablas completas. tables = coma-separadas.")
def compare_model_tables(workspace: str, tables: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("compare-model.ps1", workspace, "-Tables", tables), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Índice ligero del modelo BD: {TABLA: [COL1, COL2, ...]}. ~15K tokens vs 180K del modelo completo. Usar para impact analysis, búsqueda de columnas, verificar qué tablas existen.")
def get_model_index(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config: return json.dumps(config, ensure_ascii=False)

    model = _load_model(Path(config.get("model_path", "")))
    if model is None:
        return json.dumps({"error": "Modelo BD no encontrado"}, ensure_ascii=False)

    raw = model.get("tables", {})
    items = raw.items() if isinstance(raw, dict) else \
            [(t.get("name", t.get("tableName", "?")), t) for t in raw]

    index = {}
    for name, tdef in items:
        cols = tdef.get("columns", {})
        col_names = list(cols.keys()) if isinstance(cols, dict) else \
                    [c.get("name", c.get("columnName", "?")) for c in cols]
        index[name] = col_names

    return json.dumps({
        "workspace": workspace,
        "table_count": len(index),
        "index": index,
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Busca keyword en nombres de tablas, columnas y descripciones del modelo BD. Alternativa a cargar model.json completo cuando se busca dónde vive un concepto. Devuelve tablas/columnas que hacen match.")
def search_model(workspace: str, keyword: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config: return json.dumps(config, ensure_ascii=False)

    model = _load_model(Path(config.get("model_path", "")))
    if model is None:
        return json.dumps({"error": "Modelo BD no encontrado"}, ensure_ascii=False)

    kw = keyword.upper()
    raw = model.get("tables", {})
    items = raw.items() if isinstance(raw, dict) else \
            [(t.get("name", t.get("tableName", "?")), t) for t in raw]

    results = []
    for tname, tdef in items:
        matching_cols = []
        cols = tdef.get("columns", {})
        col_items = cols.items() if isinstance(cols, dict) else \
                    [(c.get("name", "?"), c) for c in cols]
        for cname, cdef in col_items:
            if kw in cname.upper() or kw in (cdef.get("description") or "").upper():
                matching_cols.append({"name": cname, "type": cdef.get("type", "")})

        hit_table = kw in tname.upper() or kw in (tdef.get("description") or "").upper()
        if hit_table or matching_cols:
            results.append({
                "table":            tname,
                "match_table_name": kw in tname.upper(),
                "description":      tdef.get("description", ""),
                "matching_columns": matching_cols,
            })

    return json.dumps({
        "keyword":        keyword,
        "tables_matched": len(results),
        "results":        results,
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Health check: verifica que el servidor MCP está activo y devuelve hooks_dir, nº hooks disponibles y versión Python.")
def ping() -> str:
    import sys as _sys
    hooks = list(HOOKS_DIR.glob("*.ps1")) if HOOKS_DIR.exists() else []
    return json.dumps({
        "ok": True,
        "hooks_dir": str(HOOKS_DIR),
        "hooks_found": len(hooks),
        "svn_cli": _check_svn_cli(),
        "git_cli": _check_git_cli(),
        "python": _sys.version.split()[0],
    }, ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Parsea un log de errores web (NLog/log4net, ELMAH XML, formato AgendaWeb AIS: 'Error: (dd/MM/yyyy H:mm) - Codigo error: ... Descripción error: ...' y volcado de stack .NET) y agrupa las ocurrencias por FIRMA (excepción o código ORA-xxxxx/Codigo error + frame de código propio + mensaje normalizado) → [{hash,exception,origin,pantalla,message,count,first_seen,last_seen,files,samples}] ordenado por count. Devuelve solo el agregado — el log crudo nunca entra en contexto. format_detected indica el formato reconocido. PII: literales SQL entre comillas simples redactados ('...' → '<val>'). path = fichero o carpeta.")
def parse_web_log(path: str, glob: str = "*.log", desde: str = "", niveles: str = "ERROR,FATAL",
                  max_signatures: int = 30, samples: int = 2) -> str:
    args = ["-Path", path, "-Glob", glob, "-Niveles", niveles,
            "-MaxSignatures", str(max_signatures), "-Samples", str(samples)]
    if desde:
        args += ["-Desde", desde]
    return json.dumps(_run_ps("parse-weblog.ps1", *args), ensure_ascii=False, separators=(",",":"))


if __name__ == "__main__":
    mcp.run(transport="stdio")

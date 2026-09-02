"""
orchestrator-workspace MCP server — herramientas nativas para soluciones ScacsWeb.
La mayoría de tools llaman a un hook PowerShell (`hooks/*.ps1`); las tools BD/modelo
son nativas Python (reutilizan los helpers de esquema de este módulo).
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HOOKS_DIR  = Path(__file__).parent.parent / "hooks"
CACHE_DIR  = Path.home() / ".claude" / "cache" / "rs-models"

# Hooks aún no implementados en este build: fallback que el agente debe usar en su lugar.
# (Las tools BD/modelo NO están aquí — son nativas Python, no llaman a _run_ps.)
# Al implementar el hook correspondiente, quitarlo de este dict.
_HOOK_FALLBACKS = {
    "search-code.ps1":      "Usar Grep/Glob restringido a scope_dirs (get_scope).",
    "scan-aspx.ps1":        "Releer el diff .aspx/.aspx.cs para la lista de controles (ver agents/core.md).",
    "find-doc-section.ps1": "Grep del keyword en docs/scacs/.",
    "map-dependencies.ps1": "Análisis de dependencias entre soluciones no disponible (fase 3).",
    "security-scan.ps1":    "Scan de seguridad no implementado (fase 3). Revisar SQLi / credenciales / XSS en el diff a mano.",
    "git-status.ps1":       "Los repos ScacsWeb usan SVN: usar svn_status. Para Git real, invocar el CLI git directamente.",
    "git-log.ps1":          "Los repos ScacsWeb usan SVN: usar svn_log. Para Git real, invocar el CLI git directamente.",
    "git-add.ps1":          "Los repos ScacsWeb usan SVN: usar svn_add. Para Git real, invocar el CLI git directamente.",
}

mcp = FastMCP("orchestrator-workspace")

_model_cache:  dict[str, tuple[float, dict]] = {}  # path → (mtime, model) — en proceso
_config_cache: dict[str, dict]               = {}  # workspace → config    — en proceso
_scope_cache:  dict[str, tuple[float, dict]] = {}  # sln_path → (mtime, scope) — en proceso
_svn_cli: bool | None = None                        # None = no comprobado aún
_git_cli: bool | None = None                        # None = no comprobado aún


def _get_config(workspace: str) -> dict:
    """Config BD del workspace SIN password — motor/datasource/schema/user/catalog/model_path.
    Fuente canónica: C:\\AIS\\<Sln>\\bin\\Settings\\Settings.xml (ver _settings_conn).
    Cache en proceso — evita reparsear en cada tool call."""
    if workspace not in _config_cache:
        c = _settings_conn(workspace)
        if "error" in c:
            return {"error": c["error"]}  # no cachear — la solución puede publicarse después
        else:
            _config_cache[workspace] = {
                "motor":         c["motor"],
                "datasource":    c["datasource"],
                "schema":        c["schema"],
                "user":          c["user"],
                "catalog":       c.get("catalog", ""),
                "model_path":    c["model_path"],
                "sln":           c["sln"],
                "environments":  c.get("environments", 1),
                "settings_path": c.get("settings_path", ""),
            }
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
    """Nombre de proyecto AIS = nombre del .sln (carpeta C:\\AIS\\<Sln>\\). Fallback:
    carpeta anterior a trunk/ para layouts sin .sln resoluble."""
    return _resolve_sln_name(workspace) or Path(workspace).parent.name


# ---------------------------------------------------------------------------
# Conexión BD — fuente canónica: C:\AIS\<Sln>\bin\Settings\Settings.xml
#   <SETTINGS><BBDD><oledbconnectionstring value="User Id=..;Password=..;Data Source=.."/>
#   index 0 = entorno por defecto (DEV/TEST); 1+ = PRE/PROD si están definidos.
# ---------------------------------------------------------------------------

_conn_cache: dict[tuple, dict] = {}  # (workspace, index) → conexión parseada


def _clean_env() -> dict:
    """Env sin variables de proxy — el Instant Client de Oracle aborta con SP2-1502 /
    'HTTP proxy Error 46' si http_proxy apunta a un proxy inaccesible (obs. máquina dev)."""
    e = dict(os.environ)
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        e.pop(k, None)
    return e


def _resolve_sln_name(workspace: str) -> str | None:
    """Nombre del .sln (sin extensión) del workspace ScacsWeb — es también el nombre de la
    carpeta de publicación en C:\\AIS\\<Sln>\\. Busca en: raíz de trunk, dotNet/Web,
    dotNet/Batch/<Nombre>/."""
    ws = Path(workspace)
    for base in (ws, ws / "dotNet" / "Web"):
        if not base.is_dir():
            continue
        slns = sorted(base.glob("*.sln"))
        if len(slns) == 1:
            return slns[0].stem
        if len(slns) > 1:
            for s in slns:
                if (Path("C:/AIS") / s.stem).is_dir():
                    return s.stem
            return slns[0].stem
    batch = ws / "dotNet" / "Batch"
    if batch.is_dir():
        cand = [d.name for d in batch.iterdir() if d.is_dir() and (d / f"{d.name}.sln").is_file()]
        if len(cand) == 1:
            return cand[0]
    return None


def _split_conn(cs: str) -> list[str]:
    """Parte una connection string por ';'. Los descriptores Oracle (DESCRIPTION=...) no
    contienen ';', así que el split simple es seguro para los formatos ScacsWeb."""
    return [p.strip() for p in cs.split(";") if p.strip()]


def _parse_conn_string(cs: str) -> dict:
    """oledbconnectionstring .NET → {motor, datasource, user, password, catalog, schema}."""
    kv: dict[str, str] = {}
    for part in _split_conn(cs):
        k, _, v = part.partition("=")
        kv[k.strip().lower()] = v.strip()
    datasource = kv.get("data source") or kv.get("server") or ""
    user       = kv.get("user id") or kv.get("user") or kv.get("uid") or ""
    password   = kv.get("password") or kv.get("pwd") or ""
    catalog    = kv.get("initial catalog") or kv.get("database") or ""
    ds_up = datasource.upper()
    is_oracle = ("(DESCRIPTION=" in ds_up) or ("(PROTOCOL=" in ds_up) \
                or ("SERVICE_NAME" in ds_up) or ("(SID=" in ds_up)
    motor  = "ORACLE" if is_oracle else "SQLSERVER"
    schema = (user if motor == "ORACLE" else (catalog or "dbo")).upper()
    return {"motor": motor, "datasource": datasource, "user": user,
            "password": password, "catalog": catalog, "schema": schema}


def _legacy_xmlconfig(workspace: str) -> dict:
    """Compat: workspaces antiguos con docs/XMLConfig.xml en vez de Settings.xml publicado."""
    xml_path = Path(workspace) / "docs" / "XMLConfig.xml"
    try:
        root = ET.parse(xml_path).getroot()
    except Exception as e:
        return {"error": f"XMLConfig.xml ilegible: {e}"}
    db = root.find(".//DataBase")
    if db is not None and db.get("connectionString"):
        c = _parse_conn_string(db.get("connectionString"))
    else:
        con = root.find(".//Conexion")
        ds = (con.findtext("DataSource") if con is not None else "") or ""
        c = _parse_conn_string(ds)
    if db is not None and not c["password"]:
        c["password"] = db.get("password", "") or ""
    return c


def _settings_conn(workspace: str, index: int = 0) -> dict:
    """Fuente canónica de conexión BD del workspace. Devuelve
    {motor, datasource, user, password, catalog, schema, sln, model_path, environments}
    o {'error': ...}. Incluye 'password' — NO exponer el dict entero al agente
    (usar _get_config, que lo omite). Cache por (workspace, index)."""
    key = (workspace, index)
    if key in _conn_cache:
        return _conn_cache[key]

    sln = _resolve_sln_name(workspace)
    if not sln:
        result: dict = {"error": "No se pudo resolver el .sln del workspace "
                                 "(esperado 1 .sln en la raíz de trunk, dotNet/Web o dotNet/Batch/<Nombre>)."}
    else:
        settings = Path("C:/AIS") / sln / "bin" / "Settings" / "Settings.xml"
        if settings.is_file():
            try:
                root = ET.parse(settings).getroot()
                nodes = root.findall(".//BBDD/oledbconnectionstring") or \
                        root.findall(".//oledbconnectionstring")
                conns = [n.get("value", "") for n in nodes
                         if n.get("value") and "=" in n.get("value", "")]
                if not conns:
                    result = {"error": f"Settings.xml sin oledbconnectionstring utilizable "
                                       f"(¿cifrada?): {settings}"}
                else:
                    idx = index if 0 <= index < len(conns) else 0
                    result = _parse_conn_string(conns[idx])
                    result["environments"]  = len(conns)
                    result["settings_path"] = str(settings)
            except Exception as e:
                result = {"error": f"Settings.xml ilegible ({settings}): {e}"}
        elif (Path(workspace) / "docs" / "XMLConfig.xml").is_file():
            result = _legacy_xmlconfig(workspace)
        else:
            result = {"error": f"Conexión BD no resuelta: falta {settings} "
                               "(¿solución sin publicar?) y no hay docs/XMLConfig.xml legacy."}

    if "error" in result:
        return result  # no cachear errores — la solución puede publicarse después
    result["sln"]        = sln
    result["model_path"] = str(Path(workspace) / "BD" / f"{sln}-model.json")
    _conn_cache[key] = result
    return result


def _get_db_password(workspace: str) -> str:
    """Password de la conexión por defecto (Settings.xml). '' si no se resuelve."""
    return _settings_conn(workspace).get("password", "") or ""


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
                           capture_output=True, text=True, encoding="utf-8", timeout=120,
                           env=_clean_env())
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
    server: str, database: str,
    table_filter: list[str] | None = None,
    user: str = "", password: str = "", table_schema: str = "dbo",
) -> tuple:
    """Retorna (col_rows_parsed, pk_rows_parsed). col_rows puede ser str de error.
    server = host[\\instancia] (campo 'Data Source' del connstring), database = 'Initial Catalog'.
    user/password → auth SQL (-U/-P); vacío → auth Windows integrada."""
    db_schema = table_schema or "dbo"
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
        # Compat: si 'server' viniera como connstring completa (workspaces legacy), extraer campos.
        srv, db = server, (database or db_schema)
        if ";" in server or "=" in server:
            for part in server.split(";"):
                k, _, v = part.partition("=")
                k = k.strip().lower()
                if k in ("server", "data source"):
                    srv = v.strip()
                elif k in ("database", "initial catalog"):
                    db = v.strip()
        cmd = ["sqlcmd", "-S", srv, "-d", db, "-Q", sql, "-h", "-1", "-W", "-s", "|"]
        if user:
            cmd += ["-U", user, "-P", password]
        r = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", timeout=120, env=_clean_env()
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
    catalog    = config.get("catalog", "")
    model_path = Path(config.get("model_path", ""))
    password   = _get_db_password(workspace)

    if not model_path.name:
        return {"error": "model_path no resuelto (Settings.xml)"}

    if motor == "ORACLE":
        col_rows, pk_rows = _query_oracle_schema(datasource, user, password, schema)
    elif motor == "SQLSERVER":
        col_rows, pk_rows = _query_sqlserver_schema(datasource, catalog or schema,
                                                    user=user, password=password)
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


# ---------------------------------------------------------------------------
# Helpers BD/ERD: config, normalización de columnas, DDL SCACS
#   SCACS no tiene "motor" como argumento — el dialecto sale SIEMPRE de
#   XMLConfig.xml (get_db_config). Un proyecto = una BD.
# ---------------------------------------------------------------------------

def _bd_ctx(workspace: str, index: int = 0) -> dict:
    """Contexto BD del workspace: motor, datasource, schema, user, catalog, model_path, password.
    index 0 = entorno por defecto (DEV/TEST); 1+ = PRE/PROD de Settings.xml.
    Fuente: Settings.xml publicado (_settings_conn). Devuelve {'error': ...} si falta configuración."""
    c = _settings_conn(workspace, index)
    if "error" in c:
        return {"error": c["error"]}
    mp = c.get("model_path", "")
    return {
        "motor":      (c.get("motor") or "").upper(),
        "datasource": c.get("datasource", ""),
        "schema":     c.get("schema", ""),
        "user":       c.get("user", ""),
        "catalog":    c.get("catalog", ""),
        "model_path": Path(mp) if mp else None,
        "password":   c.get("password", ""),
    }


def _scripts_dir(workspace: str) -> Path:
    """C:\\AIS\\<Sln>\\scripts — destino canónico SCACS de todo .sql generado."""
    return Path("C:/AIS") / (_resolve_sln_name(workspace) or _proyecto(workspace)) / "scripts"


_TYPE_RE = re.compile(
    r"^\s*([A-Za-z0-9_ ]+?)\s*(?:\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?(?:CHAR|BYTE)?\s*\))?\s*$", re.I
)


def _norm_col(col: dict) -> dict:
    """Normaliza una columna del modelo. Acepta {'type':'NUMBER(10)'} y {'type':'NUMBER','length':10}."""
    raw = str(col.get("type", "")).strip()
    m = _TYPE_RE.match(raw)
    base   = (m.group(1).strip().upper() if m else raw.upper())
    length = int(m.group(2)) if (m and m.group(2)) else int(col.get("length") or 0)
    scale  = int(m.group(3)) if (m and m.group(3)) else int(col.get("scale") or 0)
    return {
        "type_base": base,
        "length":    length,
        "scale":     scale,
        "nullable":  bool(col.get("nullable", True)),
        "pk":        bool(col.get("pk", False)),
    }


def _ddl_type(nc: dict, engine: str) -> str:
    """Tipo DDL en el dialecto del proyecto. Oracle: VARCHAR2(n CHAR) OBLIGATORIO (references/bd.md)."""
    base, length, scale = nc["type_base"], nc["length"], nc["scale"]
    if engine == "ORACLE":
        if base in ("VARCHAR2", "VARCHAR", "NVARCHAR", "NVARCHAR2", "STRING"):
            return f"VARCHAR2({length or 4000} CHAR)"
        if base in ("CHAR", "NCHAR"):
            return f"CHAR({length or 1} CHAR)"
        if base in ("NUMBER", "NUMERIC", "DECIMAL"):
            if length and scale:
                return f"NUMBER({length},{scale})"
            return f"NUMBER({length})" if length else "NUMBER"
        if base in ("INT", "INTEGER", "SMALLINT", "BIGINT"):
            return "NUMBER(10)"
        if base in ("DATE", "DATETIME", "SMALLDATETIME"):
            return "DATE"
        if base in ("TIMESTAMP", "DATETIME2"):
            return "TIMESTAMP"
        if base in ("CLOB", "NCLOB", "TEXT", "NTEXT"):
            return "CLOB"
        if base in ("BLOB", "RAW", "VARBINARY", "IMAGE"):
            return "BLOB"
        if base in ("FLOAT", "REAL", "DOUBLE"):
            return "BINARY_DOUBLE"
        return f"{base}({length})" if length else base
    # SQLSERVER
    if base in ("VARCHAR2", "VARCHAR", "NVARCHAR", "NVARCHAR2", "STRING"):
        return f"NVARCHAR({length or 'MAX'})"
    if base in ("CHAR", "NCHAR"):
        return f"NCHAR({length or 1})"
    if base in ("NUMBER", "NUMERIC", "DECIMAL"):
        if length and scale:
            return f"DECIMAL({length},{scale})"
        if length and length <= 9:
            return "INT"
        if length:
            return "BIGINT"
        return "DECIMAL(18,2)"
    if base in ("INT", "INTEGER"):
        return "INT"
    if base in ("SMALLINT",):
        return "SMALLINT"
    if base in ("BIGINT",):
        return "BIGINT"
    if base in ("DATE",):
        return "DATE"
    if base in ("DATETIME", "TIMESTAMP", "DATETIME2", "SMALLDATETIME"):
        return "DATETIME2"
    if base in ("CLOB", "NCLOB", "TEXT", "NTEXT"):
        return "NVARCHAR(MAX)"
    if base in ("BLOB", "RAW", "VARBINARY", "IMAGE"):
        return "VARBINARY(MAX)"
    if base in ("FLOAT", "REAL", "DOUBLE"):
        return "FLOAT"
    return f"{base}({length})" if length else base


def _model_tables(model: dict, include_hidden: bool = False) -> dict:
    """{TABLA_UPPER: tdef} del modelo. Por defecto omite visible:false (regla references/bd.md)."""
    out = {}
    for tname, tdef in (model.get("tables") or {}).items():
        if not include_hidden and tdef.get("visible", True) is False:
            continue
        out[tname.upper()] = tdef
    return out


def _model_engine(model: dict, ctx: dict) -> str:
    return (model.get("engine") or ctx.get("motor") or "").upper()


# ---------------------------------------------------------------------------
# compare_model / generate_migration / generate_sql / render_erd / analyze_dalc / export_dmd
# ---------------------------------------------------------------------------

def _compare_model_impl(workspace: str, tables: str = "") -> dict:
    ctx = _bd_ctx(workspace)
    if "error" in ctx:
        return {"success": False, "error": ctx["error"]}
    if not ctx["model_path"]:
        return {"success": False, "error": "model_path no configurado en XMLConfig.xml"}
    model = _load_model(ctx["model_path"])
    if model is None:
        return {"success": False, "error": f"Modelo BD no encontrado: {ctx['model_path']}. Ejecutar sync_from_db primero."}
    engine = _model_engine(model, ctx)

    table_filter = [t.strip().upper() for t in tables.split(",") if t.strip()] or None

    if engine == "ORACLE":
        col_rows, pk_rows = _query_oracle_schema(ctx["datasource"], ctx["user"], ctx["password"], ctx["schema"], table_filter)
    elif engine == "SQLSERVER":
        col_rows, pk_rows = _query_sqlserver_schema(ctx["datasource"], ctx.get("catalog") or ctx["schema"],
                                                    table_filter, user=ctx["user"], password=ctx["password"])
    else:
        return {"success": False, "error": f"Motor no soportado: {engine!r}"}
    if isinstance(col_rows, str):
        return {"success": False, "error": col_rows, "engine": engine}

    db_tables = {t: cols for t, cols in _build_table_dict(col_rows, pk_rows).items()}
    mdl_tables = _model_tables(model)
    if table_filter:
        db_tables  = {t: v for t, v in db_tables.items() if t in table_filter}
        mdl_tables = {t: v for t, v in mdl_tables.items() if t in table_filter}

    only_in_model = sorted(set(mdl_tables) - set(db_tables))
    only_in_db    = sorted(set(db_tables) - set(mdl_tables))
    changed: dict = {}

    for tname in sorted(set(mdl_tables) & set(db_tables)):
        mcols = {c.upper(): _norm_col(v) for c, v in (mdl_tables[tname].get("columns") or {}).items()}
        dcols = {c.upper(): _norm_col(v) for c, v in db_tables[tname].items()}
        cols_only_model = sorted(set(mcols) - set(dcols))
        cols_only_db    = sorted(set(dcols) - set(mcols))
        mism = []
        for c in sorted(set(mcols) & set(dcols)):
            a, b = mcols[c], dcols[c]
            diffs = []
            if a["type_base"] != b["type_base"]:            diffs.append(f"tipo {b['type_base']}→{a['type_base']}")
            if a["length"] != b["length"]:                  diffs.append(f"longitud {b['length']}→{a['length']}")
            if a["scale"] != b["scale"]:                     diffs.append(f"escala {b['scale']}→{a['scale']}")
            if a["nullable"] != b["nullable"]:               diffs.append(f"nullable {b['nullable']}→{a['nullable']}")
            if diffs:
                mism.append({"column": c, "diffs": diffs})
        if cols_only_model or cols_only_db or mism:
            changed[tname] = {
                "columns_only_in_model": cols_only_model,
                "columns_only_in_db":    cols_only_db,
                "type_mismatches":       mism,
            }

    drift = bool(only_in_model or only_in_db or changed)
    return {
        "success": True, "engine": engine, "schema": ctx["schema"], "drift": drift,
        "tables_only_in_model": only_in_model,  # el modelo va por delante → generate_migration los CREA
        "tables_only_in_db":    only_in_db,     # en BD y no en el modelo → sync_from_db para traerlos
        "tables_changed":       changed,
        "compared":             len(set(mdl_tables) | set(db_tables)),
    }


def _sql_terminator(engine: str) -> str:
    return "\n/\n" if engine == "ORACLE" else "\nGO\n"


def _pk_cols(tdef: dict) -> list:
    return [c.upper() for c, v in (tdef.get("columns") or {}).items() if _norm_col(v)["pk"]]


def _generate_sql_impl(workspace: str) -> dict:
    ctx = _bd_ctx(workspace)
    if "error" in ctx:
        return {"success": False, "error": ctx["error"]}
    if not ctx["model_path"]:
        return {"success": False, "error": "model_path no configurado en XMLConfig.xml"}
    model = _load_model(ctx["model_path"])
    if model is None:
        return {"success": False, "error": f"Modelo BD no encontrado: {ctx['model_path']}."}
    engine = _model_engine(model, ctx)
    if engine not in ("ORACLE", "SQLSERVER"):
        return {"success": False, "error": f"Motor no soportado: {engine!r}"}

    mdl = _model_tables(model)
    lines, n_stmt, n_fk, n_idx = [], 0, 0, 0
    proyecto = _proyecto(workspace)
    lines.append(f"-- DDL generado desde el modelo BD de {proyecto}")
    lines.append(f"-- Motor: {engine} (de XMLConfig.xml) - NO editar a mano el dialecto")
    lines.append("")

    for tname in sorted(mdl):
        tdef = mdl[tname]
        cols = tdef.get("columns") or {}
        if not cols:
            continue
        coldefs = []
        for cname, cdef in cols.items():
            nc = _norm_col(cdef)
            null_kw = "" if nc["nullable"] else " NOT NULL"
            coldefs.append(f"    {cname.upper():<32} {_ddl_type(nc, engine)}{null_kw}")
        pk = _pk_cols(tdef)
        body = ",\n".join(coldefs)
        if pk:
            body += f",\n    CONSTRAINT PK_{tname} PRIMARY KEY ({', '.join(pk)})"
        lines.append(f"CREATE TABLE {tname} (\n{body}\n){_sql_terminator(engine).rstrip()}")
        lines.append("")
        n_stmt += 1

    # FKs desde relations (solo las que apuntan a tablas del modelo)
    for tname in sorted(mdl):
        for rel in (mdl[tname].get("relations") or []):
            tgt = str(rel.get("target_table", "")).upper()
            sc  = str(rel.get("source_column", "")).upper()
            tc  = str(rel.get("target_column", "")).upper()
            if not (tgt and sc and tc) or tgt not in mdl:
                continue
            if str(rel.get("type", "")).startswith("N:") or rel.get("type") in ("N:1", "1:1"):
                lines.append(
                    f"ALTER TABLE {tname} ADD CONSTRAINT FK_{tname}_{tgt} "
                    f"FOREIGN KEY ({sc}) REFERENCES {tgt} ({tc}){_sql_terminator(engine).rstrip()}"
                )
                n_fk += 1
    if n_fk:
        lines.append("")

    # índices
    for tname in sorted(mdl):
        for idx in (mdl[tname].get("indexes") or []):
            icols = [c.upper() for c in (idx.get("columns") or [])]
            if not icols:
                continue
            uniq = "UNIQUE " if idx.get("unique") else ""
            iname = idx.get("name") or f"IX_{tname}_{'_'.join(icols)}"
            lines.append(f"CREATE {uniq}INDEX {iname} ON {tname} ({', '.join(icols)}){_sql_terminator(engine).rstrip()}")
            n_idx += 1

    out_dir = _scripts_dir(workspace)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{proyecto}-ddl.sql"
    text = "\n".join(lines).rstrip() + "\n"
    out_file.write_text(text, encoding="utf-8")
    return {
        "success": True, "engine": engine, "path": str(out_file),
        "tables": n_stmt, "foreign_keys": n_fk, "indexes": n_idx, "lines": text.count("\n"),
    }


def _idempotent_add_col(engine: str, table: str, schema: str, col: str, ddl_type: str, nullable: bool) -> str:
    null_kw = "" if nullable else " NOT NULL"
    if engine == "ORACLE":
        return (
            "DECLARE v_c NUMBER;\n"
            "BEGIN\n"
            f"  SELECT COUNT(*) INTO v_c FROM ALL_TAB_COLUMNS\n"
            f"   WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{col}' AND OWNER = '{schema}';\n"
            "  IF v_c = 0 THEN\n"
            f"    EXECUTE IMMEDIATE 'ALTER TABLE {table} ADD ({col} {ddl_type}{null_kw})';\n"
            "  END IF;\n"
            "END;\n/"
        )
    return (
        f"IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS\n"
        f"               WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{col}')\n"
        f"    ALTER TABLE {table} ADD {col} {ddl_type}{('' if nullable else ' NOT NULL')};\nGO"
    )


def _generate_migration_impl(workspace: str) -> dict:
    cmp = _compare_model_impl(workspace)
    if not cmp.get("success"):
        return cmp
    ctx = _bd_ctx(workspace)
    engine = cmp["engine"]
    schema = cmp["schema"]
    model = _load_model(ctx["model_path"]) or {}
    mdl = _model_tables(model)

    lines = [
        f"-- Migracion modelo -> BD para {_proyecto(workspace)}",
        f"-- Motor: {engine}. Idempotente (references/bd.md). Revisar antes de ejecutar en produccion.",
        "",
    ]
    n = 0

    for tname in cmp["tables_only_in_model"]:
        tdef = mdl.get(tname, {})
        cols = tdef.get("columns") or {}
        coldefs = []
        for cname, cdef in cols.items():
            nc = _norm_col(cdef)
            coldefs.append(f"    {cname.upper():<32} {_ddl_type(nc, engine)}{'' if nc['nullable'] else ' NOT NULL'}")
        pk = _pk_cols(tdef)
        body = ",\n".join(coldefs)
        if pk:
            body += f",\n    CONSTRAINT PK_{tname} PRIMARY KEY ({', '.join(pk)})"
        if engine == "ORACLE":
            lines.append(
                "DECLARE v_c NUMBER;\nBEGIN\n"
                f"  SELECT COUNT(*) INTO v_c FROM ALL_TABLES WHERE TABLE_NAME = '{tname}' AND OWNER = '{schema}';\n"
                "  IF v_c = 0 THEN EXECUTE IMMEDIATE '\n"
                f"CREATE TABLE {tname} (\n{body}\n)';\n  END IF;\nEND;\n/"
            )
        else:
            lines.append(
                f"IF OBJECT_ID(N'{schema or 'dbo'}.{tname}', N'U') IS NULL\n"
                f"CREATE TABLE {tname} (\n{body}\n);\nGO"
            )
        lines.append("")
        n += 1

    for tname, ch in cmp["tables_changed"].items():
        tdef = mdl.get(tname, {})
        cols = tdef.get("columns") or {}
        for cname in ch["columns_only_in_model"]:
            nc = _norm_col(cols.get(cname, {}))
            lines.append(_idempotent_add_col(engine, tname, schema, cname, _ddl_type(nc, engine), nc["nullable"]))
            lines.append("")
            n += 1
        for mism in ch["type_mismatches"]:
            cname = mism["column"]
            nc = _norm_col(cols.get(cname, {}))
            verb = "MODIFY" if engine == "ORACLE" else "ALTER COLUMN"
            paren = f"({cname} {_ddl_type(nc, engine)})" if engine == "ORACLE" else f"{cname} {_ddl_type(nc, engine)}"
            lines.append(f"-- REVISAR: cambio de tipo en {tname}.{cname} — {', '.join(mism['diffs'])}")
            lines.append(f"ALTER TABLE {tname} {verb} {paren};{'' if engine=='ORACLE' else chr(10)+'GO'}")
            lines.append("")
            n += 1
        for cname in ch["columns_only_in_db"]:
            lines.append(f"-- Columna en BD y no en el modelo: {tname}.{cname}")
            lines.append(f"-- ALTER TABLE {tname} DROP COLUMN {cname};  -- descomentar solo si es seguro")
            lines.append("")

    out_dir = _scripts_dir(workspace)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{_proyecto(workspace)}-migration.sql"
    text = "\n".join(lines).rstrip() + "\n"
    out_file.write_text(text, encoding="utf-8")
    return {
        "success": True, "engine": engine, "path": str(out_file), "statements": n,
        "tables_created": len(cmp["tables_only_in_model"]),
        "tables_altered": len(cmp["tables_changed"]),
        "drift": cmp["drift"],
    }


def _render_erd_impl(workspace: str) -> dict:
    ctx = _bd_ctx(workspace)
    if "error" in ctx:
        return {"success": False, "error": ctx["error"]}
    if not ctx["model_path"]:
        return {"success": False, "error": "model_path no configurado"}
    model = _load_model(ctx["model_path"])
    if model is None:
        return {"success": False, "error": f"Modelo BD no encontrado: {ctx['model_path']}."}
    mdl = _model_tables(model, include_hidden=True)
    proyecto = _proyecto(workspace)

    def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    mer = ["erDiagram"]
    rel_count = 0
    for tname in sorted(mdl):
        tdef = mdl[tname]
        mer.append(f"    {tname} {{")
        for cname, cdef in (tdef.get("columns") or {}).items():
            nc = _norm_col(cdef)
            tag = "PK" if nc["pk"] else ""
            mer.append(f"        {nc['type_base'] or 'X'} {cname.upper()} {tag}".rstrip())
        mer.append("    }")
    for tname in sorted(mdl):
        for rel in (mdl[tname].get("relations") or []):
            tgt = str(rel.get("target_table", "")).upper()
            if tgt not in mdl:
                continue
            card = {"1:N": "||--o{", "N:1": "}o--||", "1:1": "||--||", "N:M": "}o--o{"}.get(rel.get("type", ""), "||--o{")
            mer.append(f"    {tname} {card} {tgt} : \"{esc(rel.get('source_column',''))}\"")
            rel_count += 1

    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>ERD {esc(proyecto)}</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>body{{font-family:system-ui,Segoe UI,sans-serif;margin:1.5rem;background:#fafafa}}
h1{{font-size:1.1rem}} .meta{{color:#666;font-size:.85rem;margin-bottom:1rem}}
.mermaid{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:1rem;overflow:auto}}</style>
</head><body>
<h1>ERD — {esc(proyecto)}</h1>
<div class="meta">{len(mdl)} tablas · {rel_count} relaciones · motor {esc(_model_engine(model, ctx))} · generado {__import__('datetime').datetime.now():%Y-%m-%d %H:%M}</div>
<pre class="mermaid">
{chr(10).join(mer)}
</pre>
<script>mermaid.initialize({{startOnLoad:true,er:{{layoutDirection:'LR'}}}});</script>
</body></html>"""

    out_dir = Path(workspace) / "BD"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{proyecto}-erd.html"
    out_file.write_text(html, encoding="utf-8")
    try:
        os.startfile(str(out_file))  # noqa: S606 — abrir en navegador (Windows)
        opened = True
    except Exception:
        opened = False
    return {"success": True, "path": str(out_file), "table_count": len(mdl), "relation_count": rel_count, "opened": opened}


_DALC_FROM_RE = re.compile(r"\bFROM\s+([A-Za-z_][\w$#]*)\s+(?:AS\s+)?([A-Za-z_]\w*)", re.I)
_DALC_JOIN_RE = re.compile(r"\bJOIN\s+([A-Za-z_][\w$#]*)\s+(?:AS\s+)?([A-Za-z_]\w*)\s+ON\s+(.+?)(?:\bWHERE\b|\bJOIN\b|\bGROUP\b|\bORDER\b|$)", re.I | re.S)
_DALC_EQ_RE   = re.compile(r"([A-Za-z_]\w*)\.([A-Za-z_][\w$#]*)\s*=\s*([A-Za-z_]\w*)\.([A-Za-z_][\w$#]*)")


def _analyze_dalc_impl(workspace: str, sln_path: str = "") -> dict:
    ctx = _bd_ctx(workspace)
    if "error" in ctx:
        return {"success": False, "error": ctx["error"]}
    if not ctx["model_path"]:
        return {"success": False, "error": "model_path no configurado"}
    model = _load_model(ctx["model_path"])
    if model is None:
        return {"success": False, "error": f"Modelo BD no encontrado: {ctx['model_path']}."}

    roots = []
    if sln_path:
        scope = _get_scope(sln_path)
        for d in (scope.get("scope_dirs") or []):
            p = Path(d)
            roots.append(p if p.is_absolute() else Path(workspace) / d)
    if not roots:
        roots = [Path(workspace)]

    dalc_files = []
    for root in roots:
        if root.exists():
            dalc_files += [f for f in root.rglob("*.cs") if re.search(r"dalc", f.name, re.I)]
    dalc_files = sorted(set(dalc_files))

    known = {t.upper() for t in (model.get("tables") or {})}
    found: dict = {}  # (src_tbl, src_col, tgt_tbl, tgt_col) -> source_file

    for f in dalc_files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for sql in re.findall(r'"([^"]*\bFROM\b[^"]*)"', txt, re.I) + re.findall(r'@"([^"]*\bFROM\b[^"]*)"', txt, re.I):
            alias2tbl = {a.upper(): t.upper() for t, a in _DALC_FROM_RE.findall(sql)}
            for jt, ja, oncond in _DALC_JOIN_RE.findall(sql):
                alias2tbl[ja.upper()] = jt.upper()
                for a1, c1, a2, c2 in _DALC_EQ_RE.findall(oncond):
                    t1, t2 = alias2tbl.get(a1.upper()), alias2tbl.get(a2.upper())
                    if t1 and t2 and t1 != t2 and t1 in known and t2 in known:
                        found[(t1, c1.upper(), t2, c2.upper())] = str(f)

    tables = model.setdefault("tables", {})
    # index de tablas por nombre real (respetando el casing del modelo)
    real_name = {k.upper(): k for k in tables}
    added = 0
    for (t1, c1, t2, c2), src in found.items():
        key = real_name.get(t1)
        if not key:
            continue
        rels = tables[key].setdefault("relations", [])
        dup = any(
            str(r.get("target_table", "")).upper() == t2
            and str(r.get("source_column", "")).upper() == c1
            and str(r.get("target_column", "")).upper() == c2
            for r in rels
        )
        if dup:
            continue
        rels.append({
            "target_table": real_name.get(t2, t2),
            "source_column": c1, "target_column": c2,
            "type": "N:1", "inferred_from": "JoinClause", "confidence": "low",
            "source_file": src, "source": "dalc",
        })
        added += 1

    if added:
        from datetime import datetime
        model["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _write_model_json(ctx["model_path"], model)

    return {
        "success": True, "dalcs_scanned": len(dalc_files),
        "relations_found": len(found), "relations_added": added,
        "model_path": str(ctx["model_path"]),
        "note": "Relaciones inferidas con confidence:low — revisar antes de fiarse.",
    }


def _export_dmd_impl(workspace: str) -> dict:
    """Exporta a Oracle Data Modeler .dmd (XML). Formato mínimo — tablas, columnas, PK, FK."""
    ctx = _bd_ctx(workspace)
    if "error" in ctx:
        return {"success": False, "error": ctx["error"]}
    if not ctx["model_path"]:
        return {"success": False, "error": "model_path no configurado"}
    model = _load_model(ctx["model_path"])
    if model is None:
        return {"success": False, "error": f"Modelo BD no encontrado: {ctx['model_path']}."}
    mdl = _model_tables(model, include_hidden=True)
    proyecto = _proyecto(workspace)

    def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    tab_ids, col_ids = {}, {}
    i = 0
    for tname in sorted(mdl):
        i += 1
        tab_ids[tname] = f"TAB{i:04d}"
        for j, cname in enumerate((mdl[tname].get("columns") or {}), 1):
            col_ids[(tname, cname.upper())] = f"C{i:04d}{j:03d}"

    parts = ['<?xml version="1.0" encoding="UTF-8" ?>', f'<model name="{esc(proyecto)}">', '  <relationalModels>',
             '    <relationalModel id="RM0001">', '      <tables>']
    for tname in sorted(mdl):
        tdef = mdl[tname]
        parts.append(f'        <table id="{tab_ids[tname]}" name="{esc(tname)}">')
        parts.append('          <columns>')
        pk = []
        for cname, cdef in (tdef.get("columns") or {}).items():
            nc = _norm_col(cdef)
            cid = col_ids[(tname, cname.upper())]
            if nc["pk"]:
                pk.append(cid)
            params = str(nc["length"]) if nc["length"] else ""
            parts.append(
                f'            <column id="{cid}" name="{esc(cname.upper())}" dataTypeName="{esc(nc["type_base"])}" '
                f'dataTypeParameters="{params}" mandatory="{str(not nc["nullable"]).lower()}" '
                f'primaryKey="{str(nc["pk"]).lower()}"><comment>{esc(cdef.get("description",""))}</comment></column>'
            )
        parts.append('          </columns>')
        if pk:
            parts.append('          <primaryKey>')
            parts += [f'            <primaryKeyColumn columnID="{c}"/>' for c in pk]
            parts.append('          </primaryKey>')
        parts.append(f'          <comment>{esc(tdef.get("description",""))}</comment>')
        parts.append('        </table>')
    parts.append('      </tables>')

    parts.append('      <fkAssociations>')
    fk = 0
    for tname in sorted(mdl):
        for rel in (mdl[tname].get("relations") or []):
            tgt = str(rel.get("target_table", "")).upper()
            sc  = (tname, str(rel.get("source_column", "")).upper())
            tc  = (tgt, str(rel.get("target_column", "")).upper())
            if tgt in tab_ids and sc in col_ids and tc in col_ids:
                fk += 1
                parts.append(
                    f'        <fkAssociation id="FK{fk:04d}" name="FK_{esc(tname)}_{esc(tgt)}" '
                    f'referredTableID="{tab_ids[tgt]}" referringTableID="{tab_ids[tname]}">'
                    f'<fkAssociationColumns><fkAssociationColumn referredColumnID="{col_ids[tc]}" '
                    f'referringColumnID="{col_ids[sc]}"/></fkAssociationColumns></fkAssociation>'
                )
    parts.append('      </fkAssociations>')
    parts += ['    </relationalModel>', '  </relationalModels>', '</model>']

    out_dir = Path(workspace) / "BD"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{proyecto}.dmd"
    out_file.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return {"success": True, "path": str(out_file), "table_count": len(mdl), "fk_count": fk,
            "note": "Formato .dmd mínimo — Oracle Data Modeler puede pedir reconciliación al importar."}


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


@mcp.tool(description="Resuelve la conexión BD de la solución desde C:\\AIS\\<Sln>\\bin\\Settings\\Settings.xml (tag oledbconnectionstring) → motor, datasource, schema, catalog, user, sln, environments, model_path. NO devuelve password. Usar antes de operaciones BD. Fallback legacy: docs/XMLConfig.xml.")
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


@mcp.tool(description="SELECT en vivo contra la BD publicada de la solución (cadena de C:\\AIS\\<Sln>\\bin\\Settings\\Settings.xml → oledbconnectionstring). SQL Server u Oracle, autodetectado. SOLO SELECT, sin multi-statement. max_rows limita filas en contexto (default 200). env_index: 0=DEV/TEST (default), 1+=PRE/PROD. Usar SIEMPRE que se necesiten registros/valores reales de tablas.")
def db_query(workspace: str, sql: str, max_rows: int = 200, env_index: int = 0) -> str:
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

    config = _settings_conn(workspace, env_index)
    if "error" in config:
        return json.dumps({"error": config["error"]}, ensure_ascii=False)

    motor      = config.get("motor", "")
    datasource = config.get("datasource", "")
    schema     = config.get("schema", "")
    user       = config.get("user", "")
    catalog    = config.get("catalog", "")
    password   = config.get("password", "")

    if motor == "SQLSERVER":
        cmd = ["sqlcmd", "-S", datasource, "-d", catalog or schema, "-Q", sql_norm, "-h", "-1", "-W"]
        if user:
            cmd += ["-U", user, "-P", password]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=_clean_env())
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
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=_clean_env())
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


@mcp.tool(description="Compara model.json con el esquema real de la BD (motor de XMLConfig) → tablas/columnas solo en el modelo, solo en BD, y con tipo/longitud/nullable distinto. Respeta visible:false. Nativa Python.")
def compare_model(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_compare_model_impl(workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Extrae controles AIS de .aspx con textos para registrar en RIDIOMA y RCONTROLES.")
def scan_aspx(sln_path: str) -> str:
    return json.dumps(_run_ps("scan-aspx.ps1", "-SlnPath", sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Registra ejecución del pipeline en executions/history.json. status: success|fail|partial. Llamar al final del pipeline.")
def log_execution(workspace: str, solution: str, task: str, status: str = "success", agents: str = "") -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_run_ps("log-execution.ps1", workspace, solution, task, "-Status", status, "-Agents", agents), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Script SQL idempotente modelo→BD en el dialecto de XMLConfig: CREATE TABLE (guardado), ALTER TABLE ADD (guardado por ALL_TAB_COLUMNS/INFORMATION_SCHEMA), MODIFY marcado -- REVISAR, DROP COLUMN comentado. Escribe C:\\AIS\\<proy>\\scripts\\<proy>-migration.sql. Nativa Python.")
def generate_migration(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_generate_migration_impl(workspace), ensure_ascii=False, separators=(",",":"))


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
    catalog    = config.get("catalog", "")
    model_path = Path(config.get("model_path", ""))
    password   = _get_db_password(workspace)
    table_list = [t.strip().upper() for t in tables.split(",") if t.strip()]
    if not table_list:
        return json.dumps({"error": "No tables specified"}, ensure_ascii=False)
    if motor == "ORACLE":
        col_rows, pk_rows = _query_oracle_schema(datasource, user, password, schema, table_filter=table_list)
    elif motor == "SQLSERVER":
        col_rows, pk_rows = _query_sqlserver_schema(datasource, catalog or schema, table_filter=table_list,
                                                    user=user, password=password)
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


@mcp.tool(description="Genera DDL SQL (CREATE TABLE + PK + FK + índices) desde el modelo BD en el dialecto de XMLConfig — Oracle usa VARCHAR2(n CHAR). Escribe C:\\AIS\\<proyecto>\\scripts\\<proyecto>-ddl.sql. Sin argumento de motor (un proyecto = una BD). El SQL no entra en contexto. Nativa Python.")
def generate_sql(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_generate_sql_impl(workspace), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Exporta el modelo BD a Oracle Data Modeler (.dmd XML mínimo: tablas, columnas, PK, FK) → <workspace>\\BD\\<proyecto>.dmd. El XML no entra en contexto. Nativa Python.")
def export_dmd(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_export_dmd_impl(workspace), ensure_ascii=False, separators=(",",":"))


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


@mcp.tool(description="Infiere relaciones entre tablas analizando 'JOIN ... ON a.X = b.Y' en el SQL embebido de los DALC (*Dalc*.cs). Añade al modelo con confidence:low; no toca source:manual. sln_path opcional acota el scope. Nativa Python.")
def analyze_dalc(workspace: str, sln_path: str = "") -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_analyze_dalc_impl(workspace, sln_path), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Genera un ERD HTML (mermaid erDiagram) del modelo BD y lo abre en el navegador → <workspace>\\BD\\<proyecto>-erd.html. Devuelve ruta y contadores — el modelo no entra en contexto. Nativa Python.")
def render_erd(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_render_erd_impl(workspace), ensure_ascii=False, separators=(",",":"))


def _schema_from_model(model_path: Path | None, table_list: list[str]) -> tuple[dict, list] | None:
    """Esquema de tablas desde el snapshot model.json. None si no hay modelo."""
    if not model_path:
        return None
    model = _load_model(model_path)
    if model is None:
        return None
    raw = model.get("tables", {})
    index = {k.upper(): v for k, v in raw.items()} if isinstance(raw, dict) else \
            {(t.get("name") or t.get("tableName", "?")).upper(): t for t in raw}
    result: dict = {}
    not_found: list = []
    for tname in table_list:
        tdef = index.get(tname)
        if not tdef:
            not_found.append(tname)
            continue
        cols = tdef.get("columns", {})
        col_list = [{"name": k, **v} for k, v in cols.items()] if isinstance(cols, dict) else list(cols)
        result[tname] = {
            "source": "model",
            "description": tdef.get("description", ""),
            "visible": tdef.get("visible", True),
            "columns": col_list,
            "relations": tdef.get("relations", []),
            "indexes": tdef.get("indexes", []),
        }
    return result, not_found


@mcp.tool(description="Esquema de tablas (columnas tipo/longitud/nullable/pk; relaciones e índices si vienen del snapshot). source='auto' (default): consulta la BD EN VIVO vía Settings.xml y solo si la conexión falla cae al snapshot BD/<Sln>-model.json con warning. source='db': solo vivo (error si no conecta). source='model': solo snapshot. env_index: 0=DEV/TEST (default), 1+=PRE/PROD de Settings.xml. tables = coma-separadas.")
def get_table_schema(workspace: str, tables: str, source: str = "auto", env_index: int = 0) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    table_list = [t.strip().upper() for t in tables.split(",") if t.strip()]
    if not table_list:
        return json.dumps({"error": "Sin tablas indicadas"}, ensure_ascii=False)

    ctx = _bd_ctx(workspace, env_index)
    ctx_err = ctx.get("error") if isinstance(ctx, dict) else None
    model_path = ctx.get("model_path") if isinstance(ctx, dict) and not ctx_err else None
    warning: str | None = None

    # --- vía viva (auto | db) ---
    if source in ("auto", "db"):
        if ctx_err:
            warning = f"sin conexión ({ctx_err})"
        else:
            motor = ctx["motor"]
            if motor == "ORACLE":
                col_rows, pk_rows = _query_oracle_schema(
                    ctx["datasource"], ctx["user"], ctx["password"], ctx["schema"], table_list)
            elif motor == "SQLSERVER":
                col_rows, pk_rows = _query_sqlserver_schema(
                    ctx["datasource"], ctx.get("catalog") or ctx["schema"], table_list,
                    user=ctx["user"], password=ctx["password"])
            else:
                col_rows, pk_rows = f"motor no soportado: {motor!r}", []
            if isinstance(col_rows, str):
                warning = f"consulta viva falló ({col_rows})"
            else:
                built = _build_table_dict(col_rows, pk_rows)
                # Enriquecer con indexes/relations/description del snapshot (si existe) — las
                # columnas son de la BD viva; indexes/relations pueden estar algo desfasados.
                snap = _load_model(model_path) if model_path else None
                snap_idx = {}
                if snap:
                    raw = snap.get("tables", {})
                    snap_idx = {k.upper(): v for k, v in raw.items()} if isinstance(raw, dict) else \
                               {(x.get("name") or "?").upper(): x for x in raw}
                live: dict = {}
                for t in table_list:
                    if t in built:
                        entry = {"source": "db",
                                 "columns": [{"name": c, **v} for c, v in built[t].items()]}
                        sd = snap_idx.get(t)
                        if sd:
                            entry["description"]     = sd.get("description", "")
                            entry["relations"]       = sd.get("relations", [])
                            entry["indexes"]         = sd.get("indexes", [])
                            entry["meta_from_snapshot"] = True
                        live[t] = entry
                return json.dumps({
                    "workspace": workspace, "motor": motor, "schema": ctx["schema"],
                    "source": "db", "tables": live,
                    "not_found": [t for t in table_list if t not in live],
                }, ensure_ascii=False, separators=(",",":"))
        if source == "db":
            return json.dumps({"error": warning or "consulta viva falló", "workspace": workspace},
                              ensure_ascii=False)

    # --- snapshot model.json (source='model', o fallback de 'auto') ---
    from_model = _schema_from_model(model_path, table_list)
    if from_model is None:
        return json.dumps({
            "error": (f"{warning}; " if warning else "") +
                     "sin snapshot model.json — ejecuta 'sincroniza el modelo BD' o revisa la publicación de la solución",
            "workspace": workspace,
        }, ensure_ascii=False)
    result, not_found = from_model
    out = {
        "workspace": workspace,
        "motor": (ctx.get("motor") if isinstance(ctx, dict) else None),
        "schema": (ctx.get("schema") if isinstance(ctx, dict) else None),
        "source": "model",
        "tables": result,
        "not_found": not_found,
    }
    if warning:
        out["warning"] = f"{warning} — esquema del snapshot, posiblemente desactualizado"
    return json.dumps(out, ensure_ascii=False, separators=(",",":"))


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


@mcp.tool(description="Compara solo tablas específicas del modelo con la BD real (dialecto de XMLConfig). tables = coma-separadas. Post-migración, cuando se conocen las tablas tocadas. Nativa Python.")
def compare_model_tables(workspace: str, tables: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    return json.dumps(_compare_model_impl(workspace, tables), ensure_ascii=False, separators=(",",":"))


@mcp.tool(description="Índice ligero del SNAPSHOT model.json: {TABLA: [COL1, COL2, ...]}. Para impact analysis y ojear qué tablas hay. Para datos frescos de tablas/columnas/registros → get_table_schema (vivo) o db_query. Requiere BD/<Sln>-model.json (ejecutar 'sincroniza el modelo BD').")
def get_model_index(workspace: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config: return json.dumps(config, ensure_ascii=False)

    model = _load_model(Path(config.get("model_path", "")))
    if model is None:
        return json.dumps({"error": "Snapshot model.json no encontrado. Para esquema en vivo usar get_table_schema o db_query; para generar el snapshot, 'sincroniza el modelo BD' (sync_from_db)."}, ensure_ascii=False)

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


@mcp.tool(description="Busca keyword en nombres de tabla/columna/descripción del SNAPSHOT model.json — para localizar dónde vive un concepto. Confirma siempre contra la BD viva (get_table_schema / db_query). Requiere BD/<Sln>-model.json.")
def search_model(workspace: str, keyword: str) -> str:
    if err := _check_workspace(workspace): return json.dumps(err, ensure_ascii=False)
    config = _get_config(workspace)
    if "error" in config: return json.dumps(config, ensure_ascii=False)

    model = _load_model(Path(config.get("model_path", "")))
    if model is None:
        return json.dumps({"error": "Snapshot model.json no encontrado. Para buscar en vivo usar db_query contra ALL_TAB_COLUMNS/INFORMATION_SCHEMA.COLUMNS."}, ensure_ascii=False)

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

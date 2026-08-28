# Orchestrator Plugin — Arquitectura

Documento canónico del plugin `orchestrator-skill-full`. Fuente de verdad para entender la anatomía y los patrones de extensión. Leer §9 antes de añadir cualquier artefacto; leer §10 antes de cerrar cualquier cambio.

Repositorio: `https://github.com/aisaplica/Orchestrator-Agent.git`

---

## §1 — Propósito

Pipeline de desarrollo automatizado para proyectos ScacsWeb (ASP.NET / C# / .NET Framework). Cubre: análisis, planificación, implementación, validación, build, BD (Oracle 19c / SQL Server), SVN/Git, MantisBT y documentación técnica.

---

## §2 — Estructura del repositorio

```
orchestrator-skill-full/
├── .claude-plugin/
│   ├── plugin.json          ← versión canónica del plugin
│   └── marketplace.json     ← descriptor para marketplace local
├── .mcp.json                ← declaración del MCP server
├── SKILL.md                 ← skill raíz (legacy, apunta a skills/)
├── README.md
├── CHANGELOG.md
│
├── commands/                ← slash commands discoverables en el menú / de Claude Code
│   ├── orchestrator-agent.md        ← pipeline principal
│   ├── orchestrator-analizar.md
│   ├── orchestrator-auditoria.md
│   └── ... (20 ficheros — uno por modo directo)
│
├── skills/                  ← skills invocables (orchestrator-skill-full:<name>)
│   ├── orchestrator-agent/
│   │   └── SKILL.md         ← pipeline completo (punto de entrada principal)
│   └── mantis/
│       └── SKILL.md         ← ciclo de vida MantisBT
│
├── agents/                  ← agentes especializados (leídos inline por las skills). 47 ficheros
│   ├── auditoria.md         ← plantilla de referencia para nuevos agentes
│   ├── planner.md core.md bd.md analyzer.md validator.md fixer.md test.md build.md db-env.md   ← pipeline
│   ├── idiomas-standalone.md documentar.md   ← pasos condicionales del pipeline
│   ├── mantis.md            ← inline en pipeline (Mantis #NNNN)
│   └── ...                  ← resto: uno por modo directo (auditoria, impacto, diff-svn, historial,
│                                comparar-modelo, comparar-entornos, estructura, commit-svn, stats,
│                                validar-entorno, validar-requerimiento, seguridad, dependencias,
│                                scacs-docs, schema, seed, perf, hotspots, dead-code, doc-drift,
│                                explicar, format, rename, deshacer, migrar, generar-dalc, init,
│                                sync-indexes, release-notes, log-errores, incidencia, help, dashboard)
│
├── hooks/                   ← scripts PowerShell (fallback de las MCP tools). UTF-8 CON BOM (PS5.1)
│   │                          23 ficheros implementados. NO todas las MCP tools tienen hook —
│   │                          ver estado (✅/⚠️/🐍) en references/hooks.md
│   ├── compile-check.ps1 lib-msbuild.ps1 test-runner-check.ps1 create-test-project.ps1
│   ├── validate-solution.ps1 parse-sln.ps1 find-symbol.ps1 edit-ansi.ps1
│   ├── get-config.ps1 check-env.ps1 log-execution.ps1 parse-weblog.ps1
│   ├── detect-vcs.ps1 svn-diff.ps1 svn-log.ps1 svn-diff-revision.ps1 svn-add.ps1 git-diff-revision.ps1
│   ├── batch-build.ps1 online-publish.ps1 copy-ais.ps1
│   └── mantis-cli.ps1 mantis-get-issue.ps1   ← usados por agents/mantis.md, no por el MCP
│
├── references/              ← contexto técnico leído por agentes
│   ├── arquitectura.md
│   ├── bd.md
│   ├── conventions.md
│   ├── dalc-patterns.md
│   ├── dmd-format.md
│   ├── encuadre-checklist.md ← checklist patrones tarea/contexto/alcance (base: prompt-master)
│   ├── hooks.md             ← tabla Preferente/Fallback MCP↔hook
│   ├── json-schema.md
│   ├── mantis.md
│   ├── mcp.md               ← documentación del MCP server
│   ├── testing.md
│   └── troubleshooting.md
│
├── mcp/
│   └── orchestrator-workspace-server.py   ← MCP server (40 @mcp.tool). Las tools sin hook y sin
│                                             impl Python nativa devuelven {"status":"not_implemented"}
│
├── runner/
│   └── runner.ps1           ← runner de acciones de workspace
│
└── docs/
    ├── plugin-architecture.md   ← este archivo
    ├── .mantis-dev-config.json  ← catálogo proyectos ScacsWeb + cadena estados Mantis
    └── scacs/
        └── 00-index.md          ← índice de documentación técnica ScacsWeb
```

**Artefactos de runtime (no versionados, fuera del repo del plugin):**
- `<workspace>\executions\history.json` — historial del pipeline, escrito por `hooks/log-execution.ps1` en el workspace del usuario (no en `$SKILL_DIR`, que se borra al actualizar el plugin). Lo leen `historial`, `stats` y `dashboard`. Tope 500 vivas; excedente en `<workspace>\executions\archive\history-YYYY-MM.json`.

---

## §3 — Manifests

### plugin.json (`.claude-plugin/plugin.json`)

```json
{
  "name": "orchestrator-skill-full",
  "version": "X.Y.Z",
  "description": "...",
  "author": { "name": "ScacsWeb / Ingenieros" }
}
```

La versión en `plugin.json` y `marketplace.json` **siempre deben ser idénticas**. Claude Code detecta actualizaciones cuando sube la versión.

### marketplace.json (`.claude-plugin/marketplace.json`)

Descriptor del marketplace local. Contiene la sección `plugins[].version` que debe coincidir con `plugin.json`. Usar el campo `source: "."` para instalación local desde el repo.

### .mcp.json

Declara el servidor `orchestrator-workspace` (tipo `stdio`, ejecuta `orchestrator-workspace-server.py`). No modificar salvo que se cambie el mecanismo de arranque del MCP.

---

## §4 — Skills

**Ubicación:** `skills/<nombre>/SKILL.md`
**Invocación:** `orchestrator-skill-full:<nombre>`

### Frontmatter obligatorio

```yaml
---
name: <nombre>
metadata:
  version: "X.Y.Z"
description: 'Descripción para autodiscovery. Incluir cuándo usarla y ejemplos de frases trigger.'
---
```

### PASO 0 — Localización de SKILL_DIR (obligatorio en toda skill)

Toda skill debe incluir PASO 0 al inicio. Copiar exactamente de `skills/orchestrator-agent/SKILL.md`:
1. Obtener "Base directory for this skill" del contexto del sistema
2. Subir desde esa ruta hasta encontrar el directorio con `agents/`
3. Fallbacks: rpm/ (marketplace remoto), instalación manual

`SKILL_DIR` apunta a la raíz del plugin — NO al directorio de la skill.
Usar `$SKILL_DIR\agents\<nombre>.md`, `$SKILL_DIR\hooks\<nombre>.ps1`, etc.

### Skills existentes

| Skill | Propósito |
|-------|-----------|
| `orchestrator-agent` | Pipeline completo de desarrollo (11 pasos + 18 modos directos) |
| `mantis` | Ciclo de vida MantisBT (4 fases: selección, encuadre, pipeline, validación) |
| `plugin-dev` | Meta-desarrollo del plugin (este documento es su fuente canónica) |

---

## §5 — Agentes

**Ubicación:** `agents/<nombre>.md`
**Uso:** leídos inline por las skills con `Read $SKILL_DIR\agents\<nombre>.md`

### Formato

```markdown
name: orchestrator-<nombre>

# Rol

<descripción del rol del agente, una o dos líneas>

# Objetivo

<qué hace concretamente>

# Contexto de ejecución

<desde qué skill se llama, modo directo o pipeline>

# Proceso

[pasos concretos]
```

> No usar YAML con `---` delimiters en agents/ — usar el formato simple `name:` + secciones markdown.

### Agentes del pipeline principal

| Agente | Paso pipeline | Cuándo |
|--------|--------------|--------|
| `planner` | 1 | Siempre — primer paso |
| `core` | 4 | Siempre — implementación |
| `bd` | 5 | Solo si el cambio afecta BD |
| `analyzer` | 6 | Siempre |
| `validator` | 7 | Siempre |
| `fixer` | 7b | Solo si validator detecta errores (máx 2 ciclos) |
| `test` | 8 | Siempre — ejecuta `run_tests`; si `skipped` → `create_test_project` y reintenta |
| `idiomas-standalone` | 8b | Solo proyectos Online con SIControles/SIIdioma |
| `documentar` | 8c | Solo si planner lo incluyó |
| `build` | 9 | Siempre |
| `db-env` | 10 | Solo si se modificaron tablas/columnas/DALCs |

### Agentes de modos directos

| Agente | Modo |
|--------|------|
| `auditoria` | `/orchestrator-auditoria` |
| `analyzer` | `/orchestrator-analizar` |
| `impacto` | `/orchestrator-impacto` |
| `diff-svn` | `/orchestrator-diff` |
| `historial` | `/orchestrator-historial` |
| `comparar-modelo` | `/orchestrator-comparar-modelo` |
| `idiomas-standalone` | `/orchestrator-idiomas` |
| `documentar` | `/orchestrator-doc` |
| `validar-entorno` | `/orchestrator-env` |
| `estructura` | `/orchestrator-estructura` |
| `commit-svn` | `/orchestrator-commit` |
| `test` | `/orchestrator-test`, `/orchestrator-crear-tests` |
| `db-env` | `/orchestrator-erd` |
| `stats` | `/orchestrator-stats` |
| `validar-requerimiento` | `/orchestrator-validar-req` |
| `seguridad` | `/orchestrator-security` |
| `dependencias` | `/orchestrator-deps` |
| `scacs-docs` | `/orchestrator-scacs-docs` |
| `mantis` | Inline en pipeline (Mantis #NNNN) |

---

## §6 — MCP Server

**Archivo:** `mcp/orchestrator-workspace-server.py`
**Nombre del server:** `orchestrator-workspace`
**Tool prefix:** `mcp__orchestrator-workspace__`

### Tools disponibles (40)

> No todas tienen hook fallback implementado. `references/hooks.md` marca el estado de cada una:
> ✅ hook implementado · 🐍 impl Python nativa (sin hook) · ⚠️ ni hook ni impl → devuelve `{"status":"not_implemented","fallback":"..."}`.
> Pendientes (fase 2/3): `compare_model`, `compare_model_tables`, `generate_migration`, `generate_sql`,
> `render_erd`, `export_dmd`, `analyze_dalc`, `map_dependencies`, `security_scan`, `scan_aspx`,
> `search_code`, `find_doc_section`, `git_status`, `git_log`, `git_add`.

| Categoría | Tools |
|-----------|-------|
| Sistema | `ping`, `check_env`, `get_db_config` |
| Solución | `validate_solution`, `get_scope` |
| Búsqueda | `find_symbol`, `batch_find_symbols`, `search_code`, `find_doc_section` |
| BD/Modelo | `get_model_index`, `get_table_schema`, `search_model`, `sync_model_tables`, `sync_from_db`, `sync_indexes`, `compare_model`, `compare_model_tables`, `generate_sql`, `generate_migration`, `export_dmd`, `render_erd`, `analyze_dalc` |
| Build/Test | `compile_check`, `run_tests`, `create_test_project` |
| VCS | `detect_vcs`, `svn_status`, `svn_log`, `svn_diff_revision`, `svn_add`, `git_status`, `git_log`, `git_diff_revision`, `git_add` |
| ASPX | `scan_aspx` |
| Dependencias | `map_dependencies` |
| Log | `log_execution` |
| Seguridad | `security_scan` |
| BD directa | `db_query` |

### Convención Preferente/Fallback

Cada tool MCP tiene un hook PowerShell equivalente (tabla completa en `references/hooks.md`).
- Usar siempre la tool MCP
- Si no responde → ejecutar el hook equivalente
- Documentar ambos cuando se añade una tool nueva

### Patrón de implementación

```python
@mcp.tool(description="Descripción clara de qué hace la tool")
def nombre_tool(param1: str, param2: str = "default") -> str:
    """Descripción docstring."""
    return _run_ps("hook-equivalente.ps1", param1, param2)
```

---

## §7 — Hooks

**Ubicación:** `hooks/*.ps1`
**Convención:** kebab-case, nombre descriptivo de la acción

### Estructura básica de un hook

```powershell
param(
    [Parameter(Mandatory)][string]$Param1,
    [string]$Param2 = "default"
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

# Validaciones
if (-not (Test-Path $Param1)) {
    Write-Error "Descripción del error"
    exit 1
}

# Lógica principal
# ...

# Output: JSON estructurado o texto plano
$result | ConvertTo-Json -Depth 10
```

**Regla:** toda herramienta que necesita PowerShell tiene un hook en `hooks/`.
Las tools MCP son el wrapper Python que llama al hook via `_run_ps()`.

---

## §8 — References

**Ubicación:** `references/*.md`
**Uso:** leídas por agentes con `Read $SKILL_DIR\references\<nombre>.md`

| Archivo | Contenido |
|---------|-----------|
| `arquitectura.md` | Arquitectura de las soluciones ScacsWeb (capas, proyectos) |
| `bd.md` | Contexto de BD: Oracle 19c, SQL Server, patrones de acceso |
| `conventions.md` | Naming conventions, coding standards ScacsWeb |
| `dalc-patterns.md` | Patrones DALC (Data Access Layer Component) |
| `dmd-format.md` | Formato del modelo de BD (DMD) |
| `encuadre-checklist.md` | Checklist de patrones tarea/contexto/alcance para sharpear requerimientos vagos (Mantis, planner) — subconjunto adaptado de la skill `prompt-master` |
| `hooks.md` | Tabla completa Preferente (MCP) / Fallback (hook) |
| `json-schema.md` | Esquemas JSON usados por el MCP server |
| `mantis.md` | Configuración MantisBT, credenciales, endpoints (read+write) |
| `mcp.md` | Documentación del MCP server (tools, parámetros, ejemplos) |
| `testing.md` | Estrategia de testing, patrones de tests xUnit |
| `troubleshooting.md` | Soluciones a problemas frecuentes |

---

## §9 — Cómo extender el plugin

### Regla general

Antes de crear cualquier artefacto:
1. Leer este documento (§9 y §10)
2. Leer el/los archivo(s) plantilla correspondiente(s)
3. Leer los archivos que se van a editar
4. No escribir nada antes de presentar el plan y obtener aprobación

---

### §9.1 — Nuevo modo directo

Un modo directo tiene 3 componentes:

**Componente 1: `skills/<nombre>/SKILL.md`**

```yaml
---
name: <nombre>
metadata:
  version: "X.Y.Z"
description: '<triggers claros. Frases exactas del usuario que disparan este modo>'
---

# PASO 0 — OBLIGATORIO
[copiar de skills/orchestrator-agent/SKILL.md]

# <Nombre del modo>

<Breve descripción del modo>

## Proceso

1. Leer el agente: `Read $SKILL_DIR\agents\<nombre>.md`
2. Seguir las instrucciones del agente inline
```

**Componente 2: `agents/<nombre>.md`**

Copiar el patrón de `agents/auditoria.md`:

```markdown
name: orchestrator-<nombre>

# Rol

<descripción del rol>

# Objetivo

<qué hace>

# Proceso

[pasos detallados]
```

**Componente 3: Fila en `skills/orchestrator-agent/SKILL.md` (tabla `# Modos directos`)**

```markdown
| Nuevo modo | `/orchestrator-<nombre>`, "<frase trigger>" | `$SKILL_DIR\agents\<nombre>.md` |
```

**Archivos a crear/editar:**
- `skills/<nombre>/SKILL.md` — CREAR
- `agents/<nombre>.md` — CREAR
- `skills/orchestrator-agent/SKILL.md` — EDITAR (añadir fila en tabla)

---

### §9.2 — Nueva tool MCP + hook equivalente

**Componente 1: Tool en `mcp/orchestrator-workspace-server.py`**

Añadir al final del archivo antes de `if __name__ == "__main__":`:

```python
@mcp.tool(description="Descripción clara. Mencionar parámetros y lo que devuelve.")
def nombre_tool(workspace: str, param: str) -> str:
    """Descripción docstring."""
    return _run_ps("nombre-hook.ps1", workspace, param)
```

**Componente 2: `hooks/nombre-hook.ps1`**

Copiar la estructura de un hook existente de la misma categoría.

**Sincronización:**
- `references/mcp.md` — documentar la nueva tool
- `references/hooks.md` — añadir fila Preferente/Fallback

---

### §9.3 — Nueva skill standalone

Una skill standalone (sin modo directo asociado, como `mantis` o `plugin-dev`):

**Componente único: `skills/<nombre>/SKILL.md`**

Igual que §9.1 componente 1, pero más completa — toda la lógica va en el SKILL.md, sin agente separado. Puede leer agentes existentes si los necesita.

**Archivos a crear:**
- `skills/<nombre>/SKILL.md` — CREAR

---

### §9.4 — Nueva reference

Añadir contexto técnico que los agentes deben poder leer:

```markdown
# <Título>

[contenido técnico]
```

**Archivos a crear:**
- `references/<nombre>.md` — CREAR

Documentar en `references/mcp.md` o `references/hooks.md` si es relevante para esas áreas.

---

### §9.6 — Nuevo slash command (`commands/`)

Los ficheros en `commands/` registran modos directos como slash commands discoverables en el menú
`/` de Claude Code. Cada fichero tiene nombre kebab-case igual al comando sin la barra.

**Componente único: `commands/<nombre>.md`**

```markdown
---
description: "<descripción visible en el menú />"
argument-hint: "<argumentos>"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in <modo> mode.

Usage: /orchestrator-<modo> <args>
Example: /orchestrator-<modo> ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\<agente>.md` inline
and follow its instructions. Pass `sln_path` = $ARGUMENTS, `workspace` = cwd. Relay output verbatim.
```

Para modos con detección de VCS añadir antes de leer el agente:
```
Call `detect_vcs(workspace)` first — if "none", inform the user and stop.
```

**Archivos a crear:**
- `commands/<nombre>.md` — CREAR

**Regla:** el nuevo slash command debe corresponder a un modo directo ya existente o uno nuevo
completo (§9.1). No crear `commands/<nombre>.md` sin su agente y su fila en la tabla de modos.

---

### §9.5 — Cambio de manifest / infraestructura

Para cambios en `.mcp.json`, `plugin.json` (sin ser version bump), `.claude-plugin/`:

- Leer el archivo actual completo antes de editar
- Documentar el motivo del cambio en CHANGELOG.md
- Si cambia cómo se arranca el MCP → actualizar también `references/mcp.md`

---

## §10 — Puntos de sincronización de documentación

Después de cualquier cambio, ejecutar esta checklist **antes de reportar éxito**:

### Siempre (todo cambio)

- [ ] `CHANGELOG.md` — nueva entrada con la **versión ya bumpeada** y fecha
- [ ] `plugin.json` — versión bumpeada
- [ ] `marketplace.json` — versión bumpeada (debe ser idéntica a plugin.json)
- [ ] Commit git con mensaje descriptivo

### Nuevo modo directo (§9.1)

- [ ] `skills/<nombre>/SKILL.md` creado con PASO 0
- [ ] `agents/<nombre>.md` creado
- [ ] `skills/orchestrator-agent/SKILL.md` — tabla `# Modos directos` actualizada
- [ ] `README.md` — si el modo es visible al usuario

### Nueva tool MCP (§9.2)

- [ ] Tool añadida a `mcp/orchestrator-workspace-server.py`
- [ ] Hook equivalente creado en `hooks/`
- [ ] `references/mcp.md` — documentada la nueva tool
- [ ] `references/hooks.md` — añadida fila Preferente/Fallback

### Nueva skill standalone (§9.3)

- [ ] `skills/<nombre>/SKILL.md` creado con PASO 0
- [ ] `README.md` — si la skill es visible al usuario

### Nuevo slash command (§9.6)

- [ ] `commands/<nombre>.md` creado
- [ ] Agente correspondiente existe en `agents/`
- [ ] Modo directo registrado en tabla de `skills/orchestrator-agent/SKILL.md`

### Cambio de anatomía del plugin

- [ ] Este archivo `docs/plugin-architecture.md` actualizado

### Semver para el version bump

| Tipo de cambio | Bump |
|----------------|------|
| Fix de bug, corrección de doc, ajuste de texto | **patch** (X.Y.Z+1) |
| Nuevo modo, tool, hook, skill, reference | **minor** (X.Y+1.0) |
| Cambio incompatible (rename, eliminación, contrato MCP) | **major** (X+1.0.0) |

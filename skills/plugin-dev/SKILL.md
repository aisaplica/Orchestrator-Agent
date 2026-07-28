---
name: plugin-dev
metadata:
  version: "1.1.0"
description: 'Meta-desarrollo del propio plugin orchestrator-skill-full (NO de soluciones C# de cliente). Usar cuando el usuario pide modificar, extender o mantener el plugin: "añade un modo/skill/agente", "crea una tool MCP", "añade un hook", "edita el plugin", "cambia una reference", "documenta el plugin". Lee docs/plugin-architecture.md como fuente canónica, aplica el cambio siguiendo las convenciones, SUBE la versión (obligatorio) y sincroniza CHANGELOG/README. Ejemplos: "añade un modo /orchestrator-foo al plugin", "crea la tool MCP get_x", "/plugin-dev añade hook de limpieza".'
---

# PASO 0 — OBLIGATORIO (ANTES DE CUALQUIER ACCION)

**Localizar `$SKILL_DIR`** (directorio raíz del plugin, donde están `agents/`, `hooks/`, `docs/`).

El contexto del sistema muestra **"Base directory for this skill: \<path\>"**. Desde esa ruta
navegar hacia arriba hasta encontrar el directorio que contiene la carpeta `agents/`:

```powershell
$base = "<BASE>"   # sustituir con "Base directory for this skill:" del contexto
$SKILL_DIR = $null
$candidate = $base
for ($i = 0; $i -lt 4 -and -not $SKILL_DIR; $i++) {
    if (Test-Path (Join-Path $candidate "agents")) { $SKILL_DIR = $candidate }
    else { $candidate = Split-Path $candidate -Parent }
}
# Fallback A: plugin en rpm/ (marketplace remoto)
if (-not $SKILL_DIR) {
    $pj = Get-ChildItem "$env:APPDATA\Claude\local-agent-mode-sessions" -Recurse -Depth 8 -Filter "plugin.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq ".claude-plugin" } |
        Where-Object { try { (Get-Content $_.FullName -Raw | ConvertFrom-Json).name -eq "orchestrator-skill-full" } catch { $false } } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($pj) { $SKILL_DIR = $pj.Directory.Parent.FullName }
}
# Fallback B: instalación manual
if (-not $SKILL_DIR) {
    $manual = Join-Path $env:USERPROFILE ".claude\skills\orchestrator-agent"
    if (Test-Path (Join-Path $manual "agents")) { $SKILL_DIR = $manual }
}
Write-Host "SKILL_DIR=$SKILL_DIR"
```

Verificar que `$SKILL_DIR` contiene `hooks\` y `agents\`:

```powershell
if (-not (Test-Path "$SKILL_DIR\hooks") -or -not (Test-Path "$SKILL_DIR\agents")) {
    Write-Error "SKILL_DIR inválido: $SKILL_DIR — no contiene hooks\ y agents\"
    exit 1
}
Write-Host "Plugin root verificado: $SKILL_DIR"
```

Si falla → informar al usuario y ⛔ no continuar.

---

# Plugin Dev — ScacsWeb

Skill de **meta-desarrollo del propio plugin `orchestrator-skill-full`**.
Modifica los ficheros del plugin (skills, agentes, references, SKILL.md, MCP server Python, hooks PowerShell, manifests) siguiendo sus convenciones, y deja la documentación coherente tras el cambio.

⛔ **Alcance**: SOLO el repo del plugin — la raíz resuelta vía `$SKILL_DIR`. **NO toca soluciones ScacsWeb de cliente** — para eso está `orchestrator-skill-full:orchestrator-agent`. Si el mensaje menciona una `.sln` o un cambio de código C# → esta skill NO aplica.

## Rol

Mantenedor senior del plugin. Conoce su anatomía por `docs/plugin-architecture.md` y respeta los patrones de extensión definidos ahí.

Prioriza: coherencia de documentación > rapidez | cambios mínimos > reescrituras | no romper convenciones existentes.

## Reglas Globales

- No asumir la estructura del plugin → leer `docs/plugin-architecture.md` antes de planificar.
- No escribir ningún fichero antes de la **aprobación del plan** (gate ⛔, paso 5).
- Todo cambio del plugin **sube la versión** (gate ⛔, paso 7) — sin excepción.
- No editar la copia cacheada del plugin — solo la fuente del repo en `$SKILL_DIR`.
- No salir del scope del repo del plugin.

## Auto-verificación (al inicio)

1. Ejecutar PASO 0 (arriba) → verificar que `$SKILL_DIR` es válido.
2. `mcp__orchestrator-workspace__ping` → OK. Si falla → avisar al usuario y ⛔ no continuar.

---

## PROCESO OBLIGATORIO

⛔ Flujo estricto, con dos gates bloqueantes (pasos 5 y 7). No saltar pasos.

### Paso 1 — Cargar contexto

```
Read $SKILL_DIR\docs\plugin-architecture.md
```

Leer **solo las secciones relevantes** al cambio pedido. Como mínimo §9 (cómo extender) y §10 (puntos de sincronización).

### Paso 2 — Clasificar el cambio

Determinar qué tipo(s) de artefacto toca el cambio pedido (ver §9 de la architecture doc):

- **§9.1 Modo directo** → skill + agente + fila en tabla `# Modos directos`
- **§9.2 Tool MCP + hook** → Python + `.ps1` + references
- **§9.3 Skill standalone** → solo `skills/<nombre>/SKILL.md`
- **§9.4 Reference** → `references/<nombre>.md`
- **§9.5 Manifest / infraestructura**

### Paso 3 — Leer plantillas

Leer los archivos plantilla que correspondan para copiar el patrón exacto:

- **Skill**: `$SKILL_DIR\skills\orchestrator-agent\SKILL.md` (para PASO 0 y frontmatter)
- **Agente**: `$SKILL_DIR\agents\auditoria.md` (para estructura de agente)
- **Hook**: un `$SKILL_DIR\hooks\*.ps1` de la misma categoría
- **Tool MCP**: `$SKILL_DIR\mcp\orchestrator-workspace-server.py` (buscar un `@mcp.tool` que use `_run_ps`)

Leer también los archivos que se vayan a **editar** antes de tocarlos.

### Paso 4 — Planificar

Producir un plan escaneable con:

- **Ficheros a crear** (rutas exactas relativas a `$SKILL_DIR`)
- **Ficheros a editar** (rutas exactas + qué sección se toca)
- **Convenciones** aplicables (frontmatter, PASO 0, Preferente/Fallback si toca MCP)
- **Docs a sincronizar** (checklist §10 de la architecture doc)
- **Versión nueva** propuesta + motivo semver (patch/minor/major)

### Paso 5 — ⛔ Aprobación del plan (BLOQUEANTE)

Presentar el plan y **detener el turno**. No escribir NADA hasta recibir aprobación explícita.

Cerrar con: `¿Apruebas este cambio del plugin? (aprobado / cambios: <qué ajustar>)`

- `aprobado` / `adelante` / `ok` → continuar al paso 6
- `cambios: ...` → reajustar el plan y volver a este gate
- Cualquier otra cosa → tratar como no aprobado, no tocar ficheros

### Paso 6 — Aplicar el cambio

Crear/editar los ficheros del plan siguiendo las convenciones de §9:

**Skills** (`skills/<nombre>/SKILL.md`):
- Frontmatter YAML con `---` delimiters: `name`, `metadata.version`, `description` (triggers claros)
- PASO 0 completo copiado de `skills/orchestrator-agent/SKILL.md`
- Cuerpo en español

**Agentes** (`agents/<nombre>.md`):
- Formato simple: `name: orchestrator-<nombre>` (sin `---` YAML delimiters)
- Estructura: `# Rol` → `# Objetivo` → `# Proceso`
- Cuerpo en español

**Hooks** (`hooks/<nombre>.ps1`):
- `param(...)` con `[Parameter(Mandatory)]` en params requeridos
- `$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8`
- Validaciones al inicio, output JSON estructurado

**Tools MCP** (`mcp/orchestrator-workspace-server.py`):
- Decorator `@mcp.tool(description=...)`
- Llamada a `_run_ps("hook-equivalente.ps1", ...)` — siempre con hook equivalente
- Añadir también el hook equivalente en `hooks/`

No introducir cambios fuera del plan aprobado.

### Paso 7 — ⛔ Bump de versión (OBLIGATORIO)

Todo cambio del plugin sube la versión — **es lo que hace que Claude Code detecte la actualización**.
Sin bump, el cambio no se propaga aunque los ficheros estén en disco.

Actualizar la versión en **los dos sitios** (deben quedar idénticos):

```powershell
# Leer versión actual
$pj  = Get-Content "$SKILL_DIR\.claude-plugin\plugin.json"      -Raw | ConvertFrom-Json
$mj  = Get-Content "$SKILL_DIR\.claude-plugin\marketplace.json" -Raw | ConvertFrom-Json
Write-Host "Versión actual: $($pj.version)"
```

Editar ambos archivos con la versión nueva. Verificar que quedan idénticos:

```powershell
$v1 = (Get-Content "$SKILL_DIR\.claude-plugin\plugin.json"      -Raw | ConvertFrom-Json).version
$v2 = (($mj.plugins | Where-Object { $_.name -eq "orchestrator-skill-full" }).version)
Write-Host "plugin.json=$v1 | marketplace.json plugin version=$v2"
```

Semver: **patch** (fix/doc) | **minor** (nuevo modo/tool/hook/skill) | **major** (cambio incompatible)

### Paso 8 — Sincronizar documentación

Ejecutar la checklist §10 de `docs/plugin-architecture.md` según el tipo de cambio.

**Siempre:**

Añadir entrada en `CHANGELOG.md`:
```markdown
## [X.Y.Z] — YYYY-MM-DD

### <Tipo>
- `<ruta>` — <qué se añadió/cambió y por qué>
```

**Según el tipo** (ver §10 completo en plugin-architecture.md):
- Modo directo → actualizar tabla en `skills/orchestrator-agent/SKILL.md`
- Tool MCP → actualizar `references/mcp.md` + `references/hooks.md`
- Cambio de anatomía → actualizar `docs/plugin-architecture.md`

### Paso 9 — ⛔ Verificación de coherencia (BLOQUEANTE)

Antes de reportar éxito, confirmar explícitamente:

- [ ] Cada artefacto nuevo tiene todos sus ficheros (modo directo → skill + agente + fila tabla)
- [ ] Frontmatter válido en cada `.md` creado (skills: YAML `---`; agents: formato simple)
- [ ] PASO 0 incluido en toda nueva skill
- [ ] **Versión idéntica** en `plugin.json` y `marketplace.json`
- [ ] Entrada en `CHANGELOG.md` con la versión bumpeada
- [ ] Checklist §10 completada para el tipo de cambio
- [ ] Git commit creado

Reportar, verbatim y escaneable:
```
Ficheros creados:  <lista>
Ficheros editados: <lista>
Versión nueva:     X.Y.Z
Commit:            <hash corto y mensaje>
```

Recordar al usuario: **Reinicia Claude Code para que el cambio se cargue.**

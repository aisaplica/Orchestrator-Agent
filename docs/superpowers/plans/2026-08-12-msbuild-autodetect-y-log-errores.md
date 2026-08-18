# MSBuild Autodetect + Log Errores Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (1) auto-detectar el compilador correcto en `compile_check` leyendo los `.csproj`, eliminando el falso "no compila" en soluciones WebForms; (2) añadir un comando `/orchestrator-log-errores` que parsea logs de producción ASP.NET, deduplica errores por firma y propone tareas Mantis.

**Architecture:**
- Punto 1: `hooks/lib-msbuild.ps1` (detector) + `hooks/compile-check.ps1` (compilador con autodetección). El MCP ya llama a `compile-check.ps1` pero el archivo no existe — esta es la causa actual de que `compile_check` falle en cualquier workspace.
- Punto 3: `hooks/parse-weblog.ps1` (parser de log → JSON agregado) + tool MCP `parse_web_log` + `agents/log-errores.md` (skill Mantis-only) + `commands/orchestrator-log-errores.md`. El agente recibe solo el JSON deduplicado — el log crudo nunca entra en contexto.

**Tech Stack:** PowerShell 5.1, Python 3, FastMCP, MantisBT REST API v1.

---

## Subsistema A — MSBuild Autodetect (Punto 1)

### Task 1: hooks/lib-msbuild.ps1

**Files:**
- Create: `hooks/lib-msbuild.ps1`

- [ ] **Step 1: Crear hooks/lib-msbuild.ps1**

Puerto directo de `rs-enterprise-plugin/hooks/lib-msbuild.ps1`. Es genérico (no tiene referencias RS-específicas).

```powershell
# hooks/lib-msbuild.ps1
#Requires -Version 5.1
<#
.SYNOPSIS
    Decide con qué compilador construir una .sln — MSBuild de Visual Studio o CLI `dotnet` —
    leyendo los proyectos de la solución. Librería: dot-sourcear desde el hook que la necesite.

.DESCRIPTION
    ⛔ POR QUÉ EXISTE. El hook previo llamaba siempre a `dotnet`. En soluciones ScacsWeb Online
    (WebForms .NET Framework) eso falla con MSB4019 — `dotnet` no trae
    `Microsoft.WebApplication.targets`. Y el parser de diagnósticos solo reconocía `CS####`,
    así que el MSB4019 real quedaba invisible: error_count=0 con exit_code=1.
    Resultado: el validator reportaba "compilación no verificada" y había que compilar a mano.
    ⛔ Ante la duda, MSBuild. MSBuild compila también SDK-style; `dotnet` NO compila .NET Framework.
#>

$script:OrchestratorMsBuildPath = $null
$script:OrchestratorVsTestPath  = $null

function Test-OrchestratorTfmFramework {
    param([string]$Tfm)
    if ([string]::IsNullOrWhiteSpace($Tfm)) { return $false }
    foreach ($t in ($Tfm -split ';')) {
        $valor = $t.Trim()
        if (-not $valor) { continue }
        if ($valor -match '^(?i)v\d')     { return $true }
        if ($valor -match '^(?i)net\d+$') { return $true }
    }
    return $false
}

function Get-OrchestratorProyectoInfo {
    param([Parameter(Mandatory=$true)][string]$ProjectPath, [string]$Nombre = "")

    if (-not $Nombre) { $Nombre = [System.IO.Path]::GetFileNameWithoutExtension($ProjectPath) }

    $info = [ordered]@{
        name             = $Nombre
        project          = $ProjectPath
        exists           = $false
        sdk_style        = $false
        legacy           = $false
        target_framework = ""
        framework_full   = $false
        com              = $false
        web              = $false
    }

    if (-not (Test-Path -LiteralPath $ProjectPath)) { return [pscustomobject]$info }
    $info.exists = $true

    $xml = Get-Content -LiteralPath $ProjectPath -Encoding UTF8 -Raw
    if (-not $xml) { return [pscustomobject]$info }

    $info.sdk_style = ($xml -match '(?i)<Project[^>]*\sSdk\s*=') -or ($xml -match '(?i)<Import[^>]*\sSdk\s*=')
    $info.legacy    = -not $info.sdk_style

    if     ($xml -match '(?i)<TargetFrameworks?>\s*([^<]+?)\s*</TargetFrameworks?>')          { $info.target_framework = $Matches[1] }
    elseif ($xml -match '(?i)<TargetFrameworkVersion>\s*([^<]+?)\s*</TargetFrameworkVersion>') { $info.target_framework = $Matches[1] }

    $info.framework_full = Test-OrchestratorTfmFramework -Tfm $info.target_framework
    $info.com = ($xml -match '(?i)<COMReference|<COMFileReference')
    $info.web = ($xml -match '(?i)Microsoft\.WebApplication\.targets') -or
                ($xml -match '(?i)\{349c5851-65df-11da-9384-00065b846f21\}')

    return [pscustomobject]$info
}

function Get-OrchestratorProyectosSln {
    param([Parameter(Mandatory=$true)][string]$SlnPath)

    $slnDir    = Split-Path -Parent $SlnPath
    $proyectos = @()

    foreach ($linea in (Get-Content -LiteralPath $SlnPath -Encoding UTF8)) {
        if ($linea -notmatch 'Project\([^)]+\)\s*=\s*"([^"]+)",\s*"([^"]+\.(?:csproj|vbproj))"') { continue }
        $nombre = $Matches[1].Trim()
        $rel    = $Matches[2].Trim().Replace('/', '\')
        $ruta   = [System.IO.Path]::GetFullPath((Join-Path $slnDir $rel))
        $proyectos += (Get-OrchestratorProyectoInfo -ProjectPath $ruta -Nombre $nombre)
    }

    return ,@($proyectos)
}

function Get-OrchestratorVsWherePaths {
    return @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'),
        (Join-Path $env:ProgramFiles        'Microsoft Visual Studio\Installer\vswhere.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
}

function Find-OrchestratorMsBuild {
    if ($script:OrchestratorMsBuildPath) { return $script:OrchestratorMsBuildPath }

    foreach ($vswhere in (Get-OrchestratorVsWherePaths)) {
        try {
            $ruta = & $vswhere -products * -sort -requires Microsoft.Component.MSBuild `
                        -find 'MSBuild\**\Bin\MSBuild.exe' 2>$null | Select-Object -First 1
        } catch { $ruta = $null }
        if ($ruta -and (Test-Path -LiteralPath $ruta)) {
            $script:OrchestratorMsBuildPath = $ruta
            return $ruta
        }
    }

    $enPath = Get-Command 'msbuild.exe' -ErrorAction SilentlyContinue
    if ($enPath) {
        $script:OrchestratorMsBuildPath = $enPath.Source
        return $script:OrchestratorMsBuildPath
    }

    return $null
}

function Find-OrchestratorVsTestConsole {
    if ($script:OrchestratorVsTestPath) { return $script:OrchestratorVsTestPath }

    foreach ($vswhere in (Get-OrchestratorVsWherePaths)) {
        try {
            $ruta = & $vswhere -products * -sort `
                        -find 'Common7\IDE\CommonExtensions\Microsoft\TestWindow\vstest.console.exe' 2>$null |
                        Select-Object -First 1
        } catch { $ruta = $null }
        if ($ruta -and (Test-Path -LiteralPath $ruta)) {
            $script:OrchestratorVsTestPath = $ruta
            return $ruta
        }
    }

    $enPath = Get-Command 'vstest.console.exe' -ErrorAction SilentlyContinue
    if ($enPath) {
        $script:OrchestratorVsTestPath = $enPath.Source
        return $script:OrchestratorVsTestPath
    }

    return $null
}

function Get-OrchestratorBuildToolchain {
    param(
        [Parameter(Mandatory=$true)][string]$SlnPath,
        [ValidateSet('auto','dotnet','msbuild')][string]$Preferencia = 'auto'
    )

    $proyectos = @(Get-OrchestratorProyectosSln -SlnPath $SlnPath)
    $legibles  = @($proyectos | Where-Object { $_.exists })
    $motivos   = @()

    foreach ($p in $legibles) {
        if ($p.framework_full)     { $motivos += "$($p.name): TFM '$($p.target_framework)' (.NET Framework)" }
        elseif ($p.legacy)         { $motivos += "$($p.name): .csproj en formato antiguo (no SDK-style)" }
        if ($p.web)                { $motivos += "$($p.name): proyecto web (Microsoft.WebApplication.targets)" }
        if ($p.com -and $p.legacy) { $motivos += "$($p.name): COMReference" }
    }
    $motivos  = @($motivos | Select-Object -Unique)
    $requiere = $motivos.Count -gt 0

    $builder = if ($Preferencia -eq 'auto') { if ($requiere) { 'msbuild' } else { 'dotnet' } } else { $Preferencia }

    if ($requiere) {
        $muestra = @($motivos | Select-Object -First 5) -join '; '
        if ($motivos.Count -gt 5) { $muestra += " (y $($motivos.Count - 5) más)" }
        $reason = "MSBuild de Visual Studio — $muestra"
    } elseif ($legibles.Count -eq 0) {
        $reason = "No se pudo leer ningún proyecto; se asume dotnet"
    } else {
        $reason = "CLI dotnet — todos los proyectos ($($legibles.Count)) son SDK-style .NET moderno"
    }

    $resultado = [ordered]@{
        builder              = $builder
        builder_path         = $null
        requires_msbuild     = $requiere
        reason               = $reason
        forced               = ($Preferencia -ne 'auto')
        projects_unreadable  = @($proyectos | Where-Object { -not $_.exists }).Count
        projects             = @($proyectos | ForEach-Object {
            [ordered]@{
                name             = $_.name
                target_framework = $_.target_framework
                sdk_style        = $_.sdk_style
                web              = $_.web
                com              = $_.com
                exists           = $_.exists
            }
        })
        error                = $null
    }

    if ($builder -eq 'msbuild') {
        $ruta = Find-OrchestratorMsBuild
        if ($ruta) { $resultado.builder_path = $ruta }
        else {
            $resultado.error = "Esta solución necesita MSBuild de Visual Studio ($reason) y no se encontró: " +
                               "ni vswhere.exe en 'Microsoft Visual Studio\Installer', ni msbuild.exe en PATH. " +
                               "Instala Visual Studio o Build Tools. ⛔ Compilación NO verificada: " +
                               "problema de entorno, NO un fallo del código."
        }
    } else {
        $enPath = Get-Command 'dotnet' -ErrorAction SilentlyContinue
        if ($enPath) { $resultado.builder_path = $enPath.Source }
        else {
            $resultado.error = "dotnet CLI no encontrado en PATH. ⛔ Compilación NO verificada: " +
                               "problema de entorno, NO un fallo del código."
        }
    }

    return $resultado
}
```

- [ ] **Step 2: Verificar que el archivo tiene BOM UTF-8**

El convenio del plugin es que los `.ps1` llevan BOM. Guardar con el encoding correcto — VS Code lo hace por defecto en Windows. Verificar con:

```powershell
$bytes = [IO.File]::ReadAllBytes("C:\Desarrollo\GIT\ScacsWeb\IA\Orchestrator-Agent\hooks\lib-msbuild.ps1")
Write-Host "BOM: $($bytes[0].ToString('x2')) $($bytes[1].ToString('x2')) $($bytes[2].ToString('x2'))"
# Esperado: ef bb bf
```

- [ ] **Step 3: Commit**

```bash
git add hooks/lib-msbuild.ps1
git commit -m "feat(hooks): lib-msbuild.ps1 — autodetectar compilador MSBuild vs dotnet"
```

---

### Task 2: hooks/compile-check.ps1

**Files:**
- Create: `hooks/compile-check.ps1`

> **Contexto:** el MCP ya llama a este hook (`_run_ps("compile-check.ps1", ...)`) pero el archivo no existe. Esto causa que `compile_check` falle con un error genérico de PS en cualquier workspace.

- [ ] **Step 1: Crear hooks/compile-check.ps1**

```powershell
# hooks/compile-check.ps1
#Requires -Version 5.1
<#
.SYNOPSIS
    Compila la solución y devuelve errores/warnings como JSON.
    El compilador se AUTODETECTA leyendo los .csproj (lib-msbuild.ps1):
    MSBuild si hay proyectos .NET Framework / WebForms / COM, dotnet si todos son SDK-style modernos.

.PARAMETER SlnPath
    Ruta completa al .sln

.PARAMETER NoRestore
    Omite restore NuGet (más rápido cuando restore ya se hizo)

.PARAMETER Builder
    auto (default) | dotnet | msbuild  — fuerza el compilador
#>
param(
    [Parameter(Mandatory=$true)][string]$SlnPath,
    [switch]$NoRestore,
    [ValidateSet('auto','dotnet','msbuild')][string]$Builder = 'auto'
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib-msbuild.ps1")

if (-not (Test-Path $SlnPath)) {
    @{ success = $false; error = "Archivo no encontrado: $SlnPath" } | ConvertTo-Json -Compress
    exit 1
}

$toolchain = Get-OrchestratorBuildToolchain -SlnPath $SlnPath -Preferencia $Builder

if ($toolchain.error) {
    @{
        success        = $false
        builder        = $toolchain.builder
        builder_error  = $toolchain.error
        builder_reason = $toolchain.reason
        error_count    = 0
        warning_count  = 0
        errors         = @()
        warnings       = @()
    } | ConvertTo-Json -Depth 4 -Compress
    exit 1
}

# Forzar idioma inglés: en máquinas con CLI localizado MSBuild emite "advertencia CS0168"
# en vez de "warning CS0168" y el parser perdería todos los warnings sin avisar.
$idiomaPrevio = $env:DOTNET_CLI_UI_LANGUAGE
$vslangPrevio = $env:VSLANG
$env:DOTNET_CLI_UI_LANGUAGE = "en"
$env:VSLANG = "1033"

try {
    if ($toolchain.builder -eq 'msbuild') {
        $buildArgs = @($SlnPath, "-t:Build", "-v:minimal", "-nologo", "-nodeReuse:false")
        if (-not $NoRestore) { $buildArgs = @("-restore") + $buildArgs }
    } else {
        $buildArgs = @("build", $SlnPath, "-v", "quiet", "--nologo")
        if ($NoRestore) { $buildArgs += "--no-restore" }
    }

    # ErrorActionPreference = Continue durante la llamada:
    # con Stop, cualquier línea por stderr del compilador sería un error terminante
    # y el hook moriría sin JSON justo cuando hay algo que reportar.
    $eapPrevio = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $raw      = & $toolchain.builder_path @buildArgs 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $eapPrevio
} finally {
    $env:DOTNET_CLI_UI_LANGUAGE = $idiomaPrevio
    $env:VSLANG = $vslangPrevio
}

# Parsear errores/warnings del compilador.
# Acepta: CS####, MSB####, NU#### (restore), cualquier [A-Za-z]+\d+ — no solo CS####.
# Acepta "advertencia"/"aviso" además de "warning" — por si el SDK ignora el env var.
$diagnostics = @()
foreach ($line in $raw) {
    $texto = "$line"
    if ($texto -match '^(.+)\((\d+),(\d+)\):\s+(error|warning|advertencia|aviso)\s+([A-Za-z]+\d+):\s+(.+?)(\s+\[.+\])?$') {
        $sev = $Matches[4].ToLowerInvariant()
        if ($sev -eq "advertencia" -or $sev -eq "aviso") { $sev = "warning" }
        $diagnostics += @{ file = $Matches[1].Trim(); line = [int]$Matches[2]; col = [int]$Matches[3]; severity = $sev; code = $Matches[5]; message = $Matches[6].Trim() }
    } elseif ($texto -match '^(?:(.+?)\s*:\s*)?(error|warning|advertencia|aviso)\s+([A-Za-z]+\d+):\s+(.+?)(\s+\[.+\])?$') {
        $sev = $Matches[2].ToLowerInvariant()
        if ($sev -eq "advertencia" -or $sev -eq "aviso") { $sev = "warning" }
        $diagnostics += @{ file = if ($Matches[1]) { $Matches[1].Trim() } else { "" }; line = 0; col = 0; severity = $sev; code = $Matches[3]; message = $Matches[4].Trim() }
    }
}

$errors   = @($diagnostics | Where-Object { $_.severity -eq "error" })
$warnings = @($diagnostics | Where-Object { $_.severity -eq "warning" })

@{
    success        = ($exitCode -eq 0)
    exit_code      = $exitCode
    builder        = $toolchain.builder
    builder_path   = $toolchain.builder_path
    builder_reason = $toolchain.reason
    builder_forced = $toolchain.forced
    projects       = $toolchain.projects
    error_count    = $errors.Count
    warning_count  = $warnings.Count
    errors         = $errors
    warnings       = $warnings
    raw_lines      = if ($exitCode -ne 0 -and $diagnostics.Count -eq 0) { @($raw | Where-Object { $_ -match '\S' }) } else { @() }
} | ConvertTo-Json -Depth 4 -Compress
```

- [ ] **Step 2: Verificar ejecución básica contra una .sln real**

```powershell
cd "C:\Desarrollo\GIT\ScacsWeb\IA\Orchestrator-Agent"
$result = powershell -NoProfile -ExecutionPolicy Bypass -File ".\hooks\compile-check.ps1" `
    "<ruta-real-a-alguna.sln>" -NoRestore | ConvertFrom-Json
Write-Host "builder: $($result.builder)"
Write-Host "builder_reason: $($result.builder_reason)"
Write-Host "success: $($result.success)"
```

Esperado en un proyecto WebForms: `builder: msbuild`.
Esperado en un proyecto Batch SDK-style: `builder: dotnet`.

- [ ] **Step 3: Commit**

```bash
git add hooks/compile-check.ps1
git commit -m "feat(hooks): compile-check.ps1 — compilar con autodetección MSBuild/dotnet"
```

---

### Task 3: Actualizar compile_check en el MCP

**Files:**
- Modify: `mcp/orchestrator-workspace-server.py:527-537`

- [ ] **Step 1: Añadir parámetro `builder` y actualizar descripción**

Localizar el bloque actual (líneas ~527-537) y reemplazarlo:

```python
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
```

- [ ] **Step 2: Actualizar descripción de `validate_solution` (línea ~497)**

La descripción actual es genérica. No cambia la lógica, solo la descripción:

```python
@mcp.tool(description="Confirma que la .sln existe y es accesible. Usar en paso 1 del pipeline antes de parse-sln.")
def validate_solution(sln_path: str) -> str:
    return json.dumps(_run_ps("validate-solution.ps1", sln_path), ensure_ascii=False, separators=(",",":"))
```

- [ ] **Step 3: Reiniciar el MCP y verificar**

El MCP arranca solo si Claude Code lo necesita. Para verificar que el nuevo `compile_check` llega:

```bash
# En el workspace de ScacsWeb, en una sesión nueva de Claude Code:
# mcp__orchestrator-workspace__compile_check(sln_path="<ruta.sln>")
# Verificar que la respuesta incluye campo "builder" y "builder_reason"
```

- [ ] **Step 4: Actualizar agents/validator.md — Paso 1**

En `agents/validator.md`, el Paso 1 documenta que el compilador no puede verificar .NET Framework. Con el nuevo hook eso ya no es verdad. Reemplazar el bloque de advertencia:

Localizar el texto actual en `agents/validator.md` que dice:
```
- Si dotnet no disponible o sln no compila por razones de entorno → marcar como "compilación no verificable" y aplicar solo paso 2.
```

Reemplazar por:
```
- Si `builder_error` presente → compilador necesario no instalado (entorno, no código): marcar como "compilación no verificable" y aplicar solo paso 2. Reportar el `builder_error` al usuario.
- `builder` informa qué compilador se usó (dotnet | msbuild) y `builder_reason` explica por qué.
```

- [ ] **Step 5: Commit**

```bash
git add mcp/orchestrator-workspace-server.py agents/validator.md
git commit -m "feat(mcp,agents): compile_check con autodetección builder + descripción validator"
```

---

## Subsistema B — Log Errores (Punto 3)

### Task 4: hooks/parse-weblog.ps1

**Files:**
- Create: `hooks/parse-weblog.ps1`

Puerto de `rs-enterprise-plugin/hooks/parse-weblog.ps1` con estas adaptaciones para ScacsWeb:
1. Eliminar `lib-pii.ps1` (no existe en nuestro plugin).
2. Mantener la redacción de literales SQL (`'...' → '<val>'`) inline — es la protección más crítica (evita datos de usuario dentro de un INSERT/WHERE en el ticket).
3. Eliminar `Remove-RsPii` (que cubría DNI/NIE/IBAN por forma). Puede añadirse en el futuro si se necesita.
4. Prefijos de función: `Orchestrator` en lugar de `Rs`.

- [ ] **Step 1: Crear hooks/parse-weblog.ps1**

```powershell
# hooks/parse-weblog.ps1
#Requires -Version 5.1
<#
.SYNOPSIS
    Parsea logs de error de la capa web (NLog/log4net, ELMAH XML, formato AgendaWeb AIS
    y volcados de stack .NET), agrupa las ocurrencias por FIRMA y devuelve solo el agregado.

.DESCRIPTION
    Un log repite el mismo fallo cientos de veces. Este hook colapsa las N ocurrencias
    de un mismo fallo en una firma con su recuento y una muestra — NUNCA emite el log completo.

    Firma = SHA1( tipo de excepción + frame más profundo de código propio + mensaje normalizado ).
    "Cliente 4711 no existe" y "Cliente 8322 no existe" son la misma firma.

    ⚠️ PII: los logs web llevan datos reales. Literales SQL entre comillas simples se redactan
    ('...' → '<val>') antes de salir en el JSON — es donde viaja la PII en los INSERT/WHERE
    del formato AgendaWeb. La redacción se aplica solo a la salida, nunca a la clave de firma.

    FORMATO AgendaWeb AIS. Cabecera:
        Error: (11/08/2026 13:45) - Codigo error: -2147467259 ... Descripción error: ORA-12899: ...
    Líneas siguientes: stack ("   en Clase.Metodo(...)").
    En este formato la excepción útil es el CÓDIGO (ORA-xxxxx o Codigo error: N), no el tipo .NET.

.PARAMETER Path
    Fichero de log o carpeta que los contiene.

.PARAMETER Glob
    Patrón de fichero cuando -Path es carpeta. Por defecto "*.log".

.PARAMETER Desde
    Fecha/hora ISO mínima (yyyy-MM-dd [HH:mm:ss]). Descarta eventos anteriores.

.PARAMETER Niveles
    Niveles a considerar, coma-separados. Por defecto "ERROR,FATAL".

.PARAMETER MaxSignatures
    Máximo de firmas distintas devueltas (las más frecuentes). Por defecto 30.

.PARAMETER Samples
    Muestras por firma. Por defecto 2.

.PARAMETER MaxLines
    Tope de líneas leídas en total. Por defecto 500000.

.EXAMPLE
    .\parse-weblog.ps1 -Path "C:\AIS\<Proyecto>\AgendaWeb\logs" -Desde 2026-08-01
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Glob = "*.log",
    [string]$Desde,
    [string]$Niveles = "ERROR,FATAL",
    [int]$MaxSignatures = 30,
    [int]$Samples = 2,
    [int]$MaxLines = 500000
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 8 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

if (-not (Test-Path -LiteralPath $Path)) { Fail "Ruta no encontrada: $Path" }

$item = Get-Item -LiteralPath $Path
if ($item.PSIsContainer) {
    $files = @(Get-ChildItem -LiteralPath $Path -Filter $Glob -File -Recurse -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending)
    if ($files.Count -eq 0) { Fail "Sin ficheros que casen con '$Glob' en $Path" }
} else {
    $files = @($item)
}

$desdeDt = $null
if ($Desde) {
    [datetime]$parsed = [datetime]::MinValue
    if ([datetime]::TryParse($Desde, [ref]$parsed)) { $desdeDt = $parsed }
    else { Fail "-Desde no es una fecha válida: $Desde" }
}

$nivelSet = @($Niveles -split ',' | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })

# --- Patrones ---
$rxStamp     = [regex]::new('^\s*[\[(]?(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:[.,]\d+)?|\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}(?::\d{2})?)')
$rxNivel     = [regex]::new('\b(FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b')
$rxExcepcion = [regex]::new('([A-Za-z_][\w.]*(?:Exception|Error))\b')
$rxFrame     = [regex]::new('(?:^|[\s\)])(?:at|en)\s+([\w.<>`+]+\.[\w<>`+]+)\s*\(')
$rxPlataforma = [regex]::new('^(System\.|Microsoft\.|mscorlib|Newtonsoft\.|lambda_method|NLog\.|log4net\.)')
$rxPantalla  = [regex]::new('([\w]+)\.(aspx|ascx)\.cs')

# Formato AgendaWeb AIS (rs-cerrores compatible)
$rxRsCab    = [regex]::new('^\s*([A-Za-z_][\w]*)\s*:\s*\(\s*(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\)\s*-')
$rxRsDesc   = [regex]::new('Descripci.{0,3}n\s+error:\s*(.*)$')
$rxRsCodigo = [regex]::new('Codigo\s+error:\s*(-?\d+)')
$rxOra      = [regex]::new('\bORA-\d{5}\b')
# Redacción de literales SQL: donde viajan los datos de usuario en INSERT/WHERE
$rxLiteral  = [regex]::new("'[^']{0,400}'")

function Get-OrchestratorNivelEtiqueta([string]$etiqueta) {
    if (-not $etiqueta) { return "" }
    if ($etiqueta -match '(?i)fatal')       { return "FATAL" }
    if ($etiqueta -match '(?i)error|fail')  { return "ERROR" }
    if ($etiqueta -match '(?i)warn')        { return "WARNING" }
    if ($etiqueta -match '(?i)info')        { return "INFO" }
    if ($etiqueta -match '(?i)debug')       { return "DEBUG" }
    if ($etiqueta -match '(?i)trace')       { return "TRACE" }
    return ""
}

function Normalizar([string]$t) {
    if (-not $t) { return "" }
    $t = [regex]::Replace($t, '[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}', '<guid>')
    $t = [regex]::Replace($t, '\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}:\d{2})?', '<fecha>')
    $t = [regex]::Replace($t, '\d{2}/\d{2}/\d{4}', '<fecha>')
    $t = [regex]::Replace($t, '[A-Za-z]:\\[^\s"'']+', '<ruta>')
    $t = [regex]::Replace($t, '0x[0-9a-fA-F]+', '<hex>')
    $t = [regex]::Replace($t, '\d+', '#')
    return $t.Trim()
}

function Get-OrchestratorCodificacion([string]$ruta) {
    # Sin BOM: prueba UTF-8 estricto; si falla, usa ANSI de la cultura actual.
    # Los logs de web .NET en Windows salen en la codepage ANSI — leerlos como UTF-8
    # convierte los acentos en U+FFFD y "Descripción error:" deja de casar.
    try {
        $bytes = New-Object byte[] 65536
        $fs = [IO.File]::OpenRead($ruta)
        try { $n = $fs.Read($bytes, 0, $bytes.Length) } finally { $fs.Dispose() }
        if ($n -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            return New-Object Text.UTF8Encoding($true)
        }
        while ($n -gt 0 -and ($bytes[$n - 1] -band 0xC0) -eq 0x80) { $n-- }
        if ($n -gt 0) { $n-- }
        $estricto = New-Object Text.UTF8Encoding($false, $true)
        [void]$estricto.GetString($bytes, 0, [Math]::Max($n, 0))
        return New-Object Text.UTF8Encoding($false)
    } catch {
        try {
            $cp = [int][Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
            try { [Text.Encoding]::RegisterProvider([Text.CodePagesEncodingProvider]::Instance) } catch { }
            return [Text.Encoding]::GetEncoding($cp)
        } catch { return [Text.Encoding]::Default }
    }
}

function Hash8([string]$t) {
    $sha = [Security.Cryptography.SHA1]::Create()
    try {
        $bytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($t))
        return (($bytes | ForEach-Object { $_.ToString("x2") }) -join '').Substring(0, 8)
    } finally { $sha.Dispose() }
}

function Recortar([string]$t, [int]$max) {
    if (-not $t) { return "" }
    $t = ($t -replace '[\x00-\x08\x0B\x0C\x0E-\x1F]', ' ').Trim()
    if ($t.Length -gt $max) { return $t.Substring(0, $max) + "..." }
    return $t
}

function Proteger([string]$t) {
    # Redacta literales SQL entre comillas simples ('...' → '<val>') para evitar
    # que datos de usuario dentro de INSERT/WHERE lleguen al ticket de Mantis.
    if (-not $t) { return $t }
    return $rxLiteral.Replace($t, "'<val>'")
}

# --- Acumulador ---
$firmas       = @{}
$totalEventos = 0
$lineas       = 0
$topeLineas   = $false
$formatos     = @{}

function Registrar($evento, $fichero) {
    $texto   = ($evento.Lineas -join "`n")
    $primera = $evento.Lineas[0]

    $frame = ""
    foreach ($l in $evento.Lineas) {
        foreach ($mF in $rxFrame.Matches($l)) {
            $cand = $mF.Groups[1].Value
            if (-not $rxPlataforma.IsMatch($cand)) { $frame = $cand; break }
            if (-not $frame) { $frame = $cand }
        }
        if ($frame -and -not $rxPlataforma.IsMatch($frame)) { break }
    }

    $pantalla = ""
    foreach ($l in $evento.Lineas) {
        $mP = $rxPantalla.Match($l)
        if (-not $mP.Success) { continue }
        if ($mP.Groups[2].Value -ieq "aspx") { $pantalla = $mP.Groups[1].Value; break }
        if (-not $pantalla) { $pantalla = $mP.Groups[1].Value }
    }

    if ($evento.Formato -eq "agendaweb") {
        $mOra = $rxOra.Match($texto)
        $mCod = $rxRsCodigo.Match($primera)
        if ($mOra.Success) {
            $exc = $mOra.Value
        } elseif ($mCod.Success -and $mCod.Groups[1].Value -ne "0") {
            $exc = "COD" + $mCod.Groups[1].Value
        } else {
            $mEx = $rxExcepcion.Match($texto)
            $exc = if ($mEx.Success) { $mEx.Groups[1].Value }
                   elseif ($mCod.Success) { "COD" + $mCod.Groups[1].Value }
                   else { "SinCodigo" }
        }
        $mDesc = $rxRsDesc.Match($primera)
        $msg = if ($mDesc.Success) { $mDesc.Groups[1].Value } else { $rxRsCab.Replace($primera, '', 1) }
        $msg = $msg.Trim(" ", "-", "|", "`t")
    } else {
        $mEx = $rxExcepcion.Match($texto)
        $exc = if ($mEx.Success) { $mEx.Groups[1].Value } else { "SinExcepcion" }
        $msg = $rxStamp.Replace($primera, '')
        $msg = $rxNivel.Replace($msg, '', 1)
        $msg = $msg.Trim(" ", "-", "|", "[", "]", ":", "`t")
    }

    $clave = "$exc|$frame|$(Normalizar $msg)"
    $hash  = Hash8 $clave

    if (-not $firmas.ContainsKey($hash)) {
        $firmas[$hash] = [PSCustomObject]@{
            hash       = $hash
            exception  = $exc
            origin     = $frame
            pantalla   = $pantalla
            message    = Recortar (Proteger $msg) 300
            count      = 0
            first_seen = $evento.Stamp
            last_seen  = $evento.Stamp
            files      = @()
            samples    = @()
        }
    }

    $f = $firmas[$hash]
    $f.count++
    if ($evento.Stamp) {
        if (-not $f.first_seen -or $evento.Stamp -lt $f.first_seen) { $f.first_seen = $evento.Stamp }
        if (-not $f.last_seen  -or $evento.Stamp -gt $f.last_seen)  { $f.last_seen  = $evento.Stamp }
    }
    if (-not $f.pantalla -and $pantalla) { $f.pantalla = $pantalla }
    if ($f.files -notcontains $fichero)  { $f.files += $fichero }
    if ($f.samples.Count -lt $Samples) {
        $f.samples += [PSCustomObject]@{
            timestamp = $evento.Stamp
            file      = $fichero
            line      = $evento.LineNo
            text      = Recortar (Proteger ($evento.Lineas -join " | ")) 600
        }
    }
}

# --- Barrido ---
foreach ($file in $files) {
    if ($topeLineas) { break }
    $nombre = $file.Name

    # ELMAH XML
    $esXml = $file.Extension -ieq ".xml"
    if ($esXml) {
        try { [xml]$xml = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 } catch { continue }
        $nodos = @($xml.SelectNodes("//error"))
        if ($nodos.Count -eq 0) { continue }
        $formatos["elmah-xml"] = $true
        foreach ($n in $nodos) {
            $stamp = "$($n.time)"
            if ($desdeDt) {
                [datetime]$dt = [datetime]::MinValue
                if ([datetime]::TryParse($stamp, [ref]$dt) -and $dt -lt $desdeDt) { continue }
            }
            $totalEventos++
            $cuerpo = @("$($n.type): $($n.message)")
            if ($n.detail) { $cuerpo += (("$($n.detail)" -split "`n") | Select-Object -First 20) }
            Registrar @{ Lineas = $cuerpo; Stamp = $stamp; LineNo = 0; Formato = "elmah-xml" } $nombre
        }
        continue
    }

    $evento = $null
    $omitir = $false
    $nLinea = 0
    try {
        foreach ($linea in [IO.File]::ReadLines($file.FullName, (Get-OrchestratorCodificacion $file.FullName))) {
            $nLinea++
            $lineas++
            if ($lineas -ge $MaxLines) { $topeLineas = $true; break }

            # Formato AgendaWeb AIS — probar primero (su cabecera no casa $rxStamp)
            $mRs = $rxRsCab.Match($linea)
            if ($mRs.Success) {
                if ($evento) { $totalEventos++; Registrar $evento $nombre }
                $evento = $null
                $omitir = $false

                $nivel = Get-OrchestratorNivelEtiqueta $mRs.Groups[1].Value
                if ($nivel -and ($nivelSet -notcontains $nivel) -and
                    -not ($nivel -eq "WARNING" -and $nivelSet -contains "WARN")) { $omitir = $true; continue }

                $stamp = "{0:D4}-{1:D2}-{2:D2} {3:D2}:{4:D2}:{5:D2}" -f `
                         [int]$mRs.Groups[4].Value, [int]$mRs.Groups[3].Value, [int]$mRs.Groups[2].Value, `
                         [int]$mRs.Groups[5].Value, [int]$mRs.Groups[6].Value,
                         $(if ($mRs.Groups[7].Success) { [int]$mRs.Groups[7].Value } else { 0 })

                if ($desdeDt) {
                    [datetime]$dt = [datetime]::MinValue
                    if ([datetime]::TryParseExact($stamp, "yyyy-MM-dd HH:mm:ss",
                            [Globalization.CultureInfo]::InvariantCulture,
                            [Globalization.DateTimeStyles]::None, [ref]$dt) -and $dt -lt $desdeDt) {
                        $omitir = $true; continue
                    }
                }

                $formatos["agendaweb"] = $true
                $evento = @{ Lineas = @($linea); Stamp = $stamp; LineNo = $nLinea; Formato = "agendaweb" }
                continue
            }

            if ($evento -and $evento.Formato -eq "agendaweb") {
                if ($evento.Lineas.Count -lt 40) { $evento.Lineas += $linea }
                continue
            }

            $mStamp = $rxStamp.Match($linea)
            if ($mStamp.Success) {
                if ($evento) { $totalEventos++; Registrar $evento $nombre }
                $evento = $null
                $omitir = $false

                $stamp  = $mStamp.Groups[1].Value
                $mNivel = $rxNivel.Match($linea)
                $nivel  = if ($mNivel.Success) { $mNivel.Groups[1].Value.ToUpper() } else { "" }

                if ($nivel -and ($nivelSet -notcontains $nivel) -and
                    -not ($nivel -eq "WARNING" -and $nivelSet -contains "WARN")) { $omitir = $true; continue }
                if (-not $nivel -and -not $rxExcepcion.IsMatch($linea)) { $omitir = $true; continue }

                if ($desdeDt) {
                    [datetime]$dt = [datetime]::MinValue
                    if ([datetime]::TryParse(($stamp -replace ',', '.'), [ref]$dt) -and $dt -lt $desdeDt) { $omitir = $true; continue }
                }

                $formatos["nlog-log4net"] = $true
                $evento = @{ Lineas = @($linea); Stamp = $stamp; LineNo = $nLinea; Formato = "nlog-log4net" }
                continue
            }

            if ($evento) {
                if ($evento.Lineas.Count -lt 40) { $evento.Lineas += $linea }
                continue
            }

            if ($omitir) { continue }

            if ($rxExcepcion.IsMatch($linea) -and $linea.Trim()) {
                $formatos["stacktrace-plano"] = $true
                $evento = @{ Lineas = @($linea); Stamp = ""; LineNo = $nLinea; Formato = "stacktrace-plano" }
            }
        }
    } catch { continue }
    if ($evento) { $totalEventos++; Registrar $evento $nombre }
}

if ($firmas.Count -eq 0) {
    Emit @{
        success         = $true
        path            = $Path
        files_scanned   = $files.Count
        lines_scanned   = $lineas
        total_events    = 0
        format_detected = "desconocido"
        signatures      = @()
        truncated       = $false
        message         = "Sin errores reconocidos. Revisar -Glob, -Niveles o -Desde; o el formato no es reconocido (soportados: nlog-log4net, elmah-xml, agendaweb, stacktrace-plano)."
    }
    exit 0
}

$orden     = @($firmas.Values | Sort-Object -Property count -Descending)
$devueltas = @($orden | Select-Object -First $MaxSignatures)
$formato   = if ($formatos.Keys.Count -eq 0) { "desconocido" }
             elseif ($formatos.Keys.Count -eq 1) { @($formatos.Keys)[0] }
             else { "mixto (" + (@($formatos.Keys) -join ', ') + ")" }

Emit @{
    success             = $true
    path                = $Path
    files_scanned       = $files.Count
    lines_scanned       = $lineas
    scan_truncated      = $topeLineas
    total_events        = $totalEventos
    format_detected     = $formato
    distinct_signatures = $orden.Count
    signatures          = $devueltas
    truncated           = ($orden.Count -gt $devueltas.Count)
}
```

- [ ] **Step 2: Verificación básica con un log real**

```powershell
cd "C:\Desarrollo\GIT\ScacsWeb\IA\Orchestrator-Agent"
$r = powershell -NoProfile -ExecutionPolicy Bypass -File ".\hooks\parse-weblog.ps1" `
    -Path "C:\AIS\<Proyecto>\AgendaWeb\logs" | ConvertFrom-Json
Write-Host "success: $($r.success)"
Write-Host "total_events: $($r.total_events)"
Write-Host "format_detected: $($r.format_detected)"
Write-Host "distinct_signatures: $($r.distinct_signatures)"
```

Si no hay log disponible, usar un fichero de prueba mínimo:

```powershell
# Crear fixture mínimo
$logContent = @"
Error: (11/08/2026 13:45) - Codigo error: -2147467259 Codigo error sql: 0 Descripción error: ORA-01403: no se han encontrado datos
   en Scacs.Business.CConector.EjecutarQuery(String sql)
   en Scacs.Presentation.frmBuscarExpediente.Page_Load(Object sender, EventArgs e)
Error: (11/08/2026 14:12) - Codigo error: -2147467259 Codigo error sql: 0 Descripción error: ORA-01403: no se han encontrado datos
   en Scacs.Business.CConector.EjecutarQuery(String sql)
"@
$logContent | Set-Content "$env:TEMP\test-ais.log" -Encoding UTF8

$r = powershell -NoProfile -ExecutionPolicy Bypass -File ".\hooks\parse-weblog.ps1" `
    -Path "$env:TEMP\test-ais.log" | ConvertFrom-Json
# Esperado: total_events=2, distinct_signatures=1, format_detected=agendaweb
Write-Host "total_events: $($r.total_events) | signatures: $($r.distinct_signatures) | format: $($r.format_detected)"
```

- [ ] **Step 3: Commit**

```bash
git add hooks/parse-weblog.ps1
git commit -m "feat(hooks): parse-weblog.ps1 — parser de log web con dedup por firma"
```

---

### Task 5: Añadir `create` a hooks/mantis-cli.ps1

**Files:**
- Modify: `hooks/mantis-cli.ps1`

La skill de log-errores crea issues en Mantis. Nuestro `mantis-cli.ps1` no tiene acción `create`. Añadirla.

- [ ] **Step 1: Añadir parámetros al bloque param**

En `hooks/mantis-cli.ps1`, localizar:

```powershell
param(
    [Parameter(Mandatory)]
    [ValidateSet("get-issue","list-issues","list-projects","get-statuses","patch-status","post-note","attach-file")]
    [string]$Action,
```

Reemplazar por:

```powershell
param(
    [Parameter(Mandatory)]
    [ValidateSet("get-issue","list-issues","list-projects","get-statuses","patch-status","post-note","attach-file","create")]
    [string]$Action,
```

- [ ] **Step 2: Añadir parámetros Summary, Description, Category, Priority, Severity, Tags**

Localizar el bloque de parámetros (tras `[string]$ProjectId`) y añadir:

```powershell
    [string]$Summary,
    [string]$Description,
    [string]$Category,
    [string]$Priority,
    [string]$Severity,
    [string]$Tags,
```

- [ ] **Step 3: Añadir la rama `create` al switch**

Localizar el cierre del switch (`}` final del bloque switch) y añadir antes:

```powershell
    "create" {
        if (-not $ProjectId) { Write-Error "-ProjectId requerido para create"; exit 1 }
        if (-not $Summary)   { Write-Error "-Summary requerido para create"; exit 1 }

        $body = @{
            summary     = $Summary
            project     = @{ id = [int]$ProjectId }
            description = if ($Description) { $Description } else { $Summary }
        }
        if ($Category) { $body.category = @{ name = $Category } }
        if ($Priority) { $body.priority = @{ label = $Priority } }
        if ($Severity) { $body.severity = @{ label = $Severity } }
        if ($Tags) {
            $body.tags = @($Tags -split ',' | ForEach-Object {
                @{ name = $_.Trim() }
            } | Where-Object { $_.name })
        }

        $r = Invoke-Mantis -Method Post -Path "/issues" -Body $body
        # Devolver solo los campos relevantes para el dedup posterior
        @{
            id      = $r.issue.id
            summary = $r.issue.summary
            status  = $r.issue.status.label
        } | ConvertTo-Json -Depth 3
    }
```

- [ ] **Step 4: Actualizar el .SYNOPSIS del fichero**

Localizar la línea `.PARAMETER Action` en el encabezado y actualizar:

```
.PARAMETER Action
    get-issue | list-issues | list-projects | get-statuses |
    patch-status | post-note | attach-file | create
```

Añadir también al bloque `.EXAMPLE`:

```
    .\mantis-cli.ps1 -Action create -ProjectId 215 -Summary "Bug en búsqueda" -Description "..." -Category "Bug" -Priority "normal" -Severity "mayor" -Tags "log-abc12345,produccion"
```

- [ ] **Step 5: Verificar**

```powershell
# Solo verifica que el script parsea correctamente los parámetros nuevos (sin crear issue real)
# en una sesión con credenciales configuradas:
powershell -NoProfile -ExecutionPolicy Bypass -Command {
    & ".\hooks\mantis-cli.ps1" -Action create -ProjectId 999 -Summary "Test" -Description "Prueba" 2>&1
}
# Esperado: error 404 del API (proyecto 999 no existe) — confirma que llega al endpoint
```

- [ ] **Step 6: Commit**

```bash
git add hooks/mantis-cli.ps1
git commit -m "feat(hooks): mantis-cli create — alta de issues desde log-errores"
```

---

### Task 6: Añadir parse_web_log al MCP

**Files:**
- Modify: `mcp/orchestrator-workspace-server.py`

- [ ] **Step 1: Añadir la tool `parse_web_log` antes del cierre del fichero**

Localizar el último `@mcp.tool` del fichero y añadir después:

```python
@mcp.tool(description="Parsea un log de errores web (NLog/log4net, ELMAH XML, formato AgendaWeb AIS: 'Error: (dd/MM/yyyy H:mm) - Codigo error: ... Descripción error: ...' y volcado de stack .NET) y agrupa las ocurrencias por FIRMA (excepción o código ORA-xxxxx/Codigo error + frame de código propio + mensaje normalizado) → [{hash,exception,origin,pantalla,message,count,first_seen,last_seen,files,samples}] ordenado por count. Devuelve solo el agregado — el log crudo nunca entra en contexto. format_detected indica el formato reconocido. PII: literales SQL entre comillas simples redactados ('...' → '<val>'). path = fichero o carpeta.")
def parse_web_log(path: str, glob: str = "*.log", desde: str = "", niveles: str = "ERROR,FATAL",
                  max_signatures: int = 30, samples: int = 2) -> str:
    args = ["-Path", path, "-Glob", glob, "-Niveles", niveles,
            "-MaxSignatures", str(max_signatures), "-Samples", str(samples)]
    if desde:
        args += ["-Desde", desde]
    return json.dumps(_run_ps("parse-weblog.ps1", *args), ensure_ascii=False, separators=(",",":"))
```

- [ ] **Step 2: Verificar que el MCP expone la tool**

Reiniciar Claude Code (el MCP se reinicia automáticamente). Buscar `parse_web_log` en las tools disponibles. En una sesión nueva:

```
mcp__orchestrator-workspace__parse_web_log(path="C:\\temp\\test-ais.log")
```

Esperado: JSON con `success: true`, `total_events`, `signatures`.

- [ ] **Step 3: Commit**

```bash
git add mcp/orchestrator-workspace-server.py
git commit -m "feat(mcp): parse_web_log — tool para analizar logs de producción"
```

---

### Task 7: agents/log-errores.md

**Files:**
- Create: `agents/log-errores.md`

- [ ] **Step 1: Crear agents/log-errores.md**

```markdown
---
name: orchestrator-log-errores
description: 'Analiza el log de errores de la web AIS, deduplica los tipos de error por firma, abre una tarea por tipo en Mantis y propone lanzar el pipeline para cada una. Usar cuando el usuario quiere convertir un log en tareas: "/orchestrator-log-errores", "analiza el log de errores", "qué errores está dando la web", "crea tickets con los errores del log".'
---

> Config Mantis: `references/mantis.md`
> Hook: `hooks/parse-weblog.ps1`

# Log Errores

Convierte un log de errores de la capa web en **tareas accionables en Mantis**.
Un log repite el mismo fallo cientos de veces: lo que se abre como tarea son los **tipos de error distintos**, no las líneas.
La deduplicación la hace el hook `parse-weblog.ps1` (tool `parse_web_log`) por **firma** — el log nunca entra entero en contexto.

# Rol

Triador de errores de producción. Una tarea por causa real, confirmación antes de crear nada, dedup contra Mantis antes de escribir.

# Reglas

- ⛔ Toda escritura en Mantis (create, post-note) va detrás de confirmación explícita.
- ⛔ Nunca crear issues sin pasar por el gate de Fase 2.
- ⛔ No adivinar la ruta del log — si no viene en el argumento, preguntarla.
- ⛔ No leer el log crudo con Read/Grep — puede pesar cientos de MB y llevar datos personales. La única puerta es `parse_web_log`.
- No analizar el código en esta skill. El triaje clasifica *qué* falla; el *cómo* lo decide el pipeline en la siguiente tarea.

# Fase 0 — Fuente del log

1. La ruta llega como argumento. Si **no** llega → preguntar. No inventar rutas.
2. Opciones que el usuario puede pasar:
   - `--desde YYYY-MM-DD` → parámetro `desde`
   - `--max N` → `max_signatures`
   - `--glob *.log` → `glob`
   - `--niveles ERROR,FATAL` → `niveles`
3. Anunciar en una línea: ruta, ventana, niveles — antes de empezar.

# Fase 1 — Parseo y deduplicación

1. Llamar `mcp__orchestrator-workspace__parse_web_log(path, glob, desde, niveles, max_signatures, samples)`.
2. Si `success:false` → mostrar el `error` y parar.
3. Si `signatures` vacío → mostrar el `message` de la tool y parar.
4. ⛔ **Contrastar `total_events` con `lines_scanned`**: si hay decenas de miles de líneas pero pocos eventos, o `format_detected` es `desconocido`, el formato no se reconoció — decirlo y parar, no triar un recuento falso.
5. Si `truncated` o `scan_truncated` son `true` → **decirlo explícitamente**.
6. Presentar tabla ordenada por frecuencia:

   | # | hash | excepción/código | origen | pantalla | ocurrencias | primera → última |
   |---|------|-----------------|--------|----------|-------------|-----------------|

   `pantalla` puede venir vacía — no inventarla.

# Fase 2 — Triaje y propuesta de tareas (gate ⛔)

1. Clasificar cada firma sin abrir el código:
   - **código** — bug propio (NullReference, DALC, lógica). → tarea.
   - **dato** — registro inexistente, FK/PK. → tarea, prioridad menor.
   - **configuración** — cadena de conexión, permiso, ruta, setting. → tarea de entorno.
   - **infra** — timeout, caída de servicio externo. → proponer aparte, el usuario decide.
   - **ruido** — trazas de terceros, cancelaciones de navegador, bots. → descartar.
2. Proponer **una tarea por firma accionable**:
   - **Resumen**: `[log:<hash>] <Excepción/Código> en <Origen>` (+ ` (<pantalla>)` si está)
   - **Descripción**: excepción · origen · pantalla · ocurrencias · ventana `primera → última` · ficheros · muestra (ya redactada) · categoría.
   - **Prioridad sugerida**: frecuencia × severidad. Justificar en una línea.
3. Si dos firmas son el mismo fallo visto desde dos sitios (misma excepción, mismo origen) → proponer **fundir** en una tarea.
4. ⛔ **Gate**: presentar la lista numerada y esperar ajuste del usuario. Hasta aprobación, nada existe en Mantis.

# Fase 3 — Alta en Mantis

1. **Resolución del proyecto**: el `.mantis-dev-config.json` en `docs\` del workspace tiene `project_id`. Si no existe → preguntar.
2. **Dedup contra Mantis**: antes de crear, buscar cada `[log:<hash>]` en issues abiertas:
   ```powershell
   .\hooks\mantis-cli.ps1 -Action list-issues -ProjectId <id> -PageSize 200
   ```
   Filtrar el marcador `[log:<hash>]` en los resúmenes. Si ya existe una issue abierta → **no duplicar**: ofrecer añadir nota con nuevas ocurrencias (`post-note`).
3. ⛔ **Confirmación del lote**: mostrar los campos completos de cada issue antes de crear. Una sola confirmación cubre el lote, pero el contenido se enseña issue a issue.
4. Crear cada issue:
   ```powershell
   .\hooks\mantis-cli.ps1 -Action create `
       -ProjectId <id> `
       -Summary "[log:<hash>] <Excepción> en <Origen>" `
       -Description "<descripción completa>" `
       -Category "Bug" `
       -Priority "normal" `
       -Severity "mayor" `
       -Tags "log-<hash>,produccion"
   ```
5. Si una issue falla → reportar el error y **seguir con las demás**. Al final: tabla `firma → id creada (o "ya existía #N")`.

# Fase 4 — Propuesta de pipeline

1. Listar las tareas creadas y **proponer** trabajarlas con el pipeline, ordenadas por prioridad de Fase 2.
2. ⛔ El usuario elige cuál empezar. No lanzar varias, no lanzar sin que lo pida.
3. Para la elegida, seguir el flujo estándar de `agents/mantis.md` desde Fase 2 (encuadre del requisito con la issue ya creada).

# Límites

⛔ F0–F2 son autónomos y no necesitan Mantis conectado. F3 usa `mantis-cli.ps1` con token — si falla la autenticación, reportarlo y parar sin abortar el análisis.
```

- [ ] **Step 2: Commit**

```bash
git add agents/log-errores.md
git commit -m "feat(agents): log-errores — skill de triaje de log web a tareas Mantis"
```

---

### Task 8: commands/orchestrator-log-errores.md

**Files:**
- Create: `commands/orchestrator-log-errores.md`

- [ ] **Step 1: Crear commands/orchestrator-log-errores.md**

```markdown
---
description: "Analiza el log de errores de la web AIS, deduplica los tipos de error y abre una tarea Mantis por tipo."
argument-hint: "<ruta log|carpeta> [--desde YYYY-MM-DD] [--max N] [--glob *.log] [--niveles ERROR,FATAL]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in log-errores mode.

Usage: /orchestrator-log-errores <ruta log|carpeta> [--desde YYYY-MM-DD] [--max N] [--glob *.log] [--niveles ERROR,FATAL]
Examples:
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs\web.log --desde 2026-08-01
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs --max 10 --niveles ERROR,FATAL,WARN

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Read `$SKILL_DIR\agents\log-errores.md` inline and follow its instructions.
2. The log is analyzed by `mcp__orchestrator-workspace__parse_web_log` — the raw log never enters context.
3. Phases: F0 source · F1 parse+dedup · F2 triage+gate · F3 create in Mantis · F4 propose pipeline.
4. ⛔ Relay tool output verbatim. ⛔ Confirm before any Mantis write.
```

- [ ] **Step 2: Verificar que Claude Code registra el comando**

Reiniciar sesión de Claude Code y verificar que `/orchestrator-log-errores` aparece en autocompletado.

- [ ] **Step 3: Commit final**

```bash
git add commands/orchestrator-log-errores.md
git commit -m "feat(commands): /orchestrator-log-errores — comando de análisis de log web"
```

---

## Self-Review

**Spec coverage:**
- [x] Punto 1: lib-msbuild.ps1 → Task 1
- [x] Punto 1: compile-check.ps1 → Task 2
- [x] Punto 1: MCP + validator.md → Task 3
- [x] Punto 3: parse-weblog.ps1 → Task 4
- [x] Punto 3: mantis-cli create → Task 5
- [x] Punto 3: parse_web_log MCP → Task 6
- [x] Punto 3: agents/log-errores.md → Task 7
- [x] Punto 3: commands/orchestrator-log-errores.md → Task 8

**Sin placeholders:** verificado — todo el código es código real, no fragmentos TBD.

**Consistencia de tipos:**
- `Get-OrchestratorBuildToolchain` devuelve el mismo hashtable que consume `compile-check.ps1` ✓
- `parse_web_log` MCP usa `_run_ps("parse-weblog.ps1", *args)` con los mismos parámetros del hook ✓
- `mantis-cli.ps1 create` devuelve `{id, summary, status}` — suficiente para el dedup en Fase 3 ✓

**Dependencias entre tasks:**
- Task 2 depende de Task 1 (compile-check.ps1 dot-sourcea lib-msbuild.ps1)
- Task 3 depende de Task 2 (MCP llama a compile-check.ps1)
- Task 6 depende de Task 4 (MCP llama a parse-weblog.ps1)
- Task 7 depende de Task 5 y Task 6 (usa mantis-cli create y parse_web_log)
- Task 8 depende de Task 7 (el comando referencia agents/log-errores.md)
- Tasks del Subsistema A y B son independientes entre sí — pueden ejecutarse en paralelo

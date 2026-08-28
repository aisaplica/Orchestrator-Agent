#Requires -Version 5.1
<#
.SYNOPSIS
    Registra una ejecución del pipeline Orchestrator en <Workspace>\executions\history.json.

.DESCRIPTION
    Hook equivalente de la tool MCP `log_execution`. Es el ÚNICO backend real:
    el MCP server (`_run_ps("log-execution.ps1", ...)`) delega aquí, y el paso 11
    del pipeline (`skills/orchestrator-agent/SKILL.md`) cae a este hook si el MCP
    no responde.

    Appendea al array JSON. Tope 500 entradas vivas; el excedente se archiva por
    mes en `executions\archive\history-YYYY-MM.json`.

    Esquema de cada entrada (consumido por historial.md / stats.md / dashboard.md):
        { id, timestamp, solution, workspace, task, status, agents[] }

.PARAMETER Workspace
    Carpeta raíz del workspace (cwd de la sesión Claude Code).

.PARAMETER Solution
    Nombre de la solución (sin extensión .sln).

.PARAMETER Task
    Descripción de la tarea ejecutada por el pipeline.

.PARAMETER Status
    success | fail | partial. Por defecto success.

.PARAMETER Agents
    Lista de agentes usados, coma-separada (ej: "planner,core,validator,tester").

.EXAMPLE
    .\log-execution.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk" Ingenieros "Añadir validación NOMBRE" -Status success -Agents "planner,core,validator,tester"
#>
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$Solution,
    [Parameter(Mandatory = $true)][string]$Task,
    [ValidateSet('success', 'fail', 'partial')][string]$Status = 'success',
    [string]$Agents = ''
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 6 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

function Write-JsonArray($path, $items) {
    # PS5.1: ConvertTo-Json colapsa un array de 0/1 elementos -> construir los corchetes a mano.
    $arr = [object[]]$items
    if ($null -eq $arr -or $arr.Count -eq 0) {
        $json = "[]"
    }
    elseif ($arr.Count -eq 1) {
        $json = "[" + ($arr[0] | ConvertTo-Json -Depth 6) + "]"
    }
    else {
        $json = $arr | ConvertTo-Json -Depth 6
    }
    [IO.File]::WriteAllText($path, $json, (New-Object Text.UTF8Encoding($true)))
}

function Add-JsonArrayTo($list, $path) {
    # PS5.1: ConvertFrom-Json emite el array como UN objeto (sin enumerar) -> aplanar a mano.
    # Muta la lista recibida; no devuelve nada (evita el desenrollado de colecciones al retornar).
    if (-not (Test-Path -LiteralPath $path)) { return }
    $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    if (-not $raw -or -not $raw.Trim()) { return }
    $parsed = $raw | ConvertFrom-Json
    if ($parsed -is [System.Collections.IEnumerable] -and $parsed -isnot [string]) {
        foreach ($e in $parsed) { if ($e) { [void]$list.Add($e) } }
    }
    elseif ($parsed) {
        [void]$list.Add($parsed)
    }
}

if (-not (Test-Path -LiteralPath $Workspace)) { Fail "Workspace no encontrado: $Workspace" }

$dir = Join-Path $Workspace "executions"
if (-not (Test-Path -LiteralPath $dir)) {
    try { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    catch { Fail "No se pudo crear $dir : $_" }
}
$histPath = Join-Path $dir "history.json"

# --- cargar historial existente en una lista plana ---
$list = New-Object System.Collections.Generic.List[object]
if (Test-Path -LiteralPath $histPath) {
    try { Add-JsonArrayTo $list $histPath }
    catch {
        # historial corrupto -> respaldar y empezar limpio, sin perder la ejecución actual
        $list.Clear()
        $bak = Join-Path $dir ("history.corrupt-{0}.json" -f (Get-Date -Format "yyyyMMddHHmmss"))
        try { Move-Item -LiteralPath $histPath -Destination $bak -Force } catch { }
    }
}

# --- nueva entrada ---
$agentsArr = @($Agents -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$id = -join ((1..8) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) })

$list.Add([PSCustomObject][ordered]@{
        id        = $id
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        solution  = $Solution
        workspace = $Workspace
        task      = $Task
        status    = $Status
        agents    = $agentsArr
    })

# --- tope 500 vivas + archivo mensual del excedente ---
$archived = 0
if ($list.Count -gt 500) {
    $overflowCount = $list.Count - 500
    $overflow = @($list.GetRange(0, $overflowCount))
    $list.RemoveRange(0, $overflowCount)

    $archiveDir = Join-Path $dir "archive"
    if (-not (Test-Path -LiteralPath $archiveDir)) { New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null }

    foreach ($grp in ($overflow | Group-Object { ([string]$_.timestamp).PadRight(7).Substring(0, 7) })) {
        $apath = Join-Path $archiveDir ("history-{0}.json" -f $grp.Name)
        $acc = New-Object System.Collections.Generic.List[object]
        try { Add-JsonArrayTo $acc $apath } catch { $acc.Clear() }
        foreach ($e in $grp.Group) { [void]$acc.Add($e) }
        Write-JsonArray $apath $acc.ToArray()
        $archived += $grp.Count
    }
}

# --- escribir historial (UTF-8 con BOM, requisito PS5.1) ---
try { Write-JsonArray $histPath $list.ToArray() }
catch { Fail "Error al escribir $histPath : $_" }

Emit @{ success = $true; id = $id; total = $list.Count; archived = $archived; path = $histPath }
exit 0

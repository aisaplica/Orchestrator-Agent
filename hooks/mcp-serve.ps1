#Requires -Version 5.1
<#
.SYNOPSIS
    Arranca el daemon HTTP del MCP server `orchestrator-workspace` si no está ya en marcha.

.DESCRIPTION
    Desde v1.16.0 el MCP server se sirve por streamable-http en localhost
    (`http://127.0.0.1:<port>/mcp`) en vez de stdio — el transporte stdio se cuelga
    bajo el runtime de Claude Code en Windows.

    Este hook lo lanza en SessionStart:
      1. Si el puerto ya responde  -> no hace nada (idempotente, no duplica procesos).
      2. Si no: resuelve el interprete Python y lanza
         `pythonw orchestrator-workspace-server.py --http --port <port>`
         desacoplado (sobrevive a Claude Code), con log en
         %LOCALAPPDATA%\orchestrator-workspace\server.log
      3. Espera hasta ~12 s a que el puerto responda.

    El daemon es residente: sesiones posteriores lo encuentran ya arriba.

.PARAMETER Port
    Puerto TCP local. Default 7337. Override: $env:ORCH_MCP_PORT.
    Debe coincidir con el de `.mcp.json`.

.PARAMETER Force
    Mata el daemon que escuche en el puerto y relanza. Para reinicio manual.

.EXAMPLE
    .\mcp-serve.ps1
    .\mcp-serve.ps1 -Force
#>
param(
    [int]$Port = 0,
    [switch]$Force
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 4 -Compress }

if ($Port -le 0) {
    $Port = if ($env:ORCH_MCP_PORT) { [int]$env:ORCH_MCP_PORT } else { 7337 }
}

$ServerPy = Join-Path $PSScriptRoot "..\mcp\orchestrator-workspace-server.py"
$ServerPy = [System.IO.Path]::GetFullPath($ServerPy)
$LogDir   = Join-Path $env:LOCALAPPDATA "orchestrator-workspace"
$LogFile  = Join-Path $LogDir "server.log"
$ErrFile  = Join-Path $LogDir "server.err.log"

function Test-Port([int]$p) {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $c.BeginConnect("127.0.0.1", $p, $null, $null)
        if ($iar.AsyncWaitHandle.WaitOne(300)) { $c.EndConnect($iar); return $true }
        return $false
    } catch { return $false }
    finally { $c.Close() }
}

function Get-PidOnPort([int]$p) {
    try {
        (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop |
            Select-Object -First 1 -ExpandProperty OwningProcess)
    } catch { $null }
}

# --- Force: matar daemon existente -----------------------------------------
if ($Force) {
    $existing = Get-PidOnPort $Port
    if ($existing) {
        try { Stop-Process -Id $existing -Force -ErrorAction Stop; Start-Sleep -Milliseconds 500 }
        catch { Emit @{ ok = $false; error = "No se pudo matar PID $existing en puerto $Port : $_" }; exit 1 }
    }
}

# --- Ya en marcha ---------------------------------------------------------
if (-not $Force -and (Test-Port $Port)) {
    Emit @{ ok = $true; status = "already-running"; port = $Port }
    exit 0
}

# --- Validaciones --------------------------------------------------------
if (-not (Test-Path -LiteralPath $ServerPy)) {
    Emit @{ ok = $false; error = "Server no encontrado: $ServerPy" }
    exit 1
}
$portPid = Get-PidOnPort $Port
if ($portPid -and -not $Force) {
    # Puerto ocupado pero no respondio al TcpClient: probablemente otro proceso.
    Emit @{ ok = $false; error = "Puerto $Port ocupado por PID $portPid (no es el daemon). Cambia ORCH_MCP_PORT y el puerto en .mcp.json." }
    exit 1
}

# --- Resolver interprete ------------------------------------------------
$py = $null
if ($env:ORCH_MCP_PYTHON -and (Test-Path -LiteralPath $env:ORCH_MCP_PYTHON)) {
    $py = $env:ORCH_MCP_PYTHON
} else {
    foreach ($cand in @("pythonw.exe", "python.exe")) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if ($cmd) { $py = $cmd.Source; break }
    }
    if (-not $py) {
        $cmd = Get-Command "py.exe" -ErrorAction SilentlyContinue
        if ($cmd) { $py = $cmd.Source }  # se invoca como: py -3 <server>
    }
}
if (-not $py) {
    Emit @{ ok = $false; error = "No se encontro interprete Python (pythonw/python/py). Instala Python 3.11+ o define ORCH_MCP_PYTHON." }
    exit 1
}

# --- Lanzar daemon -----------------------------------------------------
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = "[{0}] --- arranque daemon (puerto {1}) ---" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Port
Add-Content -LiteralPath (Join-Path $LogDir "launch.log") -Value $stamp -Encoding UTF8

$argList = @()
if ($py -like "*py.exe") { $argList += "-3" }
$argList += @("`"$ServerPy`"", "--http", "--host", "127.0.0.1", "--port", "$Port")

try {
    Start-Process -FilePath $py -ArgumentList $argList `
        -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $ErrFile `
        -ErrorAction Stop | Out-Null
} catch {
    Emit @{ ok = $false; error = "Start-Process fallo: $_"; python = $py }
    exit 1
}

# --- Esperar a que responda -----------------------------------------
$deadline = (Get-Date).AddSeconds(12)
while ((Get-Date) -lt $deadline) {
    if (Test-Port $Port) {
        Emit @{ ok = $true; status = "started"; port = $Port; python = $py; log = $LogFile }
        exit 0
    }
    Start-Sleep -Milliseconds 400
}

Emit @{ ok = $false; status = "timeout"; port = $Port; python = $py; log = $LogFile;
        hint = "El daemon no respondio en 12 s. Revisa $ErrFile. Claude Code reintentara la conexion." }
exit 0

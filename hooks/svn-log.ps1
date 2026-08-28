#Requires -Version 5.1
<#
.SYNOPSIS
    Historial de commits SVN del workspace → JSON { revision, author, date, message }.

.DESCRIPTION
    Equivalente hook de la tool MCP `svn_log`. Usa `svn log --xml`. Requiere el CLI
    de svn en PATH; si no está, devuelve error con fallback a TortoiseSVN.

.PARAMETER Workspace
    Carpeta del workspace (o cualquier subcarpeta de la working copy).

.PARAMETER Solution
    Filtro opcional: solo commits cuyo mensaje contenga este texto (case-insensitive).

.PARAMETER Limit
    Máximo de commits a devolver. Por defecto 10.

.EXAMPLE
    .\svn-log.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk" -Limit 20
    .\svn-log.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk" -Solution BatchCirbe
#>
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [string]$Solution = "",
    [int]$Limit = 10
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 5 -Compress }
function Fail($msg, $extra) {
    $o = @{ success = $false; error = "$msg" }
    if ($extra) { foreach ($k in $extra.Keys) { $o[$k] = $extra[$k] } }
    Emit $o; exit 0
}

if (-not (Test-Path -LiteralPath $Workspace)) { Fail "Workspace no encontrado: $Workspace" }

try {
    $null = & svn --version --quiet 2>&1
    if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
}
catch {
    Fail "svn CLI no disponible en PATH" @{ fallback = "TortoiseSVN -> clic derecho en el workspace -> Show Log" }
}

# pedir de más si vamos a filtrar por mensaje
$fetch = if ($Solution) { [Math]::Max($Limit * 5, 50) } else { $Limit }

$xmlRaw = & svn log $Workspace --xml --limit $fetch 2>&1
if ($LASTEXITCODE -ne 0) { Fail "svn log falló: $($xmlRaw -join ' ')" }

try { [xml]$xml = ($xmlRaw -join "`n") }
catch { Fail "Respuesta de svn log no es XML válido" }

$commits = @()
foreach ($e in @($xml.log.logentry)) {
    if (-not $e) { continue }
    $msg = ($e.msg -as [string]).Trim()
    if ($Solution -and $msg -notmatch [regex]::Escape($Solution)) { continue }
    $rawDate = ($e.date -as [string]).Trim()
    $commits += [PSCustomObject]@{
        revision = [int]$e.revision
        author   = ($e.author -as [string]).Trim()
        date     = if ($rawDate.Length -ge 19) { $rawDate.Substring(0, 19).Replace("T", " ") } else { $rawDate }
        message  = $msg
    }
    if ($commits.Count -ge $Limit) { break }
}

Emit @{
    success   = $true
    workspace = $Workspace
    filter    = $Solution
    count     = $commits.Count
    commits   = $commits
}
exit 0

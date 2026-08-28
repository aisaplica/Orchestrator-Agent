#Requires -Version 5.1
<#
.SYNOPSIS
    Detecta qué control de versiones gobierna un workspace: 'svn', 'git' o 'none'.

.DESCRIPTION
    Sube por las carpetas desde el workspace buscando `.svn` o `.git`. No necesita
    los CLI de svn/git — solo mira el sistema de ficheros. Es el paso previo
    obligatorio a cualquier tool `svn_*` / `git_*`: sin esto no hay forma de saber
    cuál usar.

    Si encuentra ambos (raro), gana el más cercano al workspace; a igualdad, svn
    (el habitual en ScacsWeb).

.PARAMETER Workspace
    Carpeta del workspace (cwd de la sesión Claude Code).

.EXAMPLE
    .\detect-vcs.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk"
#>
param(
    [Parameter(Mandatory = $true)][string]$Workspace
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 4 -Compress }

if (-not (Test-Path -LiteralPath $Workspace)) {
    Emit @{ vcs = "none"; root = $null; error = "Workspace no encontrado: $Workspace" }
    exit 0
}

$svnRoot = $null
$gitRoot = $null

try { $dir = (Get-Item -LiteralPath $Workspace).FullName } catch { $dir = $Workspace }

for ($i = 0; $i -lt 40 -and $dir; $i++) {
    if (-not $svnRoot -and (Test-Path -LiteralPath (Join-Path $dir ".svn"))) { $svnRoot = $dir }
    if (-not $gitRoot -and (Test-Path -LiteralPath (Join-Path $dir ".git"))) { $gitRoot = $dir }
    if ($svnRoot -and $gitRoot) { break }
    $parent = Split-Path $dir -Parent
    if ($parent -eq $dir) { break }
    $dir = $parent
}

if ($svnRoot -and $gitRoot) {
    # el más cercano (ruta más larga) gana; empate -> svn
    if ($gitRoot.Length -gt $svnRoot.Length) { Emit @{ vcs = "git"; root = $gitRoot } }
    else { Emit @{ vcs = "svn"; root = $svnRoot } }
}
elseif ($svnRoot) { Emit @{ vcs = "svn"; root = $svnRoot } }
elseif ($gitRoot) { Emit @{ vcs = "git"; root = $gitRoot } }
else { Emit @{ vcs = "none"; root = $null } }

exit 0

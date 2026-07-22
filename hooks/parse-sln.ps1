<#
.SYNOPSIS
    Parsea un archivo .sln y devuelve scope, tipo y metadata como JSON.
    Elimina la necesidad de que el LLM lea y parsee el .sln manualmente.

.PARAMETER SlnPath
    Ruta completa al archivo .sln

.EXAMPLE
    .\parse-sln.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk\SCACSWebCDI.sln"
    .\parse-sln.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk\dotNet\Batch\BatchCirbe\BatchCirbe.sln"
#>
param(
    [Parameter(Mandatory=$true)][string]$SlnPath
)


$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

if (-not (Test-Path $SlnPath)) {
    @{ error = "Archivo no encontrado: $SlnPath" } | ConvertTo-Json
    exit 1
}

$slnFile  = Get-Item $SlnPath
$slnDir   = $slnFile.DirectoryName
$slnName  = $slnFile.BaseName   # sin .sln
$content  = Get-Content $SlnPath -Encoding UTF8

# Inferir tipo: Batch = .sln bajo dotNet\Batch\; Online = cualquier otro (raiz trunk)
$tipo = if ($SlnPath -match '\\dotNet\\Batch\\') { 'Batch' } else { 'Online' }

# Extraer rutas de .csproj
$projectDirs = @()
$projects    = @()

foreach ($line in $content) {
    if ($line -match 'Project\([^)]+\)\s*=\s*"([^"]+)",\s*"([^"]+\.csproj)"') {
        $projName    = $Matches[1].Trim()
        $projRelPath = $Matches[2].Trim().Replace('/', '\')
        # GetFullPath normaliza "..\" — Join-Path solo concatena literal y deja rutas como
        # "dotNet\..\Negocio\X" sin resolver, rompiendo a herramientas downstream que
        # esperan una ruta absoluta limpia (ej. búsquedas de código, Test-Path).
        $projDir     = [System.IO.Path]::GetFullPath((Join-Path $slnDir (Split-Path $projRelPath -Parent)))
        $projCsproj  = [System.IO.Path]::GetFullPath((Join-Path $slnDir $projRelPath))
        $projectDirs += $projDir
        $projects    += @{ name = $projName; csproj = $projCsproj; dir = $projDir }
    }
}

# Inferir workspace:
# - Batch: trunk\dotNet\Batch\<BatchName>\<BatchName>.sln → workspace = trunk (3 niveles arriba)
# - Online: sln en raiz trunk → $slnDir ya ES el workspace
$workspace = $slnDir
if ($SlnPath -match '\\dotNet\\Batch\\') {
    $workspace = (Get-Item $slnDir).Parent.Parent.Parent.FullName
}

@{
    solution      = $slnName
    sln_path      = $SlnPath
    sln_dir       = $slnDir
    tipo          = $tipo
    workspace     = $workspace
    scope_dirs    = $projectDirs
    projects      = $projects
    project_count = $projects.Count
} | ConvertTo-Json -Depth 4

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

    $eapPrevio = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $raw      = & $toolchain.builder_path @buildArgs 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $eapPrevio
} finally {
    $env:DOTNET_CLI_UI_LANGUAGE = $idiomaPrevio
    $env:VSLANG = $vslangPrevio
}

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

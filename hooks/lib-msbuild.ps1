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

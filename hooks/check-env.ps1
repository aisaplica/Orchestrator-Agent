<#
.SYNOPSIS
    Valida el entorno de trabajo Orchestrator Agent ScacsWeb.
.PARAMETER workspace
    Ruta del workspace (carpeta raíz del proyecto trunk/).
.PARAMETER proyecto
    Nombre del proyecto AIS (ej: SCACSWebCDI).
.EXAMPLE
    .\check-env.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk" "SCACSWebCDI"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$workspace,

    [Parameter(Mandatory=$true)]
    [string]$proyecto
)

$results = @()
$overallStatus = "LISTO"

function Add-Check {
    param([string]$Name, [string]$Status, [string]$Detail)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
    $script:results += [PSCustomObject]@{
        Check  = $Name
        Status = $Status
        Detail = $Detail
    }
    if ($Status -eq "FAIL" -and $script:overallStatus -ne "BLOQUEANTE") {
        $script:overallStatus = "BLOQUEANTE"
    } elseif ($Status -eq "WARN" -and $script:overallStatus -eq "LISTO") {
        $script:overallStatus = "ATENCION"
    }
}

# Check 0: env.json del plugin
$pluginRoot = Split-Path $PSScriptRoot -Parent
$envJson     = Join-Path $pluginRoot "env.json"
$envTemplate = Join-Path $pluginRoot "env.template.json"
if (Test-Path $envJson) {
    try {
        $env = Get-Content $envJson -Raw -Encoding UTF8 | ConvertFrom-Json
        $placeholders = ($env | ConvertTo-Json -Depth 10 | Select-String "<COMPLETAR>|<TU_|<URL_|<HOST>|<PASSWORD>|<USUARIO>|<API_KEY>" -AllMatches).Matches.Count
        if ($placeholders -gt 0) {
            Add-Check "env.json" "WARN" "Existe pero tiene $placeholders placeholders sin rellenar"
        } else {
            Add-Check "env.json" "OK" "Configurado"
        }
    } catch {
        Add-Check "env.json" "WARN" "Existe pero error al parsear JSON"
    }
} elseif (Test-Path $envTemplate) {
    Copy-Item $envTemplate $envJson
    Add-Check "env.json" "FAIL" "No existia — creado desde plantilla. Rellena $envJson con tus credenciales reales."
} else {
    Add-Check "env.json" "FAIL" "No existe env.json ni env.template.json en $pluginRoot"
}

# Check 1: Conexion BD — Settings.xml publicado (fuente canonica), XMLConfig.xml legacy como fallback
$settingsPath = "C:\AIS\$proyecto\bin\Settings\Settings.xml"
$legacyXml    = Join-Path $workspace "docs\XMLConfig.xml"
if (Test-Path $settingsPath) {
    try {
        [xml]$xml = Get-Content $settingsPath -Raw -Encoding UTF8
        $conns = @($xml.SelectNodes("//*[local-name()='oledbconnectionstring']") | ForEach-Object { $_.value } | Where-Object { $_ -and $_.Contains('=') })
        if ($conns.Count -gt 0) {
            $isOracle = $conns[0].ToUpper().Contains('(DESCRIPTION=') -or $conns[0].ToUpper().Contains('SERVICE_NAME') -or $conns[0].ToUpper().Contains('(SID=')
            $motor = if ($isOracle) { "ORACLE" } else { "SQLSERVER" }
            Add-Check "Conexion BD" "OK" "Settings.xml — Motor: $motor, entornos: $($conns.Count)"
        } else {
            Add-Check "Conexion BD" "WARN" "Settings.xml sin oledbconnectionstring utilizable (cifrada?)"
        }
    } catch {
        Add-Check "Conexion BD" "WARN" "Settings.xml existe pero error al parsear: $($_.Exception.Message)"
    }
} elseif (Test-Path $legacyXml) {
    Add-Check "Conexion BD" "WARN" "Solo docs\XMLConfig.xml legacy — publica la solucion para generar $settingsPath"
} else {
    Add-Check "Conexion BD" "FAIL" "No encontrado $settingsPath (solucion sin publicar) ni docs\XMLConfig.xml"
}

# Check 2: Ruta AIS base
$aisBase = "C:\AIS\$proyecto\"
if (Test-Path $aisBase) {
    Add-Check "Ruta AIS" "OK" $aisBase
} else {
    Add-Check "Ruta AIS" "WARN" "No existe: $aisBase (puede ser proyecto nuevo)"
}

# Check 3: dotnet SDK
try {
    $dotnetOut = & dotnet --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Check "dotnet SDK" "OK" "$dotnetOut"
    } else {
        Add-Check "dotnet SDK" "FAIL" "dotnet no disponible o error: $dotnetOut"
    }
} catch {
    Add-Check "dotnet SDK" "FAIL" "dotnet no encontrado en PATH"
}

# Check 4: SVN (primario en ScacsWeb — TortoiseSVN)
try {
    $svnOut = & svn --version --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Check "SVN" "OK" "$svnOut"
    } else {
        Add-Check "SVN" "WARN" "svn no disponible — modos SVN no funcionarán"
    }
} catch {
    Add-Check "SVN" "WARN" "svn no encontrado en PATH — modos SVN no funcionarán"
}

# Check 4b: Git (secundario — puede que el proyecto no use Git)
try {
    $gitOut = & git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Check "Git" "OK" "$gitOut"
    } else {
        Add-Check "Git" "WARN" "git no disponible — modos Git no funcionarán"
    }
} catch {
    Add-Check "Git" "WARN" "git no encontrado en PATH — modos Git no funcionarán"
}

# Check 5: Modelo BD (informativo)
$modelPath = Join-Path $workspace "BD\$proyecto-model.json"
if (Test-Path $modelPath) {
    try {
        $model = Get-Content $modelPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $updatedAt  = $model.updated_at
        $tableCount = ($model.tables | Get-Member -MemberType NoteProperty).Count
        Add-Check "Modelo BD" "OK" "Actualizado: $updatedAt, Tablas: $tableCount"
    } catch {
        Add-Check "Modelo BD" "WARN" "Existe pero error al leer JSON"
    }
} else {
    Add-Check "Modelo BD" "INFO" "No existe aún — ejecutar 'sincroniza el modelo BD'"
}

# Check 6: Documentación agentic SCACS
$docsPath = Join-Path $workspace "docs\scacs\00-index.md"
if (Test-Path $docsPath) {
    Add-Check "Docs agentic" "OK" "Indice maestro SCACS presente"
} else {
    Add-Check "Docs agentic" "WARN" "No encontrado — agente funcionará sin contexto técnico completo"
}

# Output JSON estructurado para consumo del agente
$output = @{
    workspace   = $workspace
    proyecto    = $proyecto
    timestamp   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    overall     = $overallStatus
    checks      = $results
}

$output | ConvertTo-Json -Depth 4

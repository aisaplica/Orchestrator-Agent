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

# Check 1: XMLConfig.xml
$xmlPath = Join-Path $workspace "docs\XMLConfig.xml"
if (Test-Path $xmlPath) {
    try {
        [xml]$xml = Get-Content $xmlPath -Raw -Encoding UTF8
        $motorNode = $xml.SelectSingleNode("//*[local-name()='Motor' or local-name()='motor']")
        $motor = if ($motorNode) { $motorNode.InnerText } else { $null }
        $dsNode = $xml.SelectSingleNode("//*[local-name()='DataSource' or local-name()='datasource' or local-name()='ConnectionString']")
        $ds    = if ($dsNode) { $dsNode.InnerText } else { $null }
        $detail = if ($motor) { "Motor: $motor" } else { "Existe (motor no detectado)" }
        if ($ds) { $detail += ", DS: $($ds.Substring(0, [Math]::Min(30,$ds.Length)))" }
        Add-Check "XMLConfig.xml" "OK" $detail
    } catch {
        Add-Check "XMLConfig.xml" "WARN" "Existe pero error al parsear: $($_.Exception.Message)"
    }
} else {
    Add-Check "XMLConfig.xml" "FAIL" "No encontrado: $xmlPath"
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

#Requires -Version 5.1
<#
.SYNOPSIS
    Lee XMLConfig.xml y devuelve configuración BD como JSON.
.PARAMETER Workspace
    Ruta raíz del proyecto (trunk/).
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace
)

$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$xmlPath = Join-Path $Workspace "docs\XMLConfig.xml"
if (-not (Test-Path $xmlPath)) {
    @{ error = "XMLConfig.xml no encontrado: $xmlPath" } | ConvertTo-Json -Compress
    exit 1
}

try {
    [xml]$xml = Get-Content $xmlPath -Raw -Encoding UTF8
} catch {
    @{ error = "Error al parsear XMLConfig.xml: $($_.Exception.Message)" } | ConvertTo-Json -Compress
    exit 1
}

# Motor
$motorNode = $xml.SelectSingleNode("//*[local-name()='Motor' or local-name()='motor']")
$motor = if ($motorNode) { $motorNode.InnerText.Trim().ToUpper() } else { "SQLSERVER" }

# DataSource / ConnectionString
$dsNode  = $xml.SelectSingleNode("//*[local-name()='DataSource'    or local-name()='datasource']")
$csNode  = $xml.SelectSingleNode("//*[local-name()='ConnectionString' or local-name()='connectionstring']")
$datasource = if ($dsNode) { $dsNode.InnerText.Trim() } elseif ($csNode) { $csNode.InnerText.Trim() } else { "" }

# Schema / Database owner
$schemaNode = $xml.SelectSingleNode("//*[local-name()='Schema' or local-name()='schema' or local-name()='Database' or local-name()='database']")
$schema = if ($schemaNode) { $schemaNode.InnerText.Trim() } else { "" }

# User
$userNode = $xml.SelectSingleNode("//*[local-name()='User' or local-name()='user' or local-name()='Usuario' or local-name()='usuario']")
$user = if ($userNode) { $userNode.InnerText.Trim() } else { "" }

# Fallback: extraer schema/user del connection string (SQL Server)
if (-not $schema -and $datasource -match "(?:Database|Initial Catalog)\s*=\s*([^;]+)") {
    $schema = $matches[1].Trim()
}
if (-not $user -and $datasource -match "User\s*(?:Id|ID)?\s*=\s*([^;]+)") {
    $user = $matches[1].Trim()
}

# model_path: workspace\BD\<proyecto>-model.json
# proyecto = carpeta padre de trunk/ (e.g. C:\...\SCACSWebCDI\trunk → SCACSWebCDI)
$proyecto = Split-Path (Split-Path $Workspace -Parent) -Leaf
$modelPath = Join-Path $Workspace "BD\$proyecto-model.json"

@{
    motor      = $motor
    datasource = $datasource
    schema     = $schema
    user       = $user
    model_path = $modelPath
    proyecto   = $proyecto
} | ConvertTo-Json -Compress

<#
.SYNOPSIS
    Obtiene los detalles de un issue de MantisBT via REST API y devuelve JSON.

.PARAMETER IssueId
    Número de issue Mantis (sin prefijo #).

.PARAMETER Url
    URL base de la instancia MantisBT. Por defecto: $env:MANTIS_URL.

.PARAMETER ApiKey
    API key de MantisBT. Por defecto: $env:MANTIS_API_KEY.

.EXAMPLE
    .\mantis-get-issue.ps1 -IssueId 1234
    .\mantis-get-issue.ps1 -IssueId 1234 -Url "https://mantis.ejemplo.com" -ApiKey "abc123"
#>
param(
    [Parameter(Mandatory)][string]$IssueId,
    [string]$Url    = $env:MANTIS_URL,
    [string]$ApiKey = $env:MANTIS_API_KEY
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

if (-not $Url) {
    Write-Error "MANTIS_URL no definida. Establecer variable de entorno o pasar -Url. Ver references/mantis.md"
    exit 1
}
if (-not $ApiKey) {
    Write-Error "MANTIS_API_KEY no definida. Establecer variable de entorno o pasar -ApiKey. Ver references/mantis.md"
    exit 1
}

$uri     = "$($Url.TrimEnd('/'))/issues/$IssueId"
$headers = @{ Authorization = $ApiKey }

try {
    $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get -ErrorAction Stop
    $response | ConvertTo-Json -Depth 10
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401) {
        Write-Error "Mantis: credenciales incorrectas (401). Verificar MANTIS_API_KEY."
    } elseif ($statusCode -eq 403) {
        Write-Error "Mantis: acceso denegado al issue $IssueId (403). Verificar permisos de la API key."
    } elseif ($statusCode -eq 404) {
        Write-Error "Mantis: issue $IssueId no encontrado (404)."
    } else {
        Write-Error "Mantis error al obtener issue $IssueId`: $_"
    }
    exit 1
}

<#
.SYNOPSIS
    CLI unificado para MantisBT REST API. Lee y escribe issues.

.PARAMETER Action
    get-issue | list-issues | list-projects | get-statuses |
    patch-status | post-note | attach-file

.PARAMETER IssueId
    Número de issue Mantis (sin #). Requerido para: get-issue, patch-status, post-note, attach-file.

.PARAMETER ProjectId
    ID interno del proyecto Mantis. Requerido para: list-issues.

.PARAMETER Status
    Estado destino (nombre o ID numérico). Requerido para: patch-status.

.PARAMETER Text
    Cuerpo del comentario. Requerido para: post-note.

.PARAMETER FilePath
    Ruta local al archivo a adjuntar. Requerido para: attach-file.

.PARAMETER PageSize
    Número de issues a devolver en list-issues. Default: 100.

.PARAMETER Url
    URL base de la instancia MantisBT. Default: env.json > $env:MANTIS_URL.

.PARAMETER ApiKey
    API key de MantisBT. Default: env.json > $env:MANTIS_API_KEY.

.EXAMPLE
    .\mantis-cli.ps1 -Action get-issue -IssueId 1234
    .\mantis-cli.ps1 -Action list-issues -ProjectId 215
    .\mantis-cli.ps1 -Action patch-status -IssueId 1234 -Status "en proceso"
    .\mantis-cli.ps1 -Action post-note -IssueId 1234 -Text "Desarrollo iniciado."
    .\mantis-cli.ps1 -Action attach-file -IssueId 1234 -FilePath "C:\scripts\migration.sql"
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet("get-issue","list-issues","list-projects","get-statuses","patch-status","post-note","attach-file")]
    [string]$Action,

    [string]$IssueId,
    [string]$ProjectId,
    [string]$Status,
    [string]$Text,
    [string]$FilePath,
    [int]$PageSize = 100,
    [string]$Url,
    [string]$ApiKey
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

# --- Resolución de credenciales ---
function Resolve-MantisCredentials {
    param([string]$UrlParam, [string]$KeyParam)

    $url = $UrlParam
    $key = $KeyParam

    if (-not $url -or -not $key) {
        $envPath = Join-Path $env:USERPROFILE ".claude\skills\project-db-env\env.json"
        if (Test-Path $envPath) {
            try {
                $cfg = Get-Content $envPath -Raw | ConvertFrom-Json
                if (-not $url) { $url = $cfg.herramientas.mantis.url }
                if (-not $key) { $key = $cfg.herramientas.mantis.api_key }
            } catch { }
        }
    }

    if (-not $url) { $url = $env:MANTIS_URL }
    if (-not $key) { $key = $env:MANTIS_API_KEY }

    if (-not $url) {
        Write-Error "MANTIS_URL no definida. Configurar en project-db-env/env.json o variable de entorno MANTIS_URL."
        exit 1
    }
    if (-not $key) {
        Write-Error "MANTIS_API_KEY no definida. Configurar en project-db-env/env.json o variable de entorno MANTIS_API_KEY."
        exit 1
    }

    return @{ Url = $url.TrimEnd('/'); Key = $key }
}

$creds = Resolve-MantisCredentials -UrlParam $Url -KeyParam $ApiKey
$headers = @{ Authorization = $creds.Key; "Content-Type" = "application/json" }

function Invoke-Mantis {
    param([string]$Method, [string]$Path, [hashtable]$Body = $null)
    $uri = "$($creds.Url)$Path"
    try {
        if ($Body) {
            $json = $Body | ConvertTo-Json -Depth 10
            Invoke-RestMethod -Uri $uri -Headers $headers -Method $Method -Body $json -ErrorAction Stop
        } else {
            Invoke-RestMethod -Uri $uri -Headers $headers -Method $Method -ErrorAction Stop
        }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        $msg  = switch ($code) {
            401 { "Credenciales incorrectas (401). Verificar API key." }
            403 { "Acceso denegado (403). Verificar permisos de la API key." }
            404 { "Recurso no encontrado (404): $Path" }
            default { "Error $code`: $_" }
        }
        Write-Error "Mantis [$Method $Path]: $msg"
        exit 1
    }
}

switch ($Action) {

    "get-issue" {
        if (-not $IssueId) { Write-Error "-IssueId requerido para get-issue"; exit 1 }
        $r = Invoke-Mantis -Method Get -Path "/issues/$IssueId"
        $r | ConvertTo-Json -Depth 10
    }

    "list-issues" {
        if (-not $ProjectId) { Write-Error "-ProjectId requerido para list-issues"; exit 1 }
        $r = Invoke-Mantis -Method Get -Path "/issues?project_id=$ProjectId&page_size=$PageSize"
        $r | ConvertTo-Json -Depth 10
    }

    "list-projects" {
        $r = Invoke-Mantis -Method Get -Path "/projects"
        $r | ConvertTo-Json -Depth 10
    }

    "get-statuses" {
        # Devuelve los estados disponibles en esta instancia Mantis
        $r = Invoke-Mantis -Method Get -Path "/issues?page_size=1"
        if ($r.issues -and $r.issues.Count -gt 0) {
            # No hay endpoint directo; extraer del primer issue como referencia
            Write-Host "Estado del issue de muestra:"
            $r.issues[0].status | ConvertTo-Json
        } else {
            # Fallback: devolver estados estándar MantisBT
            @(
                @{id=10; label="nueva"},
                @{id=20; label="reconocida"},
                @{id=30; label="asignada"},
                @{id=40; label="comentada"},
                @{id=50; label="confirmada"},
                @{id=80; label="resuelta"},
                @{id=90; label="cerrada"}
            ) | ConvertTo-Json
        }
    }

    "patch-status" {
        if (-not $IssueId) { Write-Error "-IssueId requerido para patch-status"; exit 1 }
        if (-not $Status)  { Write-Error "-Status requerido para patch-status"; exit 1 }

        $body = if ($Status -match '^\d+$') {
            @{ status = @{ id = [int]$Status } }
        } else {
            @{ status = @{ label = $Status } }
        }

        $r = Invoke-Mantis -Method Patch -Path "/issues/$IssueId" -Body $body
        $r | ConvertTo-Json -Depth 5
    }

    "post-note" {
        if (-not $IssueId) { Write-Error "-IssueId requerido para post-note"; exit 1 }
        if (-not $Text)    { Write-Error "-Text requerido para post-note"; exit 1 }

        $body = @{ text = @{ body = $Text } }
        $r = Invoke-Mantis -Method Post -Path "/issues/$IssueId/notes" -Body $body
        $r | ConvertTo-Json -Depth 5
    }

    "attach-file" {
        if (-not $IssueId)  { Write-Error "-IssueId requerido para attach-file"; exit 1 }
        if (-not $FilePath) { Write-Error "-FilePath requerido para attach-file"; exit 1 }
        if (-not (Test-Path $FilePath)) { Write-Error "Archivo no encontrado: $FilePath"; exit 1 }

        $fileName    = Split-Path $FilePath -Leaf
        $fileBytes   = [System.IO.File]::ReadAllBytes($FilePath)
        $fileContent = [System.Convert]::ToBase64String($fileBytes)
        $mimeType    = if ($fileName -match '\.sql$') { "text/plain" }
                       elseif ($fileName -match '\.zip$') { "application/zip" }
                       else { "application/octet-stream" }

        $body = @{
            files = @(
                @{
                    name    = $fileName
                    content = $fileContent
                    type    = $mimeType
                }
            )
        }

        # Usar headers sin Content-Type para dejar que Invoke-RestMethod gestione multipart
        $headersFile = @{ Authorization = $creds.Key; "Content-Type" = "application/json" }
        $json = $body | ConvertTo-Json -Depth 5
        try {
            $r = Invoke-RestMethod -Uri "$($creds.Url)/issues/$IssueId/files" -Headers $headersFile -Method Post -Body $json -ErrorAction Stop
            $r | ConvertTo-Json -Depth 5
        } catch {
            Write-Error "Error al adjuntar archivo: $_"
            exit 1
        }
    }
}

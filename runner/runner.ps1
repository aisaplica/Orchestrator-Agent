param(
    [string]$InputFile = ""
)

Write-Host "====================================="
Write-Host " ORCHESTRATOR RUNNER"
Write-Host "====================================="

# Localizar hooks/ relativo a este mismo script (portable, sin rutas hardcodeadas)
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot  = Split-Path -Parent $scriptDir
$hooksRoot  = Join-Path $skillRoot "hooks"

$content = $null

# =====================================
# MODO 1: InputFile (inline / manual)
# Prioridad alta: si se pasa -InputFile no leer stdin
# =====================================
if ($InputFile) {
    if (!(Test-Path $InputFile)) {
        Write-Host "ERROR: Input file not found: $InputFile"
        exit 1
    }
    Write-Host "Mode: InputFile"
    $content = Get-Content $InputFile -Raw
}

# =====================================
# MODO 2: Stop hook (stdin JSON con transcript_path)
# Solo si NO se paso -InputFile
# =====================================
if (-not $content) {
    try {
        $stdinContent = $input | Out-String
        if ($stdinContent -and $stdinContent.Trim()) {
            $hookData = $stdinContent | ConvertFrom-Json
            $transcriptPath = $hookData.transcript_path
            if ($transcriptPath -and (Test-Path $transcriptPath)) {
                Write-Host "Mode: Stop hook (transcript)"
                $lastText = $null
                Get-Content $transcriptPath -Encoding UTF8 | ForEach-Object {
                    $line = $_.Trim()
                    if (-not $line) { return }
                    try {
                        $msg = $line | ConvertFrom-Json
                        if ($msg.role -eq "assistant") {
                            if ($msg.content -is [string]) { $lastText = $msg.content }
                            elseif ($msg.content -is [array]) {
                                foreach ($block in $msg.content) {
                                    if ($block.type -eq "text" -and $block.text) { $lastText = $block.text }
                                }
                            }
                        }
                    } catch {}
                }
                $content = $lastText
            }
        }
    } catch {}
}

if (-not $content -or -not $content.Trim()) {
    Write-Host "No input content found"
    exit 0
}

Write-Host "Analyzing agent output..."

# =====================================
# EXTRAER TYPE
# =====================================
if ($content -match "TYPE:\s*(.+)") {
    $type = $matches[1].Trim()
    Write-Host "Detected TYPE: $type"
} else {
    Write-Host "No executable TYPE found"
    exit 0
}

# =====================================
# EXTRAER COMMAND
# =====================================
if ($content -match "COMMAND:\s*(.+)") {
    $command = $matches[1].Trim()
    Write-Host "Detected COMMAND: $command"
} else {
    Write-Host "No COMMAND found"
    exit 0
}

# =====================================
# SEGURIDAD
# =====================================

# Resolver .\hooks\ relativo → hooks/ dentro de la skill (portable)
$command = $command -replace '\.[\\/]hooks[\\/]', "$hooksRoot\"

# Solo permitir scripts dentro de hooks/
if ($command -notmatch [regex]::Escape($hooksRoot)) {
    Write-Host "SECURITY BLOCK: Command not in skill hooks path"
    exit 1
}

# Bloquear comandos peligrosos
if ($command -match "\brm\b|\bdel\b|\bformat\b|\bshutdown\b|Remove-Item") {
    Write-Host "SECURITY BLOCK: Dangerous command detected"
    exit 1
}

# =====================================
# EJECUCION
# =====================================

Set-Location $skillRoot | Out-Null

# Envolver script path en comillas si contiene espacios (necesario para Invoke-Expression)
$command = $command -replace '^(.+?\.ps1)', '& "$1"'

Write-Host "Executing: $command"
Write-Host "-------------------------------------"

try {
    Invoke-Expression $command
    $exitCode = $LASTEXITCODE
    Write-Host "-------------------------------------"
    if ($exitCode -ne 0) {
        Write-Host "Execution FAILED with exit code: $exitCode"
        exit $exitCode
    }
    Write-Host "Execution completed successfully"
}
catch {
    Write-Host "-------------------------------------"
    Write-Host "Execution failed: $_"
    exit 1
}

Write-Host "Runner finished"

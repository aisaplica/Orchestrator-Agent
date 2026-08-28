#Requires -Version 5.1
<#
.SYNOPSIS
    Ejecuta los tests de una solución (`dotnet test`) y devuelve el resultado como JSON.

.DESCRIPTION
    Equivalente hook de la tool MCP `run_tests` — paso 8 del pipeline y `/orchestrator-test`.

    1. Parsea la .sln y busca proyectos de test (nombre `*test*`, `<IsTestProject>`,
       o paquetes xunit/MSTest/NUnit/Microsoft.NET.Test.Sdk).
    2. Si no hay ninguno → { skipped: true } (el pipeline debe crear uno con create-test-project.ps1).
    3. Si hay → `dotnet test` con logger TRX y parsea el .trx → passed/failed/failures[].

    NOTA WebForms: en soluciones ScacsWeb Online `dotnet test` puede fallar con MSB4019
    si el build toca el proyecto web. Para esos casos usar `vstest.console.exe` directo
    sobre el .dll de test ya compilado (ver agents/build.md). Este hook cubre el caso
    SDK-style estándar.

.PARAMETER SlnPath
    Ruta al archivo .sln.

.PARAMETER NoBuild
    Pasa --no-build a `dotnet test` (asume binarios ya compilados).

.EXAMPLE
    .\test-runner-check.ps1 "C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk\Ingenieros.sln"
#>
param(
    [Parameter(Mandatory = $true)][string]$SlnPath,
    [switch]$NoBuild
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 6 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

if (-not (Test-Path -LiteralPath $SlnPath -PathType Leaf)) { Fail "No existe la .sln: $SlnPath" }
$slnDir = Split-Path -Parent (Resolve-Path -LiteralPath $SlnPath)

# --- localizar proyectos de test en la .sln ---
$slnText = Get-Content -LiteralPath $SlnPath -Raw
$projRel = [regex]::Matches($slnText, 'Project\("\{[^}]+\}"\)\s*=\s*"[^"]+",\s*"([^"]+\.csproj)"') |
    ForEach-Object { $_.Groups[1].Value }

$testProjects = @()
foreach ($rel in $projRel) {
    $full = Join-Path $slnDir ($rel -replace '\\', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $full)) { continue }
    $csproj = Get-Content -LiteralPath $full -Raw
    $isTest = ($csproj -match '(?i)<IsTestProject>\s*true') -or
              ($csproj -match '(?i)Microsoft\.NET\.Test\.Sdk') -or
              ($csproj -match '(?i)"(xunit|MSTest\.TestFramework|NUnit)"') -or
              ($csproj -match '(?i)Include="(xunit|MSTest\.TestFramework|NUnit)"') -or
              ([IO.Path]::GetFileNameWithoutExtension($full) -match '(?i)tests?$')
    if ($isTest) { $testProjects += $full }
}

if ($testProjects.Count -eq 0) {
    Emit @{
        success        = $true
        skipped        = $true
        skipped_reason = "No se detectó proyecto de tests en la .sln. Crear uno con create-test-project.ps1 / create_test_project."
        passed         = 0; failed = 0; total = 0
    }
    exit 0
}

# --- dotnet disponible? ---
try {
    $null = & dotnet --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
}
catch { Fail "dotnet CLI no disponible en PATH — no se pueden ejecutar los tests" }

# --- ejecutar ---
$resultsDir = Join-Path ([IO.Path]::GetTempPath()) ("orch-tests-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
$trxName = "results.trx"

$dtArgs = @("test", $SlnPath, "--nologo", "--logger", "trx;LogFileName=$trxName", "--results-directory", $resultsDir)
if ($NoBuild) { $dtArgs += "--no-build" }

$stdout = & dotnet @dtArgs 2>&1
$dotnetExit = $LASTEXITCODE

$trxPath = Join-Path $resultsDir $trxName
if (-not (Test-Path -LiteralPath $trxPath)) {
    Emit @{
        success     = $false
        error       = "dotnet test no generó TRX (exit $dotnetExit). Posible fallo de build o MSB4019 (WebForms → usar vstest.console.exe)."
        dotnet_exit = $dotnetExit
        output_tail = (($stdout | Select-Object -Last 15) -join "`n")
    }
    Remove-Item -LiteralPath $resultsDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 0
}

# --- parsear TRX ---
[xml]$trx = Get-Content -LiteralPath $trxPath -Raw
$counters = $trx.TestRun.ResultSummary.Counters
$total = [int]$counters.total
$passed = [int]$counters.passed
$failed = [int]$counters.failed
$skipped = [int]$counters.total - [int]$counters.executed

$durSec = 0.0
try {
    $times = $trx.TestRun.Times
    if ($times.start -and $times.finish) {
        $durSec = [Math]::Round((([datetime]$times.finish) - ([datetime]$times.start)).TotalSeconds, 1)
    }
} catch { }

$failures = @()
foreach ($r in @($trx.TestRun.Results.UnitTestResult)) {
    if (-not $r) { continue }
    if ($r.outcome -ne "Failed") { continue }
    $msg = ""
    $stack = ""
    if ($r.Output -and $r.Output.ErrorInfo) {
        $msg = ($r.Output.ErrorInfo.Message -as [string]).Trim()
        $stack = ($r.Output.ErrorInfo.StackTrace -as [string]).Trim()
    }
    $loc = ""
    if ($stack -match '(?m)^\s*(?:at|en)\s+(.+?\.[A-Za-z_<>]+\([^)]*\))') { $loc = $Matches[1] }
    $failures += [PSCustomObject]@{
        name     = ($r.testName -as [string])
        error    = if ($msg.Length -gt 500) { $msg.Substring(0, 500) + "..." } else { $msg }
        location = $loc
    }
}

Remove-Item -LiteralPath $resultsDir -Recurse -Force -ErrorAction SilentlyContinue

Emit @{
    success        = ($failed -eq 0 -and $dotnetExit -eq 0)
    skipped        = $false
    test_projects  = $testProjects.Count
    total          = $total
    passed         = $passed
    failed         = $failed
    skipped_tests  = $skipped
    duration_s     = $durSec
    failures       = $failures
    dotnet_exit    = $dotnetExit
}
exit 0

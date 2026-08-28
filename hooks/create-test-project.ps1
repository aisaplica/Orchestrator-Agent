#Requires -Version 5.1
<#
.SYNOPSIS
    Crea un proyecto de tests y lo añade a la .sln.

.DESCRIPTION
    Equivalente hook de la tool MCP `create_test_project`. Se usa cuando `run_tests`
    devuelve skipped=true. Crea `<slnDir>\tests\<ProjectName>\<ProjectName>.csproj`
    con `dotnet new`, y lo engancha a la solución con `dotnet sln add`.

.PARAMETER SlnPath
    Ruta al archivo .sln.

.PARAMETER Framework
    xunit | mstest | nunit. Por defecto xunit.

.PARAMETER ProjectName
    Nombre del proyecto. Por defecto `<NombreSln>.Tests`.

.EXAMPLE
    .\create-test-project.ps1 "C:\...\Ingenieros.sln" -Framework xunit
#>
param(
    [Parameter(Mandatory = $true)][string]$SlnPath,
    [ValidateSet('xunit', 'mstest', 'nunit')][string]$Framework = 'xunit',
    [string]$ProjectName = ''
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 5 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

if (-not (Test-Path -LiteralPath $SlnPath -PathType Leaf)) { Fail "No existe la .sln: $SlnPath" }
$slnDir = Split-Path -Parent (Resolve-Path -LiteralPath $SlnPath).Path
$slnName = [IO.Path]::GetFileNameWithoutExtension($SlnPath)

if (-not $ProjectName) { $ProjectName = "$slnName.Tests" }
if ($ProjectName -notmatch '^[A-Za-z_][A-Za-z0-9_.]*$') { Fail "ProjectName inválido: $ProjectName" }

try {
    $null = & dotnet --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
}
catch { Fail "dotnet CLI no disponible en PATH" }

$projDir = Join-Path (Join-Path $slnDir "tests") $ProjectName
$projPath = Join-Path $projDir "$ProjectName.csproj"

if (Test-Path -LiteralPath $projPath) { Fail "Ya existe: $projPath" }
New-Item -ItemType Directory -Path $projDir -Force | Out-Null

$newOut = & dotnet new $Framework --name $ProjectName --output $projDir 2>&1
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $projPath)) {
    Remove-Item -LiteralPath $projDir -Recurse -Force -ErrorAction SilentlyContinue
    Fail "dotnet new $Framework falló: $(($newOut | Select-Object -Last 5) -join ' ')"
}

$addOut = & dotnet sln $SlnPath add $projPath 2>&1
$added = ($LASTEXITCODE -eq 0)

Emit @{
    success       = $true
    project_name  = $ProjectName
    project_path  = $projPath
    framework     = $Framework
    added_to_sln  = $added
    add_output    = if (-not $added) { (($addOut | Select-Object -Last 5) -join ' ') } else { $null }
    note          = "Proyecto vacío con el test de plantilla. Generar tests reales con el agente crear-tests / tester."
}
exit 0

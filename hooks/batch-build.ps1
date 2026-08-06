param(
    [string]$solution,
    [string]$workspace
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
$solutionPath = "$workspace\dotNet\Batch\$solution\$solution.sln"

Write-Host "Building Batch solution: $solutionPath"

if (!(Test-Path $solutionPath)) {
    Write-Error "Solution not found: $solutionPath"
    exit 1
}

dotnet build "$solutionPath" -c Debug
dotnet build "$solutionPath" -c Release

# Localizar bin\Release bajo dotNet\Batch\<solution>
$batchRoot = "$workspace\dotNet\Batch\$solution"
$candidatos = @(
    "$batchRoot\bin\Release",
    "$batchRoot\$solution\bin\Release"
)
$exePath = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $exePath) {
    $found = Get-ChildItem $batchRoot -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue |
             Where-Object { $_.DirectoryName -match "bin.Release" } |
             Select-Object -First 1
    if ($found) { $exePath = $found.DirectoryName }
}

if (-not $exePath) {
    Write-Error "No se encontro bin\Release para $solution bajo $batchRoot"
    exit 1
}

Write-Host "Binaries en: $exePath"

# Obtener proyecto AIS (carpeta anterior a src)
$project = (Get-Item $workspace).Parent.Parent.Name
$aisPath = "C:\AIS\$project\bin"

Write-Host "Copiando a $aisPath"

if (!(Test-Path $aisPath)) {
    New-Item -ItemType Directory -Path $aisPath -Force | Out-Null
}

# Borrar solo los ficheros que se van a copiar (no limpiar destino completo)
Get-ChildItem "$exePath" -File -Recurse | ForEach-Object {
    $rel = $_.FullName.Substring($exePath.Length).TrimStart('\')
    $dst = Join-Path $aisPath $rel
    if (Test-Path $dst) { Remove-Item $dst -Force }
}

Copy-Item "$exePath\*" $aisPath -Recurse -Force
Write-Host "OK — binarios copiados a $aisPath"

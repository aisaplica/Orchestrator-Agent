param(
    [string]$path
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
if (!(Test-Path $path)) {
    Write-Host "Solution not found"
    exit 1
}

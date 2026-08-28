#Requires -Version 5.1
<#
.SYNOPSIS
    Localiza símbolos C# en scope_dirs. Una sola pasada Select-String multi-patrón.
.PARAMETER ScopeDirs
    Directorios de búsqueda, coma-separados.
.PARAMETER Symbols
    Símbolos a localizar, coma-separados. Acepta uno o varios.
.PARAMETER Type
    Filtro de tipo: class|interface|enum|method|property|any (default: any).
#>
param(
    [string]$ScopeDirs = "",
    [string]$Symbols   = "",
    [string]$Type      = "any"
)

$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$symbolList = @($Symbols -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })

if ($symbolList.Count -eq 0) {
    @{ error = "No symbols provided" } | ConvertTo-Json -Compress
    exit 1
}

$dirs = @($ScopeDirs -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -and (Test-Path $_) })

if ($dirs.Count -eq 0) {
    @{ error = "No valid scope directories: $ScopeDirs"; symbols = @{} } | ConvertTo-Json -Depth 3 -Compress
    exit 1
}

# Recopilar ficheros .cs, excluir bin\ y obj\ para no desperdiciar presupuesto en código generado
$files = @(
    $dirs | ForEach-Object {
        Get-ChildItem -Path $_ -Filter "*.cs" -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' }
    }
)

function Get-Pattern([string]$sym, [string]$type) {
    $e = [regex]::Escape($sym)
    switch ($type) {
        "class"     { return "\bclass\s+$e\b" }
        "interface" { return "\binterface\s+$e\b" }
        "enum"      { return "\benum\s+$e\b" }
        "method"    { return "\b$e\s*\(" }
        "property"  { return "\b$e\s*(?:\{|=>)" }
        default     { return $e }
    }
}

# Construir mapa patrón→símbolo para agrupar resultados
$patternToSym = @{}
$patterns = @($symbolList | ForEach-Object {
    $p = Get-Pattern $_ $Type
    $patternToSym[$p] = $_
    $p
})

# Inicializar resultados con arrays vacíos explícitos
$results = @{}
foreach ($sym in $symbolList) {
    $results[$sym] = @{ found = $false; count = 0; matches = [System.Collections.Generic.List[object]]::new() }
}

if ($files.Count -gt 0) {
    # Una sola pasada Select-String sobre todos los ficheros con todos los patrones.
    # Select-String acepta array de patrones: devuelve hits etiquetados con $hit.Pattern.
    $hits = $files | Select-String -Pattern $patterns -CaseSensitive:$false -ErrorAction SilentlyContinue
    foreach ($hit in $hits) {
        $sym = $patternToSym[$hit.Pattern]
        if (-not $sym) { continue }
        $results[$sym].matches.Add([PSCustomObject]@{
            file    = $hit.Path
            line    = $hit.LineNumber
            content = $hit.Line.Trim()
        })
    }
    foreach ($sym in $symbolList) {
        # Usar .Count sobre List<T> — sin el bug de Sort-Object -Unique (RS fix)
        $cnt = $results[$sym].matches.Count
        $results[$sym].count = $cnt
        $results[$sym].found = $cnt -gt 0
    }
}

@{ symbols = $results; file_count = $files.Count } | ConvertTo-Json -Depth 6 -Compress

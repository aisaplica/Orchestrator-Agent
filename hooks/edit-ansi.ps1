#Requires -Version 5.1
<#
.SYNOPSIS
    Edita un archivo fuente respetando su codificación original — evita corromper
    acentos al reescribir un .cs/.aspx ANSI/Windows-1252 como UTF-8.

.DESCRIPTION
    Las tools Edit/Write de Claude Code escriben SIEMPRE UTF-8. Muchos fuentes
    ScacsWeb (.cs, .aspx, .ascx, .asax, .config) están en Windows-1252 sin BOM:
    reescribirlos con Edit/Write rompe 'á é í ó ú ñ ¿ ¡' en comentarios, strings
    y literales, sin error de compilación — el bug aparece en runtime o en pantalla.

    Este hook detecta la codificación real del archivo (BOM / heurística UTF-8
    estricta / fallback codepage ANSI del sistema) y reescribe con la MISMA,
    aplicando un find/replace de texto.

.PARAMETER Path
    Archivo a editar.

.PARAMETER Search
    Texto a buscar. Literal por defecto; expresión regular .NET con -Regex.

.PARAMETER Replace
    Texto de reemplazo. Puede ser cadena vacía (borrar). Con -Regex admite $1, $2…

.PARAMETER All
    Reemplazar todas las ocurrencias. Por defecto solo la primera.

.PARAMETER Regex
    Interpretar -Search como expresión regular .NET.

.EXAMPLE
    .\edit-ansi.ps1 -Path "C:\...\ClienteDALC.cs" -Search "// versión antigua" -Replace "// versión revisada" -All

.EXAMPLE
    .\edit-ansi.ps1 -Path "C:\...\Datos.aspx.cs" -Regex -Search 'throw new GraveException\("EX001"' -Replace 'throw new GraveException("EX042"'
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Search,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Replace,
    [switch]$All,
    [switch]$Regex
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 6 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { Fail "Archivo no encontrado: $Path" }

try { [Text.Encoding]::RegisterProvider([Text.CodePagesEncodingProvider]::Instance) } catch { }

# --- detectar codificación (mismo patrón que parse-weblog.ps1) ---
$bytes = [IO.File]::ReadAllBytes($Path)
$enc = $null
$label = ""
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $enc = New-Object Text.UTF8Encoding($true)
    $label = "utf-8-bom"
}
else {
    try {
        $strict = New-Object Text.UTF8Encoding($false, $true)
        [void]$strict.GetString($bytes)
        $enc = New-Object Text.UTF8Encoding($false)
        $label = "utf-8"
    }
    catch {
        $cp = [int][Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
        if (-not $cp -or $cp -eq 0) { $cp = 1252 }
        try { $enc = [Text.Encoding]::GetEncoding($cp) } catch { $enc = [Text.Encoding]::GetEncoding(1252) }
        $label = "ansi-cp$($enc.CodePage)"
    }
}

$content = $enc.GetString($bytes)
if ($content.Length -gt 0 -and $content[0] -eq [char]0xFEFF) { $content = $content.Substring(1) }

# --- reemplazo ---
$count = 0
if ($Regex) {
    try { $rx = [regex]$Search } catch { Fail "Regex inválida: $_" }
    if (-not $rx.IsMatch($content)) { Fail "Patrón no encontrado: $Search" }
    if ($All) {
        $count = $rx.Matches($content).Count
        $new = $rx.Replace($content, $Replace)
    }
    else {
        $count = 1
        $new = $rx.Replace($content, $Replace, 1)
    }
}
else {
    $idx = $content.IndexOf($Search, [StringComparison]::Ordinal)
    if ($idx -lt 0) { Fail "Texto no encontrado: $Search" }
    if ($All) {
        $parts = $content.Split(@($Search), [StringSplitOptions]::None)
        $count = $parts.Length - 1
        $new = [string]::Join($Replace, $parts)
    }
    else {
        $count = 1
        $new = $content.Remove($idx, $Search.Length).Insert($idx, $Replace)
    }
}

if ($new -ceq $content) { Fail "Reemplazo sin efecto (¿Search igual a Replace?)" }

# --- escribir con la MISMA codificación detectada ---
try { [IO.File]::WriteAllText($Path, $new, $enc) }
catch { Fail "Error al escribir: $_" }

Emit @{ success = $true; path = $Path; encoding = $label; replacements = $count }
exit 0

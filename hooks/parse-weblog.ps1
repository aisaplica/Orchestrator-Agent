#Requires -Version 5.1
<#
.SYNOPSIS
    Parsea logs de error de la capa web (NLog/log4net, ELMAH XML, formato AgendaWeb AIS
    y volcados de stack .NET), agrupa las ocurrencias por FIRMA y devuelve solo el agregado.

.DESCRIPTION
    Un log repite el mismo fallo cientos de veces. Este hook colapsa las N ocurrencias
    de un mismo fallo en una firma con su recuento y una muestra — NUNCA emite el log completo.

    Firma = SHA1( tipo de excepción + frame más profundo de código propio + mensaje normalizado ).
    "Cliente 4711 no existe" y "Cliente 8322 no existe" son la misma firma.

    ⚠️ PII: los logs web llevan datos reales. Literales SQL entre comillas simples se redactan
    ('...' → '<val>') antes de salir en el JSON — es donde viaja la PII en los INSERT/WHERE
    del formato AgendaWeb. La redacción se aplica solo a la salida, nunca a la clave de firma.

    FORMATO AgendaWeb AIS. Cabecera:
        Error: (11/08/2026 13:45) - Codigo error: -2147467259 ... Descripción error: ORA-12899: ...
    Líneas siguientes: stack ("   en Clase.Metodo(...)").
    En este formato la excepción útil es el CÓDIGO (ORA-xxxxx o Codigo error: N), no el tipo .NET.

.PARAMETER Path
    Fichero de log o carpeta que los contiene.

.PARAMETER Glob
    Patrón de fichero cuando -Path es carpeta. Por defecto "*.log".

.PARAMETER Desde
    Fecha/hora ISO mínima (yyyy-MM-dd [HH:mm:ss]). Descarta eventos anteriores.

.PARAMETER Niveles
    Niveles a considerar, coma-separados. Por defecto "ERROR,FATAL".

.PARAMETER MaxSignatures
    Máximo de firmas distintas devueltas (las más frecuentes). Por defecto 30.

.PARAMETER Samples
    Muestras por firma. Por defecto 2.

.PARAMETER MaxLines
    Tope de líneas leídas en total. Por defecto 500000.

.EXAMPLE
    .\parse-weblog.ps1 -Path "C:\AIS\<Proyecto>\AgendaWeb\logs" -Desde 2026-08-01
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Glob = "*.log",
    [string]$Desde,
    [string]$Niveles = "ERROR,FATAL",
    [int]$MaxSignatures = 30,
    [int]$Samples = 2,
    [int]$MaxLines = 500000
)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Emit($obj) { $obj | ConvertTo-Json -Depth 8 -Compress }
function Fail($msg) { Emit @{ success = $false; error = "$msg" }; exit 0 }

if (-not (Test-Path -LiteralPath $Path)) { Fail "Ruta no encontrada: $Path" }

$item = Get-Item -LiteralPath $Path
if ($item.PSIsContainer) {
    $files = @(Get-ChildItem -LiteralPath $Path -Filter $Glob -File -Recurse -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending)
    if ($files.Count -eq 0) { Fail "Sin ficheros que casen con '$Glob' en $Path" }
} else {
    $files = @($item)
}

$desdeDt = $null
if ($Desde) {
    [datetime]$parsed = [datetime]::MinValue
    if ([datetime]::TryParse($Desde, [ref]$parsed)) { $desdeDt = $parsed }
    else { Fail "-Desde no es una fecha válida: $Desde" }
}

$nivelSet = @($Niveles -split ',' | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })

# --- Patrones ---
$rxStamp     = [regex]::new('^\s*[\[(]?(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:[.,]\d+)?|\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}(?::\d{2})?)')
$rxNivel     = [regex]::new('\b(FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b')
$rxExcepcion = [regex]::new('([A-Za-z_][\w.]*(?:Exception|Error))\b')
$rxFrame     = [regex]::new('(?:^|[\s\)])(?:at|en)\s+([\w.<>`+]+\.[\w<>`+]+)\s*\(')
$rxPlataforma = [regex]::new('^(System\.|Microsoft\.|mscorlib|Newtonsoft\.|lambda_method|NLog\.|log4net\.)')
$rxPantalla  = [regex]::new('([\w]+)\.(aspx|ascx)\.cs')

# Formato AgendaWeb AIS
$rxRsCab    = [regex]::new('^\s*([A-Za-z_][\w]*)\s*:\s*\(\s*(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\)\s*-')
$rxRsDesc   = [regex]::new('Descripci.{0,3}n\s+error:\s*(.*)$')
$rxRsCodigo = [regex]::new('Codigo\s+error:\s*(-?\d+)')
$rxOra      = [regex]::new('\bORA-\d{5}\b')
$rxLiteral  = [regex]::new("'[^']{0,400}'")

function Get-OrchestratorNivelEtiqueta([string]$etiqueta) {
    if (-not $etiqueta) { return "" }
    if ($etiqueta -match '(?i)fatal')       { return "FATAL" }
    if ($etiqueta -match '(?i)error|fail')  { return "ERROR" }
    if ($etiqueta -match '(?i)warn')        { return "WARNING" }
    if ($etiqueta -match '(?i)info')        { return "INFO" }
    if ($etiqueta -match '(?i)debug')       { return "DEBUG" }
    if ($etiqueta -match '(?i)trace')       { return "TRACE" }
    return ""
}

function Normalizar([string]$t) {
    if (-not $t) { return "" }
    $t = [regex]::Replace($t, '[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}', '<guid>')
    $t = [regex]::Replace($t, '\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}:\d{2})?', '<fecha>')
    $t = [regex]::Replace($t, '\d{2}/\d{2}/\d{4}', '<fecha>')
    $t = [regex]::Replace($t, '[A-Za-z]:\\[^\s"'']+', '<ruta>')
    $t = [regex]::Replace($t, '0x[0-9a-fA-F]+', '<hex>')
    $t = [regex]::Replace($t, '\d+', '#')
    return $t.Trim()
}

function Get-OrchestratorCodificacion([string]$ruta) {
    try {
        $bytes = New-Object byte[] 65536
        $fs = [IO.File]::OpenRead($ruta)
        try { $n = $fs.Read($bytes, 0, $bytes.Length) } finally { $fs.Dispose() }
        if ($n -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            return New-Object Text.UTF8Encoding($true)
        }
        while ($n -gt 0 -and ($bytes[$n - 1] -band 0xC0) -eq 0x80) { $n-- }
        if ($n -gt 0) { $n-- }
        $estricto = New-Object Text.UTF8Encoding($false, $true)
        [void]$estricto.GetString($bytes, 0, [Math]::Max($n, 0))
        return New-Object Text.UTF8Encoding($false)
    } catch {
        try {
            $cp = [int][Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
            try { [Text.Encoding]::RegisterProvider([Text.CodePagesEncodingProvider]::Instance) } catch { }
            return [Text.Encoding]::GetEncoding($cp)
        } catch { return [Text.Encoding]::Default }
    }
}

function Hash8([string]$t) {
    $sha = [Security.Cryptography.SHA1]::Create()
    try {
        $bytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($t))
        return (($bytes | ForEach-Object { $_.ToString("x2") }) -join '').Substring(0, 8)
    } finally { $sha.Dispose() }
}

function Recortar([string]$t, [int]$max) {
    if (-not $t) { return "" }
    $t = ($t -replace '[\x00-\x08\x0B\x0C\x0E-\x1F]', ' ').Trim()
    if ($t.Length -gt $max) { return $t.Substring(0, $max) + "..." }
    return $t
}

function Proteger([string]$t) {
    if (-not $t) { return $t }
    return $rxLiteral.Replace($t, "'<val>'")
}

$firmas       = @{}
$totalEventos = 0
$lineas       = 0
$topeLineas   = $false
$formatos     = @{}

function Registrar($evento, $fichero) {
    $texto   = ($evento.Lineas -join "`n")
    $primera = $evento.Lineas[0]

    $frame = ""
    foreach ($l in $evento.Lineas) {
        foreach ($mF in $rxFrame.Matches($l)) {
            $cand = $mF.Groups[1].Value
            if (-not $rxPlataforma.IsMatch($cand)) { $frame = $cand; break }
            if (-not $frame) { $frame = $cand }
        }
        if ($frame -and -not $rxPlataforma.IsMatch($frame)) { break }
    }

    $pantalla = ""
    foreach ($l in $evento.Lineas) {
        $mP = $rxPantalla.Match($l)
        if (-not $mP.Success) { continue }
        if ($mP.Groups[2].Value -ieq "aspx") { $pantalla = $mP.Groups[1].Value; break }
        if (-not $pantalla) { $pantalla = $mP.Groups[1].Value }
    }

    if ($evento.Formato -eq "agendaweb") {
        $mOra = $rxOra.Match($texto)
        $mCod = $rxRsCodigo.Match($primera)
        if ($mOra.Success) {
            $exc = $mOra.Value
        } elseif ($mCod.Success -and $mCod.Groups[1].Value -ne "0") {
            $exc = "COD" + $mCod.Groups[1].Value
        } else {
            $mEx = $rxExcepcion.Match($texto)
            $exc = if ($mEx.Success) { $mEx.Groups[1].Value }
                   elseif ($mCod.Success) { "COD" + $mCod.Groups[1].Value }
                   else { "SinCodigo" }
        }
        $mDesc = $rxRsDesc.Match($primera)
        $msg = if ($mDesc.Success) { $mDesc.Groups[1].Value } else { $rxRsCab.Replace($primera, '', 1) }
        $msg = $msg.Trim(" ", "-", "|", "`t")
    } else {
        $mEx = $rxExcepcion.Match($texto)
        $exc = if ($mEx.Success) { $mEx.Groups[1].Value } else { "SinExcepcion" }
        $msg = $rxStamp.Replace($primera, '')
        $msg = $rxNivel.Replace($msg, '', 1)
        $msg = $msg.Trim(" ", "-", "|", "[", "]", ":", "`t")
    }

    $clave = "$exc|$frame|$(Normalizar $msg)"
    $hash  = Hash8 $clave

    if (-not $firmas.ContainsKey($hash)) {
        $firmas[$hash] = [PSCustomObject]@{
            hash       = $hash
            exception  = $exc
            origin     = $frame
            pantalla   = $pantalla
            message    = Recortar (Proteger $msg) 300
            count      = 0
            first_seen = $evento.Stamp
            last_seen  = $evento.Stamp
            files      = @()
            samples    = @()
        }
    }

    $f = $firmas[$hash]
    $f.count++
    if ($evento.Stamp) {
        if (-not $f.first_seen -or $evento.Stamp -lt $f.first_seen) { $f.first_seen = $evento.Stamp }
        if (-not $f.last_seen  -or $evento.Stamp -gt $f.last_seen)  { $f.last_seen  = $evento.Stamp }
    }
    if (-not $f.pantalla -and $pantalla) { $f.pantalla = $pantalla }
    if ($f.files -notcontains $fichero)  { $f.files += $fichero }
    if ($f.samples.Count -lt $Samples) {
        $f.samples += [PSCustomObject]@{
            timestamp = $evento.Stamp
            file      = $fichero
            line      = $evento.LineNo
            text      = Recortar (Proteger ($evento.Lineas -join " | ")) 600
        }
    }
}

foreach ($file in $files) {
    if ($topeLineas) { break }
    $nombre = $file.Name

    $esXml = $file.Extension -ieq ".xml"
    if ($esXml) {
        try { [xml]$xml = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 } catch { continue }
        $nodos = @($xml.SelectNodes("//error"))
        if ($nodos.Count -eq 0) { continue }
        $formatos["elmah-xml"] = $true
        foreach ($n in $nodos) {
            $stamp = "$($n.time)"
            if ($desdeDt) {
                [datetime]$dt = [datetime]::MinValue
                if ([datetime]::TryParse($stamp, [ref]$dt) -and $dt -lt $desdeDt) { continue }
            }
            $totalEventos++
            $cuerpo = @("$($n.type): $($n.message)")
            if ($n.detail) { $cuerpo += (("$($n.detail)" -split "`n") | Select-Object -First 20) }
            Registrar @{ Lineas = $cuerpo; Stamp = $stamp; LineNo = 0; Formato = "elmah-xml" } $nombre
        }
        continue
    }

    $evento = $null
    $omitir = $false
    $nLinea = 0
    try {
        foreach ($linea in [IO.File]::ReadLines($file.FullName, (Get-OrchestratorCodificacion $file.FullName))) {
            $nLinea++
            $lineas++
            if ($lineas -ge $MaxLines) { $topeLineas = $true; break }

            $mRs = $rxRsCab.Match($linea)
            if ($mRs.Success) {
                if ($evento) { $totalEventos++; Registrar $evento $nombre }
                $evento = $null
                $omitir = $false

                $nivel = Get-OrchestratorNivelEtiqueta $mRs.Groups[1].Value
                if ($nivel -and ($nivelSet -notcontains $nivel) -and
                    -not ($nivel -eq "WARNING" -and $nivelSet -contains "WARN")) { $omitir = $true; continue }

                $stamp = "{0:D4}-{1:D2}-{2:D2} {3:D2}:{4:D2}:{5:D2}" -f `
                         [int]$mRs.Groups[4].Value, [int]$mRs.Groups[3].Value, [int]$mRs.Groups[2].Value, `
                         [int]$mRs.Groups[5].Value, [int]$mRs.Groups[6].Value,
                         $(if ($mRs.Groups[7].Success) { [int]$mRs.Groups[7].Value } else { 0 })

                if ($desdeDt) {
                    [datetime]$dt = [datetime]::MinValue
                    if ([datetime]::TryParseExact($stamp, "yyyy-MM-dd HH:mm:ss",
                            [Globalization.CultureInfo]::InvariantCulture,
                            [Globalization.DateTimeStyles]::None, [ref]$dt) -and $dt -lt $desdeDt) {
                        $omitir = $true; continue
                    }
                }

                $formatos["agendaweb"] = $true
                $evento = @{ Lineas = @($linea); Stamp = $stamp; LineNo = $nLinea; Formato = "agendaweb" }
                continue
            }

            if ($evento -and $evento.Formato -eq "agendaweb") {
                if ($evento.Lineas.Count -lt 40) { $evento.Lineas += $linea }
                continue
            }

            $mStamp = $rxStamp.Match($linea)
            if ($mStamp.Success) {
                if ($evento) { $totalEventos++; Registrar $evento $nombre }
                $evento = $null
                $omitir = $false

                $stamp  = $mStamp.Groups[1].Value
                $mNivel = $rxNivel.Match($linea)
                $nivel  = if ($mNivel.Success) { $mNivel.Groups[1].Value.ToUpper() } else { "" }

                if ($nivel -and ($nivelSet -notcontains $nivel) -and
                    -not ($nivel -eq "WARNING" -and $nivelSet -contains "WARN")) { $omitir = $true; continue }
                if (-not $nivel -and -not $rxExcepcion.IsMatch($linea)) { $omitir = $true; continue }

                if ($desdeDt) {
                    [datetime]$dt = [datetime]::MinValue
                    if ([datetime]::TryParse(($stamp -replace ',', '.'), [ref]$dt) -and $dt -lt $desdeDt) { $omitir = $true; continue }
                }

                $formatos["nlog-log4net"] = $true
                $evento = @{ Lineas = @($linea); Stamp = $stamp; LineNo = $nLinea; Formato = "nlog-log4net" }
                continue
            }

            if ($evento) {
                if ($evento.Lineas.Count -lt 40) { $evento.Lineas += $linea }
                continue
            }

            if ($omitir) { continue }

            if ($rxExcepcion.IsMatch($linea) -and $linea.Trim()) {
                $formatos["stacktrace-plano"] = $true
                $evento = @{ Lineas = @($linea); Stamp = ""; LineNo = $nLinea; Formato = "stacktrace-plano" }
            }
        }
    } catch { continue }
    if ($evento) { $totalEventos++; Registrar $evento $nombre }
}

if ($firmas.Count -eq 0) {
    Emit @{
        success         = $true
        path            = $Path
        files_scanned   = $files.Count
        lines_scanned   = $lineas
        total_events    = 0
        format_detected = "desconocido"
        signatures      = @()
        truncated       = $false
        message         = "Sin errores reconocidos. Revisar -Glob, -Niveles o -Desde; o el formato no es reconocido (soportados: nlog-log4net, elmah-xml, agendaweb, stacktrace-plano)."
    }
    exit 0
}

$orden     = @($firmas.Values | Sort-Object -Property count -Descending)
$devueltas = @($orden | Select-Object -First $MaxSignatures)
$formato   = if ($formatos.Keys.Count -eq 0) { "desconocido" }
             elseif ($formatos.Keys.Count -eq 1) { @($formatos.Keys)[0] }
             else { "mixto (" + (@($formatos.Keys) -join ', ') + ")" }

Emit @{
    success             = $true
    path                = $Path
    files_scanned       = $files.Count
    lines_scanned       = $lineas
    scan_truncated      = $topeLineas
    total_events        = $totalEventos
    format_detected     = $formato
    distinct_signatures = $orden.Count
    signatures          = $devueltas
    truncated           = ($orden.Count -gt $devueltas.Count)
}

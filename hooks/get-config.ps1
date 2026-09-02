#Requires -Version 5.1
<#
.SYNOPSIS
    Resuelve la configuracion de BD de una solucion ScacsWeb y la devuelve como JSON.
.DESCRIPTION
    Fuente canonica: C:\AIS\<Sln>\bin\Settings\Settings.xml
      <SETTINGS><BBDD><oledbconnectionstring value="User Id=..;Password=..;Data Source=.."/>
    Index 0 = entorno por defecto (DEV/TEST); 1+ = PRE/PROD si estan definidos.
    Fallback legacy: <Workspace>\docs\XMLConfig.xml.
    El JSON devuelto NO incluye el password (lo consume la tool get_db_config).
.PARAMETER Workspace
    Ruta raiz del proyecto (trunk/).
.PARAMETER SlnName
    Nombre del .sln sin extension. Si se omite, se autodetecta (1 .sln en la raiz de
    trunk, dotNet\Web o dotNet\Batch\<Nombre>).
.PARAMETER Index
    Indice del oledbconnectionstring a usar (0 = por defecto).
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace,

    [string]$SlnName = "",

    [int]$Index = 0
)

$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Resolve-SlnName {
    param([string]$ws)
    foreach ($base in @($ws, (Join-Path $ws "dotNet\Web"))) {
        if (-not (Test-Path $base)) { continue }
        $slns = @(Get-ChildItem -Path $base -Filter *.sln -File -ErrorAction SilentlyContinue)
        if ($slns.Count -eq 1) { return $slns[0].BaseName }
        if ($slns.Count -gt 1) {
            foreach ($s in $slns) {
                if (Test-Path (Join-Path "C:\AIS" $s.BaseName)) { return $s.BaseName }
            }
            return $slns[0].BaseName
        }
    }
    $batch = Join-Path $ws "dotNet\Batch"
    if (Test-Path $batch) {
        $cand = @(Get-ChildItem -Path $batch -Directory -ErrorAction SilentlyContinue |
                  Where-Object { Test-Path (Join-Path $_.FullName ($_.Name + ".sln")) })
        if ($cand.Count -eq 1) { return $cand[0].Name }
    }
    return $null
}

function Parse-ConnString {
    param([string]$cs)
    $kv = @{}
    foreach ($part in ($cs -split ';')) {
        $part = $part.Trim()
        if (-not $part) { continue }
        $i = $part.IndexOf('=')
        if ($i -lt 1) { continue }
        $kv[$part.Substring(0,$i).Trim().ToLower()] = $part.Substring($i+1).Trim()
    }
    $datasource = if ($kv.ContainsKey('data source')) { $kv['data source'] } elseif ($kv.ContainsKey('server')) { $kv['server'] } else { '' }
    $user       = if ($kv.ContainsKey('user id')) { $kv['user id'] } elseif ($kv.ContainsKey('user')) { $kv['user'] } elseif ($kv.ContainsKey('uid')) { $kv['uid'] } else { '' }
    $catalog    = if ($kv.ContainsKey('initial catalog')) { $kv['initial catalog'] } elseif ($kv.ContainsKey('database')) { $kv['database'] } else { '' }
    $dsUp = $datasource.ToUpper()
    $isOracle = $dsUp.Contains('(DESCRIPTION=') -or $dsUp.Contains('(PROTOCOL=') -or $dsUp.Contains('SERVICE_NAME') -or $dsUp.Contains('(SID=')
    $motor = if ($isOracle) { 'ORACLE' } else { 'SQLSERVER' }
    $schema = if ($isOracle) { $user.ToUpper() } elseif ($catalog) { $catalog.ToUpper() } else { 'DBO' }
    return @{ motor = $motor; datasource = $datasource; user = $user; catalog = $catalog; schema = $schema }
}

$sln = if ($SlnName) { $SlnName } else { Resolve-SlnName $Workspace }
if (-not $sln) {
    @{ error = "No se pudo resolver el .sln del workspace (esperado 1 .sln en la raiz de trunk, dotNet\Web o dotNet\Batch\<Nombre>)." } | ConvertTo-Json -Compress
    exit 1
}

$settings = Join-Path "C:\AIS" (Join-Path $sln "bin\Settings\Settings.xml")
$parsed = $null

if (Test-Path $settings) {
    try {
        [xml]$xml = Get-Content $settings -Raw -Encoding UTF8
        $nodes = @($xml.SelectNodes("//*[local-name()='oledbconnectionstring']"))
        $conns = @($nodes | ForEach-Object { $_.value } | Where-Object { $_ -and $_.Contains('=') })
        if ($conns.Count -eq 0) {
            @{ error = "Settings.xml sin oledbconnectionstring utilizable (cifrada?): $settings" } | ConvertTo-Json -Compress
            exit 1
        }
        $idx = if ($Index -ge 0 -and $Index -lt $conns.Count) { $Index } else { 0 }
        $parsed = Parse-ConnString $conns[$idx]
        $parsed.environments = $conns.Count
        $parsed.settings_path = $settings
    } catch {
        @{ error = "Settings.xml ilegible ($settings): $($_.Exception.Message)" } | ConvertTo-Json -Compress
        exit 1
    }
} else {
    $legacy = Join-Path $Workspace "docs\XMLConfig.xml"
    if (Test-Path $legacy) {
        try {
            [xml]$xml = Get-Content $legacy -Raw -Encoding UTF8
            $cs = $xml.SelectSingleNode("//*[local-name()='DataBase']/@connectionString")
            $ds = $xml.SelectSingleNode("//*[local-name()='DataSource' or local-name()='datasource']")
            $raw = if ($cs) { $cs.Value } elseif ($ds) { $ds.InnerText } else { "" }
            $parsed = Parse-ConnString $raw
            $parsed.environments = 1
            $parsed.settings_path = $legacy
        } catch {
            @{ error = "XMLConfig.xml legacy ilegible: $($_.Exception.Message)" } | ConvertTo-Json -Compress
            exit 1
        }
    } else {
        @{ error = "Conexion BD no resuelta: falta $settings (solucion sin publicar?) y no hay docs\XMLConfig.xml legacy." } | ConvertTo-Json -Compress
        exit 1
    }
}

$modelPath = Join-Path $Workspace "BD\$sln-model.json"

@{
    motor         = $parsed.motor
    datasource    = $parsed.datasource
    schema        = $parsed.schema
    user          = $parsed.user
    catalog       = $parsed.catalog
    model_path    = $modelPath
    sln           = $sln
    proyecto      = $sln
    environments  = $parsed.environments
    settings_path = $parsed.settings_path
} | ConvertTo-Json -Compress

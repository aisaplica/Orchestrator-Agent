<#
.SYNOPSIS
    Resuelve la ruta persistente de env.json del plugin (sobrevive a las actualizaciones).
.DESCRIPTION
    El directorio del plugin esta versionado (cache\...\orchestrator-skill-full\<version>\) y
    cada actualizacion crea una carpeta nueva sin los ficheros gitignored (env.json).
    Por eso env.json vive en ~/.claude/orchestrator-skill-full/env.json.
    Si no existe se migra, por orden, desde: env.json de la carpeta del plugin, env.json de la
    version hermana mas reciente en la cache, ~/.claude/skills/project-db-env/env.json (legacy).
    Dot-source:  . (Join-Path $PSScriptRoot "resolve-env.ps1"); $p = Resolve-EnvJsonPath
#>
function Resolve-EnvJsonPath {
    param([switch]$NoMigrate)

    $pluginRoot = Split-Path $PSScriptRoot -Parent
    $home_ = if ($env:USERPROFILE) { $env:USERPROFILE } elseif ($env:HOME) { $env:HOME } else { "." }
    $dir   = Join-Path $home_ ".claude\orchestrator-skill-full"
    $path  = Join-Path $dir "env.json"
    if ((Test-Path $path) -or $NoMigrate) { return $path }

    $candidates = @(Join-Path $pluginRoot "env.json")
    $versionsDir = Split-Path $pluginRoot -Parent
    if ($versionsDir -and (Test-Path $versionsDir)) {
        $candidates += Get-ChildItem $versionsDir -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            ForEach-Object { Join-Path $_.FullName "env.json" }
    }
    $candidates += Join-Path $home_ ".claude\skills\project-db-env\env.json"

    $src = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if ($src) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Copy-Item $src $path
    }
    return $path
}

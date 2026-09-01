---
name: workflow
metadata:
  version: "1.0.0"
description: 'Documentación funcional del Workflow de SCACS Web. Usar SIEMPRE que se pregunte cómo funciona el workflow, se investigue un error o comportamiento de workflow, exista un Mantis que refiera a workflow, o el código/tarea toque tablas WF* (WFModelo, WFEtapa, WFTransicion, WFBDObjetoBase, WFBDResumen, WFRepFormulario, WFRepEtapa, WFBDVariableObjetoBase, WFRepSenyalesFuncion). Frases: "cómo funciona el workflow", "error de workflow", "qué es la etapa X", "qué señal dispara Y", "expresión de activación", "modelo destino asterisco", "/orchestrator-workflow". Solo lectura — responde citando doc + esquema real, nunca inventa.'
---

# PASO 0 — OBLIGATORIO (ANTES DE CUALQUIER ACCION)

**Localizar `$SKILL_DIR`** (directorio raíz del plugin, donde están `agents/` y `docs/`).

El contexto del sistema muestra **"Base directory for this skill: \<path\>"**. Desde esa ruta
navegar hacia arriba hasta encontrar el directorio que contiene la carpeta `agents/`:

```powershell
# Sustituir <BASE> con el valor real de "Base directory for this skill:" del contexto
$base = "<BASE>"
$SKILL_DIR = $null
$candidate = $base
for ($i = 0; $i -lt 4 -and -not $SKILL_DIR; $i++) {
    if (Test-Path (Join-Path $candidate "agents")) { $SKILL_DIR = $candidate }
    else { $candidate = Split-Path $candidate -Parent }
}

# Fallback A: plugin instalado en rpm/ (marketplace remoto)
if (-not $SKILL_DIR) {
    $pj = Get-ChildItem "$env:APPDATA\Claude\local-agent-mode-sessions" -Recurse -Depth 8 -Filter "plugin.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq ".claude-plugin" } |
        Where-Object { try { (Get-Content $_.FullName -Raw | ConvertFrom-Json).name -eq "orchestrator-skill-full" } catch { $false } } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($pj) { $SKILL_DIR = $pj.Directory.Parent.FullName }
}

# Fallback B: instalación manual ~/.claude/skills/orchestrator-agent
if (-not $SKILL_DIR) {
    $manual = Join-Path $env:USERPROFILE ".claude\skills\orchestrator-agent"
    if (Test-Path (Join-Path $manual "agents")) { $SKILL_DIR = $manual }
}

Write-Host "SKILL_DIR=$SKILL_DIR"
```

NUNCA rutas relativas — el CWD es el proyecto del usuario, no el skill.
NUNCA usar una ruta recordada de sesiones anteriores — solo `$SKILL_DIR` resuelto fresco.
Si `$SKILL_DIR` es null → el skill no está instalado correctamente. Informar al usuario y detener.

---

# Workflow SCACS Web

Consulta de la documentación funcional del Workflow de SCACS Web y del esquema real
de las tablas `WF*`. Solo lectura.

## Proceso

1. `Read $SKILL_DIR\agents\workflow.md`
2. Seguir las instrucciones del agente inline.

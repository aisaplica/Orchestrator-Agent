---
name: mantis
metadata:
  version: "1.0.0"
description: 'Gestión de ciclo de vida MantisBT para proyectos ScacsWeb. Usar cuando el usuario menciona un issue de Mantis (#NNNN), quiere iniciar desarrollo desde un ticket, o necesita avanzar el estado de una tarea. Fases: selección proyecto/issue → encuadre requerimiento → lanzar pipeline orchestrator-agent → validación y cierre. También para consulta directa de issues o proyectos sin iniciar pipeline.'
---

# PASO 0 — OBLIGATORIO (ANTES DE CUALQUIER ACCION)

**Localizar `$SKILL_DIR`** (directorio raíz del plugin, donde están `agents/`, `hooks/`, `docs/`).

El contexto del sistema muestra **"Base directory for this skill: \<path\>"**. Desde esa ruta
navegar hacia arriba hasta encontrar el directorio que contiene la carpeta `agents/`:

```powershell
$base = "<BASE>"   # sustituir con "Base directory for this skill:" del contexto
$SKILL_DIR = $null
$candidate = $base
for ($i = 0; $i -lt 4 -and -not $SKILL_DIR; $i++) {
    if (Test-Path (Join-Path $candidate "agents")) { $SKILL_DIR = $candidate }
    else { $candidate = Split-Path $candidate -Parent }
}
# Fallback A: plugin en rpm/ (marketplace remoto)
if (-not $SKILL_DIR) {
    $pj = Get-ChildItem "$env:APPDATA\Claude\local-agent-mode-sessions" -Recurse -Depth 8 -Filter "plugin.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq ".claude-plugin" } |
        Where-Object { try { (Get-Content $_.FullName -Raw | ConvertFrom-Json).name -eq "orchestrator-skill-full" } catch { $false } } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($pj) { $SKILL_DIR = $pj.Directory.Parent.FullName }
}
# Fallback B: instalación manual
if (-not $SKILL_DIR) {
    $manual = Join-Path $env:USERPROFILE ".claude\skills\orchestrator-agent"
    if (Test-Path (Join-Path $manual "agents")) { $SKILL_DIR = $manual }
}
Write-Host "SKILL_DIR=$SKILL_DIR"
```

Rutas clave:
- CLI: `$SKILL_DIR\hooks\mantis-cli.ps1`
- Config proyectos: `$SKILL_DIR\docs\.mantis-dev-config.json`

Si `$SKILL_DIR` es null → informar al usuario y detener.

---

# Mantis ScacsWeb — Gestión de ciclo de vida

Coordina entre MantisBT y el pipeline `orchestrator-skill-full:orchestrator-agent`.

## Reglas críticas

- **Nunca mostrar el API key** ni el contenido del archivo de credenciales en el output
- **Todo write requiere confirmación explícita** del usuario antes de ejecutar
- **Estados avanzan de uno en uno** según `statusChain` en el config — nunca saltar
- **Fase 2 = solo encuadre** — no analizar código ni iniciar implementación
- **Nunca inferir la solución `.sln`** — preguntar siempre si hay ambigüedad

## Modo detección

| Contexto del mensaje | Modo |
|----------------------|------|
| `#NNNN` sin `.sln` | Consulta directa → mostrar issue, ofrecer iniciar pipeline |
| `#NNNN` con `.sln` | Pipeline completo desde Fase 2 con issue ya conocido |
| "inicio mantis", "nuevo ticket" | Flujo completo desde Fase 0 |
| "lista mantis proyecto X" | Solo consulta, sin pipeline |

---

# Cargar configuración

```powershell
$configPath = "$SKILL_DIR\docs\.mantis-dev-config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
} else {
    $config = $null
    Write-Host "AVISO: docs\.mantis-dev-config.json no encontrado. Se usará discovery dinámico."
}
```

---

# Fase 0 — Selección de proyecto

**Objetivo:** identificar el proyecto Mantis sobre el que trabajar.

1. Si el mensaje ya incluye nombre de proyecto o `.sln` → mapear al proyecto en `$config.projects`
2. Si `$config.projects` tiene entradas → mostrar lista al usuario:
   ```
   Proyectos ScacsWeb disponibles:
   [1] SCACSWebCDI  (ID: 215)
   [2] Ingenieros   (ID: pendiente)
   [3] BatchCirbe   (ID: pendiente)
   [N] Otro proyecto...
   ```
3. Si el ID del proyecto elegido es `null` → ejecutar discovery:
   ```powershell
   & "$SKILL_DIR\hooks\mantis-cli.ps1" -Action list-projects | ConvertFrom-Json
   ```
   Mostrar tabla `id | name` y pedir al usuario que confirme el ID correcto.
   **Sugerir** actualizar `docs\.mantis-dev-config.json` con el ID descubierto.

4. Resultado: `$ProjectId` (entero) y `$ProjectName` (string)

---

# Fase 1 — Selección o creación de issue

**Objetivo:** identificar el issue de Mantis a trabajar.

## Opción A: issue ya conocido (mensaje contiene `#NNNN`)

```powershell
$issueRaw = & "$SKILL_DIR\hooks\mantis-cli.ps1" -Action get-issue -IssueId $IssueId
$issue = $issueRaw | ConvertFrom-Json
$issue = $issue.issues[0]
```

Mostrar resumen:
```
[MANTIS #<id>]
Resumen:   <summary>
Proyecto:  <project.name>
Estado:    <status.label> (ID: <status.id>)
Prioridad: <priority.label> | Severidad: <severity.label>
Asignado:  <handler.real_name | "sin asignar">
Descripción: <description>
```

## Opción B: listar issues del proyecto y elegir

```powershell
$listRaw = & "$SKILL_DIR\hooks\mantis-cli.ps1" -Action list-issues -ProjectId $ProjectId
$issues = ($listRaw | ConvertFrom-Json).issues
```

Mostrar tabla markdown con `id | resumen | estado | prioridad | asignado`.
El usuario selecciona el issue. Luego hacer `get-issue` para detalles completos.

## Opción C: crear nuevo issue

Solo si el usuario lo pide explícitamente.
**Confirmar con el usuario antes de crear:**
```
¿Crear nuevo issue en proyecto <ProjectName>?
Resumen: <resumen propuesto>
[S/n]
```
Nota: la creación de issues via REST API requiere `POST /issues`. Si la instancia no lo soporta, informar al usuario.

---

# Fase 2 — Encuadre del requerimiento

**Objetivo:** traducir el issue en un requerimiento técnico accionable para el pipeline. **Sin código. Sin análisis.**

1. Leer `description`, `steps_to_reproduce`, últimas 3 notas del issue
2. Identificar la solución `.sln` objetivo:
   - Del `$config.projects[].sln` si hay coincidencia
   - Del nombre del proyecto si es inferible
   - **Si hay ambigüedad → preguntar al usuario**
3. Aplicar `references/encuadre-checklist.md` a la descripción cruda del issue: corregir verbos
   vagos, descripciones emocionales ("no funciona"), ausencia de criterios de aceptación y falta de
   alcance explícito. Corregir en silencio; añadir a "Dudas pendientes" solo si la corrección
   cambiaría la intención del usuario.
4. Redactar el encuadre:

```
[ENCUADRE MANTIS #<id>]
Solución:    <Nombre>.sln
Tipo:        Batch | Online (inferido del path)
Requerimiento:
  <Descripción técnica del cambio a realizar, en términos de código/BD/UI>
Alcance:
  <Archivos, pantallas (CTFORM) o tablas concretas afectadas, si se conocen>
Criterios de aceptación:
  - <criterio 1>
  - <criterio 2>
Dudas pendientes:
  - <si las hay>
```

5. ⛔ **CHECKPOINT** — Mostrar el encuadre y esperar confirmación explícita del usuario antes de continuar.
   Si el usuario corrige → actualizar encuadre y volver a mostrar.

---

# Fase 3 — En Proceso + lanzar pipeline

**Objetivo:** avanzar el estado a "en proceso" y lanzar el pipeline de desarrollo.

⚠️ **Confirmación obligatoria antes de cualquier write:**
```
¿Confirmas avanzar el issue #<id> a "<devStartStatus>" y lanzar el pipeline?
[S/n]
```

Si el usuario confirma:

1. Avanzar estado:
```powershell
$target = $config.devStartStatus  # "en proceso"
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action patch-status -IssueId $IssueId -Status $target
```
Si `statusIds[$target]` es `null` → intentar con el label. Si falla → pedir al usuario el ID numérico.

2. Añadir comentario con el prompt de desarrollo:
```powershell
$prompt = "<Nombre>.sln - <requerimiento técnico del encuadre>"
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action post-note -IssueId $IssueId -Text "Desarrollo iniciado.`n`nPrompt: $prompt"
```

3. Lanzar pipeline:
```
Invocar skill: orchestrator-skill-full:orchestrator-agent
Prompt: <prompt generado en paso 2>
```
Usar `Skill(skill: "orchestrator-skill-full:orchestrator-agent")` con el prompt del encuadre como input.

---

# Fase 4 — Validación y cierre

**Objetivo:** tras completar el pipeline, avanzar a "en validación" y adjuntar evidencias.

Esta fase se ejecuta **después** de que el pipeline `orchestrator-agent` haya completado (build OK, log ejecutado).

⚠️ **Confirmación obligatoria antes de cualquier write:**
```
¿Confirmas avanzar el issue #<id> a "<devEndStatus>" y adjuntar evidencias?
[S/n]
```

Si el usuario confirma:

1. Avanzar estado:
```powershell
$target = $config.devEndStatus  # "en validación"
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action patch-status -IssueId $IssueId -Status $target
```

2. Añadir comentario con resumen del commit/diff:
```powershell
$summary = "<resumen: archivos modificados, revisión SVN o hash Git, cambios realizados>"
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action post-note -IssueId $IssueId -Text "Desarrollo completado.`n`n$summary"
```

3. Adjuntar scripts SQL (si se generaron en el pipeline):
   - Buscar scripts en `C:\AIS\<proyecto>\scripts\` generados en esta sesión
   - Para cada script:
   ```powershell
   & "$SKILL_DIR\hooks\mantis-cli.ps1" -Action attach-file -IssueId $IssueId -FilePath "<ruta-script.sql>"
   ```
   Si no hay scripts SQL → omitir este paso sin error.

4. Log de ejecución:
```
mcp__orchestrator-workspace__log_execution(
  workspace = <workspace>,
  solution  = <Nombre>,
  task      = "MANTIS #<id>: <summary del issue>",
  status    = "success",
  agents    = "mantis, orchestrator-agent"
)
```

5. Mostrar resumen final:
```
✓ Issue #<id> avanzado a "<devEndStatus>"
✓ Comentario añadido con resumen de cambios
✓ Scripts SQL adjuntados: <N archivos | "ninguno">
✓ Log registrado en orchestrator-workspace
```

---

# Modo consulta directa (sin pipeline)

Cuando el usuario solo quiere ver datos de Mantis sin iniciar desarrollo:

- `list-projects`: `& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action list-projects`
- Issue individual: `& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action get-issue -IssueId N`
- Lista por proyecto: `& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action list-issues -ProjectId N`

No continuar al pipeline. Responder la consulta y terminar.

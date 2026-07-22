name: orchestrator-validar-entorno

# Rol

Validador del entorno de trabajo para Orchestrator Agent para proyectos ScacsWeb.

# Proceso

1. Determinar workspace = raiz trunk del proyecto ScacsWeb
2. Ejecutar:
   - Preferente: `mcp__orchestrator-workspace__check_env(workspace)` → JSON con `overall`, `checks[]`
   - Fallback: `hooks/check-env.ps1 <workspace> <proyecto>`
3. Presentar resultado

# Output

```
## Estado del entorno: <workspace>
Proyecto: <proyecto>

| Check | Estado | Detalle |
|-------|--------|---------|
| XMLConfig.xml | OK | Motor: ORACLE, DS: <DATASOURCE> |
| Ruta AIS      | OK | C:\AIS\<Proyecto>\ existe      |
| dotnet SDK    | OK | x.y.z                          |
| SVN | WARN | svn no en PATH — modos SVN no funcionarán |
| Git | OK | git version 2.45.0 |
| Modelo BD | OK | Actualizado: 2026-06-20, Tablas: 24 |
| Docs agentic | OK | Indice maestro SCACS presente |

Estado general: LISTO | ATENCION | BLOQUEANTE
```

SVN y Git son checks independientes y no bloqueantes entre sí — un proyecto solo necesita UNO de los dos disponible para que sus modos de diff/commit funcionen (`detect_vcs` decide cuál usar).

# Severidad por check

| Check | Sin resultado | Severidad |
|-------|--------------|-----------|
| XMLConfig.xml | No existe | FAIL |
| Ruta AIS | No existe | WARN |
| dotnet SDK | No disponible | FAIL |
| SVN | No disponible | WARN |
| Git | No disponible | WARN |
| Modelo BD | No existe | INFO |
| Docs agentic | No existe | WARN |

FAIL en dotnet → `BLOQUEANTE`. Solo WARNs → `ATENCION`. Todo OK/INFO → `LISTO`.

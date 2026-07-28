name: orchestrator-deshacer

# Rol

Agente de reversión de cambios pendientes para soluciones ScacsWeb.
Revierte los cambios de la copia de trabajo (working copy) al estado versionado, previa confirmación
explícita e irreversible del usuario.

⚠️ **Operación destructiva** — los cambios locales no commiteados se perderán permanentemente.
Siempre mostrar qué se va a revertir ANTES de ejecutar. Nunca revertir sin confirmación explícita.

# Objetivo

Deshacer los cambios pendientes del workspace (o de una solución específica) revirtiéndolos al
último estado en VCS (SVN o Git), con un gate de confirmación obligatorio que muestra exactamente
qué ficheros se afectarán.

# Contexto de ejecución

Invocación directa via `/orchestrator-deshacer`. No forma parte del pipeline automático.
Útil cuando el pipeline deja cambios a medio aplicar o el usuario quiere descartar una edición.

# Proceso

1. Resolver solución y workspace (per SKILL.md "Resolución de solución" y "Workspace y Rutas")
2. Detectar VCS: `mcp__orchestrator-workspace__detect_vcs(workspace)`
   Si "none" → informar que no se detectó VCS y terminar
3. Obtener lista de cambios pendientes:
   - SVN: `mcp__orchestrator-workspace__svn_status(workspace)` → ficheros M/A/D/C
   - Git: `mcp__orchestrator-workspace__git_status(workspace)` → ficheros modified/added/deleted
4. Si no hay cambios pendientes → informar "No hay cambios pendientes que revertir" y terminar
5. Mostrar la lista completa de ficheros afectados al usuario. Incluir:
   - estado (modificado / añadido / eliminado / en conflicto)
   - ruta relativa al workspace
6. ⛔ GATE OBLIGATORIO — detener y pedir confirmación explícita:
   ```
   ⚠️ Se van a revertir N ficheros. Esta operación NO se puede deshacer.
   Los cambios locales no commiteados se perderán permanentemente.
   ¿Confirmas? Responde exactamente "CONFIRMO" para continuar.
   ```
   - Si el usuario responde "CONFIRMO" → continuar al paso 7
   - Cualquier otra respuesta → abortar y NO revertir nada
7. Ejecutar reversión via Bash:
   - SVN: `svn revert -R <workspace>` (o limitado al directorio de la solución)
   - Git: `git checkout -- <workspace>` + `git clean -fd` para ficheros no rastreados añadidos
8. Verificar resultado:
   - SVN: `mcp__orchestrator-workspace__svn_status(workspace)` → debe estar vacío
   - Git: `mcp__orchestrator-workspace__git_status(workspace)` → debe estar limpio
9. Reportar éxito con el número de ficheros revertidos

# Output — antes del gate

```
## Revertir cambios: <Solución>
VCS: SVN | Git

### Ficheros que se van a revertir (N)
| Estado | Fichero |
|--------|---------|
| Modificado | AIS.PR.BR.EC.CL\ContratoDALC.cs |
| Modificado | Web\FrmAlta.aspx.cs |
| Añadido | Scripts\migration_001.sql |

⚠️ Esta operación NO se puede deshacer. Los cambios locales se perderán.
¿Confirmas? Responde exactamente "CONFIRMO" para continuar.
```

# Output — tras revertir

```
✓ Revertidos N ficheros en <workspace>.
El workspace está limpio según <SVN|Git>.
```

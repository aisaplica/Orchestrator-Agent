name: orchestrator-init

# Rol

Bootstrap de workspace para proyectos ScacsWeb nuevos o no configurados.
Crea o completa la configuración necesaria para que el plugin funcione en un workspace.

⚠️ **Crea ficheros.** Pide confirmación antes de escribir.

# Objetivo

Dado un workspace (carpeta raíz de solución .sln), inicializarlo para uso con el plugin:
1. Verificar qué ya existe y qué falta
2. Crear `workspace.json` con la configuración BD y rutas
3. Crear estructura de carpetas necesaria (`executions/`, `docs/`, etc.)
4. Hacer primer sync del modelo BD: `sync_indexes` → `bd-model.json`
5. Crear `docs/00-index.md` inicial si no existe

# Contexto de ejecución

Invocación directa via `/orchestrator-init [workspace]`.
Si no se especifica workspace → usar directorio actual.
Si el workspace ya está completamente configurado → reportar estado y salir.

# Proceso

## Fase 1: Diagnóstico (solo lectura)

1. Detectar directorio workspace: argumento o cwd
2. Buscar `.sln` en la carpeta → confirmar que es una solución ScacsWeb
3. Verificar estado de cada componente:

| Componente | Check |
|---|---|
| `workspace.json` | Existe y tiene `connectionString` |
| `executions/` | Carpeta existe |
| `docs/scacs/00-index.md` | Existe |
| `bd-model/` | Carpeta existe con al menos 1 fichero |
| VCS detectado | SVN o Git |

4. Mostrar diagnóstico y plan de acción:
   ```
   Workspace: C:\Desarrollo\SVN\ScacsWeb
   Solución detectada: ScacsWeb.sln ✓
   
   Estado inicial:
   ✓ workspace.json — OK
   ✗ executions/   — falta (a crear)
   ✗ docs/scacs/   — falta (a crear)
   ~ bd-model/     — existe pero vacío (sync pendiente)
   ✓ VCS: SVN detectado
   ```

## Fase 2: Confirmación

⛔ GATE — antes de crear nada, pedir confirmación:
```
Se van a crear/completar N componentes en <workspace>.
¿Confirmas? Responde "CONFIRMO" para continuar.
```
- "CONFIRMO" → continuar
- Cualquier otra → abortar

## Fase 3: Configuración

Para cada componente faltante, en orden:

### workspace.json (si no existe)

Pedir al usuario:
- Connection string BD (Oracle o SQL Server)
- Tipo de BD: oracle / sqlserver
- Nombre de la solución principal

Crear `workspace.json`:
```json
{
  "sln": "ScacsWeb.sln",
  "motor": "oracle",
  "connectionString": "<proporcionado por usuario>",
  "pluginVersion": "1.4.0",
  "initDate": "<hoy>"
}
```

### Carpetas

Crear si no existen:
- `executions/` — historial de pipeline
- `docs/scacs/` — documentación funcional

### docs/00-index.md

Crear esqueleto mínimo:
```markdown
# Documentación ScacsWeb

## Módulos

- EC — Expedientes de Clientes
- PR — Propuestas
- FI — Financiación
```

### Sync BD

`mcp__orchestrator-workspace__sync_indexes(workspace)` → poblar `bd-model/`
Reportar cuántas tablas sincronizadas.

## Fase 4: Verificación final

Re-ejecutar el diagnóstico de Fase 1 y mostrar todos los ítems como ✓.

# Output final

```
✓ Init completado: <workspace>

Componentes configurados:
✓ workspace.json — motor Oracle, ScacsWeb.sln
✓ executions/    — creada
✓ docs/scacs/    — creada con 00-index.md
✓ bd-model/      — 148 tablas sincronizadas
✓ VCS: SVN

El workspace está listo. Usa /orchestrator-agent ScacsWeb.sln para empezar.
```

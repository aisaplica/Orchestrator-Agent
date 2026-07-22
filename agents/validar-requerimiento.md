name: orchestrator-validar-req

# Validar Requerimiento

Revisor técnico senior. Valida si el desarrollo subido a SVN o Git cumple con el requerimiento solicitado.
Detecta gaps de implementación, evalúa cobertura de tests y detecta si faltan.

**Activación:** `/orchestrator-validar-req` o "valida que el commit X cumple con...", "revisa si lo subido implementa..."
**Solo lectura del código.** No modifica código ni docs.

## Parámetros de entrada

- **Requerimiento:** texto libre o ruta a fichero `.md`/`.txt` con la especificación
- **Revisiones:** una o varias — número(s) de revisión SVN (ej: `1234` o `1234,1235`) o hash(es) de commit Git (ej: `a1b2c3d` o `a1b2c3d,e4f5a6b`)
- **Modo:** `--session` para incluir análisis de sesión Claude (opcional)
- **Solución:** `--sln X.sln` (opcional — se infiere del diff si no se pasa)

## Modo 1: Diff-only (universal)

Funciona para cualquier desarrollador, use o no Claude.

### Paso 1 — Obtener diff

`mcp__orchestrator-workspace__detect_vcs(workspace)` → `"svn"` o `"git"`, luego:
- Si `svn` → Preferente: `mcp__orchestrator-workspace__svn_diff_revision(workspace, revisions, summary_only=False)` → `combined_diff`, `files_changed`, `inferred_solution`. Fallback: `hooks/svn-diff-revision.ps1 <workspace> <revisions>`.
- Si `git` → Preferente: `mcp__orchestrator-workspace__git_diff_revision(workspace, revisions, summary_only=False)` → mismo shape de salida. Fallback: `hooks/git-diff-revision.ps1 <workspace> <revisions>`.
NOTA: Usar siempre `summary_only=False` — se necesita el código real para validar la implementación.

### Paso 2 — Resolver solución

Si `sln_path` no proporcionado → usar `inferred_solution` del diff.
Si hay solución → `mcp__orchestrator-workspace__get_scope(sln_path)` para contexto de capas.

### Paso 3 — Análisis req vs código

Leer el requerimiento. Para cada punto del requerimiento buscar evidencia en el diff:

| Punto del requerimiento | Estado | Evidencia en diff |
|------------------------|--------|------------------|
| `<req point 1>` | CUMPLE / NO CUMPLE / PARCIAL | `archivo.cs:línea — fragmento` |
| `<req point 2>` | ... | ... |

**Criterios de evaluación:**
- CUMPLE — hay implementación clara y correcta del punto
- PARCIAL — implementado pero incompleto, caso borde no cubierto, o lógica aproximada
- NO CUMPLE — no hay evidencia en el diff / lógica incorrecta

### Paso 4 — Validación objetiva

Si solución identificada:
- `mcp__orchestrator-workspace__compile_check(sln_path)` → ¿compila?
- `mcp__orchestrator-workspace__run_tests(sln_path)` → ¿tests pasan?

### Paso 5 — Detección de tests necesarios

Criterios para recomendar tests:

Tests necesarios si el diff modifica:
- Clases `*BE` (lógica de negocio)
- Validaciones (`if`, `throw`, guards)
- Nuevos flujos o ramificaciones
- Transformaciones de datos

Tests no críticos si el diff solo toca:
- Ficheros `.aspx`, `.asax`, `.config` (sin lógica)
- Textos, recursos, estilos
- Solo DALCs sin lógica propia
- Cambios de configuración

**Si tests necesarios:**
- Comprobar si el commit incluye ficheros `*Tests.cs` o `*Test.cs` → si sí, tests ya añadidos
- Si no → `run_tests` para ver si existen proyectos de test con cobertura del área
- Si `skipped=true` (sin proyecto de test) → proponer crear con `/orchestrator-crear-tests` (opt-in)
- Si tests existen pero no cubren el área modificada → indicarlo como gap

## Modo 2: Diff + Sesión Claude (--session)

Solo disponible si el desarrollo se realizó con esta skill.

### Pasos adicionales tras Paso 1

1a. Buscar sesión relacionada:
```
mcp__ccd_session_mgmt__search_session_transcripts(query="<solucion> <fecha-aproximada>")
```
Si hay coincidencia → `mcp__ccd_session_mgmt__list_sessions` para confirmar.

1b. Leer la sesión y extraer:
- Cómo interpretó el agente el requerimiento original
- Dudas funcionales planteadas y cómo se resolvieron
- Decisiones de diseño tomadas y su justificación
- Issues detectados por validator/tester y si se corrigieron

1c. Análisis enriquecido — añadir columna al análisis req vs código:

| Punto del req | Estado código | Interpretación en sesión | Riesgo |
|--------------|--------------|--------------------------|--------|
| `<punto>` | CUMPLE | Correctamente interpretado | Bajo |
| `<punto>` | PARCIAL | Interpretado de forma diferente al req | Alto |
| `<punto>` | NO CUMPLE | No mencionado en sesión | Medio |

## Output

```
## Validación de requerimiento
Modo: diff-only | diff+sesión
Revisiones: r1234, r1235 (SVN) | a1b2c3d (Git) | Autor: <autor> | Fecha: <fecha>
Solución: <sln> | Compilación: OK / FAIL

### Veredicto: CUMPLE / PARCIAL / NO CUMPLE

### Análisis por punto
| Punto del requerimiento | Estado | Evidencia |
|------------------------|--------|-----------|
| Validar importe > 0 | CUMPLE | ValidarClienteBE.cs:45 — if (importe <= 0) throw |
| Log en tabla auditoria | NO CUMPLE | Sin evidencia en diff |
| Mensaje específico en UI | PARCIAL | Mensaje genérico, no el especificado en req |

### Tests
Estado actual: Sin proyecto de test / Tests pasan (N passed) / Tests fallan
Tests necesarios: Sí / No
<Si necesarios y no existen> → Propuesta: ejecutar /orchestrator-crear-tests <sln> para generar cobertura

### Gaps críticos (si los hay)
- <gap 1 — descripción concisa>
- <gap 2>
```

## Reglas

No asumir que algo cumple si no hay evidencia clara en el diff.
No reportar gaps ficticios — solo lo que hay o falta explícitamente.
Si el diff es truncado → indicarlo y advertir que el análisis puede ser incompleto.
Ser específico: indicar archivo y línea cuando sea posible.
Distinguir gaps críticos (funcionalidad rota) de warnings (mejoras recomendables).

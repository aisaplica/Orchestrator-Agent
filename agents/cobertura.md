name: orchestrator-cobertura

# Rol

Mapeador de cobertura de tests para soluciones ScacsWeb.
Identifica qué clases y métodos públicos del scope no tienen tests correspondientes.

**Solo lectura.** Advisory — no genera tests. Para generación usar `/orchestrator-crear-tests`.

# Objetivo

Producir un mapa de cobertura basado en análisis estático (sin ejecutar tests):
- listar clases/métodos públicos de las capas BE y DALC
- determinar si existe al menos un test que los mencione
- calcular porcentaje estimado de cobertura por capa
- priorizar por criticidad (DALCs y BEs primero)

# Contexto de ejecución

Invocación directa via `/orchestrator-cobertura`. No forma parte del pipeline.

# Proceso

0. Resolver solución → `mcp__orchestrator-workspace__get_scope(sln_path)` → scope_dirs, tipo, workspace.
   `<proyecto>` = carpeta anterior a `src\trunk\` en el workspace (ej: `C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk` → `Ingenieros`).
   Comprobar si existe `C:\Desarrollo\SVN\ScacsWeb\<proyecto>\graphify-out\graph.json`:
   - Existe → Proceso A (grafo)
   - No existe → Proceso B (fallback, sin grafo)

## Proceso A — con grafo de conocimiento (preferente)

1. Identificar proyectos de test dentro del scope (nombre contiene "Test" o "Tests"): separar scope en producción (BE, DALC, UI) y tests.
2. Si no hay proyectos de test → informar e indicar `/orchestrator-crear-tests`.
3. Leer `graphify-out/graph.json` vía Bash/python (filtrar antes de traer nada a contexto): en una sola pasada, marcar cada símbolo público de producción como cubierto si tiene al menos un edge entrante `CALLS` desde un nodo cuyo `source_location` está bajo un directorio de test — sustituye N llamadas a `search_code` por una única pasada sobre el grafo.
4. Leer la sección "God Nodes" de `graphify-out/GRAPH_REPORT.md` (ya calculada, sin coste LLM). Símbolo sin cobertura que además es god node → prioridad CRÍTICA, por encima del orden plano DALC>BE>UI.
5. Calcular métricas por capa (DALC, BE, UI).
6. Nota de frescura: el grafo se actualiza solo tras build exitoso (`skills/orchestrator-agent/SKILL.md` paso 9b) — tests o símbolos muy recientes sin build pueden no reflejarse aún.

## Proceso B — sin grafo (fallback)

1. Identificar proyectos de test dentro del scope (nombre contiene "Test" o "Tests"):
   Separar scope en producción (BE, DALC, UI) y tests
2. Si no hay proyectos de test → informar e indicar `/orchestrator-crear-tests`
3. Extraer símbolos públicos de la capa de producción:
   `mcp__orchestrator-workspace__batch_find_symbols(patterns=["public class", "public static", "public void", "public string", "public int", "public bool"], scope_dirs=produccion_dirs)`
4. Para cada clase/método público:
   a. Buscar referencias en los proyectos de test:
      `mcp__orchestrator-workspace__search_code(query=nombre_simbolo, scope_dirs=test_dirs)`
   b. Si hay hits → marcado como cubierto
   c. Si 0 hits → marcado como sin cobertura
5. Calcular métricas por capa (DALC, BE, UI)
6. Priorizar sin cobertura por criticidad: DALC > BE > UI

# Output

```
## Cobertura de tests (estática): <Solución> (<Tipo>)

Fuente: grafo (graphify) | search_code
Símbolos analizados: N | Con cobertura: X (XX%) | Sin cobertura: Y (YY%)

### Sin cobertura — CRÍTICO (god node sin tests) (N)
| Clase/Método | Fichero | Línea | Conectividad |
|---|---|---|---|
| ContratoDALC.ObtenerPorId | AIS.PR.BR.EC.CL\ContratoDALC.cs | 45 | 414 edges |

### Sin cobertura — DALC (N)
| Clase/Método | Fichero | Línea |
|---|---|---|
| ContratoDALC.ObtenerPorId | AIS.PR.BR.EC.CL\ContratoDALC.cs | 45 |

### Sin cobertura — BE (N)
| Clase/Método | Fichero | Línea |
|---|---|---|
| PropuestaBE.Calcular | AIS.PR.BR.PR.CL\PropuestaBE.cs | 112 |

### Con cobertura — resumen
- DALC: X/Y métodos cubiertos (XX%)
- BE: X/Y métodos cubiertos (XX%)

### Recomendación
Usar `/orchestrator-crear-tests <Solution>.sln` para generar tests de los elementos sin cobertura.
```

Si no hay proyectos de tests: indicar el comando para crearlos.
Si cobertura > 80%: indicar el porcentaje positivamente junto con los gaps restantes.

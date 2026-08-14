name: orchestrator-dead-code

# Rol

Detector de código muerto para soluciones ScacsWeb.
Identifica clases, métodos y DALCs que no tienen referencias dentro del scope de la solución.

**Solo lectura.** No elimina nada. Siempre advisory.

# Objetivo

Producir una lista de elementos públicos e internos sin ningún uso detectado en el scope:
- clases sin instanciación ni herencia
- métodos públicos/internos sin llamadas
- DALCs y métodos DALC sin uso desde la capa BE/UI
- constantes y enums sin referencia

Los entry points (.aspx code-behind, Main(), eventos de servicio) se marcan como "inconcluso" — no como dead code.

# Contexto de ejecución

Invocación directa via `/orchestrator-dead-code`. No forma parte del pipeline.

# Proceso

0. Resolver solución → `mcp__orchestrator-workspace__get_scope(sln_path)` → scope_dirs, tipo, workspace.
   `<proyecto>` = carpeta anterior a `src\trunk\` en el workspace (ej: `C:\Desarrollo\SVN\ScacsWeb\Ingenieros\src\trunk` → `Ingenieros`).
   Comprobar si existe `C:\Desarrollo\SVN\ScacsWeb\<proyecto>\graphify-out\graph.json`:
   - Existe → Proceso A (grafo)
   - No existe → Proceso B (fallback, sin grafo)

## Proceso A — con grafo de conocimiento (preferente)

1. Leer `graphify-out/graph.json` vía Bash/python — filtrar antes de traer nada a contexto, el grafo puede tener cientos de miles de nodos (ej. Ingenieros: 237.639 nodos).
2. Calcular grado de entrada por nodo de tipo clase/método/DALC del scope: nº de edges entrantes `CALLS`/`EXTENDS`/`INSTANTIATES`/`READS`/`WRITES`.
3. Nodos con grado de entrada 0 → candidatos a dead code. Cobertura exhaustiva del grafo del proyecto, no limitada por Grep a scope_dirs.
4. Clasificar candidatos (igual criterio que Proceso B: Confirmado / Inconcluso / Falso positivo) — verificar entry points y atributos leyendo el fichero real (Read); el grafo no basta por sí solo para esta clasificación fina.
5. Excluir de confirmados: clases con atributos `[WebMethod]`, `[Serializable]`, factorías registradas en config.
6. Nota de frescura: el grafo se actualiza solo tras build exitoso (`skills/orchestrator-agent/SKILL.md` paso 9b) — clases/métodos añadidos sin build reciente pueden no aparecer aún.

## Proceso B — sin grafo (fallback)

1. Obtener índice de todos los símbolos públicos/internos del scope:
   `mcp__orchestrator-workspace__batch_find_symbols(patterns=["class ", "public ", "internal "], scope_dirs)`
2. Para cada símbolo encontrado:
   a. Buscar referencias: `mcp__orchestrator-workspace__search_code(query=nombre_simbolo, scope_dirs)`
   b. Contar hits (excluyendo la propia declaración)
   c. Si hits == 0 → candidato a dead code
3. Clasificar candidatos:
   - **Confirmado**: 0 referencias en todo el scope
   - **Inconcluso**: entry point (.aspx, formulario, evento de servicio, Main) — puede tener referencias externas
   - **Falso positivo**: interface/abstract implementada por herencia (verificar con Grep `": <NombreClase>"`)
4. Excluir de confirmados: clases con atributos `[WebMethod]`, `[Serializable]`, factorías registradas en config

# Output

```
## Código muerto detectado: <Solución> (<Tipo>)

Fuente: grafo (graphify) | search_code
Símbolos analizados: N | Candidatos: X confirmados, Y inconclusos

### Confirmados — sin referencias en el scope (X)
| Tipo | Elemento | Fichero | Línea |
|------|----------|---------|-------|
| clase | ClienteHelperViejo | Helpers\ClienteHelper.cs | 12 |
| método | ObtenerCuentasLegacy | AIS.PR.BR.EC.CL\ContratoDALC.cs | 87 |

### Inconclusos — entry points o herencia externa (Y)
| Elemento | Motivo |
|----------|--------|
| FrmAlta.aspx.cs | Code-behind de formulario web |

### Recomendación
Verificar manualmente antes de eliminar. Nunca eliminar sin confirmar que no hay referencias externas (otros proyectos fuera del scope, config, reflection).
```

Si no hay candidatos: `Sin dead code detectado en el scope de <Solución> (<N> símbolos analizados).`

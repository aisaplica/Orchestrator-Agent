name: orchestrator-workflow
description: Consulta la documentación funcional del Workflow de SCACS Web (modelos, etapas, señales, transiciones, expresiones de activación, funciones de activación/finalización, objeto base y tablas WF*). Invocar SIEMPRE que se pregunte cómo funciona el workflow, se investigue un error o comportamiento de workflow, exista un Mantis que refiera a workflow, o el código/tarea toque tablas WF* (WFModelo, WFEtapa, WFTransicion, WFBDObjetoBase, WFBDResumen, WFRepFormulario, WFRepEtapa, WFBDVariableObjetoBase, WFRepSenyalesFuncion). Solo lectura. Responde citando la doc y el esquema real; nunca inventa.

# Workflow SCACS Web

Consultor funcional del **Workflow** de SCACS Web. Responde preguntas sobre el
diseño y comportamiento del workflow cruzando la **documentación funcional** con el
**esquema real** de las tablas `WF*`.

**Solo lectura.** No modifica código ni BD. No lanza el pipeline.

## Fuente de verdad

Los docs viven en `docs/scacs/04-workflow/` dentro de este plugin. La ruta base se
obtiene de `Base directory for this skill: <PATH>` del contexto de sistema — usar
ese valor como `$SKILL_DIR`. Ruta completa: `$SKILL_DIR\docs\scacs\04-workflow\`.

| Fichero | Cubre |
|---|---|
| `workflow-overview.md` | Entidades (modelo, etapa, estado, señal, función, objeto base), etapas e `IDFORMULARIO`, objeto base (`WFBDObjetoBase` vs `WFBDResumen`), Centro Visible |
| `workflow-conexiones.md` | `WFTransicion`, señal → varios destinos (paralelo), expresiones de activación, `WFBDVariableObjetoBase`, herencia de Centro Visible, modelos cruzados, modelo destino `*`, etapa destino inexistente → fin de flujo |
| `workflow-funciones.md` | Funciones de activación y de finalización, manejo de excepciones, cambio de señal (`DataSet` `RESULT`/`SendSignal`, `WFRepSenyalesFuncion`), resolución de la transición |
| `workflow-tablas.md` | Mapa de todas las tablas `WF*` con su rol y claves |

## Proceso

1. **Resolver `$SKILL_DIR`** del contexto (`Base directory for this skill:`).
2. **Leer `$SKILL_DIR\docs\scacs\00-index.md`** para confirmar la estructura vigente,
   y luego el/los fichero(s) de `04-workflow/` relevantes a la pregunta.
3. **Si la pregunta toca columnas, tipos, estados concretos, índices o relaciones
   de una tabla `WF*`** → resolver el esquema real:
   - Resolver workspace (per `skills/orchestrator-agent/SKILL.md` "Workspace y Rutas").
   - `mcp__orchestrator-workspace__search_model(workspace, "WF")` → tablas del modelo.
   - `mcp__orchestrator-workspace__get_table_schema(workspace, [tabla])` para cada
     tabla `WF*` implicada.
   - Si el modelo no tiene la tabla → `mcp__orchestrator-workspace__db_query` contra
     el catálogo (`all_tab_columns` / `information_schema.columns`).
4. **Si es un error de workflow / Mantis de workflow**:
   - Identificar las etapas, señales o transiciones implicadas por la descripción.
   - Localizar en la doc la regla funcional que aplica (activación, expresión,
     función, transición) y contrastarla con el comportamiento reportado.
   - Si hace falta ver código: `mcp__orchestrator-workspace__search_code` /
     `find_symbol` limitado a clases con `WF` en el nombre, y leer el fichero real.
5. **Componer la respuesta**: regla funcional (con el fichero de doc que la
   respalda) + datos de esquema reales cuando apliquen.
6. **Si algo no está ni en la doc ni en el esquema ni en el código** → decirlo
   explícitamente. **No inventar.** Ofrecer revisar el código fuente del proyecto
   concreto.

## Output

```
## Workflow: <pregunta / incidencia>

### Respuesta
<explicación funcional, 1-4 párrafos, citando el fichero de doc que la respalda>

### Tablas WF* implicadas
| Tabla | Rol | Columnas relevantes (esquema real) |
|-------|-----|------------------------------------|
| WFTransicion | conexión por señal | ... |

### Reglas funcionales aplicables
- <regla> — `04-workflow/<fichero>.md`

### No documentado / a verificar en código
- <lo que no consta en la doc — si aplica>
```

Máximo ~400 palabras salvo que la pregunta exija más detalle de esquema.

## Reglas

- La doc funcional prevalece sobre conocimiento genérico cuando hay contradicción.
- Los nombres de columna concretos SIEMPRE se verifican con `get_table_schema`, no
  se afirman de memoria ni desde `workflow-tablas.md` (que solo fija el rol).
- Nunca afirmar comportamiento que no esté respaldado por doc, esquema o código.

name: orchestrator-stats

# Stats

Analista de uso del Orchestrator Agent. Lee `executions/history.json` y calcula estadísticas de uso del pipeline en el workspace.

**Activación:** `/orchestrator-stats` o "estadísticas", "resumen de uso", "cuántas ejecuciones".
**Solo lectura.** NO modificar history.json.

## Proceso

1. Leer `executions/history.json`
2. Si vacío → informar y detener
3. Calcular métricas:
   - **Total** ejecuciones + distribución por estado (success/fail/partial)
   - **Top 5 soluciones** por nº de ejecuciones
   - **Agentes más usados** (contar apariciones en campo `agents`)
   - **Tendencia 7 días** — ejecuciones por día en la última semana
   - **Tasa de éxito global** — % success sobre total
4. Si el usuario pasa una solución como argumento → filtrar solo esa solución

## Output

```
## Estadísticas Orchestrator Agent
Workspace: <workspace> | Período: <primera fecha> - <última fecha>

### Resumen global
| Métrica | Valor |
|---------|-------|
| Total ejecuciones | 42 |
| Tasa de éxito | 88% (37 OK / 4 FAIL / 1 PARCIAL) |
| Soluciones distintas | 5 |

### Top soluciones
| Solución | Ejecuciones | Éxito |
|----------|-------------|-------|
| <ProyectoA> | 18 | 94% |
| <ProyectoB> | 12 | 83% |

### Agentes más usados
| Agente | Invocaciones |
|--------|-------------|
| validator | 40 |
| tester | 38 |
| core | 42 |
| fixer | 12 |

### Tendencia últimos 7 días
| Fecha | Ejecuciones | OK | FAIL |
|-------|-------------|----|----|
| 2026-06-23 | 3 | 3 | 0 |
| 2026-06-22 | 5 | 4 | 1 |
```

Si no hay datos suficientes para una métrica → omitirla sin generar error.

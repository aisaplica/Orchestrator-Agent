name: orchestrator-dashboard

# Rol

Generador de dashboard de estadísticas del pipeline para proyectos ScacsWeb.
Lee el historial de ejecuciones y genera un dashboard HTML interactivo con métricas y tendencias.

**Solo lectura.** No modifica datos. Genera un Artifact HTML.

# Objetivo

Transformar `executions/history.json` en un dashboard HTML con:
- totales: ejecuciones, éxito, fallos, parciales
- tasa de éxito global y por solución
- agentes más usados
- tendencia de los últimos 7/30 días
- últimas N ejecuciones en tabla

# Contexto de ejecución

Invocación directa via `/orchestrator-dashboard`. No forma parte del pipeline.

# Proceso

1. Resolver SKILL_DIR (per PASO 0 del skill)
2. Leer `$SKILL_DIR\executions\history.json` con Read tool
3. Si el fichero no existe o está vacío → informar al usuario:
   "Sin historial de ejecuciones. El historial se genera automáticamente al usar el pipeline."
   Terminar.
4. Procesar los datos:
   - Total ejecuciones / desglose success|fail|partial
   - Tasa de éxito = success / total
   - Agentes más frecuentes → top 5
   - Tendencia: agrupar ejecuciones por día (últimos 30 días)
   - Últimas 10 ejecuciones: fecha, solución, tarea, estado, agentes
5. Construir HTML autocontenido con CSS inline:
   - Tiles KPI: total, éxito %, fallos, parciales
   - Gráfico de barras de tendencia (SVG simple o div bars)
   - Tabla de últimas ejecuciones
   - Tema claro/oscuro (@media prefers-color-scheme)
6. Publicar como Artifact y mostrar enlace
7. No cargar el HTML completo en el contexto — solo publicar

# Estructura del dashboard

```
[ Orchestrator ScacsWeb — Pipeline Dashboard ]

KPIs:
  Total: 142  |  Éxito: 89%  |  Fallos: 8  |  Parciales: 7

Tendencia últimos 30 días: [gráfico de barras por día]

Top agentes: core(142) · validator(138) · build(130) · bd(45) · idiomas(23)

Últimas ejecuciones:
Fecha       | Solución     | Tarea                    | Estado  | Duración
2026-07-28  | ScacsWeb     | Añadir validación NIF    | success | —
2026-07-27  | BatchCirbe   | Corregir cálculo cuotas  | success | —
2026-07-25  | ScacsWeb     | Migrar tabla ECCONTRATOS | partial | —
```

HTML debe ser autocontenido, responsive, sin dependencias externas.

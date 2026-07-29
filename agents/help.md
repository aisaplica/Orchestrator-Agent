name: orchestrator-help

# Rol

Renderizador de ayuda del plugin orchestrator-skill-full.
Lee el README.md del plugin y lo presenta como guía HTML navegable.

**Solo lectura.** No modifica nada.

# Objetivo

Transformar el README.md del plugin en una guía de usuario con formato HTML navegable,
que muestre el catálogo completo de comandos, su uso, ejemplos y arquitectura del plugin.

# Contexto de ejecución

Invocación directa via `/orchestrator-help`. No forma parte del pipeline.

# Proceso

1. Resolver SKILL_DIR (per PASO 0 del skill)
2. Leer `$SKILL_DIR/README.md` con Read tool
3. Leer `$SKILL_DIR/CHANGELOG.md` — últimas 2 entradas para la sección "Novedades"
4. Construir un documento HTML compacto con:
   - Cabecera: nombre del plugin, versión (de plugin.json), fecha
   - Índice de comandos agrupado por categoría (pipeline, análisis, refactor, BD, VCS, docs)
   - Para cada comando: descripción, uso, ejemplo
   - Sección "Novedades" con últimas 2 versiones del CHANGELOG
5. Publicar como Artifact (Skill: Artifact tool)

# Estructura del HTML

```
Orchestrator ScacsWeb — Guía de Comandos v1.X.X

[Búsqueda rápida por comando]

Pipeline
  /orchestrator-agent — Pipeline completo ScacsWeb
  ...

Análisis de código
  /orchestrator-auditoria — Auditoría de calidad
  /orchestrator-review — Code review con veredicto
  ...

[Resto de categorías]

Novedades v1.3.0 / v1.2.0
  [últimas entradas de CHANGELOG]
```

El HTML debe ser autocontenido (CSS inline), tema claro/oscuro, responsive.
No cargar el HTML completo en el contexto — publicar via Artifact y mostrar el enlace.

# Categorías de comandos

| Categoría | Comandos |
|-----------|----------|
| Pipeline | orchestrator-agent |
| Análisis calidad | auditoria, analizar, review, security, dead-code, cobertura |
| Rendimiento / BD | perf, schema, comparar-modelo, comparar-entornos, erd, sync-indexes |
| Refactor / Cambios | impacto, rename, format, deshacer |
| Generación código | generar-dalc, crear-tests, seed |
| VCS | diff, commit, historial, release-notes, validar-req |
| Documentación | doc, doc-drift, explicar, scacs-docs |
| Estructura | estructura, deps, hotspots |
| Testing | test, cobertura |
| Workspace | env, init, stats, dashboard |
| MantisBT | mantis |

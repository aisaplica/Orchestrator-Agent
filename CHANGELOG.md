# Changelog

## [1.2.0] — 2026-07-28

### Nuevos slash commands (`commands/`)

Creada la carpeta `commands/` con 20 ficheros `.md` que registran los modos del plugin como
slash commands discoverables en el menú `/` de Claude Code. Antes estos modos solo se activaban
por frases en lenguaje natural; ahora aparecen como `/orchestrator-*` en el autocompletado.

- `commands/orchestrator-agent.md` — Pipeline completo ScacsWeb
- `commands/orchestrator-analizar.md` — Análisis de diff/cambio concreto (expone `agents/analyzer.md`)
- `commands/orchestrator-auditoria.md` — Auditoría estática de toda la solución
- `commands/orchestrator-impacto.md` — Análisis de referencias a una clase/método/tabla
- `commands/orchestrator-diff.md` — Cambios pendientes SVN/Git agrupados por proyecto
- `commands/orchestrator-historial.md` — Últimas N ejecuciones del pipeline
- `commands/orchestrator-comparar-modelo.md` — Drift entre modelo BD JSON y esquema real
- `commands/orchestrator-idiomas.md` — Scripts INSERT para SIIdioma/SIControles
- `commands/orchestrator-doc.md` — Generación de documentación técnica
- `commands/orchestrator-env.md` — Validación de entorno de desarrollo
- `commands/orchestrator-estructura.md` — Mapa de capas y dependencias de la solución
- `commands/orchestrator-commit.md` — Diff + sugerencia de commit con gate de confirmación
- `commands/orchestrator-crear-tests.md` — Generación de tests unitarios
- `commands/orchestrator-erd.md` — Gestión de modelo BD, ERD y generación SQL
- `commands/orchestrator-stats.md` — Estadísticas del pipeline
- `commands/orchestrator-validar-req.md` — Verificación de requerimiento contra diff
- `commands/orchestrator-security.md` — Scan de seguridad (SQL injection, XSS, credenciales)
- `commands/orchestrator-deps.md` — Mapa de dependencias entre proyectos
- `commands/orchestrator-mantis.md` — Ciclo de vida MantisBT completo
- `commands/orchestrator-scacs-docs.md` — Navegación de documentación técnica ScacsWeb

### Nuevos modos directos

- `skills/orchestrator-agent/SKILL.md` — Añadido modo `Analizar` (`/orchestrator-analizar`) que
  expone `agents/analyzer.md` como modo directo (antes solo se usaba internamente en el pipeline).

---

## [1.1.0] — 2026-07-28

### Nuevas skills

- `skills/orchestrator-agent/SKILL.md` — Pipeline principal migrado a la estructura `skills/`. PASO 0 actualizado con mecanismo de traversal desde "Base directory for this skill" del contexto del sistema. Fallbacks: rpm/ (marketplace remoto) y instalación manual.
- `skills/mantis/SKILL.md` — Gestión de ciclo de vida MantisBT (4 fases: selección de proyecto/issue, encuadre del requerimiento, lanzamiento del pipeline con transición de estado, validación con adjuntos SQL y cierre).
- `skills/plugin-dev/SKILL.md` — Meta-desarrollo del propio plugin. Adaptado de rs-plugin-dev para ScacsWeb. Pipeline de 9 pasos con 2 gates bloqueantes (aprobación de plan + version bump). Fuente canónica: `docs/plugin-architecture.md`.

### Nuevos hooks

- `hooks/mantis-cli.ps1` — CLI unificado para MantisBT REST API. Acciones: `get-issue`, `list-issues`, `list-projects`, `get-statuses`, `patch-status`, `post-note`, `attach-file`. Resolución de credenciales: env.json > env vars > inline.
- `hooks/mantis-get-issue.ps1` — Hook legacy para fetch de issue individual (retrocompatibilidad con invocaciones anteriores).

### Nuevos agentes

- `agents/mantis.md` — Agente de consulta MantisBT read-only. Dos modos: individual (#NNNN) y lista por proyecto. Para uso inline en el pipeline cuando hay un issue asociado.

### Nuevas referencias

- `references/mantis.md` — Configuración de MantisBT: fuentes de credenciales, cómo obtener API key, endpoints read (GET) y write (PATCH/POST). Cadena de estados ScacsWeb.

### Nueva documentación

- `docs/plugin-architecture.md` — Documento canónico de arquitectura del plugin. §1–§8: anatomía (skills, agents, MCP, hooks, references). §9: patrones de extensión (modo directo, tool MCP, skill standalone, reference, manifest). §10: checklist de sincronización de docs por tipo de cambio.
- `docs/.mantis-dev-config.json` — Catálogo de proyectos ScacsWeb con IDs Mantis y cadena de estados. Template — rellenar IDs nulos con `hooks/mantis-cli.ps1 -Action list-projects`.

---

## [1.0.0] — 2026-07-24

### Lanzamiento inicial

- `SKILL.md` — Skill raíz con pipeline completo de desarrollo ScacsWeb: 11 pasos (planner → core → bd → analyzer → validator → fixer → tester → idiomas → documentar → build → db-env → log) + 18 modos directos.
- `agents/` — 23 agentes especializados: analyzer, auditoria, bd, build, commit-svn, comparar-modelo, core, crear-tests, db-env, dependencias, diff-svn, documentar, estructura, fixer, historial, idiomas-standalone, impacto, planner, scacs-docs, seguridad, stats, tester, validar-entorno, validar-requerimiento, validator.
- `mcp/orchestrator-workspace-server.py` — MCP server `orchestrator-workspace` con 38 tools: sistema, solución, búsqueda, BD/modelo, build/test, VCS (SVN+Git), ASPX, dependencias, log, seguridad, BD directa.
- `hooks/` — 10 hooks PowerShell: validate-solution, batch-build, online-publish, copy-ais, svn-diff, svn-add, svn-diff-revision, git-diff-revision, parse-sln, check-env.
- `references/` — 10 referencias técnicas: arquitectura, bd, conventions, dalc-patterns, dmd-format, hooks, json-schema, mcp, testing, troubleshooting.
- `docs/scacs/00-index.md` — Índice de documentación técnica ScacsWeb.
- `.claude-plugin/` — Plugin.json, marketplace.json para instalación local.
- `.mcp.json` — Declaración del servidor `orchestrator-workspace`.

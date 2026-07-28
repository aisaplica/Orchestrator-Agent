# Changelog

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

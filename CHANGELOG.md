# Changelog

## [1.9.0] — 2026-08-14

### Nuevas features

- `agents/dead-code.md` — Proceso A calcula grado de entrada por nodo leyendo `graphify-out/graph.json` directamente (Bash/python, sin cargar el grafo completo en contexto): grado 0 = candidato a código muerto, cobertura exhaustiva del proyecto en vez de Grep limitado a scope_dirs. Proceso B (search_code) se mantiene como fallback sin grafo.
- `agents/cobertura.md` — Proceso A determina cobertura en una sola pasada sobre `graph.json` (edges `CALLS` desde nodos de test hacia producción), sustituyendo N llamadas a `search_code`. Cruza con "God Nodes" de `GRAPH_REPORT.md` para priorizar símbolos críticos sin cobertura por encima del orden plano DALC>BE>UI. Fallback sin grafo sin cambios.
- `agents/doc-drift.md` — enriquecimiento puntual del paso 4 (no un Proceso A/B completo, la lógica de comparación doc↔código no cambia): si existe grafo, amplía los módulos afectados por el diff con `graphify query` multi-hop, capturando dependencias indirectas que también podrían necesitar actualización de documentación.
- `agents/scacs-docs.md` y `agents/dependencias.md` — evaluados, sin cambios: el primero enruta a documentación estática del framework (no al código de un proyecto), el segundo opera a nivel de referencias `.csproj` entre soluciones (granularidad distinta al grafo por proyecto de graphify). Forzar la integración ahí sería redundante o no honesto.

---

## [1.8.0] — 2026-08-14

### Nuevas features

- `agents/explicar.md` — Proceso A usa `graphify explain` como fuente primaria de la explicación (propósito, módulo/comunidad, conexiones) más `graphify query` para dependencias/tablas BD; siempre verifica flujo de datos y tablas contra el código fuente real, no solo contra el grafo. Proceso B mantiene el comportamiento actual (find_symbol + Grep) como fallback sin grafo.
- `agents/hotspots.md` — Proceso A cruza los `god_nodes` ya calculados por graphify (sección "God Nodes" de `GRAPH_REPORT.md`, sin coste LLM) con el churn VCS, sustituyendo el proxy LoC/100 por el grado de conectividad real del grafo. Si hay menos de 15 god nodes, completa el ranking con el fallback LoC. Tabla de salida añade columna "Fuente" (grafo | LoC) por fila.

---

## [1.7.0] — 2026-08-14

### Nuevas features

- `agents/impacto.md` — proceso reestructurado en dos rutas: Proceso A usa el grafo de conocimiento (`graphify-out/graph.json` del proyecto) vía `graphify query` para trazar impacto multi-hop (directo/indirecto) con `source_location`; Proceso B mantiene el Grep manual como fallback cuando el proyecto no tiene grafo generado. Output añade línea "Fuente: grafo (graphify) | Grep manual" para trazabilidad.

### Fix

- `skills/orchestrator-agent/SKILL.md` — pipeline principal (entry point real) le faltaba el paso 9b "Graphify Update" tras Build. Solo existía en el `SKILL.md` legacy de la raíz, por lo que el pipeline activo nunca refrescaba el grafo de conocimiento tras un build exitoso. Sincronizado con el legacy y añadido al checklist final (10b).

---

## [1.6.4] — 2026-08-12

### Nuevas features

- `skills/pantallas/SKILL.md` — nuevo skill `/orchestrator-pantallas <nombre>` que resuelve el código de pantalla (`CTFORM`/`CTMAPEO`) a partir de su nombre funcional consultando `SICONTROLES JOIN SIIDIOMA` (`CTTIPO=3`, `CTFORM=CTMAPEO`, `IDIDIOMA='ESP'`). Elimina el mantenimiento del MD de directorio de pantallas — los datos vienen siempre de BD.
- `skills/orchestrator-agent/SKILL.md` — sección global "Resolución de nombre de pantalla": cualquier vía de entrada al pipeline (pipeline principal, modos directos o agentes internos) que reciba una pantalla por nombre funcional invoca el skill antes de continuar. Mencionados explícitamente: `idiomas-standalone`, `explicar`, `impacto`.
- `agents/planner.md` — Paso 0 de resolución de pantalla: si el cambio describe una pantalla por nombre (no por código), el planner resuelve el `CTFORM` vía skill antes de planificar.
- `agents/idiomas-standalone.md` — paso 4 actualizado: si el usuario da un nombre de pantalla en lugar de código, invocar el skill de pantallas antes de filtrar controles.

---

## [1.6.3] — 2026-08-12

### Fix / mejora

- `agents/log-errores.md` — convención de ruta ScacsWeb: directorio base `C:\Logs\`, patrón `<Solucion><YYYYMMDD>.txt` (ej. `SCACSWebCDI20260812.txt`). Detección automática en 3 niveles: ruta completa → nombre de solución → pregunta solo la solución. Fallback a ayer si el fichero de hoy no existe.
- `agents/log-errores.md` — exclusiones ScacsWeb en triaje (Fase 2): `PostValidationBRException` (validación controlada de negocio) y errores de HOST en `BSServices` (`<ERROR><NUMERO>…</ERROR>`) no generan tarea Mantis.

---

## [1.6.2] — 2026-08-12

### Nuevas features

- `hooks/lib-msbuild.ps1` — librería que detecta si una solución .NET necesita MSBuild de Visual Studio o CLI `dotnet`, leyendo los `.csproj` de la solución. Resuelve el fallo silencioso en proyectos WebForms/COM donde `dotnet build` termina con MSB4019 pero el parser reportaba `error_count=0`.
- `hooks/compile-check.ps1` — hook de compilación con autodetección de toolchain. Dot-sourcea `lib-msbuild.ps1`, fuerza idioma `en` durante la compilación (evita que etiquetas localizadas quiebren el parser), acepta códigos `MSB####`/`NU####` además de `CS####`, y normaliza `advertencia`/`aviso` a `warning`. **IMPORTANTE:** el MCP ya llamaba a este hook pero el archivo no existía — era la causa de que `compile_check` fallara siempre.
- `hooks/parse-weblog.ps1` — parser de logs de error de la capa web. Soporta NLog/log4net, ELMAH XML, formato AgendaWeb AIS (`Error: (dd/MM/yyyy H:mm) - Codigo error: ... Descripción error: ...`) y volcados de stack .NET. Agrupa las N ocurrencias del mismo fallo en una firma SHA1 (excepción + frame más profundo de código propio + mensaje normalizado) — el log crudo nunca entra en contexto. Redacta literales SQL entre comillas simples antes de emitir el JSON.
- `hooks/mantis-cli.ps1` — acción `create` añadida: crea issues vía `POST /issues` con campos `Summary`, `Description`, `Category`, `Priority`, `Severity`, `Tags`. Devuelve `{id, summary, status}` para dedup posterior.
- `mcp/orchestrator-workspace-server.py` — tool `parse_web_log` añadida. Tool `compile_check` actualizada con parámetro `builder: auto|dotnet|msbuild` y descripción corregida con campo `builder_error`.
- `agents/log-errores.md` — skill de triaje de logs de producción a tareas Mantis. Fases: F0 fuente · F1 parseo+dedup (gate de formato) · F2 triaje+propuesta (gate de usuario) · F3 dedup contra Mantis + alta de issues · F4 propuesta de pipeline. El log nunca entra en contexto del agente.
- `commands/orchestrator-log-errores.md` — slash command `/orchestrator-log-errores <ruta> [--desde] [--max] [--glob] [--niveles]`.

### Fix

- `agents/validator.md` — Paso 1 actualizado: `builder_error` distingue "compilador no instalado (entorno)" de "fallo del código"; `builder` y `builder_reason` explican qué compilador se usó y por qué.

---

## [1.6.1] — 2026-08-12

### Nuevas features

- `agents/incidencia.md` — agente `/orchestrator-incidencia` para generar scripts SQL de incidencia idempotentes (template DDL+DML, política de idempotencia, nota en Mantis).
- `hooks/GenerarScriptIncidencia` — integrado en el pipeline principal como paso opcional post-implementación.

---

## [1.5.0] — 2026-08-06

### Fix
- `hooks/*.ps1` (12 archivos) — añadido UTF-8 BOM (`EF BB BF`). Windows PowerShell 5.1 decodifica sin BOM con codepage ANSI, corrompiendo caracteres españoles (á, é, ó, ñ) y causando fallos de parse silenciosos o mensajes basura.
- `hooks/mantis-cli.ps1` — fallback `USERPROFILE → HOME → "."` en lookup de `project-db-env/env.json`. Sin fallback, `Join-Path $null` revienta a media ejecución si la variable no existe.

### Docs
- `references/troubleshooting.md` — nueva sección "Hook falla silenciosamente / caracteres corruptos" con diagnóstico y fix para el problema de BOM en PS5.1.

---

## [1.4.0] — 2026-07-29

### Nuevos agentes (Fase 3)

11 agentes nuevos que añaden capacidades de scaffolding, infraestructura y gestión avanzada:

- `agents/sync-indexes.md` — Sincroniza índices Oracle al modelo BD JSON del workspace. Oracle-only. Expone `/orchestrator-sync-indexes`.
- `agents/help.md` — Renderiza README y CHANGELOG del plugin como página HTML navegable. Expone `/orchestrator-help`.
- `agents/schema.md` — Muestra esquema completo de tabla(s): columnas, tipos, índices, relaciones. Expone `/orchestrator-schema`.
- `agents/seed.md` — Genera N sentencias INSERT sintéticas para una tabla respetando tipos, NULLs y FKs. Escribe a `executions/seed_<tabla>_<timestamp>.sql`. Expone `/orchestrator-seed`.
- `agents/comparar-entornos.md` — Compara esquema BD entre dos workspaces (ej. dev vs producción). Detecta columnas, tipos e índices distintos. Expone `/orchestrator-comparar-entornos`.
- `agents/dashboard.md` — Genera un dashboard HTML (via Artifact) con KPIs, tendencia y últimas ejecuciones del pipeline desde `executions/history.json`. Expone `/orchestrator-dashboard`.
- `agents/format.md` — Detecta y aplica correcciones de convención ScacsWeb (naming, usings, whitespace) con gate de confirmación obligatorio ("CONFIRMO"). Expone `/orchestrator-format`.
- `agents/rename.md` — Renombra un símbolo C# y todas sus referencias en la solución con gate de confirmación. Verifica compilación tras aplicar. Expone `/orchestrator-rename`.
- `agents/generar-dalc.md` — Genera clases DALC + BE ScacsWeb completas a partir del esquema de una tabla BD. Compatible Oracle y SQL Server. Gate antes de escribir. Expone `/orchestrator-generar-dalc`.
- `agents/init.md` — Bootstrap de workspace: crea `workspace.json`, carpetas (`executions/`, `docs/`), `docs/00-index.md` y sincroniza el modelo BD inicial. Gate antes de crear. Expone `/orchestrator-init`.
- `agents/migrar.md` — Migra DALCs y SQL entre Oracle y SQL Server (o viceversa): tipos, parámetros, comandos, sintaxis SQL. Backup automático. Gate + compile check. Expone `/orchestrator-migrar`.

### Nuevos slash commands (Fase 3)

- `commands/orchestrator-sync-indexes.md`
- `commands/orchestrator-help.md`
- `commands/orchestrator-schema.md`
- `commands/orchestrator-seed.md`
- `commands/orchestrator-comparar-entornos.md`
- `commands/orchestrator-dashboard.md`
- `commands/orchestrator-format.md`
- `commands/orchestrator-rename.md`
- `commands/orchestrator-generar-dalc.md`
- `commands/orchestrator-init.md`
- `commands/orchestrator-migrar.md`

### Modos directos añadidos

`skills/orchestrator-agent/SKILL.md` — añadidas 11 filas en la tabla `# Modos directos`:
sync-indexes, help, schema, seed, comparar-entornos, dashboard, format, rename, generar-dalc, init, migrar.

---

## [1.3.0] — 2026-07-28

### Nuevos agentes (Fase 2)

10 agentes nuevos que añaden capacidades de análisis avanzado sin requerir hooks nuevos:

- `agents/review.md` — Revisión de código con veredicto APRUEBA/CAMBIOS/BLOQUEA. Cruza diff con lógica, modelo BD, seguridad y convenciones. Expone `/orchestrator-review`.
- `agents/explicar.md` — Explica en lenguaje natural qué hace una clase/método/proceso y su flujo de datos. Expone `/orchestrator-explicar`.
- `agents/hotspots.md` — Ranking de ficheros de mayor riesgo cruzando churn VCS con tamaño/complejidad. Expone `/orchestrator-hotspots`.
- `agents/dead-code.md` — Detecta clases, métodos y DALCs sin referencias en el scope. Advisory — nunca elimina. Expone `/orchestrator-dead-code`.
- `agents/perf.md` — Detecta índices faltantes, full-scans y filtros no-sargables en DALCs cruzados con el modelo BD. Expone `/orchestrator-perf`.
- `agents/test.md` — Ejecuta `dotnet test` y reporta pasados/fallidos/omitidos sin lanzar el pipeline. Expone `/orchestrator-test`.
- `agents/cobertura.md` — Mapa estático de cobertura: qué clases/métodos públicos carecen de tests. Expone `/orchestrator-cobertura`.
- `agents/release-notes.md` — Transforma historial VCS en notas de versión funcionales organizadas por categoría. Expone `/orchestrator-release-notes`.
- `agents/deshacer.md` — Revierte cambios pendientes (SVN/Git) con gate de confirmación obligatorio ("CONFIRMO"). Expone `/orchestrator-deshacer`.
- `agents/doc-drift.md` — Cruza cambios recientes en código con docs/scacs/ para detectar documentación obsoleta. Expone `/orchestrator-doc-drift`.

### Nuevos slash commands (Fase 2)

- `commands/orchestrator-review.md`
- `commands/orchestrator-explicar.md`
- `commands/orchestrator-hotspots.md`
- `commands/orchestrator-dead-code.md`
- `commands/orchestrator-perf.md`
- `commands/orchestrator-test.md`
- `commands/orchestrator-cobertura.md`
- `commands/orchestrator-release-notes.md`
- `commands/orchestrator-deshacer.md`
- `commands/orchestrator-doc-drift.md`

### Modos directos añadidos

`skills/orchestrator-agent/SKILL.md` — añadidas 10 filas en la tabla `# Modos directos`:
review, explicar, hotspots, dead-code, perf, test, cobertura, release-notes, deshacer, doc-drift.

---

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

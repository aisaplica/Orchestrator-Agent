---
description: "Analiza rendimiento de acceso a BD: índices faltantes, full-scans, filtros no-sargables."
argument-hint: "<Solution>.sln [DALC|tabla]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in performance mode.

Usage: /orchestrator-perf <Solution>.sln [DALC|tabla]
Examples:
  /orchestrator-perf ScacsWeb.sln
  /orchestrator-perf ScacsWeb.sln ContratoDALC.cs
  /orchestrator-perf ScacsWeb.sln PRPROPUESTAS

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\perf.md` inline and
follow its instructions. Cross-references DALC SQL statements against BD model indexes. Does not
modify code or BD. Pass `sln_path`, `workspace`, and optional DALC/table filter. Relay verbatim.

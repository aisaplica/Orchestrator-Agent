---
description: "Genera y persiste documentación técnica de la solución (estructura, tablas, flujo, config)."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in doc mode.

Usage: /orchestrator-doc <Solution>.sln
Example: /orchestrator-doc ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\documentar.md` inline
and follow its instructions in GenerarDoc mode. Pass `sln_path` and `workspace`. Supports two
modes: full GenerarDoc (complete solution analysis) and UpdateDocs (only changed files). Relay
output verbatim.

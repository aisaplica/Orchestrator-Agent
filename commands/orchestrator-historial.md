---
description: "Muestra las últimas N ejecuciones del pipeline desde el historial."
argument-hint: "[Solution.sln] [N]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in historial mode.

Usage: /orchestrator-historial [Solution.sln] [N]
Example: /orchestrator-historial
Example: /orchestrator-historial ScacsWeb.sln 5

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\historial.md` inline
and follow its instructions. Pass `workspace`, optional solution filter, and N (number of recent
executions to show). Read-only. Relay output verbatim.

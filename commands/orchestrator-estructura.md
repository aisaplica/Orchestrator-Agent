---
description: "Mapa de capas y dependencias de la solución, detecta referencias circulares."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in estructura mode.

Usage: /orchestrator-estructura <Solution>.sln
Example: /orchestrator-estructura ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\estructura.md` inline
and follow its instructions. Pass `workspace` and the solution file. Returns project layer map,
shared project references, and circular dependency detection. Read-only. Relay output verbatim.

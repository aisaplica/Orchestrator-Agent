---
description: "Detecta clases, métodos y DALCs sin referencias en el scope de la solución."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in dead-code mode.

Usage: /orchestrator-dead-code <Solution>.sln
Example: /orchestrator-dead-code ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\dead-code.md` inline
and follow its instructions. Pass `sln_path` (per SKILL.md "Resolución de solución"). Advisory
only — never automatically deletes code. Flags entry points as inconclusive. Relay output verbatim.

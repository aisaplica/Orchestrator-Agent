---
description: "Estadísticas del pipeline: total ejecuciones, tasa éxito, agentes más usados, tendencia 7 días."
argument-hint: "[solution]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in stats mode.

Usage: /orchestrator-stats [solution]
Example: /orchestrator-stats
Example: /orchestrator-stats ScacsWeb

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\stats.md` inline and
follow its instructions. Pass `workspace` = cwd and the solution filter if the user gave one.
Read-only, mechanical. Relay output verbatim.

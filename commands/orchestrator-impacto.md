---
description: "Analiza todas las referencias a una clase, método o tabla dentro del scope de la solución."
argument-hint: "<clase|método|tabla> en <Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in impacto mode.

Usage: /orchestrator-impacto <clase|método|tabla> en <Solution>.sln
Example: /orchestrator-impacto ECCLIENTES en ScacsWeb.sln
Example: /orchestrator-impacto ProcesoLiquidacion en BatchCirbe.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\impacto.md` inline
and follow its instructions. Pass `sln_path` (resolved per SKILL.md) and the target element
(class/method/table). Pure read-only analysis. Relay output verbatim.

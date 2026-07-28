---
description: "Análisis estático de calidad y riesgo de un diff o cambio concreto (no de toda la solución)."
argument-hint: "<Solution>.sln [revisión|ficheros]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in analizar mode.

Usage: /orchestrator-analizar <Solution>.sln [revisión|ficheros]
Example: /orchestrator-analizar ScacsWeb.sln
Example: /orchestrator-analizar BatchCirbe.sln 1234

After loading the skill (PASO 0 resolves SKILL_DIR), call `detect_vcs(workspace)` first so the
agent can reconstruct the delta. Then read `$SKILL_DIR\agents\analyzer.md` inline and follow its
instructions. Pass `sln_path` and `workspace` (per SKILL.md), the detected `vcs`, and the optional
revision/files the user gave (default: pending changes). Relay output verbatim.

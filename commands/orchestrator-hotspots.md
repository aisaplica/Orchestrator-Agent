---
description: "Puntos calientes de riesgo: cruza frecuencia de cambios VCS con complejidad del código."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in hotspots mode.

Usage: /orchestrator-hotspots <Solution>.sln
Example: /orchestrator-hotspots ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first.
2. Read `$SKILL_DIR\agents\hotspots.md` inline and follow its instructions.
Pass `sln_path`, `workspace`, and the detected `vcs`. Advisory — does not modify code.
Relay output verbatim.

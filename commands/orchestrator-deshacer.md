---
description: "Revierte los cambios pendientes del workspace (SVN o Git), previa confirmación explícita."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in deshacer mode.

Usage: /orchestrator-deshacer <Solution>.sln
Example: /orchestrator-deshacer ScacsWeb.sln

⚠️ Operación destructiva — los cambios locales no commiteados se perderán.

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first — if "none", inform the user and stop.
2. Read `$SKILL_DIR\agents\deshacer.md` inline and follow its instructions.
Pass `sln_path`, `workspace`, `vcs`. The agent shows the full list of affected files and stops to
ask for explicit confirmation ("CONFIRMO") before reverting anything. Relay output verbatim.

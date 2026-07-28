---
description: "Muestra cambios pendientes (SVN o Git, autodetectado) agrupados por solución y proyecto."
argument-hint: "[Solution.sln]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in diff mode (SVN or Git, auto-detected).

Usage: /orchestrator-diff [Solution.sln]
Example: /orchestrator-diff
Example: /orchestrator-diff ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` — if "none", inform the user and stop.
2. Read `$SKILL_DIR\agents\diff-svn.md` inline and follow its instructions.
3. Pass `workspace`, the detected `vcs`, plus the solution filter if the user gave one.
Read-only. Relay output verbatim.

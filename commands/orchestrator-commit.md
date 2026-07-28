---
description: "Muestra diff (SVN o Git, autodetectado), sugiere mensaje de commit y confirma antes de ejecutar."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in commit mode (SVN or Git, auto-detected).

Usage: /orchestrator-commit <Solution>.sln
Example: /orchestrator-commit ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` — if "none", inform the user and stop.
2. Read `$SKILL_DIR\agents\commit-svn.md` inline and follow its instructions (it branches internally on SVN/Git).
3. Pass `sln_path`, `workspace`, and the detected `vcs`.
Writes only after explicit human confirmation gate. Relay output verbatim.

---
description: "Detecta documentación técnica obsoleta respecto a cambios recientes en el código."
argument-hint: "<Solution>.sln [--rev <revisiones>]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in doc-drift mode.

Usage: /orchestrator-doc-drift <Solution>.sln [--rev <revisiones>]
Examples:
  /orchestrator-doc-drift ScacsWeb.sln
  /orchestrator-doc-drift ScacsWeb.sln --rev 1234

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first.
2. Read `$SKILL_DIR\agents\doc-drift.md` inline and follow its instructions.
Pass `sln_path`, `workspace`, `vcs`, and any `--rev` argument. Read-only, advisory. Relay verbatim.

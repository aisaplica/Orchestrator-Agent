---
description: "Revisión de código con veredicto APRUEBA/CAMBIOS/BLOQUEA (lógica + BD + seguridad sobre el delta)."
argument-hint: "<Solution>.sln [--rev <revisión>]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in review mode.

Usage: /orchestrator-review <Solution>.sln [--rev <revisión>]
Examples:
  /orchestrator-review ScacsWeb.sln
  /orchestrator-review BatchCirbe.sln --rev 1234

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first.
2. Read `$SKILL_DIR\agents\review.md` inline and follow its instructions.
Pass `sln_path` (per SKILL.md), `workspace`, `vcs`, and optional revision. Relay output verbatim.

---
description: "Genera notas de versión funcionales desde el historial de commits SVN o Git."
argument-hint: "[Solution] [N] [--desde YYYY-MM-DD]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in release-notes mode.

Usage: /orchestrator-release-notes [Solution] [N] [--desde YYYY-MM-DD]
Examples:
  /orchestrator-release-notes ScacsWeb 30
  /orchestrator-release-notes --desde 2026-07-01
  /orchestrator-release-notes BatchCirbe

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first.
2. Read `$SKILL_DIR\agents\release-notes.md` inline and follow its instructions.
Pass `workspace`, detected `vcs`, optional solution filter, N commits, and date range. Relay verbatim.

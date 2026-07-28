---
description: "Auditoría estática de calidad de toda la solución (sin modificar código)."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in auditoria mode.

Usage: /orchestrator-auditoria <Solution>.sln
Example: /orchestrator-auditoria ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\auditoria.md` inline
and follow its instructions. Pass `sln_path` (resolved per SKILL.md "Resolución de solución") and
`plugin_root` (SKILL_DIR). Advisory only — does not write code. Relay output verbatim.

---
description: "Scan de seguridad: SQL injection, credenciales hardcoded, XSS, inputs sin validar."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in seguridad mode.

Usage: /orchestrator-security <Solution>.sln
Example: /orchestrator-security ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\seguridad.md` inline
and follow its instructions. Pass `sln_path` (per SKILL.md "Resolución de solución"). Advisory
only — flags vulnerabilities, does not auto-fix. Relay output verbatim.

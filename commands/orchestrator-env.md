---
description: "Valida el entorno de desarrollo: BD, AIS, dotnet, SVN/Git, modelo BD y docs."
argument-hint: "[workspace]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in validar-entorno mode.

Usage: /orchestrator-env [workspace]
Example: /orchestrator-env

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\validar-entorno.md`
inline and follow its instructions. Pass `workspace` = cwd (or the one the user specified).
Read-only, mechanical check. Relay output verbatim.

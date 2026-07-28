---
description: "Crea proyecto de tests si no existe y genera tests unitarios para la solución."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in crear-tests mode.

Usage: /orchestrator-crear-tests <Solution>.sln
Example: /orchestrator-crear-tests ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\crear-tests.md` inline
and follow its instructions. Pass `sln_path`, `plugin_root` (SKILL_DIR), and the scope (target
classes, or pending changes). Creates the test project if missing, then generates unit tests.
Relay output verbatim.

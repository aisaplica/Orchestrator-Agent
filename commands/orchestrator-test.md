---
description: "Ejecuta los tests de la solución y reporta resultado (sin lanzar el pipeline completo)."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in test mode.

Usage: /orchestrator-test <Solution>.sln
Example: /orchestrator-test ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\test.md` inline and
follow its instructions. Runs dotnet test on the solution and reports passed/failed/skipped without
launching the full pipeline. Pass `sln_path` (per SKILL.md "Resolución de solución"). Relay verbatim.

---
description: "Crea proyecto de tests si no existe y genera tests unitarios para la solución."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in crear-tests mode.

Usage: /orchestrator-crear-tests <Solution>.sln
Example: /orchestrator-crear-tests ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR):
1. If no test project exists, scaffold one: `mcp__orchestrator-workspace__create_test_project(sln_path)`
   or `hooks/create-test-project.ps1 <sln> -Framework xunit`.
2. Then read `$SKILL_DIR\agents\test.md` inline and follow it to author and run unit tests for the
   scope (target classes, or pending changes). Pass `sln_path`, `plugin_root` (SKILL_DIR).
Relay output verbatim.

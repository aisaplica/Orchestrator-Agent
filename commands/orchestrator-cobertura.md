---
description: "Mapa de cobertura estática: qué clases y métodos públicos carecen de tests."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in cobertura mode.

Usage: /orchestrator-cobertura <Solution>.sln
Example: /orchestrator-cobertura ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\cobertura.md` inline
and follow its instructions. Cross-references the solution's public API surface against existing
test projects to identify uncovered elements. Advisory — does not generate tests.
Pass `sln_path`, `workspace`. Relay output verbatim.

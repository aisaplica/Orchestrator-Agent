---
description: "Detecta drift entre el modelo BD JSON del proyecto y el esquema real en BD."
argument-hint: "[workspace]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in comparar-modelo mode.

Usage: /orchestrator-comparar-modelo [workspace]
Example: /orchestrator-comparar-modelo

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\comparar-modelo.md`
inline and follow its instructions. Generates a comparison table between the project model JSON
(ECCLIENTES, PRPROPUESTAS, PRFINANC, etc.) and the actual database schema. Read-only, no DDL.
Relay output verbatim.

---
description: "Genera INSERTs sintéticos de prueba para una tabla ScacsWeb respetando tipos y FKs."
argument-hint: "<tabla> [N filas]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\seed.md`

Follow those instructions exactly.

Usage: `/orchestrator-seed <tabla> [N]`
Examples:
- `/orchestrator-seed ECCLIENTES`
- `/orchestrator-seed PRPROPUESTAS 20`
- `/orchestrator-seed PRFINANC 5`

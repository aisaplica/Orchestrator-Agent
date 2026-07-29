---
description: "Muestra el esquema real de tabla(s) ScacsWeb (columnas, tipos, índices, relaciones)."
argument-hint: "<tabla|keyword> [tabla2,...]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\schema.md`

Follow those instructions exactly.

Usage: `/orchestrator-schema <tabla|keyword>`
Examples:
- `/orchestrator-schema ECCLIENTES`
- `/orchestrator-schema PRPROPUESTAS, PRFINANC`
- `/orchestrator-schema clientes`
- `/orchestrator-schema EC*`

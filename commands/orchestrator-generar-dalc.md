---
description: "Genera clases DALC y BE ScacsWeb a partir del esquema de una tabla BD."
argument-hint: "<tabla> [modulo] [Solucion.sln]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\generar-dalc.md`

Follow those instructions exactly.

Usage: `/orchestrator-generar-dalc <tabla> [modulo]`
Examples:
- `/orchestrator-generar-dalc PRPROPUESTAS`
- `/orchestrator-generar-dalc ECCLIENTES EC`
- `/orchestrator-generar-dalc PRFINANC PR ScacsWeb.sln`

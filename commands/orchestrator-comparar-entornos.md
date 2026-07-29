---
description: "Compara esquema BD entre dos entornos ScacsWeb (dev vs producción, tablas y columnas)."
argument-hint: "<workspace1> [workspace2] [tablas]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\comparar-entornos.md`

Follow those instructions exactly.

Usage: `/orchestrator-comparar-entornos <workspace1> [workspace2] [tablas]`
Examples:
- `/orchestrator-comparar-entornos C:\Dev\ScacsWeb C:\Prod\ScacsWeb`
- `/orchestrator-comparar-entornos C:\Dev\ScacsWeb C:\Prod\ScacsWeb ECCLIENTES,PRPROPUESTAS`
- `/orchestrator-comparar-entornos C:\Dev\ScacsWeb`

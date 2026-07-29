---
description: "Migra DALCs y SQL entre Oracle y SQL Server con transformación automática de tipos y sintaxis."
argument-hint: "<fichero|carpeta> [--from oracle|sqlserver] [--to oracle|sqlserver]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\migrar.md`

Follow those instructions exactly.

Usage: `/orchestrator-migrar <fichero|carpeta> [--from <motor>] [--to <motor>]`
Examples:
- `/orchestrator-migrar AIS.PR.DA.PR.CL\PropuestaDALC.cs --to oracle`
- `/orchestrator-migrar AIS.EC.DA.EC.CL --from oracle --to sqlserver`
- `/orchestrator-migrar queries/propuestas.sql --to sqlserver`

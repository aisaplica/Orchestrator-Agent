---
description: "Aplica correcciones de convención ScacsWeb (naming, usings, whitespace) con gate de confirmación."
argument-hint: "<Solucion>.sln [ruta|fichero]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\format.md`

Follow those instructions exactly.

Usage: `/orchestrator-format <Solucion>.sln [ruta]`
Examples:
- `/orchestrator-format ScacsWeb.sln`
- `/orchestrator-format ScacsWeb.sln AIS.PR.BR.PR.CL`
- `/orchestrator-format ScacsWeb.sln AIS.EC.BR.EC.CL\ClienteDALC.cs`

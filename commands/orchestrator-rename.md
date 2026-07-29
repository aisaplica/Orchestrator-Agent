---
description: "Renombra un símbolo ScacsWeb y todas sus referencias con gate de confirmación."
argument-hint: "<Solucion>.sln <nombre-actual> <nuevo-nombre>"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\rename.md`

Follow those instructions exactly.

Usage: `/orchestrator-rename <Solucion>.sln <nombre-actual> <nuevo-nombre>`
Examples:
- `/orchestrator-rename ScacsWeb.sln ObtenerCliente GetCliente`
- `/orchestrator-rename ScacsWeb.sln PropuestaBE PropuestaEntity`
- `/orchestrator-rename ScacsWeb.sln ClienteDALC ClienteRepository`

---
description: "Bootstrap de workspace ScacsWeb: crea configuración BD, carpetas y sincroniza modelo inicial."
argument-hint: "[workspace_path]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\init.md`

Follow those instructions exactly.

Usage: `/orchestrator-init [workspace_path]`
Examples:
- `/orchestrator-init`
- `/orchestrator-init C:\Desarrollo\SVN\ScacsWeb`
- `/orchestrator-init C:\Proyectos\BatchCirbe`

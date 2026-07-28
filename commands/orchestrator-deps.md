---
description: "Mapa de dependencias entre soluciones, proyectos compartidos y conflictos de paquetes."
argument-hint: "[project_name]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in dependencias mode.

Usage: /orchestrator-deps [project_name]
Example: /orchestrator-deps
Example: /orchestrator-deps ScacsWeb

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\dependencias.md` inline
and follow its instructions. Receives workspace context and optional project filter. Returns
dependency map grouped by solution, shared projects, and package conflicts. Read-only. Relay
output verbatim.

---
description: "Consulta la documentación funcional del Workflow de SCACS Web (modelos, etapas, señales, transiciones, funciones, tablas WF*)."
argument-hint: "[pregunta | tabla WF* | #Mantis]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in workflow mode.

Usage: /orchestrator-workflow [pregunta | tabla WF* | #Mantis]
Example: /orchestrator-workflow qué pasa si la etapa destino no existe
Example: /orchestrator-workflow WFBDResumen
Example: /orchestrator-workflow por qué una etapa en paralelo no se activa

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\workflow.md` inline
and follow its instructions. Reads `docs/scacs/04-workflow/` and cross-checks the real `WF*` table
schema via `get_table_schema`. Read-only. Never invents behavior. Relay output verbatim.

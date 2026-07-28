---
description: "Accede y navega la documentación técnica de ScacsWeb (índice, módulos, BD, arquitectura)."
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in scacs-docs mode.

Usage: /orchestrator-scacs-docs [tema|módulo]
Example: /orchestrator-scacs-docs
Example: /orchestrator-scacs-docs ECCLIENTES
Example: /orchestrator-scacs-docs módulo propuestas

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\scacs-docs.md` inline
and follow its instructions. Navigates the ScacsWeb technical documentation index at
`docs/scacs/00-index.md` and surfaces relevant sections. Read-only. Relay output verbatim.

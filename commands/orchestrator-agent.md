---
description: "Pipeline completo ScacsWeb: planificación → análisis → validación → testing → build."
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

Trigger pattern: `<Solucion>.sln - <descripción del cambio>`
Examples:
  ScacsWeb.sln - añadir validación de importe en FrmAlta.aspx
  BatchCirbe.sln - corregir cálculo de cuotas en ProcesoLiquidacion
  SCACSWebCDI.sln - nueva búsqueda de clientes por NIF en ECCLIENTES

The skill launches the full 11-step pipeline automatically.
NOT for direct modes (audit/diff/ERD/idiomas/commit) — use dedicated /orchestrator-* commands.

Core Workflow:
1. Planner (Gate A — mandatory stop, present plan and await approval)
2. Resolve solution + scope
3. Read technical docs
4. Core → BD → Analyzer → Validator/Fixer → Tester → Build → DB-Env
5. Final checklist (Gate B) → Log

Key principles: security > speed | robustness > simplicity | minimal changes > rewrites.

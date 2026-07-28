---
description: "Explica en lenguaje natural qué hace una clase, método o proceso y su flujo de datos."
argument-hint: "<Solution>.sln <clase|método|proceso>"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in explicar mode.

Usage: /orchestrator-explicar <Solution>.sln <clase|método|proceso>
Examples:
  /orchestrator-explicar ScacsWeb.sln ContratoDALC
  /orchestrator-explicar BatchCirbe.sln ProcesoLiquidacion
  /orchestrator-explicar ScacsWeb.sln FrmAltaPropuesta.aspx

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\explicar.md` inline
and follow its instructions. Pass `sln_path`, `workspace`, and the target code element from
$ARGUMENTS. Read-only, onboarding-focused. Relay output verbatim.

---
description: "Orquesta una issue de MantisBT en un ciclo de desarrollo completo (selección → En Proceso → pipeline → commit → En Validación)."
argument-hint: "[NNNN] [Solution.sln]"
---

Invoke the `orchestrator-skill-full:mantis` skill.

Usage:
  /orchestrator-mantis          — seleccionar proyecto y listar issues abiertas
  /orchestrator-mantis 1234     — iniciar directamente con esa issue
  /orchestrator-mantis 1234 ScacsWeb.sln  — issue + solución explícita

Follows the phases in `skills/mantis/SKILL.md`:
  1. Selección de proyecto/issue
  2. Encuadre del requerimiento
  3. Lanzamiento del pipeline con transición de estado
  4. Validación, adjuntos SQL y cierre

Uses `hooks/mantis-cli.ps1` for MantisBT REST API (token auth). Relay output verbatim.

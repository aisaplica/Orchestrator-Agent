---
description: "Verifica que el diff SVN/Git implementa correctamente un requerimiento."
argument-hint: "\"<requerimiento>\" --rev <revisión>"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in validar-requerimiento mode.

Usage: /orchestrator-validar-req "<requerimiento>" --rev <revisiones> [--sln <solucion.sln>]

Arguments:
  <requerimiento>   Texto libre o ruta a fichero .md/.txt con la especificación
  --rev             Revisión(es) SVN o hash(es) Git, separadas por coma
  --sln             Solución (opcional — se infiere del diff si se omite)

Examples:
  /orchestrator-validar-req "validar que el importe es positivo" --rev 1234
  /orchestrator-validar-req "reqs/req-001.md" --rev 1234,1235 --sln ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Call `detect_vcs(workspace)` first.
2. Read `$SKILL_DIR\agents\validar-requerimiento.md` inline and follow its instructions.
Pass `workspace`, requirement text/path, revisions, and optional sln. Relay output verbatim.

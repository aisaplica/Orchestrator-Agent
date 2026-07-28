---
description: "Genera scripts INSERT para SIIdioma y SIControles de controles AIS en ficheros .aspx."
argument-hint: "<Solution>.sln"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in idiomas-standalone mode.

Usage: /orchestrator-idiomas <Solution>.sln
Example: /orchestrator-idiomas ScacsWeb.sln

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\idiomas-standalone.md`
inline and follow its instructions. Pass `sln_path` and `workspace` (per SKILL.md). Generates
INSERT scripts for SIControles (CTFORM, CTMAPEO, CTTIPO, CTTEXTO) and SIIdioma (IDTexto, IDIdioma,
IDDESCRIPCION). Relay output verbatim.

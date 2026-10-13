---
description: "Smoke test en runtime de una pantalla .aspx con agent-browser (web local, solo lectura)."
argument-hint: "[Solucion.sln|Proyecto] [--url <url_login>] [--pantalla <X.aspx>] [--evidencias <dir>]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in smoke mode.

Usage: /orchestrator-smoke [Solucion.sln|Proyecto] [--url <url_login>] [--pantalla <X.aspx>] [--evidencias <dir>]
Example: /orchestrator-smoke bancamarch --pantalla CM01010MDC1.aspx

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\smoke.md` inline
and follow its instructions. Pass `workspace` = cwd and the arguments = $ARGUMENTS.
Credentials come from `projects/<Proyecto>/smoke.json` (password `null` = ask every time) or are
asked interactively; local hosts only. Read-only navigation. Relay output verbatim.

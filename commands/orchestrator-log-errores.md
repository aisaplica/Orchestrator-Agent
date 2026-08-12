---
description: "Analiza el log de errores de la web AIS, deduplica los tipos de error y abre una tarea Mantis por tipo."
argument-hint: "<ruta log|carpeta> [--desde YYYY-MM-DD] [--max N] [--glob *.log] [--niveles ERROR,FATAL]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in log-errores mode.

Usage: /orchestrator-log-errores <ruta log|carpeta> [--desde YYYY-MM-DD] [--max N] [--glob *.log] [--niveles ERROR,FATAL]
Examples:
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs\web.log --desde 2026-08-01
- /orchestrator-log-errores C:\AIS\<Proyecto>\AgendaWeb\logs --max 10 --niveles ERROR,FATAL,WARN

After loading the skill (PASO 0 resolves SKILL_DIR):
1. Read `$SKILL_DIR\agents\log-errores.md` inline and follow its instructions.
2. The log is analyzed by `mcp__orchestrator-workspace__parse_web_log` — the raw log never enters context.
3. Phases: F0 source · F1 parse+dedup · F2 triage+gate · F3 create in Mantis · F4 propose pipeline.
4. ⛔ Relay tool output verbatim. ⛔ Confirm before any Mantis write.

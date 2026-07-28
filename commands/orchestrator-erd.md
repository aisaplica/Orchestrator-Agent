---
description: "Gestiona modelo BD JSON, renderiza ERD visual, genera SQL y sincroniza desde BD."
argument-hint: "[workspace]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill in ERD / Modelo BD mode.

Usage: /orchestrator-erd [workspace]
Example: /orchestrator-erd

After loading the skill (PASO 0 resolves SKILL_DIR), read `$SKILL_DIR\agents\db-env.md` inline
and follow its instructions. Manages the BD model JSON (ECCLIENTES, PRPROPUESTAS, PRFINANC, etc.),
renders the ERD widget, generates SQL DDL, and syncs schema from database. Pass `workspace` = cwd.
Relay output verbatim.

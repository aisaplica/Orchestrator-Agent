---
description: "Genera script SQL idempotente para una incidencia ScacsWeb con cabecera estándar y recordatorio Mantis."
argument-hint: "<mantis> <descripcion del cambio> [--motor oracle|sqlserver]"
---

Invoke the `orchestrator-skill-full:orchestrator-agent` skill.

After loading the skill and resolving SKILL_DIR (PASO 0), read the agent file inline:
`Read $SKILL_DIR\agents\incidencia.md`

Follow those instructions exactly.

Usage: `/orchestrator-incidencia <mantis> <descripcion>`
Examples:
- `/orchestrator-incidencia 12345 añadir valor 'X' en tabla SIPARAMETROS clave TIMEOUT_SESION`
- `/orchestrator-incidencia 67890 añadir columna FECBAJA a tabla ECCLIENTES`
- `/orchestrator-incidencia 11111 actualizar OGEMPRESA de '001' a '002' en SICODIGOS --motor sqlserver`

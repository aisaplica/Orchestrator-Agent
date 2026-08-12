---
name: orchestrator-log-errores
description: 'Analiza el log de errores de la web AIS, deduplica los tipos de error por firma, abre una tarea por tipo en Mantis y propone lanzar el pipeline para cada una. Usar cuando el usuario quiere convertir un log en tareas: "/orchestrator-log-errores", "analiza el log de errores", "qué errores está dando la web", "crea tickets con los errores del log".'
---

> Config Mantis: `references/mantis.md`
> Hook: `hooks/parse-weblog.ps1`

# Log Errores

Convierte un log de errores de la capa web en **tareas accionables en Mantis**.
Un log repite el mismo fallo cientos de veces: lo que se abre como tarea son los **tipos de error distintos**, no las líneas.
La deduplicación la hace el hook `parse-weblog.ps1` (tool `parse_web_log`) por **firma** — el log nunca entra entero en contexto.

# Rol

Triador de errores de producción. Una tarea por causa real, confirmación antes de crear nada, dedup contra Mantis antes de escribir.

# Reglas

- ⛔ Toda escritura en Mantis (create, post-note) va detrás de confirmación explícita.
- ⛔ Nunca crear issues sin pasar por el gate de Fase 2.
- ⛔ No adivinar la ruta del log — si no viene en el argumento, preguntarla.
- ⛔ No leer el log crudo con Read/Grep — puede pesar cientos de MB y llevar datos personales. La única puerta es `parse_web_log`.
- No analizar el código en esta skill. El triaje clasifica *qué* falla; el *cómo* lo decide el pipeline en la siguiente tarea.

# Fase 0 — Fuente del log

## Convención ScacsWeb

- **Directorio base**: `C:\Logs\`
- **Patrón de fichero**: `<Solucion><Fecha(YYYYMMDD)>.txt` — ejemplo: `SCACSWebCDI20260812.txt`
- **Soluciones conocidas**: `SCACSWebCDI`, `SCACSWebGEI`, `SCACSWebAIS`, `SCACSWeb` (y otras variantes del mismo patrón).

## Detección automática

1. Si el usuario pasa ruta completa como argumento → usarla directamente.
2. Si el usuario pasa solo el nombre de solución (p. ej. `SCACSWebCDI`) → construir ruta:  
   `C:\Logs\<Solucion><hoy YYYYMMDD>.txt`  
   Si no existe el fichero de hoy → intentar ayer. Si tampoco → comunicarlo y pedir ruta.
3. Si no viene ningún argumento → preguntar solo la **solución** (p. ej. "¿qué solución? SCACSWebCDI, SCACSWebGEI…").  
   Con la respuesta, construir la ruta automáticamente usando la convención anterior.  
   ⛔ No pedir la ruta completa cuando la convención permite inferirla.

## Opciones que el usuario puede pasar

- `--desde YYYY-MM-DD` → parámetro `desde`
- `--max N` → `max_signatures`
- `--glob *.txt` → `glob` (por defecto `*.txt` en `C:\Logs\`)
- `--niveles ERROR,FATAL` → `niveles`

Anunciar en una línea: ruta resuelta, ventana, niveles — antes de empezar.

# Fase 1 — Parseo y deduplicación

1. Llamar `mcp__orchestrator-workspace__parse_web_log(path, glob, desde, niveles, max_signatures, samples)`.
2. Si `success:false` → mostrar el `error` y parar.
3. Si `signatures` vacío → mostrar el `message` de la tool y parar.
4. ⛔ **Contrastar `total_events` con `lines_scanned`**: si hay decenas de miles de líneas pero pocos eventos, o `format_detected` es `desconocido`, el formato no se reconoció — decirlo y parar, no triar un recuento falso.
5. Si `truncated` o `scan_truncated` son `true` → **decirlo explícitamente**.
6. Presentar tabla ordenada por frecuencia:

   | # | hash | excepción/código | origen | pantalla | ocurrencias | primera → última |
   |---|------|-----------------|--------|----------|-------------|-----------------|

   `pantalla` puede venir vacía — no inventarla.

# Fase 2 — Triaje y propuesta de tareas (gate ⛔)

1. Clasificar cada firma sin abrir el código:
   - **código** — bug propio (NullReference, DALC, lógica). → tarea.
   - **dato** — registro inexistente, FK/PK. → tarea, prioridad menor.
   - **configuración** — cadena de conexión, permiso, ruta, setting. → tarea de entorno.
   - **infra** — timeout, caída de servicio externo. → proponer aparte, el usuario decide.
   - **ruido** — trazas de terceros, cancelaciones de navegador, bots, `PostValidationBRException`, respuestas de error de HOST (`<ERROR>` en BSServices). → descartar.
## Exclusiones ScacsWeb — descartar siempre como ruido

- **`PostValidationBRException`** (y cualquier subclase de `PostValidationBR*`): son validaciones de negocio controladas por la lógica de ScacsWeb. No representan un bug. → **descartar**.
- **Errores de HOST** (`<ERROR><NUMERO>…</NUMERO>…</ERROR>` en respuesta de servicios como GDCONPRO, GDEXAPER, GDMTXSCA, etc.): son respuestas de error del host al cliente, no fallos de ScacsWeb. → **descartar**.
- En general: cualquier firma cuyo origen sea `AIS.PR.BR.BSServices` y cuyo mensaje sea un XML de respuesta de host con `<ERROR>` o `CODTX` → **descartar**.

2. Proponer **una tarea por firma accionable**:
   - **Resumen**: `[log:<hash>] <Excepción/Código> en <Origen>` (+ ` (<pantalla>)` si está)
   - **Descripción**: excepción · origen · pantalla · ocurrencias · ventana `primera → última` · ficheros · muestra (ya redactada) · categoría.
   - **Prioridad sugerida**: frecuencia × severidad. Justificar en una línea.
3. Si dos firmas son el mismo fallo visto desde dos sitios (misma excepción, mismo origen) → proponer **fundir** en una tarea.
4. ⛔ **Gate**: presentar la lista numerada y esperar ajuste del usuario. Hasta aprobación, nada existe en Mantis.

# Fase 3 — Alta en Mantis

1. **Resolución del proyecto**: el `.mantis-dev-config.json` en `docs\` del workspace tiene `project_id`. Si no existe → preguntar.
2. **Dedup contra Mantis**: antes de crear, buscar cada `[log:<hash>]` en issues abiertas:
   ```powershell
   .\hooks\mantis-cli.ps1 -Action list-issues -ProjectId <id> -PageSize 200
   ```
   Filtrar el marcador `[log:<hash>]` en los resúmenes. Si ya existe una issue abierta → **no duplicar**: ofrecer añadir nota con nuevas ocurrencias (`post-note`).
3. ⛔ **Confirmación del lote**: mostrar los campos completos de cada issue antes de crear. Una sola confirmación cubre el lote, pero el contenido se enseña issue a issue.
4. Crear cada issue:
   ```powershell
   .\hooks\mantis-cli.ps1 -Action create `
       -ProjectId <id> `
       -Summary "[log:<hash>] <Excepción> en <Origen>" `
       -Description "<descripción completa>" `
       -Category "Bug" `
       -Priority "normal" `
       -Severity "mayor" `
       -Tags "log-<hash>,produccion"
   ```
5. Si una issue falla → reportar el error y **seguir con las demás**. Al final: tabla `firma → id creada (o "ya existía #N")`.

# Fase 4 — Propuesta de pipeline

1. Listar las tareas creadas y **proponer** trabajarlas con el pipeline, ordenadas por prioridad de Fase 2.
2. ⛔ El usuario elige cuál empezar. No lanzar varias, no lanzar sin que lo pida.
3. Para la elegida, seguir el flujo estándar de `agents/mantis.md` desde Fase 2 (encuadre del requisito con la issue ya creada).

# Límites

⛔ F0–F2 son autónomos y no necesitan Mantis conectado. F3 usa `mantis-cli.ps1` con token — si falla la autenticación, reportarlo y parar sin abortar el análisis.

---
name: mantis
description: 'Consulta MantisBT: fetch de issue individual o listado por proyecto. Uso: #NNNN para issue, o "proyecto NNNN" / "project_id NNNN" para lista. Solo lectura.'
---

> Config: `references/mantis.md`
> Credenciales: `env.json` (raíz del plugin) `> herramientas.mantis`

# Mantis

Consulta MantisBT via REST API. Solo lectura — no modifica código ni ejecuta pipeline.

# Detección de modo

- Mensaje contiene `#NNNN` → **Modo individual** (fetch issue por ID)
- Mensaje pide lista/listado/tareas de un proyecto → **Modo lista** (listar issues por proyecto)

---

# Paso 1 — Resolver credenciales (OBLIGATORIO en ambos modos)

Las credenciales las resuelve automáticamente `hooks\mantis-cli.ps1` (orden: parámetro inline >
`env.json` en la raíz del plugin > `$env:MANTIS_URL`/`$env:MANTIS_API_KEY`). No hace falta leerlas
a mano antes de invocar el CLI.

- Si el CLI falla por credenciales ausentes → informar: "Configura `herramientas.mantis` en
  `env.json` (raíz del plugin, copiar desde `env.template.json`) o define `MANTIS_URL`/`MANTIS_API_KEY`
  como variables de entorno."

---

# Modo individual: fetch de issue

1. Extraer IssueId del mensaje (número tras `#`, ej: `Ingenieros.sln#1234` → `1234`)
2. Resolver credenciales (Paso 1)
3. Llamar API:
   ```powershell
   $headers = @{ Authorization = $key }
   $uri = "$($url.TrimEnd('/'))/issues/$IssueId"
   $r = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get -ErrorAction Stop
   $r | ConvertTo-Json -Depth 10
   ```
   ⛔ Si falla: mostrar error exacto y preguntar si continuar con descripción manual.

4. Extraer de `issues[0]`:
   - `summary`, `description`, `project.name`, `category.name`
   - `status.label`, `priority.label`, `severity.label`
   - `reporter.real_name`, `handler.real_name`
   - `steps_to_reproduce` (si existe)
   - `notes[0..2]` → campo `text.body`

5. Emitir bloque [MANTIS] y continuar al planner:

```
**[MANTIS #<id>]**
Resumen: <summary>
Proyecto: <project.name>
Categoría: <category.name>
Estado: <status.label> | Prioridad: <priority.label> | Severidad: <severity.label>
Reportado por: <reporter.real_name> → Asignado a: <handler.real_name | "sin asignar">
Descripción: <description>
Pasos: <steps_to_reproduce | "—">
Notas: <primera nota text.body | "—">
```

---

# Modo lista: issues por proyecto

1. Extraer del mensaje:
   - `$ProjectId` — ID numérico interno de Mantis (NO el número de contrato 60xxxx)
     - Si el usuario da un nombre o número de contrato → buscar el ID real:
       ```powershell
       $headers = @{ Authorization = $key }
       $r = Invoke-RestMethod -Uri "$($url.TrimEnd('/'))/projects" -Headers $headers -Method Get -ErrorAction Stop
       $r.projects | Select-Object id, name | Format-Table -AutoSize
       ```
       Mostrar la tabla y preguntar al usuario qué ID usar, o inferir por coincidencia de nombre.
   - `$StatusFilter` — estado pedido en español:
     - "confirmadas" → "confirmada"
     - "nuevas" → "nueva"
     - "asignadas" → "asignada"
     - "resueltas" → "resuelta"
     - "cerradas" → "cerrada"
     - Si no se especifica → listar todos los estados

2. Resolver credenciales (Paso 1)

3. Llamar API y filtrar:
   ```powershell
   $headers = @{ Authorization = $key }
   $uri = "$($url.TrimEnd('/'))/issues?project_id=$ProjectId&page_size=100"
   $r = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get -ErrorAction Stop
   $issues = $r.issues
   if ($StatusFilter) {
       $issues = $issues | Where-Object { $_.status.label -eq $StatusFilter }
   }
   $issues | Select-Object id, summary,
       @{n='estado';e={$_.status.label}},
       @{n='prioridad';e={$_.priority.label}},
       @{n='asignado';e={if($_.handler.real_name){$_.handler.real_name}else{'sin asignar'}}},
       @{n='fecha';e={([datetime]$_.created_at).ToString('yyyy-MM-dd')}} | ConvertTo-Json
   ```
   ⛔ 401 → API key incorrecta. 404 → proyecto no encontrado. Vacío → informar "Sin issues para ese filtro."

4. Emitir tabla markdown:

```
**[MANTIS — Proyecto <nombre> (ID:<ProjectId>) | Estado: <StatusFilter|"todos">]**

| ID | Resumen | Estado | Prioridad | Asignado | Fecha |
|----|---------|--------|-----------|----------|-------|
| #NNN | ... | confirmada | inmediata | David G. | 2026-07-06 |

Total: N issues
```

5. NO continuar al pipeline. La consulta está completa.

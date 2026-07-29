name: orchestrator-rename

# Rol

Renombrador masivo de símbolos para proyectos ScacsWeb.
Localiza todas las referencias a un símbolo y las renombra de forma consistente.

⚠️ **Modifica código.** Requiere confirmación explícita antes de tocar ningún fichero.

# Objetivo

Dado un símbolo (clase, método, propiedad, constante, interfaz) y su nuevo nombre,
localizar todas las ocurrencias en el codebase y renombrarlas en bloque.

Garantiza:
- No quedan referencias rotas al nombre antiguo en el código C# y .aspx
- El nuevo nombre sigue las convenciones ScacsWeb (PascalCase para tipos/métodos, camelCase para vars)
- Se compila sin errores tras el cambio

# Contexto de ejecución

Invocación directa via `/orchestrator-rename`. No forma parte del pipeline.

# Input esperado

Formato: `/orchestrator-rename <sln_path> <nombre-actual> <nuevo-nombre>`
- `nombre-actual` — símbolo exacto tal como está en el código (p.ej. `ObtenerCliente`, `ECCLIENTES_v2`)
- `nuevo-nombre` — nombre destino (p.ej. `GetCliente`, `ECCLIENTES`)
- `sln_path` — opcional, se infiere del workspace

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. `mcp__orchestrator-workspace__find_symbol(workspace, nombre-actual)` → definición exacta (tipo, fichero, línea)
3. `mcp__orchestrator-workspace__search_code(workspace, nombre-actual)` → todas las referencias
4. Clasificar referencias:
   - Definición del símbolo (clase, método, propiedad)
   - Usos en lógica de negocio (.cs)
   - Usos en code-behind (.aspx.cs)
   - Referencias en .aspx (id, runat, control)
   - Otros (tests, config, comentarios)
5. Calcular impacto: N ficheros × M ocurrencias
6. ⛔ GATE OBLIGATORIO — mostrar resumen y pedir confirmación:
   ```
   Renombrar '<nombre-actual>' → '<nuevo-nombre>'
   Afecta N ficheros con M referencias en total.
   ¿Confirmas? Responde "CONFIRMO" para aplicar.
   ```
   - "CONFIRMO" → continuar
   - Cualquier otra respuesta → abortar
7. Aplicar cambios fichero a fichero con Edit tool
8. `mcp__orchestrator-workspace__compile_check(sln_path)` → verificar compilación limpia
9. Si compile_check falla → reportar qué fichero causó el error y detener

# Reglas de seguridad

NUNCA renombrar sin gate:
- Nombres de columna o tabla BD (solo en strings SQL → marcar como "requiere revisión manual")
- Propiedades de serialización con `[JsonProperty]`, `[XmlElement]`, o similares → avisar
- Métodos de interfaz pública expuesta a clientes externos → avisar
- Nombres en ficheros de recursos (.resx) → listar aparte para revisión manual

Si el nuevo nombre ya existe en el scope → abortar con error antes del gate.

# Output — antes del gate

```
## Rename: <nombre-actual> → <nuevo-nombre>

Definición encontrada: AIS.EC.BR.EC.CL\ClienteDALC.cs:142 (método público)

Referencias (N ficheros, M ocurrencias):
  AIS.EC.BR.EC.CL\ClienteDALC.cs       : 1 ocurrencia (definición)
  AIS.PR.BR.PR.CL\PropuestaBR.cs       : 3 ocurrencias (llamadas)
  AIS.WEB.EC\FrmClientes.aspx.cs       : 2 ocurrencias (code-behind)
  AIS.EC.BR.EC.CL\ClienteDALC.Tests.cs : 4 ocurrencias (tests)

⚠️ Referencias en SQL strings (requieren revisión manual):
  AIS.PR.BR.PR.CL\PropuestaBR.cs:89 — contiene '<nombre-actual>' en string SQL

Renombrar '<nombre-actual>' → '<nuevo-nombre>'
Afecta 4 ficheros con 10 referencias en total.
¿Confirmas? Responde "CONFIRMO" para aplicar.
```

# Output — tras aplicar

```
✓ Rename completado: 4 ficheros modificados, 10 referencias actualizadas.
Compile check: PASS

Pendiente revisión manual:
- AIS.PR.BR.PR.CL\PropuestaBR.cs:89 — referencia en SQL string
```

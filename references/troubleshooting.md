# Troubleshooting

---

# ❌ Problemas comunes

---

## Build falla

Causas:

- referencias incorrectas
- tipos incompatibles

---

Solución:

- revisar validator
- corregir errores antes de build

---

## Runtime falla

Causas:

- DLL faltantes
- bin incompleto

---

Solución:

- copiar TODO el bin\Release
- evitar solo copiar .exe

---

## Error de BD

Causas:

- tipo incorrecto
- longitud incorrecta

---

Solución:

- validar con bd.md
- usar CHAR_LENGTH en Oracle

---

## Tabla nueva no aparece en ALL_TABLES/ALL_OBJECTS (Oracle)

Causas:

- dictionary cache de la sesión/pool no refrescado tras un CREATE TABLE reciente
- ALL_TABLES/ALL_OBJECTS/ALL_TAB_COLUMNS quedan desactualizadas mientras la sesión persiste, aunque la tabla ya sea consultable

---

Solución:

- no repetir la consulta a vistas catálogo en bucle (máx 1 intento)
- confirmar con SELECT directo a la tabla (`SELECT * FROM <TABLA> WHERE ROWNUM=1`) — funciona aunque el catálogo no la vea
- tratar `sync_model_tables`/`get_table_schema` como autoritativos; caer a SELECT directo solo si niegan la existencia de una tabla que el usuario confirma que existe

---

## Hook falla silenciosamente / caracteres corruptos en mensajes (PS5.1)

Síntoma: hook termina sin output útil, o mensajes de error con caracteres como `â€"` o `Ã³` en lugar de `—` o `ó`.

Causa: Windows PowerShell 5.1 (intérprete de producción) decodifica archivos `.ps1` sin BOM usando la codepage ANSI del sistema. Caracteres UTF-8 multibyte (á, é, ó, ñ, …) se malinterpretan, cerrando literales de string prematuramente y causando fallos de parse o mensajes basura.

Solución: todos los `.ps1` deben tener UTF-8 con BOM (`EF BB BF` como primeros 3 bytes). Verificar con:

```powershell
$f = "hooks\mi-hook.ps1"
[System.IO.File]::ReadAllBytes($f)[0..2] -join ',' # debe dar 239,187,191
```

Fix automático (todos los hooks del plugin):

```powershell
$BOM = [byte[]](0xEF,0xBB,0xBF)
Get-ChildItem "hooks\*.ps1" | ForEach-Object {
    $raw = [System.IO.File]::ReadAllBytes($_.FullName)
    if ($raw[0..2] -ne [byte[]](0xEF,0xBB,0xBF)) {
        [System.IO.File]::WriteAllBytes($_.FullName, $BOM + $raw)
    }
}
```

---

## MCP `orchestrator-workspace` no conecta / tools no responden

Síntoma: las tools `mcp__orchestrator-workspace__*` no aparecen, o cuelgan hasta timeout.

Causa: desde v1.16.0 el MCP se sirve por HTTP en `127.0.0.1:7337` mediante un daemon
residente que arranca `hooks/mcp-serve.ps1` en `SessionStart`. Si el daemon no está
levantado, no hay conexión.

Solución:

- Reiniciar Claude Code (el hook relanza el daemon; Claude Code reintenta la conexión
  HTTP 3× + backoff). En la primera vez tras actualizar puede hacer falta un 2º reinicio.
- Comprobar el daemon: `Test-NetConnection 127.0.0.1 -Port 7337 -InformationLevel Quiet`
  (debe dar `True`).
- Relanzar a mano: `pwsh -File $SKILL_DIR\hooks\mcp-serve.ps1 -Force`.
- Revisar `%LOCALAPPDATA%\orchestrator-workspace\server.err.log`.
- Puerto 7337 ocupado por otro proceso: definir `$env:ORCH_MCP_PORT` a otro puerto y
  cambiar el mismo puerto en `.mcp.json` (`url`).
- Sin intérprete Python: instalar Python 3.11+ o definir `$env:ORCH_MCP_PYTHON` con la
  ruta a `pythonw.exe` / `python.exe`.
- Daemon colgado: matarlo y dejar que el hook lo relance —
  `Get-NetTCPConnection -LocalPort 7337 -State Listen | %{ Stop-Process -Id $_.OwningProcess -Force }`.

---

## NullReferenceException

Causas:

- falta de validación

---

Solución:

- añadir null checks
- validar inputs

---

## Resultado incorrecto

Causas:

- lógica incorrecta
- validación incompleta

---

Solución:

- revisar analyzer
- validar flujo principal

---

# ⚠️ Reglas clave

- nunca ignorar errores del validator
- no forzar build con errores
- no confiar en datos sin validar
- no repetir consultas de confirmación (BD o tools) ya respondidas por el usuario o por una llamada previa
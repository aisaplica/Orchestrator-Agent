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
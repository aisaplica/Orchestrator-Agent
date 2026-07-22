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
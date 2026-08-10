# Reglas de Base de Datos

---

# 🧠 Motores soportados

- SQL Server
- Oracle

---

# ⚙️ Configuración

Leer:

docs/XMLConfig.xml

---

# 🟡 SQL Server

Catálogo:

INFORMATION_SCHEMA.COLUMNS

---

## Longitud

CHARACTER_MAXIMUM_LENGTH

---

# 🟣 Oracle

Catálogo:

ALL_TAB_COLUMNS

---

## Longitud

CHAR_LENGTH ✅

---

## VARCHAR2 en DDL (CRÍTICO)

En scripts CREATE TABLE y ALTER TABLE, todos los campos VARCHAR2 deben declararse con semántica de caracteres:

```sql
-- ✅ Correcto
OGEMPRESA VARCHAR2(6 CHAR)
CLNOMBRE  VARCHAR2(80 CHAR)

-- ❌ Incorrecto
OGEMPRESA VARCHAR2(6)
CLNOMBRE  VARCHAR2(80)
```

Sin `CHAR`, Oracle usa semántica de bytes por defecto. Con caracteres multibyte (UTF-8) un VARCHAR2(6) puede truncar strings de 6 caracteres. Especificar `CHAR` garantiza que el tamaño es en caracteres, igual que el diseño lógico.

---

# 🚫 Prohibido

- usar DATA_LENGTH
- asumir equivalencias entre motores
- omitir `CHAR` en VARCHAR2 de Oracle (CREATE TABLE / ALTER TABLE)

---

## visible:false (Oracle)

Algunas tablas del modelo pueden tener `"visible": false`. Significa que la tabla existe en el modelo pero no está disponible en `ALL_TABLES`/`ALL_TAB_COLUMNS` con las credenciales actuales (grants insuficientes, sinónimo roto, o tabla eliminada).

Comportamiento de las herramientas MCP:
- `sync_from_db` y `sync_indexes` **preservan** la tabla sin modificarla (no la eliminan del modelo)
- `get_table_schema` devuelve el schema del modelo e indica `visible: false`
- `compare_model_tables` omite la tabla del drift

Para resolver: verificar `GRANT SELECT ON <tabla> TO <usuario>` en Oracle. Si la tabla ya no existe, eliminarla manualmente del modelo.

---

# 🔍 Validaciones obligatorias

---

## Tipos

- verificar compatibilidad con C#
- evitar conversiones implícitas

---

## Longitud

- validar tamaño vs código
- evitar truncamientos

---

## Nullabilidad

- validar campos NULL
- controlar en código

---

# ⚠️ Problemas comunes

- string más largo que BD → truncamiento
- null no controlado → excepción
- tipo incorrecto → fallo en runtime
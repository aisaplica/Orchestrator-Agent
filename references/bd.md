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
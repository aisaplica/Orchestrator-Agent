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

---

# 🔁 Scripts de incidencias — Idempotencia obligatoria

Todo script DML o DDL propuesto para resolver una incidencia debe poder ejecutarse más de una vez sin fallo ni efecto secundario.

## DML

**Tabla de configuración/parámetros sin hijos (FK entrantes):**

```sql
-- DELETE + INSERT — más legible, válido cuando no hay FK apuntando a la fila
DELETE FROM parametros WHERE clave = 'TIMEOUT_SESION';
INSERT INTO parametros (clave, valor, fecha_mod)
VALUES ('TIMEOUT_SESION', '30', SYSDATE);
COMMIT;
```

**Tabla con relaciones (FK entrantes desde otras tablas):**

```sql
-- MERGE — cubre insert+update, no rompe FK
MERGE INTO parametros p
USING (SELECT 'TIMEOUT_SESION' AS clave, '30' AS valor FROM dual) src
ON (p.clave = src.clave)
WHEN MATCHED THEN
    UPDATE SET p.valor = src.valor, p.fecha_mod = SYSDATE
WHEN NOT MATCHED THEN
    INSERT (clave, valor, fecha_mod) VALUES (src.clave, src.valor, SYSDATE);
COMMIT;
```

```sql
-- INSERT WHERE NOT EXISTS — alternativa si solo hay inserción
INSERT INTO roles (id_rol, descripcion, activo)
SELECT 99, 'AUDITOR_EXTERNO', 1
FROM dual
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE id_rol = 99);
COMMIT;
```

**Regla de selección:**

| Situación | Patrón |
|-----------|--------|
| Tabla config/parámetros, sin FK entrantes | DELETE + INSERT |
| Tabla con FK entrantes desde otras tablas | MERGE o INSERT WHERE NOT EXISTS |
| Solo actualizar si difiere | UPDATE ... WHERE valor != 'nuevo' |

**Nunca:** INSERT pelado sin guarda → `ORA-00001` en segunda ejecución.

## DDL (Oracle)

```sql
-- Añadir columna solo si no existe
DECLARE
  v_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM ALL_TAB_COLUMNS
  WHERE TABLE_NAME = 'SIPARAMETROS' AND COLUMN_NAME = 'NUEVA_COL';
  IF v_count = 0 THEN
    EXECUTE IMMEDIATE 'ALTER TABLE SIPARAMETROS ADD (NUEVA_COL VARCHAR2(10 CHAR))';
  END IF;
END;
/
```

## DDL (SQL Server)

```sql
-- Añadir columna solo si no existe
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'SIPARAMETROS' AND COLUMN_NAME = 'NUEVA_COL'
)
    ALTER TABLE SIPARAMETROS ADD NUEVA_COL NVARCHAR(10) NULL;
```

## Mantis

Si la incidencia tiene número Mantis asociado: recordar al usuario registrar el script final como **nota privada** en el issue antes de cerrar.
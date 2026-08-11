-- =============================================================================
-- SCRIPT INCIDENCIA
-- =============================================================================
-- Mantis   : #NNNN
-- Fecha    : YYYY-MM-DD
-- Autor    : <usuario>
-- Motor    : Oracle 19c | SQL Server
-- Descripción:
--   <Descripción breve del cambio>
--
-- IDEMPOTENCIA:
--   Este script puede ejecutarse más de una vez sin fallo ni efecto secundario.
--   Patrón usado: DELETE+INSERT | MERGE | INSERT WHERE NOT EXISTS | DDL con guarda
--
-- ROLLBACK:
--   <Instrucción para deshacer el cambio, o "N/A - no reversible">
-- =============================================================================

-- ► SECCIÓN 1: Verificación previa (opcional)
-- Comprobar estado actual antes de aplicar el cambio.
/*
SELECT <columnas_relevantes>
FROM   <tabla>
WHERE  <condicion>;
*/

-- ► SECCIÓN 2: Script principal (idempotente)
-- [RELLENAR — seguir política references/bd.md "Scripts de incidencias"]

-- Ejemplo DELETE+INSERT (tabla config sin FK entrantes):
/*
DELETE FROM <tabla> WHERE <pk_col> = <valor>;
INSERT INTO <tabla> (<col1>, <col2>, <col3>)
VALUES (<val1>, <val2>, SYSDATE);
COMMIT;
*/

-- Ejemplo MERGE (tabla con FK entrantes):
/*
MERGE INTO <tabla> t
USING (SELECT <val1> AS <col1>, <val2> AS <col2> FROM dual) src
ON (t.<pk_col> = src.<col1>)
WHEN MATCHED THEN
    UPDATE SET t.<col2> = src.<col2>
WHEN NOT MATCHED THEN
    INSERT (<col1>, <col2>) VALUES (src.<col1>, src.<col2>);
COMMIT;
*/

-- Ejemplo DDL Oracle (con guarda):
/*
DECLARE
  v_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM ALL_TAB_COLUMNS
  WHERE TABLE_NAME = '<TABLA>' AND COLUMN_NAME = '<COLUMNA>';
  IF v_count = 0 THEN
    EXECUTE IMMEDIATE 'ALTER TABLE <TABLA> ADD (<COLUMNA> VARCHAR2(10 CHAR))';
  END IF;
END;
/
*/

-- Ejemplo DDL SQL Server (con guarda):
/*
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '<tabla>' AND COLUMN_NAME = '<columna>'
)
    ALTER TABLE <tabla> ADD <columna> NVARCHAR(10) NULL;
*/

-- ► SECCIÓN 3: Verificación posterior
-- Confirmar que el cambio se aplicó correctamente.
/*
SELECT <columnas_relevantes>
FROM   <tabla>
WHERE  <condicion>;
*/

-- =============================================================================
-- MANTIS: Copiar este script completo en nota privada del issue #NNNN
-- =============================================================================

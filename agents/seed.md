name: orchestrator-seed

# Rol

Generador de datos de prueba para proyectos ScacsWeb.
Genera INSERT sintéticos respetando tipos, longitudes, nullabilidad y claves foráneas del modelo BD.

**Solo generación.** No ejecuta nada contra la BD. Genera un fichero .sql para revisión manual.

# Objetivo

Dado un nombre de tabla y opcionalmente un número de filas (N, por defecto 10), generar
N sentencias INSERT sintéticas con datos realistas que respetan las restricciones del esquema:
- tipos y longitudes de columna
- columnas NOT NULL tienen siempre valor
- columnas nullable a veces son NULL (simulando datos reales)
- claves primarias autoincrementales no se incluyen si son autonuméricas
- claves foráneas usan IDs de ejemplo (1, 2, 3...)

# Contexto de ejecución

Invocación directa via `/orchestrator-seed`. No forma parte del pipeline.

# Input esperado

- `tabla` — nombre exacto de la tabla (ECCLIENTES, PRPROPUESTAS, etc.)
- `N` — número de filas a generar (por defecto 10, máximo 100)
- `sln_path` — opcional, para resolver workspace

# Proceso

1. Resolver workspace (per SKILL.md "Workspace y Rutas")
2. Obtener esquema: `mcp__orchestrator-workspace__get_table_schema(workspace, [tabla])`
3. Si la tabla no está en el modelo: informar y terminar
4. Para cada columna analizar:
   - Tipo → función de generación apropiada (ver tabla de generadores)
   - Longitud → respetar el máximo
   - Nullable → 20% de probabilidad de NULL si la columna lo permite
   - PK → usar secuencia 1000, 1001, ... o excluir si es autonumérica
   - FK → usar valores 1, 2, 3 como referencias de prueba
5. Generar N sentencias INSERT
6. Escribir en `$SKILL_DIR\executions\seed_<tabla>_<timestamp>.sql` vía Write tool
7. Mostrar las primeras 3 sentencias en el chat como preview

# Tabla de generadores por tipo

| Tipo Oracle | Generador |
|-------------|-----------|
| VARCHAR2(N) | Texto aleatorio de longitud min(N, 20): nombres, texto, códigos |
| NUMBER(10) | Entero aleatorio 1-9999 |
| NUMBER(15,2) | Decimal 0.01-99999.99 |
| DATE | Fecha aleatoria últimos 2 años en formato `TO_DATE('YYYY-MM-DD','YYYY-MM-DD')` |
| TIMESTAMP | `SYSTIMESTAMP` |
| CHAR(1) | 'S' o 'N' |
| CLOB | `EMPTY_CLOB()` |

| Tipo SQL Server | Generador |
|----------------|-----------|
| VARCHAR(N) | Texto aleatorio min(N, 20) |
| INT / BIGINT | Entero 1-9999 |
| DECIMAL(p,s) | Decimal apropiado |
| DATETIME | Fecha últimos 2 años |
| BIT | 1 o 0 |
| NVARCHAR(N) | Texto unicode min(N, 20) |

# Estrategia para columnas de nombre conocido

Aplicar valores semánticos cuando el nombre da pistas:
- `*NIF*`, `*DNI*` → `'12345678A'`, `'87654321B'`, ...
- `*NOMBRE*` → `'CLIENTE TEST 1'`, `'CLIENTE TEST 2'`, ...
- `*IMPORTE*`, `*PRECIO*` → valores entre 100.00 y 10000.00
- `*FECHA*` → fechas en rango últimos 12 meses
- `*ESTADO*`, `*TIPO*` → valores cortos: `'A'`, `'B'`, `'C'`
- `*EMAIL*` → `'test1@example.com'`, `'test2@example.com'`
- `*CODIGO*` → `'COD001'`, `'COD002'`

# Output

```
## Seed: ECCLIENTES — 10 filas
Fichero generado: executions/seed_ECCLIENTES_20260728.sql

Preview (3 de 10):
```sql
INSERT INTO ECCLIENTES (IDCLIENTE, DNNIF, NOMBRE, FECALTA, IMPORTE)
VALUES (1001, '12345678A', 'CLIENTE TEST 1', TO_DATE('2025-03-15','YYYY-MM-DD'), 4500.00);

INSERT INTO ECCLIENTES (IDCLIENTE, DNNIF, NOMBRE, FECALTA, IMPORTE)
VALUES (1002, '87654321B', 'CLIENTE TEST 2', TO_DATE('2024-11-20','YYYY-MM-DD'), NULL);

INSERT INTO ECCLIENTES (IDCLIENTE, DNNIF, NOMBRE, FECALTA, IMPORTE)
VALUES (1003, '11223344C', 'CLIENTE TEST 3', TO_DATE('2026-01-08','YYYY-MM-DD'), 750.50);
```

Ver fichero completo en: executions/seed_ECCLIENTES_20260728.sql
⚠️ Revisar antes de ejecutar — NO ejecuta automáticamente contra la BD.
```

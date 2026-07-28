name: orchestrator-idiomas-standalone

> MCP: `references/mcp.md`
> Hooks: `references/hooks.md`

# Rol

Generador standalone de scripts de idiomas para controles AIS Online.
Sin modificar código fuente. Sin ejecutar pipeline.

# Objetivo

Generar los INSERTs SQL para `SIIdioma` y `SIControles` para controles AIS existentes
en páginas .aspx de una solución Online — útil para controles ya desplegados que
aún no tienen sus entradas de idioma registradas.

# Contexto de ejecución

Invocación directa. Solo generación de SQL.

⛔ Solo tipo Online — rechazar si la solución es Batch
⛔ No modificar código .cs ni .aspx
⛔ No ejecutar los scripts — solo generarlos para que el usuario los ejecute

# Proceso

1. Resolver solución → confirmar que es tipo Online
   - Si es Batch → informar: "Scripts de idiomas solo aplican a soluciones Online"
2. Extraer scope del .sln
3. Leer `docs/agentic_manual/tecnica/03_CAPAS_IDIOMAS_NOMENCLATURA.md`
4. Preguntar al usuario (si no lo especificó):
   - ¿Para qué controles o páginas .aspx? O "todos" para escanear todo el scope
   - ¿Idiomas activos? (por defecto: `ESP` — confirmar si el proyecto tiene otros)
5. Preferente: `mcp__orchestrator-workspace__scan_aspx(sln_path)` → JSON con controles AIS y textos.
   Fallback: `hooks/scan-aspx.ps1 -SlnPath <sln_path>`.
   ⚠ `scan_aspx` no es exhaustivo — no detecta todos los tipos de control AIS. Contrastar con los `.aspx` reales (ver "Gate scripts-idiomas" en `core.md`).
   Escanear ficheros .aspx del scope según lo pedido
6. Identificar controles AIS siguiendo los patrones del documento del paso 3
7. Para cada control identificado:
   - Asignar IDTexto libre: buscar el primer ID disponible a partir de 3000.
     Query a ejecutar via MCP o indicar al usuario:
     `SELECT MIN(r1.IDTexto + 1) FROM SIIdioma r1 WHERE r1.IDTexto >= 3000 AND NOT EXISTS (SELECT 1 FROM SIIdioma r2 WHERE r2.IDTexto = r1.IDTexto + 1)`
     Si no hay filas con IDTexto >= 3000 → usar 3000 como primer ID.
     Incrementar secuencialmente desde ese primer libre para los sucesivos.
   - Generar INSERT SIIdioma por cada idioma activo
   - Generar INSERT SIControles vinculando control ↔ IDTexto
8. Emitir scripts SQL completos y escribirlos a `C:\AIS\<proyecto>\scripts\<proyecto>-idiomas-<fecha>-<solucion>.sql` (ver `core.md` "Scripts SQL generados")

---

# Reglas de generación

- Un IDTexto por texto lógico (no por idioma)
- Una fila SIIdioma por idioma activo por cada IDTexto
- Una fila SIControles por control que usa ese texto
- **Mensajes de error** (`Idm.Texto(coerr.eXXXX, ...)`): generar SOLO INSERT `SIIdioma` — se resuelven directo por IDTexto. ⛔ NO generar `SIControles` para ellos. Controles con `LabelText`/`Text`/`GroupingText`/`Titulo`: SIIdioma + SIControles.
- ⛔ Nunca elegir IDTexto libre buscando huecos en `coerr.cs` — no refleja el estado real de SIIdioma (hay IDTexto sin constante). Usar siempre la query del paso 7 contra SIIdioma (vía `db_query`).
- Casing de `CTFORM`: inconsistente en filas existentes (el match en runtime usa `UPPER()`). Consultar el casing ya usado por esa página antes de insertar, por consistencia.
- Si el usuario no proporciona texto traducido → placeholder `[TEXTO_ESP]`, `[TEXTO_POR]` etc.
- No duplicar INSERTs para controles que ya tienen entrada documentada
- **Valores de CTTIPO** según tipo de control detectado:
  - `1` = AISBusinessField
  - `2` = AISGridView y todos sus tipos de columna
  - `3` = Título de pantalla (AD07011MDD)
  - `5` = AISTabPage

---

# Output

```sql
-- ============================================================
-- Scripts de idiomas: <Solución>
-- Generado: <fecha>
-- Idiomas: ESP
-- Controles procesados: N
-- IMPORTANTE: Verificar rango de IDTexto antes de ejecutar
-- IMPORTANTE: Ejecutar en BD antes de desplegar la solución
-- ============================================================

-- SIIdioma — textos por idioma
INSERT INTO SIIdioma (IDTexto, IDIdioma, IDDESCRIPCION) VALUES (3000, 'ESP', 'Nombre del cliente');
INSERT INTO SIIdioma (IDTexto, IDIdioma, IDDESCRIPCION) VALUES (3001, 'ESP', 'Fecha de cobro');

-- SIControles — vinculación control → texto
INSERT INTO SIControles (CTFORM, CTMAPEO, CTTIPO, CTTEXTO) VALUES ('frmClientes', 'lblNombreCliente', 1, 3000);
INSERT INTO SIControles (CTFORM, CTMAPEO, CTTIPO, CTTEXTO) VALUES ('frmClientes', 'lblFechaCobro', 1, 3001);

-- Total: N INSERTs SIIdioma | M INSERTs SIControles
```

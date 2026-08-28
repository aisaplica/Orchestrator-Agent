# Convenciones SCACS Web

.NET Framework 4.0 / C# 7.3 / ASP.NET WebForms

---

# Naming

| Elemento | Estilo | Ejemplo |
|----------|--------|---------|
| Clases / metodos / propiedades | PascalCase | `ClienteManager`, `ProcesarSolicitud` |
| Variables locales | camelCase | `nombreCompleto`, `datosCliente` |
| Campos privados | `_camelCase` | `_nombreUsuario`, `_connector` |
| Constantes | UPPER_CASE | `FORMATO_FECHA`, `TIMEOUT_CONEXION` |
| Controles | prefijo tipo + descripcion | `txtNombre`, `grdSolicitudes`, `btnGuardar` |

Prefijos de modulo en namespaces y nombres de clase:

| Prefijo | Dominio |
|---------|---------|
| BR | Negocio (base) |
| UI | Presentacion |
| AC | Actas |
| ADM | Administracion (CA=Catalogos, PC=Params config, PD=Params decision, SG=Seguimiento, SS=Seguridad, WF=Workflow) |
| AG | Agenda |
| AL | Alertas |
| CM | Centro de Mensajes |
| EC | Expediente de Cliente (AN=Analisis, CE=CIRBE, CL=General, ID=Datos identificativos, IN=Inicializacion, RN=Resumen) |
| GI | Generador de Informes |
| NT | Notas y documentos |
| PR | Propuestas Particulares (ID=Captura, AN=Analisis/Sancion, TR=Tramitacion) |
| PG | Propuestas Generales (FB=Financiacion Base, FN=Financiacion, GA=Garantias, IN=Intervinientes) |
| SG | Seguimiento |

> Lista completa con DLL -> `docs/scacs/05-conceptos-de-negocio/module-prefixes.md`

---

# C# - Reglas fundamentales

- **Nunca `var`** — tipos explicitos siempre:
  ```csharp
  DataSet datos = new DataSet();   // correcto
  var datos = new DataSet();       // NO
  ```

- **Nunca `new []`** — tipo completo:
  ```csharp
  new string[] { ... }   // correcto
  new [] { ... }         // NO
  ```

- **Array init inline** — no asignacion en lineas separadas:
  ```csharp
  // correcto
  SqlParameter[] argParm = new SqlParameter[2] {
      new SqlParameter("@id", SqlDbType.VarChar, 20) { Value = id },
      new SqlParameter("@emp", SqlDbType.VarChar, 6)  { Value = emp }
  };
  ```

- **`static`** si el metodo no usa campos ni propiedades de instancia

- **`const`** para literales de solo lectura:
  ```csharp
  private const string MENSAJE_ERROR = "Error inesperado.";   // correcto
  private string mensajeError = "Error inesperado.";          // NO
  ```

- Indentacion: 4 espacios, nunca tabs

- Usings base siempre presentes:
  ```csharp
  using System;
  using System.Collections.Generic;
  using System.Data;
  ```
- Usings de módulo — adaptar según el módulo activo (no usar los de PR en EC, AC, ADM, etc.):
  ```csharp
  // Módulo PR (Propuestas Particulares):
  using AIS.PR.SF;
  using AIS.PR.UI;
  using AIS.PR.UI.Controls;
  // Otros módulos: AIS.EC.*, AIS.AC.*, AIS.ADM.*, etc.
  ```

---

# Colecciones y acceso seguro

- **Validar `Count > 0`** antes de acceder por indice:
  ```csharp
  if (ds.Tables["T"].Rows.Count > 0)
  {
      string val = ds.Tables["T"].Rows[0]["Col"].ToString();
  }
  ```

- **`TryGetValue`** para diccionarios:
  ```csharp
  string valor;
  if (diccionario.TryGetValue("clave", out valor)) { ... }
  ```

- **`TryParse`** para conversiones:
  ```csharp
  int numero;
  if (int.TryParse(texto, out numero)) { ... }
  ```

- LINQ sobre DataTable: `.Rows.Cast<DataRow>()` (no `.AsEnumerable()`)

- Preferir metodos nativos sobre LINQ:
  `DataTable.Select()`, `DataTable.Compute()`, `List.Find()`, `List.FindAll()`, `Array.Find()`

---

# Validaciones y excepciones

Acumular en `ValidationBRException` y lanzar en un solo `throw`:
```csharp
ValidationBRException valEx = new ValidationBRException("EX021");

if (string.IsNullOrEmpty(nombre))
    valEx.ValidationBRExceptionList.Add(
        new ValidationBRException.ValidationBRItemException("SRV02", "", MessageIconEnum.Information));

if (string.IsNullOrEmpty(codigo))
    valEx.ValidationBRExceptionList.Add(
        new ValidationBRException.ValidationBRItemException("SRV03", "", MessageIconEnum.Information));

if (valEx.ValidationBRExceptionList.Count > 0) throw valEx;
```

Tipos de excepcion:

| Tipo | Cuando usar |
|------|-------------|
| `ValidationBRException` | Validaciones de negocio — hace rollback automatico |
| `PostValidationBRException` | Validaciones sin rollback |
| `GraveException` | Error critico de aplicacion |
| `AvisoException` | Notificacion al usuario por pantalla |

Patron try/catch:
```csharp
try
{
    // operaciones
}
catch (ValidationBRException ex)
{
    this.LogAviso(nameof(NombreMetodo), ex.ToString(), this.ToString());
    throw;
}
catch (Exception ex)
{
    this.LogFatal(nameof(NombreMetodo), ex.ToString(), this.ToString());
    throw new GraveException("EX999", ex.Message, ex);
}
```

---

# SQL (SQL Server)

- Fechas: `DateTime2`, no `DateTime`
  ```sql
  DECLARE @Fecha DATETIME2 = GETDATE();
  ```

- Conversiones: `TRY_CAST` / `TRY_CONVERT`, no `CAST` / `CONVERT`
  ```sql
  SELECT TRY_CAST(Valor AS DECIMAL(18,2)) AS Importe
  ```

- Upsert: `MERGE` sobre INSERT + UPDATE separados

- IDs: `NEXT VALUE FOR dbo.SQ_TABLA`, nunca `MAX()+1`

---

# Controles AIS

| Control | Uso |
|---------|-----|
| `AISBusinessField` | Inputs con validacion automatica |
| `AISGridView` | Grids con soporte completo |
| `AISCatalogo` | Listas desplegables de catalogo |
| `AISConfirmDialog` | Confirmaciones Si/No o Aceptar/Cancelar |
| `AISMessageDialog` | Mensajes al usuario |

No numeros magicos — usar `AIS.PR.SF.Constantes` o `AIS.PR.SF.CatalogoTipo`.

> Detalle de controles -> `docs/scacs/02-controles/`

---

# Codificación de archivos fuente (CRITICO)

Los fuentes legacy ScacsWeb (`.cs`, `.aspx`, `.ascx`, `.asax`, `.master`, `Web.config`) suelen estar en **Windows-1252 (ANSI) sin BOM**, no en UTF-8.

Las tools **Edit / Write de Claude Code escriben siempre UTF-8**. Aplicarlas sobre un archivo ANSI reescribe todo el fichero y **corrompe los acentos** (`á é í ó ú ñ ¿ ¡` → `Ã¡ Ã© ...`) en comentarios, strings y literales. No hay error de compilación — el fallo aparece en runtime o en pantalla (labels, mensajes, datos).

**Regla:**

1. Antes de editar un fuente, comprobar su codificación (BOM / heurística UTF-8 / ANSI).
2. Si es ANSI/1252 → **NO usar Edit ni Write**. Editar con:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "$SKILL_DIR\hooks\edit-ansi.ps1" -Path "<archivo>" -Search "<texto>" -Replace "<texto>" [-All] [-Regex]
   ```
   El hook detecta la codificación real y reescribe con la **misma** (sin añadir BOM).
3. Archivos nuevos creados por el pipeline (proyecto de tests, scripts SQL, etc.) → UTF-8 normal, sin problema.

Los `.ps1` del propio plugin son caso aparte: siempre UTF-8 **con** BOM (ver `references/troubleshooting.md`).

---

# Scope y buenas practicas

- Path trunk: derivado del workspace activo en Claude Code (carpeta hasta `\src\trunk\` inclusive; la raíz varía por máquina)
- No modificar codigo fuera del scope de la solucion activa
- Cambios minimos — no refactors innecesarios
- No logica de negocio en capa de presentacion
- No validaciones de negocio movidas a pantalla si deben permitir guardado parcial

# Instrucciones de Copilot - SCACS Web (.NET Framework 4 - C# 7.3)

Este proyecto es una aplicación web ASP.NET Web Forms desarrollada con .NET Framework 4.0 y C# 7.3. Sigue estas instrucciones específicas al generar código o responder preguntas.

## Configuración del Proyecto

**Framework:** .NET Framework 4.0
**Lenguaje:** C# 7.3
**Tecnología:** ASP.NET Web Forms
**Base de Datos:** SQL Server con ADO.NET y DataSets
**Controles:** Librería personalizada AIS

## Reglas Fundamentales de Codificación

### 1. Tipos de Datos Explícitos
- **NUNCA** usar `var`, siempre tipos explícitos
- **PREFERIR** usar inicialización de arrays con elementos y propiedades en línea cuando sea posible:
- Ejemplo correcto:
```csharp
SqlParameter[] argParm = new SqlParameter[2] {
    new SqlParameter("@idPropuesta", SqlDbType.VarChar, 20) { Value = propuesta },
    new SqlParameter("@empresarioConsumidor", SqlDbType.VarChar, 6) { Value = empresarioConsumidor }
};
```
- Ejemplo incorrecto:
```csharp
SqlParameter[] argParm = new SqlParameter[2];
argParm[0] = new SqlParameter("@idPropuesta", SqlDbType.VarChar, 20);
argParm[1] = new SqlParameter("@empresarioConsumidor", SqlDbType.VarChar, 6);
argParm[0].Value = propuesta;
argParm[1].Value = empresarioConsumidor;
```
- **NUNCA** usar `new []`, usar tipos completos: `new string[]`, `new int[]`
- Ejemplo correcto: `DataSet datos = new DataSet();`
- Ejemplo incorrecto: `var datos = new DataSet();`

### 2. Using Statements Obligatorios
Al generar código C#, siempre incluir los using necesarios:
```csharp
using System;
using System.Collections.Generic;
using System.Data;
using System.Web.UI;
using System.Web.UI.WebControls;
using AIS.PR.SF;
using AIS.PR.UI;
using AIS.PR.UI.Controls;
```

### 3. LINQ en DataTable
- **PREFERIR** `.Rows.Cast<DataRow>()` sobre `.AsEnumerable()`
- Ejemplo: `dataTable.Rows.Cast<DataRow>().Where(row => row.Field<bool>("Activo"))`

### 4. Métodos Nativos Preferidos
Preferir estos métodos sobre LINQ cuando sea posible:
- **DataTable**: `.Select()`, `.Compute()`
- **Array**: `Array.Find()`, `Array.Exists()`, `Array.ForEach()`
- **List**: `.Find()`, `.FindAll()`, `.Exists()`, `.RemoveAll()`

### 5. Validación de Acceso por Índice
**SIEMPRE** validar antes de acceder por índice:
```csharp
if (dsDatos.Tables["PERFILES"].Rows.Count > 0)
{
    string primerPerfil = dsDatos.Tables["PERFILES"].Rows[0]["Codigo"].ToString();
}
```

### 6. Acceso Seguro a Diccionarios y Conversiones
- **SIEMPRE** usar métodos TryGetValue para diccionarios:
```csharp
string valor;
if (diccionario.TryGetValue("clave", out valor))
{
    // Usar valor
}
```

- **SIEMPRE** usar métodos Try para conversiones:
```csharp
int numero;
if (int.TryParse(texto, out numero))
{
    // Usar numero
}

decimal importe;
if (decimal.TryParse(valor, out importe))
{
    // Usar importe
}
```

### 7. Validaciones Separadas
- Crear un mensaje de error para cada campo a validar
- Acumular todas las validaciones en un solo `throw`
- Ejemplo:
```csharp
ValidationBRException _ValBRException = new ValidationBRException("EX021");

if (string.IsNullOrEmpty(nombre))
    _ValBRException.ValidationBRExceptionList.Add(new ValidationBRException.ValidationBRItemException("SRV02", "", MessageIconEnum.Information));
```
Ver: [[validation-exceptions]], [[textos]]
### 8. Constantes y Números Mágicos
- **EVITAR** números mágicos
- Usar `AIS.PR.SF.Constantes` o `AIS.PR.SF.CatalogoTipo`
- Ejemplo: `if (estado == Constantes.ESTADO_ACTIVO)`

### 9. Constantes para Solo Lectura
- **SIEMPRE** declarar como `const` cualquier string, número o valor que solo se usará para lectura y no cambiará durante la ejecución.
- Ejemplo correcto:
```csharp
private const string MENSAJE_ERROR = "Ocurrió un error inesperado.";
private const int MAX_INTENTOS = 3;
```
- Ejemplo incorrecto:
```csharp
private string mensajeError = "Ocurrió un error inesperado."; // Solo lectura, debería ser const
```

### 10. Métodos Static
- **SIEMPRE** declarar un método como `static` si no depende de datos de instancia (no accede a campos ni propiedades de instancia).
- Ejemplo correcto:
```csharp
public static int Sumar(int a, int b)
{
    return a + b;
}
```
- Ejemplo incorrecto:
```csharp
public int Sumar(int a, int b)
{
    return a + b; // No usa datos de instancia, debería ser static
}
```

## Controles Personalizados AIS

### Controles de Diálogo
- **PREFERIR** `AISConfirmDialog` para decisiones Sí/No o Aceptar/Cancelar
- Alternativas: `AISDialog` manual o `AISMessageDialog.RegisterConfirmDialog`

### Controles de Entrada
- `AISBusinessField` para campos de entrada con validación automática
- `AISGridView` para grids con soporte completo
- `AISExcelGrid` para grids editables con soporte completo
- `AISCatalogo` para listas desplegables de catálogos

### Ejemplo de Configuración de Controles:
```csharp
protected void ConfigurarControles()
{
    this.txtNombreCliente.FieldDataType = FieldDataType.Text;
    this.txtNombreCliente.LabelText = "Nombre del Cliente";
    this.txtNombreCliente.ShowLabel = true;

    this.grdSolicitudes.AllowRowSelection = true;
    this.grdSolicitudes.AutomaticSort = true;
}
```

## Buenas Prácticas SQL Server

### 1. Tipos de Fecha
- **SIEMPRE** usar `DateTime2` en lugar de `DateTime`
```sql
DECLARE @FechaActual DATETIME2 = GETDATE();
```

### 2. Conversiones Seguras
- **SIEMPRE** usar `TRY_CAST`/`TRY_CONVERT` en lugar de `CAST`/`CONVERT`
```sql
SELECT TRY_CAST(Valor AS DECIMAL(18,2)) AS ImporteConvertido
```

### 3. MERGE sobre INSERT/UPDATE
- **PREFERIR** `MERGE` cuando se necesite insertar y actualizar

### 4. Secuenciales para IDs
- **NUNCA** usar `MAX()+1` para generar IDs
- **USAR** secuenciales: `NEXT VALUE FOR dbo.SQ_TABLA`

## Manejo de Excepciones

### Tipos de Excepciones del Proyecto:
- `ValidationBRException`: Validaciones de negocio con rollback
- `PostValidationBRException`: Validaciones sin rollback
- `GraveException`: Errores críticos de aplicación
- `AvisoException`: Notificaciones al usuario por pantalla

### Patrón de Try-Catch:
```csharp
try
{
    // Operaciones
}
catch (ValidationBRException ex)
{
    this.LogAviso(nameof(NombreDelMetodo), ex.ToString(), this.ToString());
    throw
}
catch (Exception ex)
{
    this.LogFatal(nameof(NombreDelMetodo), ex.ToString(), this.ToString());
    throw new GraveException("EX999", ex.Message, ex);
}
```

## Convenciones de Nomenclatura

- **Clases/Métodos/Propiedades**: PascalCase (`ClienteManager`, `ProcesarSolicitud`)
- **Variables locales**: camelCase (`nombreCompleto`, `datosCliente`)
- **Campos privados**: camelCase con underscore (`_nombreUsuario`, `_connector`)
- **Constantes**: UPPER_CASE (`FORMATO_FECHA`, `TIMEOUT_CONEXION`)
- **Controles**: Prefijo tipo + descripción (`txtNombre`, `grdSolicitudes`, `btnGuardar`)

## Arquitectura del Proyecto

### Capas:
1. **Presentación**: ASP.NET Web Forms con controles AIS
2. **Negocio**: C# desacoplado, accesible por reflexión/WebService
3. **Datos**: ADO.NET con DataSets, SQL Server

### Comunicación:
- Usar `AIS.PR.UI.ClientConnectorInterface` desde el proyecto Web hacia la capa de negocio
- Usar `AIS.PR.BR.BRConnector` dentro de la capa de negocio hacia otro proyecto de negocio
- Mantener datos en `FormData` durante la sesión, dentro del proyecto Web
- Usar `PageSessionContainer` para navegación entre formularios

## Instrucciones Específicas para Copilot

### Al Generar Código C#:
1. **SIEMPRE** incluir los `using` necesarios al inicio
2. **SIEMPRE** usar tipos de datos explícitos, nunca `var`
3. **SIEMPRE** agrupar validaciones y lanzarlas juntas
4. **EVITAR** espacios en blanco al final de las líneas
5. **USAR** indentación de 4 espacios, nunca tabs

### Al Generar SQL:
1. **USAR** `DateTime2` para fechas
2. **USAR** `TRY_CAST` para conversiones
3. **PREFERIR** `MERGE` sobre operaciones separadas
4. **USAR** secuenciales para generar IDs

### Al Sugerir Arquitectura:
1. **MANTENER** separación de capas estricta
2. **USAR** controles personalizados AIS cuando sea apropiado
3. **SEGUIR** patrones de la clase base de formularios
4. **IMPLEMENTAR** métodos obligatorios del framework

### Al Responder Preguntas:
1. **CONSIDERAR** las limitaciones de .NET Framework 4.0 y C# 7.3
2. **RECOMENDAR** soluciones específicas del framework AIS cuando sea relevante
3. **MENCIONAR** validaciones de seguridad y acceso por índice
4. **INCLUIR** ejemplos de uso de controles personalizados
5. **SEPARAR** en pasos o entregar tablas cuando sea posible
6. **PONER** resumen o conclusiones al principio
7. **EVITAR** información redundante

### Contexto del Framework:
- Este es un proyecto empresarial con arquitectura madura
- Los controles AIS son específicos del proyecto y muy importantes
- La seguridad y validación de datos es crítica
- El rendimiento es importante debido a grandes volúmenes de datos
- La consistencia de código es fundamental para mantenimiento

### Formato de Respuestas:
- **Resumen ejecutivo** al inicio
- **Evitar redundancia** en explicaciones
- **Usar tablas** para comparaciones o listas
- **Separar en pasos** los procedimientos complejos
- **Balancear eficiencia y legibilidad** en código

**IMPORTANTE**: Siempre considera que este proyecto usa .NET Framework 4.0 (no .NET Core/.NET 5+) y C# 7.3, por lo que algunas características modernas no están disponibles.


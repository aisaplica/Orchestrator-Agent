---
title: SCACS Web - Textos e idioma
tags:
  - arquitectura
---
La aplicación es multi-idioma, y los textos de interfaz, mensajes de error y validaciones deben estar parametrizados en base de datos.

## Tabla de textos
La tabla `SIIdioma` almacena todos los textos. Contiene:
- Código de texto (`IDTexto`)
- Código de idioma (`IDIdioma`)
- Texto (`IDDESCRIPCION`)

## Controles
La tabla `SIControles` relaciona los controles de una pantalla con los textos.

Columnas:
- `CTFORM`: Código del formulario (`Name` o nombre de la clase, o en algunos casos, un *Alias*)
- `CTMAPEO`: Identificador del control y opcionalmente propiedad separada por un punto. Ver [[#Tipos de controles]]
- `CTTIPO`: Tipo de control. No tiene ningún uso real, pero puede servir para clasificar el tipo de control
- `CTTEXTO`: Identificador de texto de la tabla idioma

### Tipos de controles
Dependiendo del tipo de control, el identificador de control puede tener un sufijo para indicar el la propiedad de texto a rellenar, normalmente en controles que admiten varias propiedades de texto.

| Control                        | Propiedad               | Tipo |
| ------------------------------ | ----------------------- | ---- |
| AISBusinessField               | `.LabelText`            | 1    |
| AISBusinessField               | `.DescriptionLabelText` | 1    |
| AISGridView                    | Nombre del campo        | 2    |
| Form                           |                         | 3    |
| AISTabPage                     |                         | 5    |
| AISCatalogo y AISCatalogoTabla | `.LabelText`            | 6    |
| AISLabel                       |                         | 7    |
| AISCheckBox                    |                         | 8    |
| AISButton                      |                         | 9    |
| AISGroupBox                    |                         | 11   |
| AISRadioButton                 |                         | 12   |
| AISDatosCliente                | `.SIPLabel`             | 14   |
| AISDatosCliente                | `.DocLabel`             | 14   |
| AISDatosCliente                | `.RazonLabel`           | 14   |
| Header                         |                         | 15   |
### Controles generales
Si hay controles usados en muchas páginas que van a tener el mismo texto, o son cabeceras, se guardan en la tabla `SICTRLGEN` para no tener que dar de alta sus textos en cada pantalla. Es una tabla igual que `SICONTROLES` pero sin identificar el formulario asociado.

## Validaciones de pantalla
Tabla `SIValidaciones`. Aquí se informan validaciones de formato o tipo de dato, o datos obligatorios necesarios para guardar (campos que forman parte de una clave primaria).

Columnas:
- `VAFORM`: Código del formulario (`Name` o nombre de la clase, o en algunos casos, un *Alias*)
- `VAMAPEO`: Nombre del campo en la tabla del FormData (a diferencia de `SIControles`, no es el id del control). Si se quiere usar como validación ad-hoc en pantalla con `MostrarValidacionUnica`, se suele poner un nombre descriptivo con un guion bajo como prefijo (ejemplo: "\_OperacionRepetida")
- `VAOBLIGATORIO`: Indica si debe validar que esté informado. Valores `S` o `N`
- `VATEXTO`: Identificador de texto de la tabla idioma
- `VATIPOVAL`: Tipo de validación. Ver [[screen-validations#Tipos de validación]]

## Excepciones
Tabla `SIExcepciones`. Para excepciones (`GraveException`, `FatalException`, `ValidationException`, `ValidationBRException`, `PostValidationBRException`).

Columnas:
- `EXID`: Identificador de excepción
- `EXTEXTO`: Identificador de texto de la tabla idioma
- `EXACCION`: Opcional, puede indicar un texto a añadir adicionalmente a la excepción. Por ejemplo, en errores no controlados, se suele informar con `AC000001` ("póngase en contacto con el departamento de informática")

## Elementos de validaciones
Tabla `SIValidacionesBR`. Para usar en los `ValidationBRItemException` o `PostValidationBRItemException`.

Columnas:
- `VBID`: Identificador de validación
- `VBTEXTO`: Identificador de texto de la tabla idioma

## Notificaciones
Tabla `SINotificaciones`. Para mensajes con `AvisoException`, que muestran un Toast, o una pregunta de confirmación (Sí/No).

Columnas:
- `NTID`: Identificador de notificación
- `NTTEXTO`: Identificador de texto de la tabla idioma
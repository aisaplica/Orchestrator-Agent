---
title: SCACS Web - AISGridView
tags: [scacs, ai, controles, grid]
---

# AISGridView

## Descripción
Control de grid personalizado.

## Propiedades
- `AllowRowSelection`: Se establecerá a `false` cuando el grid no requiere interacción
- `Height`
- `MaxHeight`
- `AutomaticSort`
- `SortExpressionAuto`

## Tipos de columnas
- `AISGridViewTextColumn`: Para texto general
- `AISGridViewContratoColumn`: Para números de contrato
- `AISGridViewPropuestaColumn`: Para números de propuesta
- `AISGridViewDateColumn`: Para fechas
- `AISGridViewDateTimeColumn`: Para fecha y hora
- `AISGridViewDecimalColumn`: Para números con decimales
- `AISGridViewNumberColumn`: Para números enteros sin decimales
- `AISGridViewCheckBoxColumn`: Para mostrar un checkbox que no esté enlazado con los datos del grid (generalmente como columna inicial). Si es editable, solo puede haber uno por grid.
- `AISGridViewLinkColumn`: Para mostrar un enlace. Se establece la propiedad CommandName para capturarla en el evento RowCommand.

## Ordenación automática
Establecer la propiedad `AllowSorting` para permitir ordenar automáticamente haciendo clic en los encabezados. Para poder ordenar, `DataSource` debe ser un `DataView` y no un `DataTable`.

## Grid con checkbox
Si se quiere permitir seleccionar más de un registro del grid, se insertará al inicio una columna `AISGridViewCheckBoxColumn`. Esta columna es independiente de los datos que muestra, se ha de establecer el estado de cada checkbox mediante los métodos `SetCheckbox` y `SetAllCheckbox` del AISGridView, y recuperar el valor con el método `GetCheckbox`.

## Menú contextual por fila
Desde ciertas versiones se permite mostrar un botón por fila con un menú de acciones. Si el grid está deshabilitado con `Enabled = false`, el menú no aparece.

### Reglas
- Los elementos se añaden en `MenuItems`.
- El texto de los elementos del menú se resuelve por base de datos.
- El evento `BuildMenuRow` permite ocultar elementos por fila.
- El clic dispara `RowCommand`.

## Obtener el elemento seleccionado
El elemento seleccionado se establece o obtiene siempre con la propiedad `SelectedIndex`. Como el grid siempre estará asociado a una tabla del `FormData`, para acceder a los datos del registro seleccionado se hará accediendo a la fila específica de la tabla del `FormData` asociada al grid, o del `DataView` si es este el que se ha asociado.
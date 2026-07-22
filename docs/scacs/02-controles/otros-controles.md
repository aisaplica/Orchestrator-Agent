---
title: SCACS Web - Otros controles AIS
tags: [scacs, ai, controles]
---

# Otros controles AIS

## `AISCheckBox`
Control de checkbox con label.

### Propiedad
- `DataEntrySize`

## `AISRadioButton`
Control de radiobutton con label.

### Propiedad
- `DataEntrySize`

## `AISDatosCliente`
Control para búsqueda de clientes. Puede mostrarse como un `AISButton` o como un control compuesto mostrando los datos principales del cliente (documento, nombre y apellidos).

### Comportamiento
- Abre un diálogo de búsqueda.
- Permite seleccionar un cliente.
- Hace PostBack al seleccionar uno.
- Rellena propiedades del cliente.
- Dispara el evento `ClientSelected`.

### Propiedades relevantes
- `SearchToolTip`
- `Icon`
- `IdFirma`
- `Razon`
- `Pais`
- `DescripcionPais`
- `TipoDocumento`
- `DescripcionTipoDocumento`
- `NumeroDocumento`
- `TipoPersona`
- `DisplayMode`
### Modos
- `Completo`
- `SoloBoton`
- `SinBoton`
## `AISLabel`
Label simple.
Normalmente no debería usarse porque el resto de controles ya incorporan label.

## `AISPanel`
Panel genérico.

## `AISGroupbox`
Contenedor para agrupar campos con línea y opcionalmente título.

## `AISTabControl`
Control de pestañas.

### Propiedades
- `SelectedIndex`
- `TabPageSelectionEnabled`
- `TabPageWidth`
- `TabPages`
- `AutoPostback`

### Evento
- `SelectedIndexChanged`

## `AISTabPage`
Pestaña dentro de un tab control.

### Propiedades
- `Text`
- `TabPageIndex`

## `AISTreeView`
Control de árbol.

### Estructura de datos esperada
- `Key`
- `Parent`
- `Value`

### Propiedades
- `DataTable`
- `AutoSelectFirstLeaf`
- `ShowOnlyValue`
- `RootKey`
- `SelectedNode`
- `SelectedValue`

### Método
- `SetSelectedNodeByKey`

## `AISChipContainer`
Control para mostrar tags clicables.

### Eventos
- `ChipClick`
- `ChipClose`

## `AISChip`
Elemento de `AISChipContainer`.

### Propiedades
- `Name`
- `Text`
- `ToolTip`
- `ShowCloseButton`

## `AISCollapsibleControl`
Control con secciones expandibles.

### Propiedades
- `Sections`
- `CollapsibleMode`

### Modos
- `Expandable`
- `Accordion`

## `AISCollapsibleSection`
Sección del control colapsable.

### Propiedades
- `Text`
- `Icon`
- `Content`
- `HeaderAdditionalContent`
- `Active`
---
title: SCACS Web - AISBusinessField
tags: [scacs, ai, controles, input]
---

# AISBusinessField

## Descripción
Control para campos de entrada de texto. Contiene:
- un `TextBox`,
- su `Label` asociado,
- un `DescriptionLabel` opcional.

## Propiedades
- `Text`
- `Value`
- `FieldState`
- `FieldDataType`
- `DataEntrySize`
- `LabelText`
- `ShowLabel`
- `LabelSize`
- `DescriptionLabelText`
- `ShowDescriptionLabel`
- `DescriptionLabelSize`

## `FieldState`
- `Enabled`: normal.
- `Readonly`: solo lectura.
- `Disabled`: deshabilitado. Equivalente a Readonly.
- `Flat`: muestra contenido sin ser editable y con label lateral.

## `FieldDataType`
- `Text`
- `Date`
- `Importe`
- `Entero`
- `Porcentaje2`
- `Porcentaje5`

## Nota
`Value` es el valor tal como se guarda en el `DataSet`, mientras que `Text` es la representación visual. Siempre que se tenga que recuperar o rellenar su valor desde un DataSet, se debe usar la propiedad Value en vez de Text.
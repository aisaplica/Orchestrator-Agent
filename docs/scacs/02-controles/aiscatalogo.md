---
title: SCACS Web - AISCatalogo
tags: [scacs, ai, controles, dropdown]
---

# AISCatalogo

## Descripción
Control desplegable para catálogos de SITABL, normalmente usado con datos obtenidos de `CatalogoBE`.

## Propiedades
- `IdCatalogo`
- `CatalogData`
- `CatalogTable`
- `DataEntrySize`
- `AutoSelectOnSingleItem`
- `LoadOptionsAjax`
- `MinimumInputLenghthSearch`

## Comportamiento importante
- `IdCatalogo` y `CatalogData` deben establecerse siempre en cada PostBack.
- Si no se hace, se perderán los datos del desplegable y el valor seleccionado.
- Estas propiedades normalmente se establecen en un método `CatalogBinding` llamado desde el `MapeoCampos`.

## Carga AJAX
Con `LoadOptionsAjax`:
- solo se carga el valor seleccionado al inicio,
- el catálogo se consulta por AJAX al abrirlo.

## Búsqueda
`MinimumInputLenghthSearch` define cuántos caracteres debe introducir el usuario para lanzar la búsqueda.
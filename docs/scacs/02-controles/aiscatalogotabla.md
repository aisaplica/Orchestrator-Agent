---
title: SCACS Web - AISCatalogoTabla
tags: [scacs, ai, controles, dropdown]
---

# AISCatalogoTabla

## Descripción
Control de lista desplegable para catálogos genéricos.

## Diferencia principal
Funciona igual que `AISCatalogo`, pero en lugar de un número de catálogo se le pasa el nombre de la tabla a consultar.

## Estructura esperada
Debe existir al menos:
- una columna para código,
- una columna para descripción.

## Propiedades
- `CatalogData`
- `CatalogTable`
- `DataEntrySize`
- `AutoSelectOnSingleItem`

## Nota importante
`CatalogData` y `CatalogTable` deben establecerse siempre en cada PostBack para no perder el valor seleccionado.
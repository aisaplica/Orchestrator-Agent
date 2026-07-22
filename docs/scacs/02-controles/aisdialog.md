---
title: SCACS Web - AISDialog
tags: [scacs, ai, controles, dialog]
---

# AISDialog

## Descripción
Diálogo modal.

## Regla importante
No usar `Visible` para mostrar u ocultar el diálogo. Debe usarse `IsModalVisible`.

## Consideraciones
- El diálogo incluye los controles en un `UpdatePanel`.
- Si se abre el modal, el `UpdatePanel` contenedor debe actualizarse.
- No debería actualizarse un `UpdatePanel` externo cuando el diálogo está abierto. Si esto sucede, quedará visible el fondo oscuro que tapa los controles de detrás del diálogo, impidiendo interactuar con el resto de la pantalla.
- Para evitar estos problemas, los diálogos se deben colocar siempre en un `UpdatePanel` propio al final de la página, que se actualice independientemente.

## Propiedades
- `IsModalVisible`
- `Titulo`
- `Content`
- `Buttons`

## Comportamiento
- Cierra por defecto.
- `IsModalVisible = true` muestra el modal.
- `IsModalVisible = false` lo oculta.
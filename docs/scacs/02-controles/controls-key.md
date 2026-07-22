---
title: SCACS Web - Controles clave
tags: [scacs, ai, controles]
---

# Controles clave

## `AISBusinessField`
Campo de entrada principal.

### Características
- Conversión automática de tipos.
- Binding con `FormData`.
- Estados: Enabled, Readonly, Disabled, Flat.

## `AISCatalogo`
Dropdown basado en catálogo.

### Claves
- Reasignar propiedades en cada PostBack.
- Soporta carga AJAX.

## `AISGridView`
Grid avanzado.

### Características
- Tipos de columnas específicos.
- Ordenación automática.
- Menú contextual.

## `AISDialog`
Modal genérico controlado por:
- `IsModalVisible`.

## `AISMessageDialog`
Gestión centralizada de:
- errores,
- confirmaciones,
- notificaciones.

### Importante
- Registrar confirmaciones en cada PostBack.
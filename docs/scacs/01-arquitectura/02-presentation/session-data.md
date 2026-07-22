---
title: SCACS Web - Mantenimiento de datos en sesión
tags: [scacs, ai, session, formdata]
---

# Mantenimiento de datos en sesión

## Objetivo
Liberar el ViewState de la página manteniendo el estado principal en sesión.

## Qué se guarda
- Principalmente el `FormData`.
- Otros datos auxiliares según el formulario.
- Metadatos de navegación y contexto mediante `PageSessionContainer`.

## `PageSessionContainer`
El `PageSessionContainer` estructura la información guardada en sesión y actúa como envoltorio del estado de la página.

### Variantes específicas
Según el dominio del formulario, puede existir una versión más concreta, por ejemplo:
- `PageSessionContainerPG`
- `PageSessionContainerGA`

Estas extensiones añaden propiedades propias del negocio, como identificadores adicionales de solicitud o garantía.

## Clave de sesión
- Cada página guarda el objeto en sesión con una clave aleatoria.
- Esa clave viaja en el `QueryString` de la página actual.
- El objeto incluye el nombre del formulario para validar que la clave pertenece a la página correcta.

## Flujo general
1. Carga inicial desde negocio.
2. Se rellena `FormData`.
3. Se guarda en sesión dentro del `PageSessionContainer`.
4. La página conserva solo la clave en la URL.
5. En recargas o postbacks, se recupera el estado desde sesión.


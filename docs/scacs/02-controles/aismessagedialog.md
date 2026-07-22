---
title: SCACS Web - AISMessageDialog
tags: [scacs, ai, controles, dialog, messages]
---

# AISMessageDialog

## Descripción
Control para mostrar mensajes y errores sin declararlo explícitamente en la página.

## Característica
No es un control ASP.NET tradicional: no hereda de `Control` ni `WebControl`.

## Constructor
Requiere:
- la página,
- el idioma.

## Uso típico
- `Show` para excepciones.
- `ShowToast` para notificaciones de guardado correcto.
- `RegisterConfirmDialog` para confirmaciones antes de acciones destructivas.

## Confirmaciones
Debe registrarse en cada carga de página, porque los eventos se pierden en cada PostBack si no se vuelven a añadir.

## Recomendación
Usarlo desde `FormEventHandler` para asociar confirmaciones a botones.

## Ejemplo de uso
Interceptar el clic en el botón `btnDelete` para mostrar un aviso de confirmación al usuario ante una acción destructiva:

```c#
AISMessageDialog msgd = new AISMessageDialog(this, _language);
msgd.RegisterConfirmDialog(this.btnDelete, new AvisoException("NT002", ""));
```
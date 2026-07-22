---
title: SCACS Web - Navegación entre formularios
tags: [scacs, ai, navigation]
---

# Navegación entre formularios
La navegación típica inicia desde el menú lateral, y de ahí se va entrando en pantallas siguiendo un flujo de navegación lineal, pudiendo pasar información entre dos momentos de navegación consecutivos.

## Flujo típico
1. Un formulario A llama a un formulario B pasándole datos.
2. B modifica datos y regresa al formulario A.
3. A recibe los datos modificados del formulario B.

## Navegación hacia adelante en el flujo
Para ir a otro formulario (formulario A llama al formulario B):
1. Se crea un nuevo `PageSessionContainer` específico.
2. Se le asignan los identificadores necesarios para consultar negocio.
3. Opcionalmente se rellena su `FormData` con información adicional.
4. Se informa la acción de formulario mediante `FormAction`.
5. Informar formulario actual y siguiente.
6. Llamar a `IrAlFormulario` pasando el `PageSessionContainer` y un *formKey* (una cadena de texto cualquiera que se puede usar para identificar cuándo volvemos de esta llamada).

Para minimizar el tamaño de la sesión, se deberían pasar solo las tablas necesarias al nuevo formulario. Solo se deberían pasar datos del FormData cuando puedan modificarse en la pantalla actual y la nueva pantalla debe leerlos sin acceder a base de datos. En caso contrario, la nueva pantalla debería recuperar la información de base de datos solo con el identificador de la entidad.

## Recepción en el formulario destino
Si el `PageSessionContainer` tiene propiedades específicas:
- se usan en `LoadAdditionalDataFromSessionKey`.
- normalmente esto se resuelve en una base heredada con propiedades añadidas.

El FormData incluirá la información adicional enviada. La carga principal de negocio sigue siendo responsabilidad de `LoadFormDataFromBusiness`.

## Navegación hacia atrás en el flujo
Para regresar del formulario B al formulario A, solo hay que llamar a `VolverAlFormularioAnterior`.

## Recepción en el formulario origen
Al navegar hacia atrás en el flujo de navegación (del formulario B al formulario A), el formulario al que regresamos (formulario A) recibirá en el método `VueltaDesdeFormulario` el `PageSessionContainer` enviado originalmente (formulario B) y el *formKey* que se envió originalmente en el `IrAlFormulario`.

De este `PageSessionContainer` se puede obtener:
- El `Result`, para saber si el usuario cambió datos y guardó, o regresó sin guardar (con la intención de descartar cualquier modificación).
- El `FormData` con los últimos cambios, para poder actualizar el FormData local si `Result` es `Ok`.
- Los identificadores de negocio para poder identificar la entidad. Por ejemplo, puede guardarse como variable del formulario para seleccionar en el `PostLoadForm` el registro del Grid sobre el que se inició la navegación.

El *formKey* puede servir para identificar qué botón o control originó la navegación, y devolver el foco a ese control.

## Redirecciones automáticas
Cuando nada más abrir una pantalla se tiene que redirigir a otra, debe hacerse en `OnLoadComplete`. Hacerlo antes romperá la gestión de sesión.
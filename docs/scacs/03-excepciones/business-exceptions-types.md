---
title: SCACS Web - Tipos de excepciones de negocio
tags: [scacs, ai, excepciones]
---

# Excepciones de negocio

## `GraveException` y `FatalException`
Son equivalentes en la práctica, aunque normalmente se usa `GraveException`.

### Uso
- Errores de aplicación.
- Excepciones capturadas y envueltas en un bloque `try-catch`.

### Parámetros
- código (de tabla `SIExcepciones`, ver [[textos]]),
- mensaje,
- excepción original opcional.

### Recomendación
- Registrar primero con `LogGrave` o `LogFatal`.
- Conservar la excepción original cuando exista.

## `ValidationBRException`
Se usa para validaciones de negocio.

### Características
- Puede contener varias validaciones.
- Usa una colección de items de validación.
- Realiza rollback.

### Texto de validación
- El código de la excepción normalmente será el `EX021` ("Error en la validación de los datos")
- El código de los items de validación se resuelve en `SIValidacionesBR` (ver [[textos]]).
- El mensaje puede complementar o concretar el error.

## `PostValidationBRException`
Es similar a `ValidationBRException`, pero no hace rollback.

### Uso
- Flujos donde se permite guardar aunque falten datos.
- Situaciones donde el usuario puede continuar más adelante.

### Comportamiento
- Hace commit al llegar a UI.
- Incluye la tabla `PostValidationBRTable`.
- Puede incluir un `FormData` adicional en la excepción, normalmente para recibirlo en pantalla.

## Recomendación funcional
- `ValidationBRException` para bloquear definitivamente.
- `PostValidationBRException` para permitir guardar y seguir más tarde, opcionalmente incluyendo en `FormdData` el `DataSet` que se habría devuelto de no haberse producido el error de validación.
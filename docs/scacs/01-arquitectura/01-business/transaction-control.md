---
title: SCACS Web - Control de transacciones
tags: [scacs, ai, transacciones]
---

# Control de transacciones

## `DataAccessKey`
En las clases de negocio se debe pasar siempre una cadena `DataAccessKey` en el constructor.

## Para qué sirve
Identifica la transacción de base de datos activa.

## Riesgo si no se pasa
Si no se transmite:
- puede abrirse una nueva transacción,
- pueden aparecer bloqueos por transacciones previas,
- se rompe la coherencia entre llamadas.

## Confirmación y rollback
Al volver a presentación:
- las transacciones pendientes se confirman automáticamente,
- salvo que ocurra una excepción no controlada,
- o una excepción distinta de `PostValidationException`.

## Comportamiento ante error
Si ocurre una excepción distinta de la permitida:
- se hace rollback automático.

## Recomendación
Toda llamada a negocio debe asumir que participa en la transacción actual y no iniciar una paralela sin necesidad.
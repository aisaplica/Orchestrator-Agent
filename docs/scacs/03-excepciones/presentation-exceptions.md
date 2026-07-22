---
title: SCACS Web - Excepciones de presentación
tags: [scacs, ai, excepciones, presentacion]
---

# Excepciones de presentación

## Regla general
Las excepciones no controladas en presentación acaban en error de ASP.NET. Para evitarlo, los métodos de evento deberían envolver su código en un bloque try-catch para gestionar las excepciones.

## Estrategia correcta
Si se quiere mostrar un error al usuario:
- capturar en `try-catch`,
- mostrar con `AISMessageDialog`.

## Restricción
No debería lanzarse una excepción desde presentación si no existe un manejo explícito.

## `ValidationException`
Similar a la validación de negocio, pero los textos se toman de `SIValidaciones`. Ver [[textos]].

### Nota
No está pensada para uso directo habitual.
Normalmente las validaciones deben hacerse en negocio para facilitar su reutilización independientemente de la pantalla.
Normalmente las validaciones de formato (fechas, números) se configuran en base de datos: ver en [[screen-validations]].

## `AvisoException`
No es una excepción funcional clásica.

### Uso
- notificaciones,
- preguntas Sí/No,
- mensajes configurados en `SINotificaciones`. Ver [[textos]].
---
title: SCACS Web - Excepciones de negocio
tags: [scacs, ai, excepciones, negocio]
---

# Excepciones de negocio

## Regla general
En SCACS, cualquier condición de error debe expresarse mediante excepciones.

## Base común
Todas las excepciones gestionadas heredan de `BaseException`.

## Clasificación
- Excepciones de negocio.
- Excepciones de presentación.

## Ventajas del modelo
- Unifica el manejo de errores.
- Permite mostrar mensajes desde base de datos.
- Hace explícito cuándo debe haber rollback o commit.

## Uso recomendado
- Negocio: lanzar excepciones controladas.
- Presentación: capturar y mostrar con diálogo.
- Evitar usar `true/false` como mecanismo principal de manejo de errores.
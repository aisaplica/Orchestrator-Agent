---
title: SCACS Web - Validación de errores
tags: [scacs, ai, excepciones, validacion]
---

# Validación de errores

## Idea clave
Las validaciones controladas forman parte del flujo normal de la aplicación y no deberían tratarse como errores técnicos.

## En negocio
- Se usan excepciones de validación de negocio.
- El texto se resuelve desde base de datos. Ver [[textos]]
- Se puede forzar rollback o commit según el tipo.

## En presentación
- Si se necesita mostrar una validación puntual, se usa `MostrarValidacionUnica`.
- No es habitual generar validaciones de negocio en la capa UI.

## Recomendación para IA
Cuando encuentres una validación:
- distinguir si bloquea guardado,
- distinguir si solo bloquea avance de flujo,
- revisar si debe ser `ValidationBRException` o `PostValidationBRException`.
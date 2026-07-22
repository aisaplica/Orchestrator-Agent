---
title: SCACS Web - Notas para asistentes de IA
tags: [scacs, ai, recomendaciones]
---

# Notas para asistentes de IA

## Validaciones
- Revisar siempre `SIValidaciones` antes de tocar lógica de guardado.
- No mover validaciones de negocio a pantalla si deben permitir guardado parcial.
- Validar filas editadas antes del guardado global cuando el error depende de la fila.

## Capas
- La presentación no debe hacer llamadas repetidas a negocio si los datos pueden venir en la carga inicial.
- El negocio se considera remoto o costoso aunque esté en la misma máquina.

## Errores
- Las excepciones son parte del contrato funcional.
- `BaseException` representa errores ya gestionados.
- No convertir errores controlados en respuestas booleanas.

## Transacciones
- `DataAccessKey` es obligatorio en constructores de negocio.
- No iniciar flujos de persistencia independientes si deben compartir la misma transacción.

## Navegación
- Cuando un formulario hijo devuelve información, comprobar siempre `Result`.
- No asumir que el `FormData` del hijo debe aplicarse si el usuario canceló.
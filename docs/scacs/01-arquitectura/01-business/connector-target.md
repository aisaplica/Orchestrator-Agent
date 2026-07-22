---
title: SCACS Web - Destino de la llamada al conector
tags: [scacs, ai, connector]
---

# Destino de la llamada al conector

## Parámetros de ejecución
El método `Execute` del conector recibe una instancia de `AIS.PR.SF.Parameters`.

## Parámetros indispensables
La instancia incluye:
- proyecto destino,
- clase destino,
- método destino.

## Proyecto destino
Debe corresponder a uno de los definidos en la tabla `SIAPPATH`. Por convención, el nombre del proyecto se forma quitando el prefijo `AIS.PR` del nombre y quitando los puntos de separación.
Ejemplo: Si el nombre del proyecto es `AIS.PR.BR.EC.AN`, el nombre de namespace del proyecto que se envía en Parameters es `BRECAN`.

## Clase destino
Normalmente es `BPC`.

## Método destino
Es una cadena procesada por `Invoke` en la clase de negocio.

## Patrón de enrutado
La clase de negocio suele:
- recibir el método como string,
- resolverlo mediante `switch`,
- ejecutar la lógica concreta,
- interpretar parámetros adicionales.

## Implicación práctica
La presentación no llama a métodos concretos de negocio de forma directa.
Llama a un contrato genérico que el backend resuelve internamente.
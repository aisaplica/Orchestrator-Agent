---
title: SCACS Web - Tratamiento de errores de negocio desde presentación
tags: [scacs, ai, connector, errores]
---

# Tratamiento de errores de negocio desde presentación

## Comportamiento del conector
El conector siempre retorna un `DataSet` o `null`.

## Caso de error
Si ocurre una excepción en negocio:
- no se propaga directamente,
- el conector retorna `null`,
- se lanza el evento de fin de ejecución con el objeto excepción.

## Papel del formulario base
El formulario base escucha ese evento y:
- muestra el mensaje de error,
- centraliza el tratamiento visual.

## Cómo interpretar el resultado
En código de presentación:
- si retorna `null`, ha habido error,
- si retorna un `DataSet`, la llamada ha ido bien.

## Llamadas sin datos
Si una llamada no debe devolver datos:
- se retorna `new DataSet()`,
- así se distingue entre éxito y error.

## Beneficio
Este diseño evita que la capa de presentación tenga que gestionar directamente excepciones de negocio en llamadas estándar.
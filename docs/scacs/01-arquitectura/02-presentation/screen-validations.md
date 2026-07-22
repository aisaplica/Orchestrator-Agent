---
title: SCACS Web - Validaciones de pantalla
tags: [scacs, ai, validaciones]
---

# Validaciones de pantalla

## Objetivo
Las validaciones de pantalla se parametrizan en base de datos para impedir el guardado de datos inválidos o incompletos.

## Fuente de configuración
- Tabla: `SIValidaciones`.
- Se define por:
  - formulario,
  - nombre de columna,
  - tipo de dato,
  - si es obligatorio o no.

## Cuándo usarlas
Deben usarse solo para:
- datos obligatorios imprescindibles,
- formatos que puedan provocar errores al guardar,
- tamaños o formatos que rompan el proceso de persistencia.

No deben usarse para validaciones de negocio que solo bloquean el avance de etapa o la llamada a servicios si aún se permite guardar parcialmente.

## Comportamiento con `FormData`
- Un formulario puede contener varias tablas.
- No se indica la tabla en la validación.
- Si la columna existe en alguna tabla del `FormData`, se valida.
- Si no existe, la validación se ignora.

## Tipos de validación
Los tipos soportados incluyen:
- `CATALOGO`
- `FECHAYYYYMM`
- `CADENA`
- `NUMERO`
- `NUMERODEC`
- `DIAS`
- `PORCENTAJE`
- `PORCENTAJE2`
- `PORCENTAJE3`
- `PORCENTAJE4`
- `PORCENTAJENEG1`
- `IMPORTE`
- `IMPORTEPOS`
- `FECHA`
- `FECHA1`
- `FECHA2`
- `HORA`
- `MAYORCERO`
- `ENTEROMAYORCERO`

## Validación adicional
Algunos tipos no solo validan formato, sino también reglas adicionales:
- fechas válidas,
- mes entre 1 y 12,
- hora válida,
- valores positivos,
- límites frente a hoy,
- porcentajes dentro de rango.

## Validación en listas
Si se edita una fila en una lista dentro del formulario, conviene validar al aceptar la fila.
Así el error aparece en contexto y no más tarde en la validación global del guardado.

## Método recomendado
Para mostrar un mensaje de validación individual, usar el método `MostrarValidacionUnica` del formulario base, pasando el valor de `VAMAPEO` de `SIVALIDACIONES`. Ver [[textos]].
---
title: SCACS Web - Ciclo de guardado
tags:
  - scacs
  - ai
  - lifecycle
  - frontend
---

# Ciclo de guardado

## Secuencia
1. `SaveItemAction`
2. `PreSaveItemAction`
3. `ValidacionsOK`
4. `PreValidationOK`
5. `UpdateDataSet`
6. `PreUpdateDataSet`
7. `AddUpdateParams`
8. `UpdateOK`
9. `UpdateDataSetForm`
10. `EmptyListControl`

## Puntos clave
- Llamar a `SaveItemAction` cuando se quieran guardar los datos de todo el formulario. Esto desencadena la secuencia de guardado.
- `PreSaveItemAction`: Implementar la lógica de guardar los datos desde los controles hacia el FormData. Sirve tanto para guardar en base de datos como para persistir los datos en sesión antes de navegar hacia otro formulario, y poder recuperar estos datos más adelante. 
- Las tablas del FormData que se deben validar por configuración (ver [[screen-validations]]) se deben añadir en `PreValidationOK` al `DataSet` que se pasa por parámetro. La tabla `BusinessEntityName` ya está incluida y no se debe añadir.
- Se puede añadir alguna validación especial en `ValidacionsOK`, pero lo recomendable es hacer validaciones en negocio.
- Solo se envía al método de guardado de negocio la tabla `BusinessEntityName` del `FormData`. Si se debe añadir alguna otra tabla, se debe añadir en `PreUpdateDataSet`.
- En `UpdateDataSetForm` se recibe el resultado de la llamada a negocio del guardado. Si el guardado implica generar un nuevo identificador de entidad, se puede obtener en este método y guardarlo en el FormData para que esté disponible en el siguiente guardado o para retornarlo al formulario anterior.

## Extensión
- `PreSaveItemAction`: cancelar guardado.
- `PreUpdateDataSet`: añadir tablas.
- `UpdateDataSetForm`: post-procesado del resultado.
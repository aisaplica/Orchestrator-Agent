---
title: SCACS Web - Ciclo de carga
tags:
  - scacs
  - ai
  - lifecycle
  - frontend
---

# Ciclo de carga

## Secuencia completa
1. `PreLoadForm`
2. `LoadFormDataFromSessionKey`
3. `LoadAdditionalDataFromSessionKey`
4. `FormEventHandler`
5. Si es PostBack:
   - `LoadFormDataFromPostBack`
6. Si no es PostBack:
   - `AddLoadParams`
   - `LoadFormDataFromBusiness`
7. `LoadFormDataFromPreviousPage`
8. Si `FormData` no es nulo:
   - si no es PostBack: `ComprobarVueltaFormularioAnterior`
   - `VueltaDesdeFormulario`
   - `FormatForm`
   - `LoadText`
   - `MapeoCampos`
   - `AdaptControlDetail`
   - `EmptyListControl`
10. Eventos del formulario y controles
11. `OnLoadComplete`
12. `SaveAdditionalDataToSessionKey`
13. `LoadMetaDataWebForm`
14. `AccessFormMode`. Según el modo de acceso:
	- `ProcessAccessNew`
	- `ProcessAccessQuery`
	- `ProcessAccessUpdate`

## Puntos de extensión habituales
- `PreLoadForm`: Inicialización de las propiedades iniciales del formulario (`TargetAssembly`, `TargetClass`, `TargetAction`, `UpdateAction`, `BusinessEntityName`)
- `FormEventHandler`: asignar eventos a controles. Los eventos se asignan directamente en el ASPX, pero habrá casos donde esto no sea posible
- `LoadAdditionalDataFromSessionKey`: Carga de datos adicionales en variables del formulario desde el PageSessionContainer (variables enviadas desde otro formulario durante la navegación, por ejemplo, un id de cliente)
- `AddLoadParams`: Agrega parámetros a la llamada al conector para la carga inicial del formulario (`TargetAction`). La base ya agrega unos estándar: FormName, Language, User, Employee, Office y AccessMode. Normalmente lo usan bases intermedias.
- `FormatForm`: Formateo de GridViews, definición de las columnas.
- `MapeoCampos`: Mapeo de campos de formulario y GridViews.
- `ProcessAccessNew`: Establecer estado de los controles cuando el nivel de acceso es ALTA
- `ProcessAccessUpdate`: Establecer estado de los controles cuando el nivel de acceso es MODIFICACIÓN. Normalmente no se usa, y la lógica de habilitar controles está en `AdaptControlDetail`.
- `ProcessAccessQuery`: Establecer estado de los controles cuando el nivel de acceso es  CONSULTA, normalmente para deshabilitar u ocultar controles. Será el que más se use para todos los controles que queremos deshabilitar si por seguridad solo tenemos acceso a la pantalla en modo consulta.
- `AdaptControlDetail`: Para habilitar/deshabilitar/ocultar campos del formulario según los datos actuales.
- `EmptyListControl`: Para habilitar/deshabilitar botones según si en los grids hay o no filas.
- `SaveMetaDataWebForm`: Define los metadatos (TabPage actual, row seleccionada del grid, etc.) que deseamos guardar en la sesión antes de navegar hacia otra pantalla. Si existe algún UserControl se tiene que llamar al método GetMetaDataWebForm del control para obtener los datos a guardar del propio control. Utiliza el datatable MetaDataWebForm del FormData.
- `LoadMetaDataWebForm`: Define la lógica de carga de metadatos en los controles del webform desde la sesión, al regresar de otra pantalla. Si existen controles independientes se tiene que llamar al método SetMetaDataWebForm que contendrá la lógica de carga de metadatos del propio control. Utiliza el datatable MetaDataWebForm del FormData.

## Consideraciones
- No PostBack = carga desde negocio.
- PostBack = recuperación desde sesión.
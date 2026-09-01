---
title: SCACS Web - Glosario
tags: [scacs, ai, glosario]
---

# Glosario

## Términos frecuentes

### `FormData`
`DataSet` principal que contiene los datos de la pantalla.

### `PageSessionContainer`
Contenedor de sesión que guarda estado, navegación y contexto.

### `FlowID`
Identificador de flujo asociado a navegación entre formularios.

### `Result`
Indica si un formulario hijo ha sido aceptado o cancelado.

### `BusinessEntityName`
Tabla principal del `FormData` que representa el negocio central de la pantalla.

### `DataAccessKey`
Clave de transacción usada para mantener coherencia entre llamadas a negocio.

### `PostBack`
Recarga de la página por interacción con controles del formulario.

### `ValidationBRException`
Excepción de negocio usada para validaciones que bloquean.

### `PostValidationBRException`
Excepción de negocio usada para validaciones que no hacen rollback.

### `AISMessageDialog`
Control auxiliar para mostrar mensajes, errores y confirmaciones.

### `AISGridView`
Grid personalizado de la plataforma SCACS Web.

### `AISCatalogo`
Control desplegable para catálogos de SITABL.

## Workflow

Ver [[04-workflow/workflow-overview]] para el detalle completo.

### `Modelo` (workflow)
Un flujo de workflow completo (`WFModelo`). Consta de varias etapas conectadas.

### `Etapa` (workflow)
Un punto del flujo dentro de un modelo (`WFEtapa`). Tiene una pantalla asociada
(`IDFORMULARIO` → `WFRepFormulario`) y, opcionalmente, una expresión de activación.

### `Señal` (workflow)
Evento de finalización de una etapa. Determina qué transición de `WFTransicion` se
aplica y, por tanto, la(s) etapa(s) destino.

### `Objeto base` (workflow)
Entidad que recorre el flujo: número de propuesta SCACS (+ financiación opcional).
Su estado actual vive en `WFBDObjetoBase`; su histórico en `WFBDResumen`.

### `Expresión de activación`
Cadena de caracteres sin repetición que condiciona la activación de una etapa
destino con varias entradas. Las no cumplidas se guardan en
`WFBDVariableObjetoBase`. Sin expresión → la etapa se activa siempre.

### `Centro Visible`
Campo de la etapa (`WFBDObjetoBase`) que determina qué usuarios de centros
superiores ven la etapa. Se hereda de la etapa anterior; una función de activación
puede cambiarlo.

### `WFTransicion`
Tabla que define, por señal, el modelo y etapa destino de una transición, con su
expresión de activación. Modelo destino `*` = volver al flujo del que se originó
el actual (subflujos comunes).

### `SendSignal`
Columna de la tabla `RESULT` en el `DataSet` que devuelve una función para cambiar
la señal recibida. La señal debe estar parametrizada en `WFRepSenyalesFuncion`.
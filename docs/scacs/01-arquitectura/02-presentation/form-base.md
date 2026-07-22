---
title: SCACS Web - Formulario base
tags:
  - scacs
  - ai
  - formbase
  - frontend
---

# Formulario base

## Descripción
Clase base que define el comportamiento estándar de todas las páginas.

## Propiedades clave

### Integración con negocio
- `Connector`: Permite hacer llamadas a métodos del backend (capa de negocio).
- `TargetAssembly`: ensamblado de negocio.
- `TargetClass`: clase de negocio, normalmente `BPC`.
- `TargetAction`: carga inicial.
- `UpdateAction`: guardado.

### Contexto de usuario
- `IdUsuario`
- `IdEmpleado`
- `IdCentro`
- `Language`

## Contexto de negocio
Existen formularios base intermedios según la entidad de negocio principal que manejan.

### Estado del formulario
- `FormData`: `DataSet` principal.
- `BusinessEntityName`: tabla principal del DataSet.
- `FormAction`: acción del formulario, cuál es la intención del usuario: ALTA, MODIFICAR, BORRAR, CONSULTAR, según constantes definidas en `AIS.PR.SF.EXTERNAL_ACCESS_*`. 
- `AccessMode`: modo de acceso según los permisos del usuario sobre este formulario, que también depende del FormAction. Por ejemplo, si se entra con un `FormAction` de MODIFICAR pero el usuario solo tiene permisos de consulta, el `AccessMode` cambia a modo CONSULTAR.
- `Result`: estado de aceptación o cancelación de la acción sobre este formulario, para indicar al volver a la pantalla anterior si se llegaron a guardar cambios o no.

### Navegación
- `PgsContainer`: gestión de sesión y navegación, uso interno.

### Control de flujo
- `RequiereFlow`: por defecto a `true`, se establecerá a `false` si el formulario se puede abrir directamente desde el menú y no depende de un flujo de pantallas.


### Métodos útiles
- `MostrarValidacionUnica`: Muestra una validación por pantalla. Ver [[screen-validations]].

## Notas importantes
- `FormData` vive en sesión.
- Evitar acceder directamente a `PgsContainer` salvo necesidad.
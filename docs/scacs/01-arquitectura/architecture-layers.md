---
title: SCACS Web - Separación de capas
tags: [scacs, ai, arquitectura, capas]
---

# Separación de capas

## Modelo general
La separación entre presentación y negocio es física.
La capa física usa un AppDomain separado de la capa de presentación, y podría residir incluso en otro servidor, conectando mediante un WebService. Por eso, el acceso a negocio se considera costoso.
Las DLLs de negocio se ubican en una carpeta separada de la web.

## Conector
La comunicación entre presentación y negocio se realiza mediante `AIS.PR.UI.ClientConnectorInterface`.

## Conector dentro de negocio
La comunicación entre proyectos de negocio se realiza mediante `AIS.PR.BR.BRConnector`, que usa una interfaz exactamente igual a `AIS.PR.UI.ClientConnectorInterface`, pero mantiene la misma transacción de base de datos.

## Estrategia de carga
En la carga inicial de la página se debe traer todo lo necesario:
- textos,
- validaciones,
- catálogos,
- datos de negocio.

La pantalla no debería pedir datos a negocio de forma incremental si puede evitarse.

## Persistencia de estado
Los datos se guardan en:
- `FormData`,
- sesión asociada a la página.

Esto reduce llamadas repetidas al negocio durante la interacción del usuario.

## Gestión de transacciones
La conexión a base de datos se inicia y se cierra automáticamente dentro de la capa de negocio. Al volver de la capa de negocio hacia la capa de presentación, la transacción hace el Commit o Rollback automáticamente.
La transacción de base de datos se mantiene identificada con la propiedad `dataAccessKey` de las clases de negocio, y es importante informar esta variable en el constructor de todas las clases de negocio.

## Actualización de DLLs de negocio
Para evitar bloqueos de DLLs, el AppDomain de negocio está configurado con `ShadowCopyFiles`. Esto permite reemplazar las DLLs aun con la aplicación en ejecución, pero no se tomará la nueva versión hasta que no se recicle el pool de aplicaciones del IIS, o se reinicie el IIS de desarrollo.

---
title: SCACS Web - Seguridad
---
## Login
El inicio de sesión se hace normalmente conectando contra un ActiveDirectory para validar usuario y contraseña. SCACS no maneja contraseñas.

También se puede configurar en el IIS el acceso con Autenticación Windows Integrada, de forma que a SCACS ya le llega la sesión de usuario iniciada y obtiene directamente quién es el usuario conectado.

## Entidad Empleado, Usuario y Centro
El identificador de login realmente corresponde con la entidad **Empleado**. El **Usuario** es un usuario lógico, asociado al login. A nivel usuario se define el **Perfil** de acceso y el **Centro**. El **Centro** es la oficina o sucursal donde está ubicado el usuario. Puede haber varios usuarios asociados a un mismo login, y en ese caso, cuando el usuario se conecta, le aparece la lista de usuarios que tiene asignados para que seleccione con cuál de ellos entrar.

Los centros tienen definida una jerarquía. Todo centro depende de uno superior, excepto el centro superior de todos. La jerarquía de centros puede usarse para controlar la visibilidad de propuestas en la agenda, o restringir acceso al expediente de cliente en base al usuario asignado al centro gestor del cliente.

### En resumen
- Empleado: El login de Windows.
- Usuario: Usuario lógico, indica el pefil y el centro. Puede haber más de uno para un mismo empleado, pero siempre se elige uno al entrar a la aplicación.

### Base de datos
En base de datos estas entidades están en estas tablas:
- Empleados: Tabla `SSEmpleados`
- Usuarios: Tabla `SSUsuarios`
- Centros: Tabla `SSCentros`
- Jerarquía de centros: Tabla `SSJerarqCent` (solo la relación directa) y `vwSSJerarqCent` (incluye para cada centro todos los superiores)
- Perfiles: Tabla `SSPerfil`

## Permisos de acceso
También llamado Facultades de Acceso, se definen por base de datos.

Cada pantalla debe estar dada de alta en la tabla de elementos de seguridad (`SSElemEstruc`) y tener definido qué perfiles tienen acceso en la tabla `SSFacAcc`. En esta tabla se define para cada perfil y elemento, si se tiene acceso en modo modificación (`7`), consulta (`1`) o sin acceso (`0`). En caso de no existir elemento, se interpreta que no tiene acceso, y el usuario no podrá acceder a la pantalla (recibirá un error indicando que no tiene acceso).

Los controles de la pantalla pueden estar también definidos en la tabla `SSElemEstruc` indicando en qué pantalla están (contenedor). A diferencia de las pantallas (seguridad explícita), si un control no está definido, no aplica ninguna restricción (seguridad implícita). La seguridad de los controles solo se usa para restringir el acceso, no para otorgar acceso. Por ejemplo, se puede poner un control en modo consulta (`1`) o se puede ocultar (`0`) , pero si por código un control se oculta o se deshabilita, no se podrá mostrar o habilitar por seguridad.


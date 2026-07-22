---
title: SCACS Web - Conceptos de negocio
tags:
  - glosario
  - negocio
  - scacs
---
## Expediente de cliente
El expediente de cliente permite consultar todos los datos de un cliente. Entre otra información, se puede encontrar:
- Datos identificativos: Si es persona física o jurídica, segmento, dirección, edad, actividad
- Documentación asociada o adjuntos: Todos los documentos adjuntados en SCACS están asociados a un cliente, y opcionalmente se pueden asociar a otras entidades.
- Accionariado y Empresas Participadas: Vistas recíprocas, donde se puede consultar quiénes son los accionistas de una empresa, y un accionista en qué empresas participa.
- Proveedores y Clientes
- Posiciones: Activo y pasivo del cliente con el banco
- CIRBE o Banco Central: Deudas del cliente en todos los bancos nacionales, reportadas por el banco central.
- Patrimonio: Inmuebles y otro patrimonio declarado del cliente
- IRPF, Declaración de Bienes: Información fiscal de personas físicas
- Estados contables o Balances: Información contable de empresas
- Rating: Normalmente evaluado a partir del resto de información del cliente
- Informes: Documento con toda la información del expediente

En la base de datos el cliente se le asigna un identificador interno, llamado **firma**, pero este identificador no es visible en la interfaz de usuario. La identificación del cliente por parte de los usuarios de la aplicación suele ser por número de documento de identidad, a menudo acompañado del tipo de documento y el país.

La entidad principal de clientes en base de datos es la tabla `ECClientes`. 
## Propuesta
Una propuesta, o solicitud, identifica una solicitud de crédito para un cliente, que debe ser evaluada y eventualmente otorgada o denegada.

La propuesta sigue un **flujo** o **workflow**, pasando por diversas etapas, normalmente en este orden:
- **Captura de datos:** El gestor del cliente incluye la información de los intervinientes de la operación solicitada (titulares, avalistas), los detalles de la operación que se solicita (tipo de producto, importe, plazo, condiciones como comisiones e intereses...), documentación aportada, informes, garantías y consultas a buró externos. En algunos casos, una propuesta puede tener varias operaciones, y cuando esto sucede existirá una lista de **financiaciones** con el detalle de cada una.
- **Análisis y opinión:** En ocasiones la propuesta es evaluada por un *scoring* automático que da un primer dictamen. Un analista o director de oficina debe evaluar la solicitud y aprobarla o denegarla. Aquí un **motor de atribuciones** evalúa si el usuario puede aprobar la solicitud, en base al importe de la operación (*riesgo*) o condiciones de la misma (*precio*), y en caso de no tener atribuciones, deberá elevar la operación a etapas que tratarán otros usuarios que sí tengan las atribuciones necesarias, normalmente un **comité**.
- **Tramitación**: Una vez aprobada la operación, puede ser necesario rellenar información adicional, como por ejemplo los datos de la cuenta corriente donde se desembolsará el préstamo, domicilio donde enviar la tarjeta de crédito, o la tasación de los inmuebles o garantías.
- **Firma de contrato**: Datos de la firma del contrato en la oficina o ante notario.
- **Alta contable**: El contrato se da de alta en *host* (el core bancario) y se procede a desembolsar el dinero en la cuenta del cliente.

En base de datos la propuesta se identifica con un código de 20 caracteres (siempre números), estructurado como 6 caracteres que identifican el centro, 4 caracteres identifican el año de creación de la propuesta, y 10 caracteres que identifican el número secuencial de propuesta dentro del centro y el año. El centro y número secuencial siempre relleno con ceros a la derecha hasta completar el ancho total. Ejemplo: `00001020260000000245` sería un identificador de propuesta, o número de propuesta, que siempre se formatea visualmente separando el centro, año y secuencial con puntos cuando se presenta al usuario. Ejemplo: `000010.2026.0000000245`.

## Agenda
Pantalla principal de trabajo donde se listan las etapas de propuestas asignadas la usuario, y también consultar las etapas disponibles que el usuario puede asignarse para trabajar. Para evitar problemas de concurrencia, un usuario debe asignarse la tarea antes de poder entrar a modificar datos o finalizar la etapa del flujo. La vista está dividida en dos (muestra unas u otras según un radio button seleccionado):
- Tareas asignadas: Asignadas al usuario actual, el usuario puede modificar, desbloquear (liberar la tarea para que la pueda tomar otro usuario), finalizar, cancelar.
- Tareas disponibles: Etapas sobre las que el usuario tiene permiso para modificar (ver [[seguridad]]), y visibilidad a nivel centro, y no están asignadas a nadie. El usuario puede asignarse la tarea para que pase a asignada.

### Resumen
Una pantalla relevante de la agenda y de propuestas es la pantalla de **resumen**. Esta pantalla muestra los datos básicos de la propuesta y el cliente, una lista de financiaciones (en caso de que exista la opción de multifinanciación), y las etapas por las que ha pasado la financiación seleccionada o la propuesta, para poder consultar todas las etapas por las que ha pasado.

## Actas
Gestiona las actas de comité, cuando una propuesta debe ser aprobada por comité. En cada acta se informa la fecha del comité, los asistentes, y las propuestas sometidas a aprobación del comité, generando un documento con los dictámenes.

## Seguimiento
Periódicamente, o bajo de manda, se analiza la capacidad crediticia y solvencia de un cliente, y se determina su *política asignada*. La política asignada puede determinar que se debe reducir la deuda del cliente por aumentar el riesgo de impago. Es una agenda similar a la de propuestas, y un flujo muy reducido de 2 o 3 estados.

## Administrador
Módulo donde gestionar los parámetros, catálogos, usuarios, empleados, centros y otras configuraciones
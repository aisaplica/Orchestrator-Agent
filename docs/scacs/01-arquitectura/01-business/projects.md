---
title: SCACS Web - División en Módulos o Proyectos
---
La parte de negocio está dividida en estos módulos o proyectos (DLLs):

## Proyectos de arquitectura
Normalmente no se tienen que hacer modificaciones en estos proyectos.
- AIS.Configuration: Acceso al archivo de configuración
- AIS.PR.BR: Proyecto base de negocio con clases comúnmente usadas.
- AIS.PR.BR.IN: Inicialización y menú
- AIS.PR.BR.LCT: Conector de negocio
- AIS.PR.BR.NT: Acceso a notas y generación de documentos
- AIS.PR.DA: Acceso a base de datos
- AIS.PR.OpenXMLDocument: Generación y lectura de documentos Word y Excel
- AIS.PR.SF: Clases de modelo, excepciones, constantes, enumeraciones, clases y métodos estáticos y utilidades
- AIS.TOOLS: Utilidades de logging y envío de mails
- log4net.vs2010: Biblioteca de logging
- SeguridadDll: Rutina de acceso a seguridad

## Proyectos generales
- AIS.PR.BR.AC: Actas
- AIS.PR.BR.ADM.CA: Administración, catálogos.
- AIS.PR.BR.ADM.PC: Administración, parámetros de configuración.
- AIS.PR.BR.ADM.PD: Administración, parámetros de decisión y dictámenes.
- AIS.PR.BR.ADM.SG: Administración, seguimiento y alertas
- AIS.PR.BR.ADM.SS: Administración, Seguridad
- AIS.PR.BR.ADM.WF: Administración, diseñador de workflow
- AIS.PR.BR.AG: Agenda
- AIS.PR.BR.AL: Alertas
- AIS.PR.BR.CM: Centro de mensajes
- AIS.PR.BR.EC.AN: Expediente de Cliente y Expediente de Grupo, Análisis
- AIS.PR.BR.EC.CE: Expediente de Cliente y Expediente de Grupo, CIRBE y Buró
- AIS.PR.BR.EC.CL: Expediente de Cliente y Expediente de Grupo, General de cliente
- AIS.PR.BR.EC.ID: Expediente de Cliente y Expediente de Grupo, Datos Identificativos
- AIS.PR.BR.EC.IN: Expediente de Cliente y Expediente de Grupo, Inicialización
- AIS.PR.BR.EC.RN: Expediente de Cliente y Expediente de Grupo, Resumen
- AIS.PR.BR.FR: Control de atribuciones de riesgo
- AIS.PR.BR.FS: Control de atribuciones de precio
- AIS.PR.BR.GI: Generador de Informes
- AIS.PR.BR.PR: Propuestas Particulares
- AIS.PR.BR.PR.AN: Etapas de Análisis y Sanción
- AIS.PR.BR.PR.ID: Etapas de captura de datos
- AIS.PR.BR.PR.TR: Etapas de Tramitación
- AIS.PR.BR.PG: Propuestas generales o Propuestas de Empresas
- AIS.PR.BR.PG.FB: Financiación Base
- AIS.PR.BR.PG.FN: Financiación
- AIS.PR.BR.PG.GA: Garantías
- AIS.PR.BR.PG.IN: Intervinientes
- AIS.PR.BR.SG: Seguimiento

## Organización de clases dentro de proyectos
La mayoría de proyectos tendrán esta organización de clases:
- BPC: Punto único de entrada del conector. Tiene referencias directas a clases de BE del mismo proyecto. En métodos de carga de pantalla, realiza la carga de textos, validaciones, seguridad, cabecera, catálogos, y datos de negocio.
- Clases con sufijo BE: Contienen la lógica de negocio. Nunca realizan acceso a base de datos directamente, esto se hace en las clases DALC. Pueden hacer llamadas a servicios. Pueden hacer referencias a métodos de otras clases BE. Generalmente solo acceden a la clase DALC relacionada (por ejemplo, la clase DatosIdentificativosBE accederá a DatosIdentificativosDALC).
- Clases con sufijo DALC: Acceden a base de datos (consultas, actualizaciones), evitarán realizar lógica compleja.

## Buenas prácticas
- El código de negocio debe escribirse en el proyecto más relevante, reaprovechando si es posible métodos de lectura o escritura de datos
- Evitar el uso de referencias directas entre proyectos, usar el conector de negocio para llamar a métodos de otros proyectos de negocio, evitando así dependencias circulares.
---
title: SCACS Web - Workflow - Mapa de tablas WF*
tags: [scacs, ai, workflow, bd, tablas]
source: "AF - Workflow.docx (601108-AF-Workflow, v001.002, 10/12/2020)"
---

# Workflow SCACS Web — Mapa de tablas `WF*`

Tablas que sustentan el workflow, agrupadas por su función. Los nombres de columna
concretos deben verificarse contra el esquema real de BD (el agente
`orchestrator-workflow` los consulta con `get_table_schema`); esta página fija el
**rol** de cada tabla según el documento funcional.

## Repositorio / definición del flujo (parametrización)

| Tabla | Rol | Claves / notas |
|---|---|---|
| `WFModelo` | Define un modelo (flujo completo) | — |
| `WFEtapa` | Etapa dentro de un modelo | Columna `IDFORMULARIO` → formulario a abrir |
| `WFRepEtapa` | Nombre de la etapa, independiente del modelo | — |
| `WFRepFormulario` | Ruta de pantalla + modo de acceso + contenedor (`PageSessionContainer`) por formulario | Referenciada desde `WFEtapa.IDFORMULARIO` |
| `WFTransicion` | Conexión entre etapas: por señal, modelo y etapa destino + expresión de activación | Una señal puede tener varias filas (destinos en paralelo); modelo destino `*` = volver al flujo de origen |
| `WFRepSenyalesFuncion` | Parametriza qué señales puede emitir una función vía `SendSignal` y cuándo | Si la señal no está aquí, el cambio de señal se ignora |

## Estado y traza del objeto base (datos de negocio)

| Tabla | Rol | Retención |
|---|---|---|
| `WFBDObjetoBase` | Estado **actual**: solo etapas **activas**. Estado (asignada/disponible), fecha inicio, usuario asignado, secuencial actual, Centro Visible | Las etapas finalizadas **se borran** |
| `WFBDResumen` | **Histórico** de todas las etapas recorridas. Fecha inicio/fin, usuario que finalizó, estado de finalización (cancelada/finalizada), evento de finalización | **Nunca se borra**; incluye `Secuencial` en la clave |
| `WFBDVariableObjetoBase` | Variables de activación **pendientes** a nivel de objeto base, a la espera de completar la expresión de activación de una etapa destino | Se eliminan al activarse la etapa |

## Claves comunes del objeto base

`WFBDObjetoBase` y `WFBDResumen` se identifican por:

- Número de propuesta
- Número de financiación
- Modelo
- Etapa
- Secuencial — **solo** en `WFBDResumen`

## Historial de versiones del documento funcional

| Versión | Fecha | Cambio |
|---|---|---|
| 001.000 | 28/01/2015 | Versión inicial |
| 001.001 | 19/02/2015 | Centro Visible añadido a `WFBDObjetoBase` |
| 001.002 | 10/12/2020 | Regresar al flujo original (modelo destino `*`) independientemente del origen |

## Ver también

- [[04-workflow/workflow-overview]]
- [[04-workflow/workflow-conexiones]]
- [[04-workflow/workflow-funciones]]
- [[01-arquitectura/01-business/transaction-control]] — `DataAccessKey`

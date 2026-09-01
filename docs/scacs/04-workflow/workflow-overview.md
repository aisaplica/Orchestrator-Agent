---
title: SCACS Web - Workflow - Visión general
tags: [scacs, ai, workflow, overview]
source: "AF - Workflow.docx (601108-AF-Workflow, v001.002, 10/12/2020)"
---

# Workflow SCACS Web — Visión general

Diseño funcional del **Workflow** de SCACS Web: cómo se modela un flujo, qué
entidades lo componen y cómo se materializa sobre las tablas `WF*`.

> El documento funcional original contiene 3 diagramas (transiciones señal→destino,
> unión de etapas en paralelo, resolución de transición tras funciones). No son
> convertibles a texto; su contenido está descrito en
> [[04-workflow/workflow-conexiones]] y [[04-workflow/workflow-funciones]].

## Propósito

Un Workflow encadena **etapas** (puntos del flujo, cada una con una pantalla
asociada) mediante **transiciones** disparadas por **señales** de finalización.
El objeto que recorre el flujo es el **objeto base**: el número de propuesta de
SCACS y, opcionalmente, su financiación asociada.

## Entidades

| Entidad | Qué identifica | Tabla(s) principales |
|---|---|---|
| **Modelo** | Un flujo de workflow completo | `WFModelo` |
| **Etapa** | Un punto del flujo (dentro de un modelo) | `WFEtapa`, nombre en `WFRepEtapa` |
| **Estado** | Estado en que puede estar una etapa (asignada / disponible) | `WFBDObjetoBase` |
| **Señal** | Evento de finalización posible de una etapa | usada en `WFTransicion` |
| **Función** | Código que se ejecuta al transicionar entre etapas | `WFRepSenyalesFuncion` |
| **Objeto base** | Nº de propuesta (+ financiación opcional) que recorre el flujo | `WFBDObjetoBase`, `WFBDResumen` |

Un modelo consta de varias etapas que se conectan entre sí formando el workflow.

Mapa completo de tablas: [[04-workflow/workflow-tablas]].

## Etapas

- La etapa indica **qué página abrir** al consultar o modificar. Es **la misma
  página** en ambos casos; solo cambia el **modo de acceso** (consulta o
  modificación).
- El formulario asociado a la etapa dentro de un modelo se guarda en `WFEtapa`,
  columna `IDFORMULARIO`.
- La tabla `WFRepFormulario` define, para cada formulario: la **ruta de pantalla**
  que se abre, el **modo de acceso** y el **contenedor** (`PageSessionContainer`)
  al que pertenece.
- El **nombre** de la etapa se mantiene en una entidad independiente del modelo:
  `WFRepEtapa`.
- La etapa puede llevar una **expresión de activación** que debe cumplirse para
  activarla — mecanismo para unir etapas en paralelo (ver
  [[04-workflow/workflow-conexiones]]).
- Al finalizar la etapa, el usuario indica la **señal de finalización**, que
  determina a qué etapa (del mismo flujo o de otro) se irá.

## Objeto base

El objeto base mantiene en todo momento el modelo, la etapa activa y su estado.

Dos tablas, con propósitos distintos:

| Tabla | Contenido | Retención |
|---|---|---|
| `WFBDObjetoBase` | Estado **actual**: solo etapas **activas** | Las etapas finalizadas **se borran** (tabla pequeña, mejor rendimiento) |
| `WFBDResumen` | **Histórico** de todas las etapas por las que ha pasado el objeto base | **No se borra** información |

### Claves

- Número de propuesta
- Número de financiación
- Modelo
- Etapa
- Secuencial (**solo** en el histórico `WFBDResumen`)

### Campos de `WFBDObjetoBase` (estado actual)

- Estado de la etapa: **asignada** o **disponible**
- Fecha de inicio de la etapa
- Usuario al que está asignada (si lo está)
- Secuencial actual de la etapa
- **Centro Visible**: determina qué usuarios de centros superiores tienen
  visibilidad sobre la etapa

### Campos de `WFBDResumen` (histórico)

- Fecha de inicio y fin de la etapa
- Usuario que la finalizó
- Estado de finalización (distingue etapa **cancelada** de **finalizada**)
- Evento (señal) de finalización empleado

## Ver también

- [[04-workflow/workflow-conexiones]] — transiciones, expresiones de activación, modelos cruzados
- [[04-workflow/workflow-funciones]] — funciones de activación y de finalización
- [[04-workflow/workflow-tablas]] — mapa de tablas `WF*`
- [[01-arquitectura/02-presentation/navigation]] — navegación entre formularios
- [[01-arquitectura/02-presentation/session-data]] — `PageSessionContainer`

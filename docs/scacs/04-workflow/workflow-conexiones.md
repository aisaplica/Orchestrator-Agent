---
title: SCACS Web - Workflow - Conexiones entre etapas
tags: [scacs, ai, workflow, transiciones]
source: "AF - Workflow.docx (601108-AF-Workflow, v001.002, 10/12/2020)"
---

# Workflow SCACS Web — Conexiones entre etapas

Cómo se define el paso de una etapa a otra, cómo se resuelven las activaciones en
paralelo y cómo se conectan modelos distintos.

Requisito previo: [[04-workflow/workflow-overview]].

## Transiciones (`WFTransicion`)

Desde una etapa se define, **para cada señal**, a qué modelo y etapa destino puede
ir. Todo ello vive en `WFTransicion`.

- Una misma señal puede tener **varias etapas destino** → se activan varias etapas
  **en paralelo**.
- Para cada etapa destino se puede indicar una **expresión de activación** que se
  generará en el destino (ver siguiente sección).

## Expresiones de activación

Sirven para que una etapa destino con **varias etapas de entrada** se active solo
cuando se cumplan ciertas condiciones (todas las entradas, o cualquiera de ellas).

- La expresión de activación de la **transición** se compara con la expresión de
  activación de la **etapa destino**.
  - Si **cumple** → la etapa se activa.
  - Si **no cumple** → la etapa **no se activa**; queda a la espera de que otra
    transición hacia la misma etapa complete la expresión.
  - Si **no se especifica** expresión → la etapa se activa **siempre**.
- La expresión es una **cadena de caracteres sin caracteres repetidos**.
- Ejemplo: etapa destino con condición `"AB"`. Para que se active cuando lleguen
  Etapa 1 **y** Etapa 2, se da la expresión `A` a la transición desde Etapa 1 y
  `B` a la transición desde Etapa 2.
- Las expresiones que aún no se cumplen se guardan a nivel de objeto base en
  `WFBDVariableObjetoBase` (variables pendientes).

### Algoritmo de activación de la etapa destino

1. Si la transición **no indica** ninguna variable de activación → la etapa se
   activa automáticamente.
2. Si la transición **indica** variables de activación → se comprueba contra las
   variables de activación de la etapa y las variables ya existentes en
   `WFBDVariableObjetoBase`:
   - **Cumple** → se activa la etapa y se **eliminan** las variables existentes de
     la tabla de pendientes.
   - **No cumple** → se **inserta** la variable en `WFBDVariableObjetoBase` para
     esa etapa y **no se crea** la etapa.

## Cierre de la etapa origen

Al cerrar (finalizar) la etapa:

- Se elimina la **asignación de la agenda** del usuario.
- Se informa en `WFBDResumen` la **fecha de finalización** y el **usuario**.

## Centro Visible en la etapa destino

- Al crearse la nueva etapa, su **Centro Visible** se hereda automáticamente del
  Centro Visible que tuviera la **etapa anterior**.
- Una **función de activación** de la etapa puede modificarlo posteriormente (ver
  [[04-workflow/workflow-funciones]]).
- Para la **primera etapa del flujo**, el Centro Visible se informa **desde
  negocio**.

## Conexiones entre etapas de modelos diferentes

Funcionan **exactamente igual** que entre etapas del mismo modelo. En
`WFTransicion` se especifica el **modelo de destino**; si es distinto al de la
etapa actual, la etapa se activa en ese otro modelo.

### Modelo destino `*` (asterisco)

Si en la transición el modelo destino es el valor especial `*`:

- Se interpreta que debe abrirse la etapa indicada **en el modelo desde donde se
  originó el modelo actual**.
- Permite definir un **subflujo común** entre varios flujos (o entre partes de un
  mismo flujo) y **retomar el flujo original** sin implementar lógica de
  finalización y creación de flujos nuevos.
- Añadido en la versión 001.002: se regresa al flujo original **independientemente
  de cuál sea su origen**.

### Etapa destino inexistente

Si la etapa destino **no existe** en el modelo destino → **el flujo termina**.

## Ver también

- [[04-workflow/workflow-funciones]] — qué se ejecuta durante la transición
- [[04-workflow/workflow-tablas]] — `WFTransicion`, `WFBDVariableObjetoBase`

---
title: SCACS Web - Workflow - Funciones de transición
tags: [scacs, ai, workflow, funciones]
source: "AF - Workflow.docx (601108-AF-Workflow, v001.002, 10/12/2020)"
---

# Workflow SCACS Web — Funciones de transición entre etapas

Las etapas permiten ejecutar **funciones** en dos momentos: al **activarse** y al
**finalizar** (según el evento de finalización elegido).

Requisito previo: [[04-workflow/workflow-overview]] y
[[04-workflow/workflow-conexiones]].

## Funciones de activación

- Se ejecutan **después** de que la etapa esté activa.
- Si una función lanza una excepción durante la activación:
  - Queda **registrada en el log**.
  - **No** deja la etapa en estado inconsistente.
- Pueden modificar el **Centro Visible** heredado de la etapa anterior.

## Funciones de finalización (por evento)

- Al finalizar una etapa, el usuario selecciona el **evento de finalización**
  (señal).
- Antes de realizar **ninguna** transición de etapa se ejecutan las funciones
  definidas para ese evento (podría no haber ninguna).
- Si una función lanza una excepción:
  - La excepción **se muestra por pantalla**.
  - La etapa **no cambia de estado**.

## Cambio de señal desde una función (`SendSignal`)

Una función puede **cambiar la señal recibida** para derivar la etapa a otro
destino:

- La función debe devolver un `DataSet` con:
  - una tabla `RESULT`,
  - una columna `SendSignal`,
  - una fila con la nueva señal en esa columna.
- La señal de salida **debe estar parametrizada** en `WFRepSenyalesFuncion`, que
  describe cuándo puede emitirse cada señal.
  - Si **no** está parametrizada → el cambio de señal **se ignora**.
- Cuando una función cambia la señal:
  - **Dejan de ejecutarse** las funciones de la señal anterior.
  - Se obtienen y ejecutan las funciones correspondientes a la **nueva** señal.

## Resolución de la transición

Una vez ejecutadas las funciones **sin error**:

1. Se busca en `WFTransicion` la conexión que corresponde a la **señal actual**.
2. Si **no hay** transición definida → la etapa se **finaliza sin crear** otra.
3. Si **hay** transición definida → se **crea la nueva etapa** (o etapas, si tiene
   varios destinos), aplicando el algoritmo de activación descrito en
   [[04-workflow/workflow-conexiones]].

## Ver también

- [[04-workflow/workflow-conexiones]] — algoritmo de activación, modelos cruzados
- [[04-workflow/workflow-tablas]] — `WFRepSenyalesFuncion`
- [[03-excepciones/business-exceptions]] — tratamiento de excepciones de negocio

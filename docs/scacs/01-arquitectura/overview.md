---
title: SCACS Web - Overview
tags: [scacs, ai, arquitectura]
---

# SCACS Web - Overview

## Propósito
SCACS Web es una aplicación web ASP.NET Web Forms desarrollada con .NET Framework 4 y C# 7.3.

## UI / Frontend
- ASP.Net Web Forms
- Diseño basado en MaterializeCSS.
- Enfoque en componentes reutilizables mediante controles personalizados.

## Arquitectura general
- Separación clara entre:
  - capa de presentación web (frontend)
  - capa de negocio (backend). Aquí estará el acceso a datos (base de datos y servicios), y la lógica principal
- Uso intensivo de:
  - `DataSet` como contenedor de datos a pasar entre capas
  - `FormData` es el `DataSet` que contiene los datos que se han de mantener en la página actual entre PostBacks, y se mantiene incluso si se navega a otra página y luego se regresa de nuevo a la página actual.
  - `PageSessionContainer` como envoltorio de datos de sesión de la página. Una de sus propiedades es el `FormData`. Sirve para enviar datos a la siguiente página durante la navegación, o recuperar los datos al volver a una página anterior.

## Conceptos clave
- Formulario base como núcleo del comportamiento común.
- Ciclos de carga y guardado definidos.
- Navegación basada en estado en sesión.
- Seguridad y modo de acceso gestionados de forma centralizada.

## Objetivo de estos documentos
Permitir a un agente de IA:
- entender el flujo de datos,
- localizar puntos de extensión,
- modificar comportamiento sin romper el ciclo base.
# Checklist de encuadre de requerimiento

Subconjunto adaptado de la skill `prompt-master` (patrones de tarea/contexto/alcance que causan
re-trabajo). Usar antes de redactar un requerimiento técnico a partir de una descripción vaga
(issue de Mantis, petición de usuario en texto libre).

**Uso:** `references/encuadre-checklist.md` — leído por `skills/mantis/SKILL.md` (Fase 2) y por
`agents/planner.md` (bloque de salida). Corregir en silencio; solo marcar "Dudas pendientes" si la
corrección cambia la intención del usuario.

---

## Patrones a detectar y corregir

| # | Patrón | Ejemplo vago | Corrección |
|---|--------|--------------|------------|
| 1 | Verbo de tarea vago | "revisar el módulo de propuestas" | Verbo + operación precisa: "corregir el cálculo de comisión en `CalcularComision()`" |
| 2 | Descripción emocional | "no funciona", "está roto", "falla todo" | Fallo técnico concreto: "lanza `NullReferenceException` al guardar cuando `cliente.Direccion` es null" |
| 3 | Sin criterios de aceptación | (ninguno) | Derivar 1-3 criterios binarios verificables desde el objetivo declarado |
| 4 | Sin alcance de archivos/tablas | "afecta a expedientes" | Alcance explícito: archivos `.aspx`/`.cs` concretos, tablas BD concretas si se conocen |
| 5 | Dos cambios en un requerimiento | "arreglar X y de paso mejorar Y" | Separar: requerimiento principal + nota de "fuera de alcance" para lo secundario |
| 6 | Alcance "todo el módulo" | "revisar toda la pantalla de propuestas" | Acotar al síntoma reportado; ampliar solo si el planner lo justifica en su análisis |
| 7 | Asume contexto no escrito | "como la vez pasada" | Reescribir el requerimiento completo sin referencias implícitas a conversaciones previas |

---

## Esqueleto de salida (Objetivo / Alcance / Criterios)

Aplicar tras corregir los patrones anteriores:

```
Objetivo:
  <Verbo preciso + qué debe cambiar, una frase>
Contexto:
  <Comportamiento actual, cuándo y cómo se reproduce el fallo>
Alcance:
  <Archivos, pantallas (CTFORM) o tablas concretas afectadas>
Fuera de alcance:
  <Qué NO se toca, si aplica>
Criterios de aceptación:
  - <criterio binario 1>
  - <criterio binario 2>
Dudas pendientes:
  - <solo si persiste ambigüedad tras aplicar el checklist>
```

No forzar un criterio o alcance inventado si el issue no da suficiente información — en ese caso
dejarlo en "Dudas pendientes" y preguntar al usuario, nunca asumir.

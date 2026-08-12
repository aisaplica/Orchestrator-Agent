---
name: orchestrator-pantallas
description: 'Usar cuando el usuario mencione una pantalla por nombre (p.ej. "pantalla de propuestas", "gestión de clientes", "búsqueda de expedientes") en proyectos ScacsWeb Online y necesite saber su código (CTFORM/CTMAPEO). También con /orchestrator-pantallas o frases como "qué código tiene la pantalla X", "busca la pantalla X", "código de pantalla".'
---

# Pantallas — Resolución nombre → código

Consulta `SICONTROLES` + `SIIDIOMA` para obtener el código (`CTFORM`/`CTMAPEO`) de una pantalla a partir de su nombre funcional. Sin mantenimiento de MD — los datos vienen siempre de BD.

## Cuándo usar

- Usuario menciona una pantalla por nombre y necesita su código para navegar al código fuente
- Antes de buscar ficheros `.aspx`/`.cs` de una pantalla concreta
- `/orchestrator-pantallas <nombre>`

## Proceso

1. Extraer el nombre de pantalla del mensaje del usuario (una o varias palabras clave)
2. Resolver workspace (per `orchestrator-agent` SKILL.md sección "Workspace y Rutas")
3. Ejecutar via `mcp__orchestrator-workspace__db_query(workspace, sql)`:

```sql
SELECT SC.CTFORM, SC.CTMAPEO, SC.CTTEXTO, SI.IDDESCRIPCION
FROM SICONTROLES SC
JOIN SIIDIOMA SI ON SC.CTTEXTO = SI.IDTEXTO
WHERE SC.CTTIPO = 3
  AND SC.CTFORM = SC.CTMAPEO
  AND SI.IDIDIOMA = 'ESP'
  AND UPPER(SI.IDDESCRIPCION) LIKE UPPER('%<nombre>%')
ORDER BY SI.IDDESCRIPCION
```

Sustituir `<nombre>` por las palabras clave extraídas del mensaje.

4. Si devuelve 0 filas → intentar términos más cortos o sinónimos; informar si persiste
5. Si devuelve 1 fila → usar `CTFORM` como código de pantalla y continuar la tarea
6. Si devuelve múltiples filas → mostrar tabla y pedir selección al usuario

## Output (cuando hay resultado)

```
## Pantalla encontrada
| CTFORM | Descripción |
|--------|-------------|
| PRPROP | Gestión de Propuestas |

Código: PRPROP — continuando con la tarea...
```

## Errores comunes

| Situación | Acción |
|-----------|--------|
| 0 filas con término largo | Probar con parte del nombre (p.ej. "propuesta" → "prop") |
| Múltiples coincidencias | Mostrar tabla, pedir confirmación antes de continuar |
| `db_query` falla | Verificar que workspace tiene configuración BD (`get_db_config`) |

## Nota de diseño

Las pantallas en `SICONTROLES` cumplen `CTTIPO=3` y `CTFORM=CTMAPEO`. El `CTFORM`/`CTMAPEO` es el código de la pantalla usado en nombres de fichero `.aspx` y clases `.cs` en el scope de la solución.

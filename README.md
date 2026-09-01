# orchestrator-skill-full

Plugin Claude Code para proyectos ScacsWeb (ASP.NET / C# / .NET Framework 4.0).
Proporciona un pipeline completo de desarrollo: analisis, implementacion, validacion,
build y gestion de modelo de base de datos, con soporte SVN y Oracle/SQL Server.

---

## Prerrequisitos

- Claude Code (ultima version)
- Python 3.9 o superior
- Git (para clonar e instalar el plugin)
- Acceso al repositorio Git interno

---

## Instalacion

### 1. Instalar el plugin en Claude Code

```
/plugin install <url-del-repositorio-git-interno>
```

Claude Code clonara el repositorio e instalara el plugin y el servidor MCP.

### 2. Instalar dependencias Python

Ejecutar una vez por maquina:

```powershell
cd <directorio-del-plugin-instalado>
.\setup.ps1
```

El script verifica Python 3.9+, instala `mcp` y `fastmcp`.

### 3. Verificar instalacion

En Claude Code:

```
/orchestrator-historial
```

Si el plugin esta activo, el agente respondera con el historial de ejecuciones.
El servidor MCP (`orchestrator-workspace`) arranca automaticamente al primer uso.

---

## Agentes disponibles

### Pipeline y validacion

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-validator` | Valida compilacion y coherencia logica del codigo |
| `/orchestrator-fixer` | Corrige errores detectados por validator |
| `/orchestrator-validar-entorno` | Verifica entorno: AIS, SVN, dotnet, modelo BD |
| `/orchestrator-validar-req` | Valida si un commit SVN/Git cumple el requerimiento |

### Analisis y revision

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-review` | Revision de codigo con veredicto APRUEBA/CAMBIOS/BLOQUEA |
| `/orchestrator-auditoria` | Revision de calidad y convenciones ScacsWeb |
| `/orchestrator-security` | Auditoria de seguridad: SQL injection, XSS, secretos |
| `/orchestrator-impacto` | Mapa de impacto de un cambio propuesto |
| `/orchestrator-deps` | Mapa de dependencias entre proyectos de una solucion |
| `/orchestrator-estructura` | Visualiza capas y dependencias de una solucion |
| `/orchestrator-explicar` | Explica que hace una clase/metodo/proceso en lenguaje natural |
| `/orchestrator-perf` | Perfil de rendimiento: N+1, consultas lentas, locks |
| `/orchestrator-dead-code` | Detecta codigo muerto: clases, metodos y rutas sin usar |
| `/orchestrator-hotspots` | Ficheros con mayor frecuencia de cambio y riesgo de conflicto |
| `/orchestrator-doc-drift` | Detecta documentacion desincronizada con el codigo |

### Historial y VCS

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-historial` | Historial SVN/Git con autor, fecha y mensaje por revision |
| `/orchestrator-stats` | Estadisticas de uso del pipeline |
| `/orchestrator-diff-svn` | Diff SVN de una revision o rango |
| `/orchestrator-commit-svn` | Prepara y ejecuta commit SVN con mensaje estructurado |

### Base de datos y modelo

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-comparar-modelo` | Compara modelo BD local con esquema real |
| `/orchestrator-schema` | Muestra esquema completo de tabla(s): columnas, tipos, indices, relaciones |
| `/orchestrator-seed` | Genera INSERT sinteticos para una tabla respetando tipos, NULLs y FKs |
| `/orchestrator-sync-indexes` | Sincroniza indices Oracle al modelo BD JSON del workspace |
| `/orchestrator-comparar-entornos` | Compara esquema BD entre dos workspaces (dev vs produccion) |
| `/orchestrator-migrar` | Migra DALCs y SQL entre Oracle y SQL Server |
| `/orchestrator-pantallas` | Busca el codigo de pantalla (CTFORM) a partir de su nombre funcional en SICONTROLES + SIIDIOMA |

### Scaffolding y generacion

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-generar-dalc` | Genera clases DALC + BE ScacsWeb a partir del esquema de una tabla |
| `/orchestrator-incidencia` | Genera script SQL de incidencia idempotente y lo registra en Mantis |
| `/orchestrator-init` | Bootstrap de workspace: workspace.json, carpetas y modelo BD inicial |
| `/orchestrator-rename` | Renombra un simbolo C# y todas sus referencias en la solucion |
| `/orchestrator-format` | Detecta y aplica correcciones de convencion ScacsWeb |

### Produccion y operaciones

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-log-errores` | Analiza log de errores web, deduplica por firma y abre tareas Mantis por tipo |
| `/orchestrator-mantis` | Consulta issues MantisBT: fetch individual o listado por proyecto |

### Utilidades

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-dashboard` | Dashboard HTML con KPIs y ultimas ejecuciones del pipeline |
| `/orchestrator-documentar` | Genera documentacion de una clase/modulo en formato ScacsWeb |
| `/orchestrator-workflow` | Consulta la documentacion funcional del Workflow (etapas, señales, transiciones, tablas WF*), cruzada con el esquema real |
| `/orchestrator-idiomas` | Gestion de literales multiidioma |
| `/orchestrator-help` | Renderiza README y CHANGELOG del plugin como pagina HTML |

---

## Arquitectura ScacsWeb asumida

El plugin asume la arquitectura estandar de proyectos ScacsWeb:

- Framework: ASP.NET WebForms / .NET Framework 4.0 / C# 7.3
- VCS: SVN (TortoiseSVN primario), Git secundario
- Bases de datos: Oracle 19c y/o SQL Server
- Estructura de solucion: modulos funcionales (`AIS.PR.BR.EC.CL`)
  con clases BPC + *BE + *DALC dentro del mismo proyecto
- Rutas AIS: `C:\AIS\<proyecto>\bin\` (Batch), `C:\AIS\<proyecto>\Web\` (Online)
- Rutas workspace: raiz trunk SVN del proyecto

Si tu proyecto sigue una arquitectura diferente, algunos agentes pueden necesitar ajuste.

---

## Servidor MCP

El servidor MCP `orchestrator-workspace` provee herramientas de:
- Analisis de VCS (SVN/Git diff, log)
- Compilacion y tests (.NET)
- Consultas a BD (Oracle/SQL Server via XMLConfig.xml)
- Gestion del modelo BD (JSON local)
- Busqueda de simbolos en codigo

El servidor corre en la maquina local del usuario (`stdio`).
Configuracion: `.mcp.json` en la raiz del plugin.

---

## Novedades v1.9.0

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-dead-code` + grafo** | Calcula grado de entrada por nodo directamente sobre `graph.json` (Bash/python) en vez de Grep por scope — grado 0 = candidato, cobertura exhaustiva del proyecto. |
| **`/orchestrator-cobertura` + grafo** | Determina cobertura en una sola pasada sobre el grafo (edges de test hacia produccion) y prioriza por "God Nodes" en vez del orden plano DALC>BE>UI. |
| **`/orchestrator-doc-drift` + grafo** | Amplia los modulos afectados por un diff con dependencias indirectas (multi-hop) via `graphify query`, ademas de los ficheros directamente tocados. |

## Novedades v1.8.0

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-explicar` + grafo** | Usa `graphify explain` como fuente primaria de la explicacion (proposito, modulo/comunidad, conexiones) mas `graphify query` para dependencias y tablas BD. Siempre verifica contra el codigo fuente real antes de dar por buena la respuesta del grafo. |
| **`/orchestrator-hotspots` + grafo** | Cruza los `god_nodes` ya calculados por graphify (grado de conectividad, sin coste LLM) con el churn VCS en vez de estimar complejidad por LoC. Completa el ranking con LoC si hay menos de 15 god nodes. |

## Novedades v1.7.0

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-impacto` + grafo** | El agente de impacto ahora usa el grafo de conocimiento (`graphify-out/graph.json`) del proyecto cuando existe: impacto multi-hop directo/indirecto via `graphify query`, con Grep manual como fallback si el proyecto no tiene grafo generado. |
| **Fix pipeline principal** | `skills/orchestrator-agent/SKILL.md` (entry point real) le faltaba el paso "Graphify Update" tras Build — solo estaba en el `SKILL.md` legacy. El grafo nunca se refrescaba tras un build exitoso. Sincronizado. |

## Novedades v1.6.4

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-pantallas`** | Nuevo skill que resuelve el codigo de pantalla (`CTFORM`) a partir de su nombre funcional consultando `SICONTROLES JOIN SIIDIOMA` en BD. Elimina el MD de directorio de pantallas — siempre actualizado desde la BD. |
| **Resolucion automatica de pantallas** | Cualquier via de entrada al pipeline (pipeline principal, modos directos, agentes internos) detecta nombres funcionales de pantalla y los resuelve via BD antes de continuar. Cero mantenimiento manual. |
| **Planner — Paso 0** | Si el cambio describe una pantalla por nombre, el planner resuelve el `CTFORM` antes de planificar. |
| **idiomas-standalone** | Si el usuario especifica una pantalla por nombre en lugar de codigo, el agente la resuelve automaticamente antes de filtrar controles. |

## Novedades v1.6.2

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-log-errores`** | Nuevo comando: analiza log de produccion (NLog, ELMAH, AgendaWeb AIS), deduplica errores por firma SHA1 y abre tareas Mantis por tipo. El log crudo nunca entra en contexto del agente. |
| **Autodeteccion MSBuild/dotnet** | `compile_check` ya no falla en soluciones WebForms/.NET Framework. `lib-msbuild.ps1` lee los `.csproj` y elige MSBuild de Visual Studio o CLI `dotnet` automaticamente. |
| **compile-check.ps1** | Hook creado (faltaba — era la causa del fallo sistematico de `compile_check`). Acepta `MSB####`, `NU####` ademas de `CS####`. Fuerza idioma `en` durante la compilacion. |
| **mantis-cli create** | Accion `create` anadida a `mantis-cli.ps1`: crea issues via REST con `Summary`, `Description`, `Category`, `Priority`, `Severity`, `Tags`. |
| **parse_web_log (MCP)** | Nueva tool MCP que llama a `parse-weblog.ps1` — parse de logs sin cargar el fichero en contexto. |

## Novedades v1.6.1

| Mejora | Descripcion |
|--------|-------------|
| **`/orchestrator-incidencia`** | Genera script SQL de incidencia idempotente (template DDL+DML) y lo registra como nota privada en Mantis. Integrado en el pipeline como paso opcional post-implementacion. |
| **Salida MCP compacta** | JSON sin espacios en herramientas de analisis → ~21% menos tokens por respuesta |
| **Runner optimizado** | Transcript leido en cola de 400 lineas (vs lectura completa) → inicio rapido en sesiones largas |
| **batch_find_symbols** | Busqueda multi-simbolo con una sola pasada `Select-String` — N veces mas rapido |
| **visible:false (Oracle)** | Tablas sin permisos en `ALL_TABLES` se marcan `visible: false` en lugar de eliminarse |
| **Escritor canonico model.json** | Toda escritura del modelo pasa por `_write_model_json` (UTF-8 BOM, CRLF, indent=2) — elimina bug de inflado 1.1→3.5MB de `ConvertTo-Json` PS5.1 |
| **get-config.ps1** | Nuevo hook: lee `XMLConfig.xml` y devuelve configuracion BD como JSON |
| **find-symbol.ps1** | Nuevo hook multi-simbolo con patron `Select-String` unico — reemplaza la version anterior de un solo simbolo |

---

## Soporte

Repositorio interno ScacsWeb / Ingenieros.

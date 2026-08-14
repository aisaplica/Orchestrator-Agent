---
title: Orchestrator Skill Full — Guía de instalación y uso
tags: [plugin, claude-code, ia, scacsweb, orchestrator]
version: v1.8.0
fecha: 2026-08-14
autor: david.gandoy@ubimia.com
---

# Orchestrator Skill Full — Guía de instalación y uso

Plugin de Claude Code para proyectos **ScacsWeb** (ASP.NET / C# / .NET Framework 4.0).  
Proporciona un pipeline completo de desarrollo asistido por IA: análisis, implementación, validación, build, gestión de modelo de base de datos, historial SVN/Git y mucho más.

---

## ¿Qué hace este plugin?

El plugin extiende Claude Code con **44 comandos de barra** (`/orchestrator-*`) y un **servidor MCP local** (`orchestrator-workspace`) que conecta Claude con las herramientas nativas del proyecto: compilador .NET, SVN/Git, Oracle/SQL Server y el modelo de base de datos en JSON.

### Valor principal

| Sin el plugin | Con el plugin |
|---|---|
| Claude no conoce la estructura ScacsWeb | Entiende BPC + BE + DALC, capas, AIS |
| Sin acceso a BD | Consulta Oracle/SQL Server vía XMLConfig.xml |
| Sin acceso a SVN | Lee diff, log y estado SVN/Git |
| Sin compilador | Invoca MSBuild y valida errores |
| Sin modelo BD | Compara modelo JSON local vs esquema real |
| Contexto BBDD en skill externo | Contexto BBDD integrado en el plugin (`env.json`) |

---

## Prerrequisitos

| Requisito | Versión mínima | Verificar |
|---|---|---|
| **Claude Code** | Última disponible | `claude --version` |
| **Python** | 3.9 o superior | `python --version` |
| **Git** | Cualquier versión reciente | `git --version` |
| **PowerShell** | 5.1 (incluido en Windows 10/11) | — |
| **SVN CLI** | Opcional (para comandos SVN) | `svn --version` |
| **dotnet / MSBuild** | .NET Framework 4.0+ | `dotnet --version` |

---

## Instalación desde Git

### Paso 1 — Instalar el plugin en Claude Code

Abre Claude Code y ejecuta el siguiente comando de barra:

```
/plugin install https://github.com/aisaplica/Orchestrator-Agent.git
```

Claude Code clonará el repositorio e instalará el plugin y el servidor MCP automáticamente.

> **Nota:** Si tu red corporativa requiere proxy o certificado SSL personalizado, configúralo en Git antes de ejecutar este comando.

### Paso 2 — Instalar dependencias Python

Ejecutar **una sola vez** por máquina. Abre PowerShell en el directorio donde Claude Code instaló el plugin:

```powershell
cd <directorio-del-plugin-instalado>
.\setup.ps1
```

El script realiza automáticamente:
- Verifica que Python 3.9+ esté disponible
- Instala los paquetes `mcp` y `fastmcp`
- Configura el servidor MCP local

El directorio del plugin suele estar en:
```
C:\Users\<tu-usuario>\.claude\plugins\cache\orchestrator-skill-full\
```

### Paso 3 — Configurar credenciales (`env.json`)

El plugin incluye un archivo `env.template.json` con la estructura de configuración de entorno. Debes crear tu propio `env.json` (ignorado por Git, nunca se sube) con tus credenciales reales:

```powershell
cd <directorio-del-plugin-instalado>
Copy-Item env.template.json env.json
```

Abre `env.json` y rellena los valores marcados con `<COMPLETAR>`:

- **`herramientas.mantis`** — URL y API key de MantisBT corporativo
- **`herramientas.svn`** — URL y credenciales del repositorio SVN
- **`credenciales_bbdd`** — usuarios y passwords por proyecto (Ingenieros, bancamarch, etc.)
- **`entornos`** — connection strings completas por proyecto y entorno (DEV/PRE/PRO)
- **`contexto_personal`** — tu nombre, rol y equipo

> **Nota:** Si no tienes `env.json`, el agente lo creará automáticamente desde la plantilla la primera vez que uses un comando de base de datos, y te pedirá que lo rellenes antes de continuar.

### Paso 4 — Verificar la instalación

En Claude Code, escribe:

```
/orchestrator-validar-entorno
```

El agente verificará: entorno dotnet/SVN/Git, rutas AIS, modelo BD y — desde esta versión — también el estado de `env.json` (si falta o tiene placeholders sin rellenar, lo indicará en el informe).

El servidor MCP `orchestrator-workspace` arranca automáticamente en el primer uso.

---

## Comandos disponibles

### Análisis y calidad

| Comando | Qué hace |
|---|---|
| `/orchestrator-analizar <Solucion>.sln [rev\|ficheros]` | Análisis estático de calidad y riesgo de un diff o cambio concreto |
| `/orchestrator-auditoria` | Revisión de calidad y convenciones ScacsWeb (BPC, DALC, naming) |
| `/orchestrator-security` | Auditoría de seguridad: SQL injection, XSS, secretos en código |
| `/orchestrator-review` | Revisión de código del diff actual antes de commit |
| `/orchestrator-hotspots` | Detecta los ficheros con más cambios y mayor riesgo acumulado (cruza `god_nodes` del grafo graphify con churn VCS si el grafo existe, LoC como fallback) |
| `/orchestrator-dead-code` | Localiza código muerto: métodos, clases y referencias sin uso |
| `/orchestrator-perf` | Análisis de rendimiento: consultas lentas, N+1, allocations |
| `/orchestrator-cobertura` | Informe de cobertura de tests del proyecto |

### Implementación y scaffolding

| Comando | Qué hace |
|---|---|
| `/orchestrator-init [workspace_path]` | Bootstrap de workspace ScacsWeb: crea config BD, carpetas y modelo inicial |
| `/orchestrator-generar-dalc` | Genera clases DALC para Oracle/SQL Server a partir del modelo BD |
| `/orchestrator-migrar` | Genera y aplica migraciones SQL desde el modelo JSON local |
| `/orchestrator-seed` | Genera scripts SQL de datos iniciales (seed) para tablas de catálogo |
| `/orchestrator-incidencia` | Genera script SQL de incidencia idempotente (DDL+DML) y lo registra como nota privada en Mantis |
| `/orchestrator-format` | Aplica formato y convenciones de estilo al código fuente |
| `/orchestrator-rename` | Renombra símbolo (clase, método, tabla) propagando todos los usos |

### Validación y entorno

| Comando | Qué hace |
|---|---|
| `/orchestrator-validator` | Valida compilación y coherencia lógica del código |
| `/orchestrator-validar-entorno` | Verifica entorno: AIS, SVN, dotnet, modelo BD |
| `/orchestrator-validar-req` | Valida si un commit SVN/Git cumple el requerimiento de Mantis |
| `/orchestrator-comparar-modelo` | Compara modelo BD JSON local con esquema real de la BD |
| `/orchestrator-comparar-entornos` | Compara configuración entre entornos (dev, pre, pro) |
| `/orchestrator-sync-indexes` | Sincroniza índices del modelo JSON con los índices reales de la BD |

### Base de datos y modelo

| Comando | Qué hace |
|---|---|
| `/orchestrator-schema [tabla]` | Muestra esquema detallado de una tabla: columnas, tipos, PKs, índices |
| `/orchestrator-erd` | Genera diagrama ERD del modelo BD en formato Mermaid |
| `/orchestrator-db-env` | Muestra configuración de conexión BD del workspace activo |
| `/orchestrator-pantallas <nombre>` | Busca el código de pantalla (`CTFORM`) a partir de su nombre funcional consultando `SICONTROLES` + `SIIDIOMA` en BD. Elimina la necesidad de un MD de directorio de pantallas — siempre actualizado desde la BD. También se activa automáticamente cuando cualquier otro comando necesita resolver un nombre de pantalla. |

### Control de versiones (SVN / Git)

| Comando | Qué hace |
|---|---|
| `/orchestrator-historial` | Historial SVN/Git con autor, fecha y mensaje por revisión |
| `/orchestrator-diff` | Diff del workspace actual o de una revisión concreta |
| `/orchestrator-commit` | Prepara y ejecuta commit SVN/Git con mensaje estructurado |
| `/orchestrator-deshacer` | Deshace cambios locales o revierte una revisión SVN/Git |
| `/orchestrator-release-notes` | Genera release notes a partir del historial de commits |

### Arquitectura y documentación

| Comando | Qué hace |
|---|---|
| `/orchestrator-estructura` | Visualiza capas y dependencias de una solución ScacsWeb |
| `/orchestrator-deps` | Mapa de dependencias entre proyectos de una solución |
| `/orchestrator-impacto` | Mapa de impacto de un cambio propuesto: qué puede romperse (usa el grafo de conocimiento `graphify-out` del proyecto si existe, Grep como fallback) |
| `/orchestrator-explicar [símbolo\|fichero]` | Explica en detalle una clase, método o fichero (usa `graphify explain` como fuente primaria si el grafo del proyecto existe, verificado siempre contra el código) |
| `/orchestrator-doc` | Genera documentación técnica de un módulo o clase |
| `/orchestrator-doc-drift` | Detecta divergencia entre documentación y código actual |
| `/orchestrator-scacs-docs` | Consulta la base de conocimiento ScacsWeb integrada |
| `/orchestrator-dashboard` | Panel resumen del estado del workspace: build, tests, cobertura |

### Tests

| Comando | Qué hace |
|---|---|
| `/orchestrator-test` | Ejecuta la suite de tests del proyecto |
| `/orchestrator-crear-tests` | Genera tests unitarios para una clase o método concreto |

### Integración con Mantis

| Comando | Qué hace |
|---|---|
| `/orchestrator-mantis #NNNN` | Consulta un issue de MantisBT por número |
| `/orchestrator-mantis proyecto NNNN` | Lista issues de un proyecto de MantisBT |

### Producción y operaciones

| Comando | Qué hace |
|---|---|
| `/orchestrator-log-errores [ruta] [--desde] [--max] [--glob] [--niveles]` | Analiza log de errores web (NLog, ELMAH, AgendaWeb AIS), deduplica por firma SHA1 y abre tareas Mantis por tipo. El log crudo nunca entra en contexto. |

### Estadísticas y utilidades

| Comando | Qué hace |
|---|---|
| `/orchestrator-stats` | Estadísticas de uso del pipeline: comandos más usados, tiempos |
| `/orchestrator-idiomas` | Detecta mezcla de idiomas en nombres de variables, métodos y clases |
| `/orchestrator-agent` | Punto de entrada genérico para tareas no cubiertas por comandos específicos |
| `/orchestrator-help` | Muestra esta ayuda como página HTML navegable |

---

## Configuración de entorno (`env.json`)

El plugin gestiona el contexto de base de datos y herramientas de forma **autónoma**, sin depender de skills externos.

### Estructura de `env.json`

```
<directorio-del-plugin>/
├── env.json              ← TU configuración local (gitignored, nunca se sube)
├── env.template.json     ← Plantilla vacía (incluida en el repositorio)
└── projects/
    ├── Ingenieros/
    │   ├── config.json   ← Metadatos del proyecto (motor, host, TNS alias...)
    │   └── schema.md     ← Esquema completo de la BD (gitignored por tamaño)
    └── bancamarch/
        ├── config.json
        └── schema.md
```

### Secciones principales de `env.json`

| Sección | Contenido |
|---|---|
| `herramientas.mantis` | URL, usuario y API key de MantisBT |
| `herramientas.svn` | URL y credenciales del repositorio SVN |
| `herramientas.correo` | SMTP para ejemplos de envío desde C# |
| `credenciales_bbdd` | Usuarios y passwords por proyecto y entorno |
| `entornos` | Connection strings Oracle/SQL Server por proyecto (DEV/PRE/PRO) |
| `contexto_personal` | Nombre, rol, empresa y equipo del desarrollador |

### Comportamiento si `env.json` no existe

El agente detecta la ausencia automáticamente:

1. Copia `env.template.json` → `env.json`
2. Informa al usuario con la ruta del archivo creado
3. **Se detiene** hasta que el usuario confirme que ha rellenado las credenciales

El comando `/orchestrator-validar-entorno` también verifica el estado de `env.json` y reporta si quedan placeholders `<COMPLETAR>` sin rellenar.

---

## Servidor MCP — `orchestrator-workspace`

El plugin incluye un servidor MCP Python que corre en local (`stdio`) y expone herramientas nativas. Claude las invoca automáticamente al ejecutar los comandos.

### Herramientas disponibles

| Herramienta MCP | Propósito |
|---|---|
| `detect_vcs` | Detecta si el workspace usa SVN, Git o ambos |
| `svn_log` / `git_log` | Historial de commits/revisiones |
| `svn_diff_revision` / `git_diff_revision` | Diff de una revisión concreta |
| `svn_status` / `git_status` | Estado de cambios pendientes |
| `compile_check` | Invoca MSBuild o `dotnet build` con autodetección de toolchain; devuelve errores/warnings clasificados |
| `validate_solution` | Validación completa de la solución .sln |
| `parse_web_log` | Parsea logs de producción (NLog, ELMAH, AgendaWeb AIS) y devuelve errores agrupados por firma SHA1 sin cargar el log en contexto |
| `run_tests` | Ejecuta tests .NET y devuelve resultados |
| `db_query` | Consulta Oracle/SQL Server vía XMLConfig.xml |
| `get_db_config` | Lee configuración de conexión del workspace |
| `get_table_schema` | Esquema detallado de una tabla |
| `get_model_index` / `search_model` | Búsqueda en modelo BD JSON local |
| `compare_model` / `compare_model_tables` | Compara modelo local vs BD real |
| `sync_from_db` / `sync_model_tables` | Sincroniza modelo JSON desde la BD |
| `sync_indexes` | Sincroniza índices del modelo |
| `export_dmd` | Exporta modelo al formato Oracle Data Modeler (.dmd) |
| `generate_migration` / `generate_sql` | Genera SQL de migración desde el modelo |
| `find_symbol` / `batch_find_symbols` | Localiza clases, métodos o propiedades en el código |
| `search_code` | Búsqueda full-text en el código fuente |
| `scan_aspx` | Escanea ficheros ASPX/ASCX de la solución |
| `analyze_dalc` | Analiza clases DALC: queries SQL embebidas, parámetros |
| `map_dependencies` | Grafo de dependencias entre proyectos |
| `render_erd` | Diagrama ERD en Mermaid |
| `security_scan` | Escanea el código en busca de vulnerabilidades |
| `check_env` | Verifica entorno: AIS, SVN, dotnet, Python, BD |
| `get_scope` | Parsea el .sln y devuelve proyectos y rutas |
| `log_execution` | Registra ejecuciones para estadísticas |
| `ping` | Test de conectividad del servidor MCP |

### Cachés del servidor

El servidor mantiene cachés en memoria y en disco para evitar llamadas repetidas:

- **Modelo BD** (`~/.claude/cache/rs-models/`): invalidado automáticamente si cambia `model.json`
- **Configuración de workspace**: por sesión, cargada una vez
- **Scope (.sln)**: invalidado si cambia el fichero `.sln`

---

## Arquitectura ScacsWeb asumida

El plugin asume la estructura estándar de proyectos ScacsWeb:

```
<workspace>/
├── <Proyecto>.sln
├── <modulo>/
│   ├── BPC/          ← Business Process Classes
│   ├── BE/           ← Business Entities
│   └── DALC/         ← Data Access Layer Classes
├── XMLConfig.xml     ← Configuración de conexión BD
└── model.json        ← Modelo BD en JSON (generado/sincronizado por el plugin)
```

| Elemento | Valor |
|---|---|
| Framework | ASP.NET WebForms / .NET Framework 4.0 / C# 7.3 |
| VCS | SVN (TortoiseSVN primario) + Git secundario |
| Bases de datos | Oracle 19c y/o SQL Server |
| Naming de módulos | `AIS.PR.BR.EC.CL` |
| Rutas AIS Batch | `C:\AIS\<proyecto>\bin\` |
| Rutas AIS Online | `C:\AIS\<proyecto>\Web\` |

> Si tu proyecto sigue una arquitectura diferente, algunos comandos pueden requerir ajuste manual.

---

## Flujo de trabajo típico

```
1. /orchestrator-init             ← Bootstrap inicial del workspace (1 vez)
2. /orchestrator-validar-entorno  ← Comprueba que todo esté OK
3. [Desarrollar el cambio]
4. /orchestrator-analizar         ← Análisis de calidad del diff
5. /orchestrator-validator        ← Valida compilación
6. /orchestrator-review           ← Revisión pre-commit
7. /orchestrator-commit           ← Commit estructurado SVN/Git
```

---

## Preguntas frecuentes

**¿El servidor MCP consume recursos en segundo plano?**  
No. Arranca únicamente cuando se ejecuta el primer comando `/orchestrator-*` en la sesión y se detiene al cerrar Claude Code.

**¿Puedo usar el plugin en proyectos que no son ScacsWeb?**  
Los comandos de análisis, revisión y historial son agnósticos. Los comandos de scaffolding (DALC, migrar, init) están pensados para ScacsWeb y pueden requerir adaptación.

**¿El plugin accede a Internet?**  
No. Todo corre en local. El único acceso de red es a la BD del proyecto (si está en un servidor) y a MantisBT (si se usan los comandos `/orchestrator-mantis`).

**¿Debo tener la skill `project-db-env` instalada?**  
No. Desde v1.6.0 el contexto de base de datos está integrado directamente en el plugin (`env.json`, `projects/*/config.json` y `projects/*/schema.md`). Si tenías la skill externa instalada puedes desinstalarla.

**¿`env.json` se sube al repositorio?**  
No. Está en `.gitignore`. Solo `env.template.json` (con placeholders) se versiona. Cada desarrollador crea su propio `env.json` local con sus credenciales reales.

**¿Cómo actualizo el plugin?**  
```
/plugin update orchestrator-skill-full
```
O manualmente con `git pull` en el directorio del plugin.

---

## Soporte

- **Repositorio:** https://github.com/aisaplica/Orchestrator-Agent.git  
- **Incidencias y sugerencias:** abrir issue en el repositorio o contactar con el equipo de IA.
- **Versión actual:** v1.8.0 (2026-08-14)

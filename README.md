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

| Comando | Descripcion |
|---------|-------------|
| `/orchestrator-historial` | Historial SVN/Git con autor, fecha y mensaje por revision |
| `/orchestrator-stats` | Estadisticas de uso del pipeline |
| `/orchestrator-deps` | Mapa de dependencias entre proyectos de una solucion |
| `/orchestrator-security` | Auditoria de seguridad: SQL injection, XSS, secretos |
| `/orchestrator-auditoria` | Revision de calidad y convenciones ScacsWeb |
| `/orchestrator-comparar-modelo` | Compara modelo BD local con esquema real |
| `/orchestrator-estructura` | Visualiza capas y dependencias de una solucion |
| `/orchestrator-fixer` | Corrige errores detectados por validator |
| `/orchestrator-validator` | Valida compilacion y coherencia logica del codigo |
| `/orchestrator-validar-entorno` | Verifica entorno: AIS, SVN, dotnet, modelo BD |
| `/orchestrator-validar-req` | Valida si un commit SVN/Git cumple el requerimiento |
| `/orchestrator-impacto` | Mapa de impacto de un cambio propuesto |

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

## Soporte

Repositorio interno ScacsWeb / Ingenieros.

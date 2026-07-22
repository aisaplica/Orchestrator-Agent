name: orchestrator-build

> Problemas comunes de build/deploy: `references/troubleshooting.md`
> Copia completa de bin (DLLs + EXEs): `hooks/copy-ais.ps1 <source> <workspace>`

# Build

Ingeniero DevOps senior. Compilación, generación de artefactos y despliegue en entorno AIS.

## Cuándo ejecutar

- **Online:** siempre, al final del pipeline (tras validator + tester OK).
- **Batch:** siempre, al final del pipeline (tras validator + tester OK). Compila + copia binarios a AIS.

⛔ NO ejecutar si: validator con errores críticos · tester fallado · dudas sin resolver · Online con controles AIS nuevos y scripts de idiomas aún no emitidos.

## Validación previa

Antes de ejecutar:
- Preferente: `mcp__orchestrator-workspace__validate_solution(sln_path)` → confirma existencia de la .sln.
- Fallback: `hooks/validate-solution.ps1 <sln_path>`.
- Si no existe → detener, pedir ruta correcta.

## Resolución de solución

| Tipo | Ruta .sln |
|------|-----------|
| Batch | `dotNet\Batch\<BatchName>\<BatchName>.sln` (una .sln por proceso) |
| Online (Web) | `.sln` en raíz trunk, p.ej. `<Proyecto>.sln` |

## Batch

1. `dotnet build "dotNet\Batch\<BatchName>\<BatchName>.sln" -c Debug`
2. `dotnet build "dotNet\Batch\<BatchName>\<BatchName>.sln" -c Release`
3. Ejecutables en `dotNet\Batch\<BatchName>\bin\Release\`
4. Copiar a AIS: `C:\AIS\<proyecto>\bin\`

COMMAND: `.\hooks\batch-build.ps1 <BatchName> "<workspace>"`

## Online

La `.sln` referencia el proyecto web como `dotNet\Web\<WebFolder>\<WebFolder>.csproj`.
Leer la `.sln` y localizar el `.csproj` que corresponde al proyecto web principal.

Perfiles de publicación: `dotNet\Web\<WebFolder>\Properties\PublishProfiles\*.pubxml`.
⛔ Listar los `.pubxml` reales y leer su `<PublishUrl>` antes de invocar el hook — no asumir el nombre del perfil.

Build usa `msbuild` (no `dotnet publish`) — proyectos Web son .NET Framework WebForms.

⛔ `dotnet build`/`dotnet test`/`mcp__orchestrator-workspace__compile_check`/`run_tests` (CLI `dotnet`) pueden fallar con `MSB4019` (falta `Microsoft.WebApplication.targets`, que el SDK de `dotnet` no trae) en cuanto el build toque el proyecto WebForms. Además `compile-check.ps1` solo parsea diagnósticos `CS####`: un `MSB####` real puede quedar invisible (`error_count=0` con `exit_code=1`). Para compilar de verdad: `msbuild.exe` real de Visual Studio (localizar con `vswhere.exe`, no asumir en PATH). Para ejecutar tests de verdad: `vstest.console.exe` directo sobre el `.dll` de test ya compilado, no `dotnet test`.

COMMAND: `.\hooks\online-publish.ps1 "<workspace>\dotNet\Web\<WebFolder>\<Project>.csproj" <ProfileName>`

## Output estructurado (CRÍTICO)

Emitir siempre antes de ejecutar:

```
TYPE: BUILD
MODE: BATCH | ONLINE
COMMAND: <comando completo>
```

Luego ejecutar inline via `runner/runner.ps1`:

```powershell
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, "TYPE: BUILD`nCOMMAND: .\hooks\batch-build.ps1 <Solution> `"<workspace>`"")
& "<BASE_DIR_DE_SKILL>\runner\runner.ps1" -InputFile $tmp
Remove-Item $tmp -Force
```

`BASE_DIR_DE_SKILL` disponible en contexto como: `Base directory for this skill: <PATH>`

## Verificación post-build (OBLIGATORIO)

La ruta base AIS (`C:\AIS\`) se obtiene de `get_db_config(workspace).ais_root` si está disponible; si no, se usa `C:\AIS\` como valor por defecto.

El runner imprime el output del hook. Evidencia mínima antes de reportar éxito:
- **Batch:** línea de copia OK a `C:\AIS\<proyecto>\bin` y exit code 0.
- **Online:** publish sin errores MSBuild (`0 Error(s)`) y destino AIS actualizado (ver `<PublishUrl>` del pubxml).

Si falta la evidencia → reportar FAIL con las últimas líneas de error. ⛔ Nunca "build OK" sin esto.

## Límites

⛔ No simular build · No devolver "build OK" sin ejecutar · No ocultar pasos · No omitir copia a AIS

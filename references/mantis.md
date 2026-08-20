# Mantis — Configuración

## Fuente de credenciales (por orden de prioridad)

1. **`env.json` del propio plugin** (recomendado, mismo archivo que usa `db-env`):
   ```
   <raíz del plugin>\env.json
   > herramientas.mantis.url
   > herramientas.mantis.api_key
   ```
   Si no existe, copiar `env.template.json` → `env.json` en la raíz del plugin y rellenar.

2. **Variables de entorno** (fallback):
   ```powershell
   $env:MANTIS_URL     = "https://soporte.ais-int.net/mantis/api/rest/index.php/"
   $env:MANTIS_API_KEY = "<tu-api-key>"
   ```

3. **Inline al invocar el hook** (alternativa sin config):
   ```powershell
   & "$SKILL_DIR\hooks\mantis-get-issue.ps1" -IssueId 1234 -Url "..." -ApiKey "..."
   ```

## Cómo obtener la API key en MantisBT

1. Login en Mantis → **Mi Cuenta** (icono usuario, esquina superior derecha)
2. Pestaña **Tokens de API**
3. **Generar nuevo token** → copiar el valor generado

## Endpoint utilizado

```
GET <MANTIS_URL>/issues/<id>          # issue individual
GET <MANTIS_URL>/issues?project_id=N  # listado por proyecto
GET <MANTIS_URL>/projects             # lista de proyectos con sus IDs internos
Header: Authorization: <API_KEY>
```

## IDs de proyecto

Los IDs internos de MantisBT NO coinciden con los números de contrato (60xxxx).
Usar `GET /projects` para obtener el mapeo nombre → ID interno.

Ejemplo: "602400 SCACS CDI HL Incidencias" → ID interno **215**

## Versión mínima de MantisBT

REST API disponible desde **MantisBT 2.0**.

---

## Operaciones write (skill mantis ciclo completo)

### CLI unificado

Usar `$SKILL_DIR\hooks\mantis-cli.ps1` para todas las operaciones (read y write):

```powershell
# Transición de estado
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action patch-status -IssueId 1234 -Status "en proceso"
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action patch-status -IssueId 1234 -Status 55   # por ID numérico

# Añadir comentario
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action post-note -IssueId 1234 -Text "Desarrollo iniciado."

# Adjuntar archivo
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action attach-file -IssueId 1234 -FilePath "C:\AIS\Proyecto\scripts\migration.sql"
```

### Endpoints write utilizados

```
PATCH /issues/:id
  Body: { "status": { "id": N } }           # transición por ID
  Body: { "status": { "label": "nombre" } }  # transición por label

POST  /issues/:id/notes
  Body: { "text": { "body": "texto" } }

POST  /issues/:id/files
  Body: { "files": [{ "name": "...", "content": "<base64>", "type": "mime" }] }
```

### Cadena de estados ScacsWeb

Configurada en `docs\.mantis-dev-config.json`. Estados estándar MantisBT:
- `nueva (10)` → `reconocida (20)` → `asignada (30)` → `confirmada (50)` → `en proceso (?)` → `en validación (?)` → `resuelta (80)` → `cerrada (90)`

Los IDs de "en proceso" y "en validación" son estados personalizados — obtener via:
```powershell
& "$SKILL_DIR\hooks\mantis-cli.ps1" -Action get-issue -IssueId NNNN  # leer issue en ese estado
```

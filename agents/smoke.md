name: orchestrator-smoke

# Rol

Tester de runtime para proyectos ScacsWeb Online. Abre la web **local** de desarrollo con la CLI
`agent-browser` (desde Bash, NO como MCP), navega a una pantalla `.aspx` y comprueba que carga sin
errores de página, de consola ni de red. **Solo lectura**: navega, nunca ejecuta acciones de negocio.

# Objetivo

Detectar pantallas que compilan pero fallan en runtime (error de ASP.NET, JS roto, 4xx/5xx en postbacks)
y dejar evidencia (captura + esqueleto) fuera del repo y fuera del contexto.

# Argumentos

`/orchestrator-smoke [<Solucion.sln>|<Proyecto>] [--url <url_login>] [--pantalla <X.aspx>] [--evidencias <dir>]`

Todo lo demás (usuario, contraseña, selección de usuario) sale del perfil del proyecto o se pregunta.

# Perfil por proyecto

Fichero `$SKILL_DIR\projects\<Proyecto>\smoke.json` (gitignored — plantilla: `$SKILL_DIR\smoke.template.json`).
`<Proyecto>` = carpeta anterior a `src\trunk\` del workspace (ej. `...\ScacsWeb\bancamarch\src\trunk` → `bancamarch`).
Cada proyecto puede tener login, pantalla de acceso y perfil de selección distintos.

| Campo | Significado |
|---|---|
| `url_login` | **Obligatorio.** URL de la pantalla de acceso |
| `login.usuario` / `login.password` / `login.boton` | Nombres accesibles de los controles de la pantalla de login. Opcional: si faltan se deducen del `snapshot -i` (textbox usuario, textbox contraseña, enlace/botón Login/Entrar/Acceder) |
| `usuario` | Usuario de login |
| `password` | `null` → **preguntar cada vez** · `""` → contraseña vacía (sin contraseña) · texto → usarla |
| `seleccion_usuario.texto_fila` | Texto de la fila a elegir si aparece una pantalla de selección de usuario. Opcional |
| `overlay_selector` | Selector CSS del overlay de carga de postbacks (ej. `#loader_general_overlay`). Opcional |
| `pantallas` | Atajos `nombre → ruta relativa` (ej. `"CM01010MDC1": "CM/CM01010MDC1.aspx"`). Opcional |

# Proceso

## 1. Precheck (cada fallo = SKIP con motivo, nunca error del pipeline)

1. `agent-browser --version`. Si falla → SKIP: "agent-browser no instalado (`npm i -g agent-browser`)".
2. Chrome for Testing: `ls "$USERPROFILE/.agent-browser/browsers"`. Si no existe → SKIP: "ejecutar `agent-browser install`".
   Sin Chrome, el primer `open` se cuelga sin salida.
3. Resolver perfil (ver §2). Con `url_login` conocida: `curl -s -o /dev/null -m 5 -w "%{http_code}" <url_login>`.
   Código `000` → SKIP: "web no levantada en <host:puerto>".

## 2. Resolver perfil y credenciales

1. Leer `projects/<Proyecto>/smoke.json` si existe.
2. **Sin perfil** → preguntar al usuario: URL de login, usuario, contraseña, fila de selección (si la hay) y pantalla.
   Al terminar el smoke, ofrecer guardar el perfil. La contraseña **solo se guarda si el usuario lo pide
   explícitamente**; si no, se guarda el perfil con `"password": null`.
3. **Con perfil y `password: null`** → preguntar la contraseña (es el valor para "preguntar cada vez").
   `password: ""` NO se pregunta: es contraseña vacía.
4. **Con perfil y pantalla sin resolver** → si `--pantalla` no es un atajo de `pantallas`, hacer `Glob **/<pantalla>`
   dentro del workspace; la carpeta padre del `.aspx` dentro del proyecto web da el módulo (ej. `CM/CM01010MDC1.aspx`).
   Si hay varios resultados → preguntar cuál.

### ⛔ Reglas de seguridad de credenciales

- **Solo hosts locales**: `localhost`, `127.0.0.1`, `[::1]`, `*.localhost`, `*.test`. Cualquier otro host
  (incluida una `url_login` de perfil que apunte a un entorno real) → **negarse**, no hacer login, informar.
- Las credenciales son usuarios de **pruebas de desarrollo**. No usar nunca credenciales reales de otro servicio.
- **No escribirlas en el texto de las órdenes ni repetirlas en respuestas**. Leer la contraseña del perfil
  dentro de la propia orden y pasarla por variable (ver §3). Una contraseña preguntada en el chat se exporta
  a una variable de la orden Bash, no se interpola en claro en la cadena visible cuando se pueda evitar.
- No incluir usuario ni contraseña en `log_execution`, en el informe ni en los ficheros de evidencia.

## 3. Flujo de navegación

Todas las órdenes `agent-browser` van con `timeout` (ej. `timeout 90`). Sesión nombrada para no mezclar con otras:
`--session smoke-<Proyecto>`. Carpeta de evidencias: `--evidencias` o `$TEMP/orchestrator-smoke/<yyyyMMdd-HHmmss>/`
(fuera del repo). Crearla antes de empezar.

```bash
A="agent-browser --session smoke-<Proyecto>"
timeout 90 $A open "<url_login>"
timeout 60 $A snapshot -i > "$EV/01-login.txt"          # refs de los campos
PW=$(python -I -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('password') or '')" "<perfil>")
timeout 30 $A fill @<ref_usuario> "<usuario>"
timeout 30 $A fill @<ref_password> "$PW"; unset PW
timeout 30 $A click @<ref_boton>
```

(Si la contraseña se preguntó en el chat y no hay perfil, pasarla a la orden por variable de entorno
temporal en esa misma orden Bash; `""` → omitir el `fill` de contraseña.)

1. **Esperar overlay antes de cada click.** Si hay `overlay_selector`:
   `timeout 30 $A wait --fn "!document.querySelector('<overlay_selector>') || getComputedStyle(document.querySelector('<overlay_selector>')).display==='none'"`.
   Sin esa espera, los clicks tras un postback fallan con "covered by loader overlay". Si agota el timeout → WARN "overlay atascado".
2. **Selección de usuario** (si `seleccion_usuario.texto_fila`): tras el login, si `get url` sigue en la pantalla de login
   o el snapshot muestra una tabla de selección → `timeout 30 $A find text "<texto_fila>" click`. Si aparece pantalla de
   selección y no hay `texto_fila` → preguntar al usuario la fila (NO volcar el grid al contexto: ~20k tokens).
3. **Pantalla destino**: `timeout 90 $A open "<base>/<modulo>/<pantalla>.aspx"` en la **misma sesión** (las cookies persisten).
   `<base>` = `url_login` sin el último segmento. Si el login ya aterriza en la pantalla pedida, no reabrir.
4. **Recogida** (todo a ficheros de evidencia, no al contexto):
   - `timeout 60 $A snapshot -d 3 > "$EV/02-esqueleto.txt"` — esqueleto (<1 KB). NO usar el snapshot completo (110 KB+ en pantallas con grid).
   - `$A errors > "$EV/03-errors.txt"` · `$A console > "$EV/04-console.txt"`
   - `$A network requests > "$EV/05-network.txt"`, filtrando después los no 200/304 con `grep -v -E ' (200|304)$'`.
   - `timeout 60 $A screenshot "$EV/06-pantalla.png"`
   - `$A get url` y `$A get title`: comprobar que la URL final es la pantalla pedida (no una redirección a login ni a una pantalla de error).
   - Detección de pantalla de error de ASP.NET: buscar en el esqueleto/título `Server Error in`, `Runtime Error`, `Error de servidor`, `Exception`.
5. **Pestañas / navegación interna** (opcional, solo si el usuario lo pide o el esqueleto muestra pestañas): `find text "<pestaña>" click`
   esperando el overlay entre una y otra, y volver a leer `errors` y los no-200 al final.
6. **Cierre**: `$A close` **siempre**, aunque haya fallado algo.

# Solo lectura — acciones prohibidas

Navegar es lo único permitido: login, selección de usuario, abrir la pantalla y cambiar de pestaña.
**Nunca** pulsar botones de acción de negocio (Finalizar, Desbloquear, Modificar, Guardar, Eliminar, Imprimir…),
ni enviar formularios de la pantalla analizada, ni cambiar de usuario o centro tras el login.

# Veredicto

| Resultado | Condición |
|---|---|
| **FAIL** | La pantalla no carga · hay `errors` de página · respuesta 5xx · pantalla de error de ASP.NET · URL final es la de login |
| **WARN** | Errores en consola · 4xx (salvo `/favicon.ico`) · overlay atascado · carga > 15 s |
| **PASS** | Nada de lo anterior |
| **SKIP** | Falla un precheck (agent-browser/Chrome ausente, web no levantada). No es un fallo |

En el pipeline (paso 9c) un SKIP **no bloquea**; un FAIL se informa al usuario pero no revierte el build.

# Output

```
## Smoke test: <pantalla> — <Proyecto>
URL: <url final>   Veredicto: PASS | WARN | FAIL | SKIP

| Check | Estado | Detalle |
|-------|--------|---------|
| Web responde | OK | <host:puerto> |
| Login | OK | <usuario>  (sin contraseña en claro) |
| Pantalla carga | OK | título: <título> |
| Errores de página | OK | 0 |
| Consola | WARN | 1 error: <resumen> |
| Red (no-200) | OK | 0 · (404 favicon.ico ignorado) |

Evidencias: <carpeta> (01-login.txt, 02-esqueleto.txt, 03-errors.txt, 04-console.txt, 05-network.txt, 06-pantalla.png)
```

Si no existía perfil, cerrar con: `¿Guardo el perfil en projects/<Proyecto>/smoke.json? (la contraseña solo si me lo pides)`.

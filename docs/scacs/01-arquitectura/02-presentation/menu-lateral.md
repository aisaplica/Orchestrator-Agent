º---
title: SCACS Web - Menú lateral
tags: [scacs, ai, menu, navigation, permissions]
---

# Menú lateral

El menú lateral es el punto de entrada principal de navegación en SCACS. Se renderiza como un `<ul id="scacs-nav">` colapsable en el lado izquierdo de la pantalla y está controlado por el control de servidor `AISMenu`.

## Declaración en MasterPage

El menú se declara en `MasterForm.Master`:

```aspx
<ais:AISMenu ID="menuscacs" runat="server" IdMenu="Main" />
```

`IdMenu` es el código del nodo raíz del árbol de menú en base de datos. En producción siempre es `Main`.

## Carga de datos

### Flujo de carga (`AISMenu.LoadMenuData`)

1. Se construye la clave de sesión `MENU_{IdMenu}` (p. ej. `MENU_Main`).
2. Si existe en sesión (`Page.Session[sessionKey]`), se usa directamente — sin llamada a BD.
3. Si no existe, se ejecuta una llamada al backend:
   ```
   ClientConnectorInterface → BRIN > MenusManager > GetMenu
     Parámetros:
       IdMenu   = _idMenu          (nodo raíz)
       User     = SessionInfo.IdUsuario
       Language = SessionInfo.Language
   ```
4. El `DataSet` resultante se guarda en sesión para el resto de la sesión del usuario.

El menú **no se recarga automáticamente** al navegar entre páginas; se reutiliza el objeto en sesión. Para forzar una recarga existe el método público `RecargarDatos()`, que elimina la clave de sesión y vuelve a llamar a `LoadMenuData`.

### Backend: `MenusManager` (`AIS.PR.BR.IN`)

`GetMenuRecursive` carga el árbol de menú de forma recursiva:

1. Llama a `GetMenuList` para obtener los hijos directos del nodo indicado.
2. Por cada hijo con `HaySubordinados = 1`, llama recursivamente a `GetMenuRecursive`.
3. Fusiona todos los niveles en un único `DataSet` con tabla `Menus`.
4. Añade la tabla `Perfil` con los datos del usuario (`getPerfilUsuario`).

## Tablas de base de datos

| Tabla        | Rol                                                                 |
|--------------|---------------------------------------------------------------------|
| `SIMenus`    | Estructura del árbol (código, padre, texto, icono, URL, orden)      |
| `SIIdioma`   | Descripciones traducidas por idioma (`IDTexto`, `IDIdioma`)         |
| `SSUsuarios` | Usuarios (`USCod`, `USPerfil`)                                      |
| `SSFacAcc`   | Control de acceso: vincula perfil con elemento de menú y nivel      |

Columnas relevantes de `SIMenus` tras el mapeo:

| Campo             | Alias en DataSet  | Descripción                              |
|-------------------|-------------------|------------------------------------------|
| `MNMenu`          | `Menu`            | Código del ítem                          |
| `MNPadre`         | `Padre`           | Código del nodo padre                    |
| `MNTexto`         | `Texto`           | Clave de traducción en `SIIdioma`        |
| `IDDescripcion`   | `Descripcion`     | Texto mostrado (ya traducido)            |
| `MNIcono`         | `Icono`           | Nombre del enum `ButtonIconEnum`         |
| `MNURL`           | `URL`             | URL destino o token especial (ver abajo) |
| `MNOrden`         | `Orden`           | Posición dentro del nivel                |
| `HaySubordinados` | `HaySubordinados` | `1` si tiene hijos, `0` si no           |

## Control de permisos

El filtrado de permisos ocurre **en la consulta SQL**, no en el renderizado. Solo se devuelven los ítems para los que el usuario tiene acceso:

```sql
EXISTS (
  SELECT * FROM SSUsuarios
  JOIN SSFacAcc ON FAPerfil = USPerfil
  WHERE USCod    = :usuario
    AND FAElem   = MNMenu
    AND FANivel  = '7'
)
```

- `USPerfil` → perfil del usuario.
- `FAElem` → código del elemento de menú (`MNMenu`).
- `FANivel = '7'` → nivel de acceso requerido para que el ítem sea visible.

El resultado es que el árbol devuelto ya está filtrado: si un usuario no tiene el nivel `7` en `SSFacAcc` para un ítem, ese ítem simplemente no aparece en el `DataSet` y nunca se renderiza.

## Renderizado (`AISMenu.RenderMenuList`)

`RenderMenuList` recorre la tabla `Menus` filtrando por `Padre` y ordenando por `Orden`. Para cada ítem:

- Si `HaySubordinados = 1` → renderiza un `<a class="collapsible-header">` con un `<div class="collapsible-body">` anidado, y llama recursivamente a `RenderMenuList` para los hijos.
- Si `HaySubordinados = 0` → renderiza un `<a href="...">` normal.
- Si `Icono` es válido → instancia `AISIcon` y lo renderiza dentro del `<a>`.
- Si el icono es `Logout` → añade entre paréntesis la descripción del perfil del usuario (de la tabla `Perfil`).

### Tokens especiales en el campo URL

Algunos ítems no tienen URL convencional sino un token que dispara un postback con lógica propia:

| Token              | `LinkButton` asociado | Acción ejecutada                                          |
|--------------------|-----------------------|-----------------------------------------------------------|
| `#SEPARADOR#`      | —                     | Renderiza un `<hr>` separador visual en lugar de un link |
| `#EXPEDIENTE#`     | `lnkExp1`             | `OpenEC00000NAV` — abre ficha del cliente seleccionado   |
| `#RATING#`         | `lnkExp2`             | `OpenRA001(simulacion: false)` — rating real             |
| `#RATINGSIMULACION#` | `lnkExp3`           | `OpenRA001(simulacion: true)` — rating simulado          |
| `#NUEVAPROPUESTA#` | `lnkExp4`             | `CrearPropuestaCliente` — nueva propuesta CDI            |
| `#REESTRUCTURA#`   | `lnkExp5`             | `CrearOperacionEspecial(Reestructura)`                   |
| `#REFINANCIACION#` | `lnkExp6`             | `CrearOperacionEspecial(Refinanciacion)`                 |
| `#RENEGOCIACION#`  | `lnkExp7`             | `CrearOperacionEspecial(Renegociacion)`                  |
| `#RENOVACION#`     | `lnkExp8`             | `CrearOperacionEspecial(Renovacion)`                     |

Los tokens de acción requieren que previamente exista en sesión un `DataSet` de clientes bajo la clave `AISDatosCliente.SESSIONKEYBUSQUEDA`. El usuario selecciona el cliente en una pantalla de búsqueda, y al pulsar el ítem de menú se opera sobre el cliente que ocupa el índice `indexCliente` en ese `DataSet`.

## HTML generado

```html
<!-- Barra superior (topnav) -->
<nav id="barraNav" class="main-topnav">
  <div class="nav-wrapper">
    <ul class="left">
      <li>
        <a href="#" class="sidenav-trigger show-on-large" data-activates="scacs-nav">
          <!-- icono menú hamburguesa -->
        </a>
      </li>
    </ul>
    <div class="left nav-logo-entidad"><img src="~/images/LogoEntidadCabecera.png" /></div>
    <div class="right nav-logo-ais"><img src="~/images/LogoAISCabecera.png" /></div>
    <div class="titulo-cabecera"><!-- Page.Title --></div>
  </div>
</nav>

<!-- Menú lateral -->
<ul id="scacs-nav" class="side-nav full collapsible collapsible-accordion">
  <li>
    <a class="collapsible-header"><!-- grupo colapsable --></a>
    <div class="collapsible-body">
      <ul>
        <li><a href="~/modulo/pantalla.aspx"><!-- ítem hoja --></a></li>
      </ul>
    </div>
  </li>
  <li><hr size="8px" color="black"></li> <!-- separador -->
</ul>
```

## Caché y recarga

| Situación                                  | Comportamiento                                            |
|--------------------------------------------|-----------------------------------------------------------|
| Primera carga tras login                   | Consulta a BD, guarda en `Session["MENU_Main"]`           |
| Navegación entre páginas (mismo usuario)   | Usa objeto en sesión, sin consulta a BD                   |
| Cambio de permisos en BD sin cerrar sesión | El menú **no se actualiza** hasta que se llame `RecargarDatos()` o se cierre y reabra sesión |
| Llamada a `RecargarDatos()`                | Elimina `Session["MENU_Main"]` y reconsulta BD            |

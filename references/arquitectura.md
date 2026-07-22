# Arquitectura SCACS Web

ASP.NET WebForms / .NET Framework 4 / C# 7.3

Dos tipos de soluciones: **Batch** (procesos) y **Online** (aplicación web).

---

# Batch

**Ubicación SLN:**
```
<trunk>\dotNet\Batch\<BatchName>\<BatchName>.sln
```

**AIS destino:** `C:\AIS\<proyecto>\bin\`

## Características

- ejecución secuencial, salida EXE
- procesos críticos con uso intensivo de BD
- errores deben detener el proceso
- orden de ejecución es crítico

## Flujo típico

1. lectura de entrada
2. validación previa
3. procesamiento
4. escritura en BD o fichero

---

# Online (Web)

**Ubicación SLN:** raíz trunk (`<Proyecto>.sln`)

**AIS destino:** `C:\AIS\<proyecto>\Web\` (tomado de pubxml `<PublishUrl>`)

## Stack de capas

```
Presentación (ASP.NET WebForms)
  |
  +-- Conector (AIS.PR.UI.ClientConnectorInterface)
       |
       +-- Negocio (AppDomain separado)
             |-- BPC  - punto de entrada; carga textos, validaciones, catálogos, datos
             |-- BE   - lógica de negocio; llama a DALC; nunca accede a BD directamente
             +-- DALC - acceso a BD (queries/updates); sin lógica compleja
```

NO: Nunca saltar BPC desde presentación.
NO: DALC solo datos, lógica va en BE.

## Conector - cómo llamar a negocio

La presentación usa `AIS.PR.UI.ClientConnectorInterface.Execute(Parameters)`.

`Parameters` lleva:
- **proyecto destino** — nombre derivado quitando `AIS.PR` y los puntos del nombre DLL
  (`AIS.PR.BR.EC.AN` -> `BRECAN`; tabla `SIAPPATH` es la autoridad)
- **clase destino** — normalmente `BPC`
- **método destino** — string que BPC resuelve internamente via `switch`

La presentación **no llama métodos concretos de negocio** — usa el contrato genérico del conector.

Comunicación entre proyectos de negocio: `AIS.PR.BR.BRConnector` (mantiene la misma transacción).

## Organización de clases en proyectos de negocio

| Sufijo | Rol |
|--------|-----|
| BPC | Punto de entrada del conector. Carga textos, validaciones, seguridad, catálogos, datos. |
| BE  | Lógica de negocio. Llama a su DALC homónima. Puede llamar a otros BE del mismo proyecto. |
| DALC | SQL directo. Sin lógica compleja. Evitar referencias cruzadas entre proyectos. |

> Lista completa de proyectos DLL -> `docs/scacs/01-arquitectura/01-business/projects.md`

## Transacciones - DataAccessKey

- **Obligatorio** pasar `DataAccessKey` en constructor de toda clase de negocio.
- Sin él: puede abrirse nueva transacción -> bloqueos, incoherencia.
- Commit/rollback automático al volver a presentación.
- Rollback automático ante cualquier excepción distinta de `PostValidationException`.
- No iniciar flujos de persistencia paralelos si deben compartir la misma transacción.

## Separación física

Las DLLs de negocio viven en AppDomain separado (puede ser otro servidor via WebService).
`ShadowCopyFiles` activo: se pueden reemplazar DLLs sin bajar la app,
pero el pool de IIS debe reciclarse para cargar la nueva versión.

---

# Presentación - FormBase

Todas las páginas heredan de una clase base que define el comportamiento estándar.

## Propiedades clave

| Propiedad | Uso |
|-----------|-----|
| `TargetAssembly` | ensamblado de negocio destino |
| `TargetClass` | clase destino (normalmente `BPC`) |
| `TargetAction` | método para carga inicial |
| `UpdateAction` | método para guardado |
| `FormData` | `DataSet` principal, vive en sesión |
| `BusinessEntityName` | tabla principal del DataSet |
| `FormAction` | intención del usuario: ALTA / MODIFICAR / BORRAR / CONSULTAR |
| `AccessMode` | permisos reales del usuario sobre este formulario |
| `Result` | estado al cerrar el formulario (aceptado / cancelado) |

## FormData y sesión

- `FormData` = `DataSet` principal de la página; se guarda en sesión.
- `PageSessionContainer` = envoltorio de sesión; incluye `FormData` y datos auxiliares.
  Clave aleatoria en QueryString identifica la sesión de cada página.
- Variantes específicas por dominio: `PageSessionContainerPG`, `PageSessionContainerGA`, etc.
- PostBack = recuperar desde sesión. No-PostBack = cargar desde negocio.

## Ciclo de carga (puntos de extensión clave)

```
PreLoadForm                   <- inicializar TargetAssembly, TargetClass, TargetAction, BusinessEntityName

[PostBack]    LoadFormDataFromPostBack
[No PostBack] AddLoadParams -> LoadFormDataFromBusiness

FormatForm                    <- formatear GridViews, definir columnas
MapeoCampos                   <- mapear campos y GridViews desde FormData
AdaptControlDetail            <- habilitar/deshabilitar/ocultar según datos actuales
EmptyListControl              <- botones según si el grid tiene filas

AccessFormMode
  ProcessAccessNew            <- estado controles en ALTA
  ProcessAccessUpdate         <- estado controles en MODIFICACION
  ProcessAccessQuery          <- deshabilitar controles en CONSULTA
```

Cargar en `LoadAdditionalDataFromSessionKey` variables enviadas desde otro formulario
(ej. id de cliente pasado en la navegación).

---

# Reglas para IA

- **Carga inicial**: traer todo (textos, validaciones, catálogos, datos) en una sola llamada a negocio.
  La presentación no debe llamar a negocio de forma incremental si puede evitarlo.
- **DataAccessKey**: obligatorio en constructores de negocio, siempre.
- **Excepciones**: son parte del contrato funcional. No convertir errores controlados en booleanos.
- **Formulario hijo**: al volver, comprobar siempre `Result` antes de aplicar su `FormData`.
- **Guardado**: revisar `SIValidaciones` antes de tocar lógica de guardado.
- **Validaciones de fila**: validar filas editadas antes del guardado global cuando el error depende de la fila.

---

# AIS (entorno de ejecución)

| Tipo | Ruta AIS |
|------|----------|
| Batch | `C:\AIS\<proyecto>\bin\` |
| Online | `C:\AIS\<proyecto>\Web\` |

El nombre del proyecto se toma de `(Get-Item $workspace).Parent.Parent.Name`
(workspace es `src\trunk`, proyecto está 2 niveles arriba).

- Copiar siempre el bin completo, evitar DLLs antiguas.
- ShadowCopyFiles: reemplazar DLLs en caliente, pero reciclar pool para activarlas.

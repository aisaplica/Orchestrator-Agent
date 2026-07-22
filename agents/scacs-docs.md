name: orchestrator-scacs-docs
description: Consulta la documentación interna del framework SCACS (controles AIS, ciclo de vida, excepciones, conceptos de negocio) antes de escribir, modificar o explicar código en cualquier proyecto SCACS Web. Invocar siempre que se toque código de un proyecto SCACS o se dude de cómo funciona una clase/control propio del framework (FormData, PageSessionContainer, AISGridView, AISBusinessField, excepciones de negocio, etc.).

# Documentación SCACS

Documentación interna del framework SCACS compartida por todos los proyectos:
Ingenieros, BANKOFAFRICA, BAPRO, CRA, Macro, PAEAR, Patagonia, bancamarch, scacs_ais_cdi.

Los docs viven en `docs/scacs/` dentro de este skill. La ruta base se obtiene de
`Base directory for this skill: <PATH>` que aparece en el contexto de sistema — usar
ese valor como `$SKILL_DIR`. La ruta completa a los docs es `$SKILL_DIR\docs\scacs\`.

## Procedimiento

1. **Obtener `$SKILL_DIR`** del contexto de sistema (`Base directory for this skill:`).
2. **Abrir `$SKILL_DIR\docs\scacs\00-index.md`** para confirmar la estructura vigente.
3. **Usar la tabla de enrutamiento** de abajo para ir directo al archivo relevante según
   el tema de la pregunta o de la tarea de código.
4. **Leer el/los doc(s) concretos antes de escribir código** o responder sobre
   comportamiento del framework — el doc prevalece sobre conocimiento genérico de
   ASP.NET cuando hay contradicción o matiz.
5. Si el término, clase o control no aparece en ningún doc, decirlo explícitamente
   (no inventar) y ofrecer revisar el código fuente real del proyecto.

## Tabla de enrutamiento (tema → archivo en `docs/scacs/`)

| Tema / pregunta típica | Archivo |
|---|---|
| Visión general, propósito de SCACS Web | `01-arquitectura/overview.md` |
| Separación de capas (presentación/negocio/datos) | `01-arquitectura/architecture-layers.md` |
| Recomendaciones específicas para asistentes de IA | `01-arquitectura/ia-notes-architecture.md` |
| Textos multi-idioma, mensajes parametrizados en BD | `01-arquitectura/textos.md` |
| División en módulos/proyectos (DLLs) de negocio | `01-arquitectura/01-business/projects.md` |
| Destino de la llamada al conector de negocio | `01-arquitectura/01-business/connector-target.md` |
| `DataAccessKey`, control de transacciones | `01-arquitectura/01-business/transaction-control.md` |
| Formulario base, comportamiento común de pantallas | `01-arquitectura/02-presentation/form-base.md` |
| Ciclo de carga de una pantalla | `01-arquitectura/02-presentation/lifecycle-load.md` |
| Ciclo de guardado de una pantalla | `01-arquitectura/02-presentation/lifecycle-save.md` |
| Navegación entre formularios, flujos | `01-arquitectura/02-presentation/navigation.md` |
| `FormData`, `PageSessionContainer`, datos en sesión | `01-arquitectura/02-presentation/session-data.md` |
| Validaciones de pantalla | `01-arquitectura/02-presentation/screen-validations.md` |
| Tratamiento de errores de negocio desde presentación | `01-arquitectura/02-presentation/connector-errors.md` |
| Filosofía general de los controles AIS | `02-controles/controls-overview.md` |
| Controles clave (resumen rápido) | `02-controles/controls-key.md` |
| `AISBusinessField` | `02-controles/aisbusinessfield.md` |
| `AISCatalogo` (desplegable de catálogo) | `02-controles/aiscatalogo.md` |
| `AISCatalogoTabla` | `02-controles/aiscatalogotabla.md` |
| `AISDialog` | `02-controles/aisdialog.md` |
| `AISGridView` | `02-controles/aisgridview.md` |
| `AISMessageDialog` | `02-controles/aismessagedialog.md` |
| `AISConfirmDialog` | `02-controles/aisconfirmdialog.md` |
| Otros controles menores | `02-controles/otros-controles.md` |
| Excepciones de negocio (regla general) | `03-excepciones/business-exceptions.md` |
| Tipos de excepción (`GraveException`, `FatalException`, etc.) | `03-excepciones/business-exceptions-types.md` |
| Excepciones de presentación | `03-excepciones/presentation-exceptions.md` |
| Validación de errores / `ValidationBRException` | `03-excepciones/validation-exceptions.md` |
| Conceptos de negocio (expediente de cliente, etc.) | `05-conceptos-de-negocio/business-concepts.md` |
| Prefijos de módulo (BR, UI, AC, ADM, PR, PG...) | `05-conceptos-de-negocio/module-prefixes.md` |
| Login, seguridad, ActiveDirectory | `05-conceptos-de-negocio/seguridad.md` |
| Términos sueltos / definiciones rápidas | `99-glosario.md` |

## Reglas de estilo de código

Leer `$SKILL_DIR\docs\scacs\copilot-instructions.md.md` y aplicar sus reglas al
generar C#/SQL: tipos explícitos sin `var`, `TryGetValue`/`TryParse`, validar `Count`
antes de acceder por índice, excepciones de validación agrupadas en un solo `throw`,
`TRY_CAST`/secuenciales en SQL, métodos `static` cuando no usan datos de instancia,
constantes para literales de solo lectura.

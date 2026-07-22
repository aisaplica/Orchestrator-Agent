
# AISConfirmDialog

## Descripción
Diálogo modal específico para mensajes Sí/No o Aceptar/Cancelar. Hereda de `AISDialog`, e incorpora los 2 botones. Solo hay que especificar el texto a mostrar, que será un código de `SINotificaciones`.

## Propiedades
- `DialogButtons`: Indica qué botones mostrar: Sí/No o Aceptar/Cancelar
- `CodigoMsg`: Código de la tabla `SINotificaciones` que mostrará

## Eventos
- `OnYESButtonClick`: Evento al hacer clic en el botón Sí o Aceptar
- `OnNOButtonClick`: Evento al hacer clic en el botón No o Cancelar
## Comportamiento
- Cierra por defecto.
- `IsModalVisible = true` muestra el modal.
- `IsModalVisible = false` lo oculta.

## Nota
Para mostrar un mensaje de confirmación únicamente al pulsar un botón, indicando al usuario “si está seguro”, y en caso de que el usuario cancele sea como si no ha hecho clic en el botón, se debería usar el control [[aismessagedialog]] en su lugar, que intercepta el clic del botón sin tener que poner un evento para el diálogo y otro para el Sí/No.
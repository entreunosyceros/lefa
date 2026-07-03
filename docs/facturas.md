# Facturas

[← Índice](README.md) · [Flujos operativos](flujos-operativos.md) · [VeriFactu y SIF](verifactu.md)

## Estados de factura

| Estado | Color en listado | Descripción |
|--------|------------------|-------------|
| Borrador | Gris claro | Editable, sin número oficial |
| Emitida | Naranja claro | Numerada y bloqueada |
| Cobrada | Verde claro | Emitida y marcada como cobrada |

## Facturas rectificativas

En el **Listado**, seleccione una factura emitida o cobrada y pulse **Rectificar**. Se crea un borrador en serie **RECT**, se **abre en *Nueva Factura*** y queda vinculado a la original. Ajuste las líneas (use **importes negativos** si debe devolver dinero) y emita. El PDF indica qué factura rectifica.

## Duplicar factura

En el **Listado**, seleccione una factura emitida o cobrada y pulse **Duplicar**. Se crea un **borrador** con el mismo cliente, líneas, serie e impuestos, el **vencimiento recalculado desde hoy** y se **abre en *Nueva Factura***.

## Vencimiento

Cada factura puede tener **fecha de vencimiento**. En el listado verá:

- *Pendiente*
- *Vence en 5 días*
- *Vencida*
- *Cobrada*

Sin automatismos: solo información clara para saber qué está pendiente de cobro.

## Historial de envío

Cada factura guarda si ya se envió por correo:

| Campo | Descripción |
|-------|-------------|
| `enviada` | `true` tras un envío correcto |
| `fecha_envio` | Cuándo se envió |
| `destinatario` | A qué email |

En el **Listado**, la columna **Envío** muestra *✓ Enviada (fecha)* o *Pendiente de enviar*.

Configuración del correo en [Correo SMTP](correo-smtp.md).

## Guardar PDFs desde el listado

En **Facturas/Borradores**:

- **Guardar PDF…** — una factura: elige archivo; varias: elige carpeta destino.
- **Abrir carpeta** — abre la carpeta de PDFs configurada en Preferencias.

Tras **Emitir** en *Nueva Factura*, también está disponible **Abrir carpeta PDFs**.

## Ver también

- [Facturae](facturae.md)
- [Correo SMTP](correo-smtp.md)
- [Flujos operativos](flujos-operativos.md)

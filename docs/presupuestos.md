# Presupuestos

[← Índice](README.md) · [Flujos operativos](flujos-operativos.md) · [Facturas](facturas.md)

## Flujo del día a día

1. **Nuevo Presupuesto** — cliente, líneas, *Emitir presupuesto* (PDF en `~/.lefa/presupuestos_pdf/`).
2. **Aceptar** — en *Listado presupuestos*, cuando el cliente dice que sí.
3. **Convertir en factura** — en *Nuevo Presupuesto* (botón verde tras emitir) o en *Listado presupuestos*. Se crea un borrador y **se abre automáticamente en *Nueva Factura*** con cliente, líneas e impuestos ya cargados; solo revise y pulse **Emitir**.

Si el presupuesto está emitido pero aún no marcado como aceptado, *Convertir en factura* lo acepta automáticamente.

## Estados del presupuesto

*Borrador* → *Emitido* → *Aceptado* → *Convertido* (o *Rechazado*).

## Trazabilidad con la factura

Al convertir, LEFA guarda en la base de datos el `factura_id` del borrador creado. En *Listado presupuestos*, un presupuesto *Convertido* muestra la factura vinculada en la columna **Factura** y el botón **Ver factura asociada** abre esa factura en *Nueva Factura*. La trazabilidad es bidireccional: la factura conserva `presupuesto_origen_id`.

## Ver también

- [Flujos operativos](flujos-operativos.md)
- [Datos locales y copias de seguridad](datos-y-backup.md)

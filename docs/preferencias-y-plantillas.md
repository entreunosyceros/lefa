# Preferencias y plantillas

[← Índice](README.md) · [Interfaz](interfaz.md) · [Facturae](facturae.md)

## Preferencias

En **Herramientas → Preferencias…** puede configurar valores por defecto que se aplican a nuevas facturas y al PDF:

| Opción | Descripción |
|--------|-------------|
| IVA / IRPF por defecto | Valores al crear una factura nueva |
| Vencimiento por defecto | Días desde la emisión (p. ej. 30) |
| Empresa emisora | Nombre, NIF, dirección, teléfono, email, **IBAN** (necesario para Facturae/FACe) |
| Forma de pago Facturae | Código por defecto (`04` = transferencia bancaria) |
| Logotipo (PDF) | Aparece en el PDF (no cambia el icono de la aplicación) |
| Formato de número | `FACT-2026-0001`, `2026-001`, `0001/2026`, `WEB-001`, etc. **No cambiar a mitad de año fiscal** (riesgo de duplicados o saltos; el hash VeriFactu es global e independiente de la serie) |
| Series de facturación | Varias series con correlativo independiente (`FACT, WEB, MANT`) |
| Carpeta PDFs | Dónde se guardan los PDF generados |
| Pie de factura (PDF) | Texto opcional al final de la factura (varias líneas) |

La UI de preferencias muestra un aviso si intenta cambiar el formato de numeración a mitad de ejercicio.

## Catálogo de servicios

**Herramientas → Catálogo de servicios…** (o **Gestionar servicios…** en *Nueva Factura*) — servicios con descripción, precio e IVA (ej. Desarrollo web 40 €/h al 21 %). Puede crear, editar o eliminar los del catálogo, incluidos los de ejemplo del primer arranque. **Añadir servicio** rellena la línea y el IVA.

## Plantillas de factura completa

**Herramientas → Plantillas de factura…** — facturas enteras reutilizables (cliente, líneas, IVA, serie). **Nueva factura desde plantilla** crea un borrador listo para emitir.

## Plantillas de líneas

No son plantillas de PDF, sino **conceptos reutilizables** para facturas recurrentes.

En **Herramientas → Plantillas de líneas…** o con **Gestionar plantillas…** en *Nueva Factura* puede crear, editar o eliminar plantillas (descripción, cantidad y precio), incluidas las de ejemplo. Al facturar, elija una en el desplegable y pulse **Añadir plantilla**.

Al instalar por primera vez se incluyen dos ejemplos:

- Mantenimiento informático mensual — 250 €
- Desarrollo software — 8 h × 35 €/h

## Ver también

- [Facturae](facturae.md)
- [Flujos operativos](flujos-operativos.md)

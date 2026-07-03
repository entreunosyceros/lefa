# Facturae (XML)

[← Índice](README.md) · [VeriFactu y SIF](verifactu.md) · [Preferencias y plantillas](preferencias-y-plantillas.md)

Al emitir una factura, LEFA genera automáticamente:

- `Factura.pdf` en la carpeta de PDFs
- `Factura.xml` en `~/.lefa/facturas_xml/`

Sin pasos extra: *Emitir factura* y listo.

## Requisitos FACe (administración pública)

El XML incluye medio de pago (por defecto `04` = transferencia), **IBAN del emisor** (en *Preferencias → Empresa emisora*) y, si el cliente es una administración, los códigos **DIR3** (oficina contable, órgano gestor, unidad tramitadora) configurables en la ficha del cliente. Sin IBAN o sin DIR3 cuando FACe los exige, la plataforma del Estado rechazará el fichero aunque el XML esté bien formado.

| Dónde configurarlo | Campo |
|--------------------|-------|
| Preferencias | IBAN emisor, forma de pago por defecto (`04`) |
| Cliente → Facturae / FACe | DIR3, IBAN cliente (opcional), forma de pago |

## Ver también

- [Facturas](facturas.md)
- [Flujos operativos](flujos-operativos.md)

# VeriFactu y SIF (España)

[← Índice](README.md) · [Facturas](facturas.md) · [Arquitectura del proyecto](arquitectura.md)

La normativa de sistemas de facturación (Reglamento del SIF y VeriFactu) es de **obligado cumplimiento** para el software que emite facturas en España. LEFA genera en local los elementos técnicos del registro: cadena de hashes, persistencia del registro y código QR con leyenda legal.

## Módulos (`lefa/verifactu/`)

| Módulo | Función |
|--------|---------|
| `hash.py` | Hash SHA-256 encadenado (cadena única para todas las series) |
| `registro.py` | Registro inmutable al emitir (JSON local) |
| `qr.py` | URL de cotejo AEAT, leyenda legal del QR y generación del PNG (35 mm en PDF) |
| `export.py` | Exportación ZIP de registros |

## Al emitir una factura

LEFA genera el registro encadenado, guarda el hash en la factura e imprime el **QR tributario** en el PDF (35×35 mm) con la leyenda legal vigente:

- *SISTEMA INFORMÁTICO NO VERIFICADO* — modalidad **No-VeriFactu** (cotejo sin remisión automática a la AEAT; configuración actual en `lefa/config.py`).
- *VERI*FACTU* — cuando se active en configuración la modalidad con envío/remisión VeriFactu.

El módulo `qr.py` construye la URL con el **formato oficial de la AEAT** (`nif`, `numserie`, fecha `DD-MM-AAAA`, importe con punto decimal y, en VeriFactu, `hash` SHA-256 completo en minúsculas).

## Cadena de hashes

El hilo VeriFactu es **único e ininterrumpido** para todo el programa (independiente de la serie `FACT`, `WEB`, `RECT`, etc.). Una rectificativa enlaza con la **última factura emitida cronológicamente**, no con la rectificativa anterior. El orden se determina por fecha de emisión e ID.

## Concurrencia en SQLite

La emisión usa `session_scope_immediate()` con **`BEGIN IMMEDIATE`**: reserva el bloqueo de escritura de la base de datos y asigna número correlativo y hash en el **mismo commit**. En SQLite, `with_for_update()` de SQLAlchemy **no bloquea filas** (se ignora); `BEGIN IMMEDIATE` es el mecanismo correcto para evitar que dos emisiones simultáneas lean el mismo último hash.

## Exportación

**Herramientas → Exportar registros VeriFactu…** empaqueta todos los registros para auditoría.

## Ver también

- [Facturae](facturae.md)
- [Datos locales y copias de seguridad](datos-y-backup.md)
- [Preferencias y plantillas](preferencias-y-plantillas.md) — formato de numeración

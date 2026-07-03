# Documentación de LEFA

[← Volver al README del proyecto](../README.md)

Guías del repositorio. Para la documentación web ampliada, consulte también la [documentación oficial en Mintlify](https://mintlify.wiki/entreunosyceros/lefa).

## Índice

| Guía | Contenido |
|------|-----------|
| [Instalación](instalacion.md) | Arranque rápido, dependencias Linux, instalación manual y variables de entorno |
| [Interfaz](interfaz.md) | Pestañas, menús, bandeja del sistema y cierre de la aplicación |
| [Flujos operativos](flujos-operativos.md) | Factura directa, presupuesto → factura y acciones habituales |
| [Facturas](facturas.md) | Rectificativas, duplicar, vencimiento, envío por email y estados |
| [Presupuestos](presupuestos.md) | Ciclo de vida y conversión en factura |
| [Preferencias y plantillas](preferencias-y-plantillas.md) | Emisor, numeración, servicios y plantillas reutilizables |
| [Correo SMTP](correo-smtp.md) | Configuración y envío de facturas por email |
| [VeriFactu y SIF](verifactu.md) | Hash encadenado, QR, registros y concurrencia SQLite |
| [Facturae](facturae.md) | Generación de XML y requisitos FACe |
| [Datos locales y copias de seguridad](datos-y-backup.md) | Carpetas `~/.lefa`, backup integrado y respaldo manual |
| [Arquitectura del proyecto](arquitectura.md) | Estructura de carpetas y módulos del código |

## Inicio rápido

```bash
cd LEFA
python3 run_app.py
```

Detalles en [Instalación](instalacion.md).

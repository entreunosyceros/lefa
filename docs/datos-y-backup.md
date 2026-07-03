# Datos locales y copias de seguridad

[← Índice](README.md) · [Instalación](instalacion.md) · [VeriFactu y SIF](verifactu.md)

## Ubicación de los datos

Todo se guarda en `~/.lefa/` (Windows: `%USERPROFILE%\.lefa`):

| Recurso | Ubicación |
|---------|-----------|
| Base de datos | `~/.lefa/lefa.db` |
| PDFs de facturas | `~/.lefa/facturas_pdf/` |
| PDFs de presupuestos | `~/.lefa/presupuestos_pdf/` |
| Facturae (XML) | `~/.lefa/facturas_xml/` |
| Registros VeriFactu | `~/.lefa/verifactu/registros/` |
| Configuración SMTP | `~/.lefa/smtp_config.json` |
| Preferencias | `~/.lefa/preferencias.json` |
| Contraseña SMTP | Llavero del sistema (keyring) |

Al primer arranque se crean **3 clientes de ejemplo** si la base de datos está vacía.

> **Nota:** Requiere un entorno de escritorio activo para interactuar con el llavero del sistema de forma segura. Véase [Correo SMTP](correo-smtp.md).

## Copia de seguridad integrada

**Archivo → Crear copia de seguridad…** genera un ZIP (`backup_2026-06-18.zip`) con:

- `lefa.db`
- `preferencias.json`
- `smtp_config.json`
- `facturas_pdf/`
- `presupuestos_pdf/`
- `facturas_xml/` (Facturae)
- `verifactu/registros/`

> La contraseña SMTP está en el llavero del sistema y **no** se incluye en el ZIP.

## Respaldo manual

También puede copiar la carpeta `~/.lefa` a un pendrive:

```bash
cp -a ~/.lefa /ruta/a/tu/pendrive/lefa-backup-$(date +%Y%m%d)
```

En Windows, copie la carpeta `%USERPROFILE%\.lefa` a un USB o disco externo.

| Contenido | Archivo / carpeta |
|-----------|-------------------|
| Base de datos | `lefa.db` |
| Facturas en PDF | `facturas_pdf/` |
| Presupuestos en PDF | `presupuestos_pdf/` |
| Facturae (XML) | `facturas_xml/` |
| VeriFactu (registros) | `verifactu/registros/` |
| Configuración SMTP | `smtp_config.json` |
| Preferencias | `preferencias.json` |
| Contraseña de correo | Llavero del sistema (keyring) |

> **Recomendación:** haga copias periódicas (semanal o mensual). Si restaura en otro equipo, copie la carpeta de vuelta a `~/.lefa` y reconfigure la contraseña SMTP si el llavero no se transfiere.

## Ver también

- [Instalación](instalacion.md)
- [Correo SMTP](correo-smtp.md)

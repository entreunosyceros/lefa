# Correo SMTP

[← Índice](README.md) · [Facturas](facturas.md) · [Interfaz](interfaz.md)

Antes de enviar facturas por email, configure su cuenta en **Herramientas → Configurar correo electrónico…**

| Campo | Descripción |
|-------|-------------|
| Servidor SMTP | Ej. `smtp.gmail.com`, `smtp.office365.com` |
| Puerto | 587 (STARTTLS) o 465 (SSL) |
| Seguridad | STARTTLS, SSL o sin cifrado |
| Usuario | Cuenta de correo |
| Contraseña | Guardada en el llavero del sistema |
| Remitente | Dirección que verá el cliente |

Use **Probar conexión** para validar la configuración. Opcionalmente puede enviar un correo de prueba al remitente.

> **Gmail / Outlook:** suele requerir una [contraseña de aplicación](https://support.google.com/accounts/answer/185833), no la contraseña habitual de la cuenta.

> **Nota headless:** en Linux sin escritorio activo, `keyring` puede fallar al no encontrar el demonio D-Bus de la sesión (GNOME Keyring, KWallet, etc.).

## Ver también

- [Facturas](facturas.md) — historial de envío
- [Datos locales y copias de seguridad](datos-y-backup.md)

# Política de seguridad

## Versiones con soporte

| Versión | Soportada |
| ------- | --------- |
| 1.0.x   | ✅        |
| < 1.0   | ❌        |

## Alcance

LEFA es una **aplicación de escritorio** (PyQt6 + SQLite) pensada para ejecutarse en el equipo del usuario. Los datos (facturas, clientes, PDFs, registros VeriFactu) residen en `~/.lefa/`. En el ámbito de seguridad nos interesa especialmente:

- Inyección SQL o corrupción de datos en la base SQLite local.
- Exposición involuntaria de credenciales SMTP o contraseñas del llavero del sistema (`keyring`).
- Lectura o escritura no autorizada de archivos fuera de las rutas previstas (`~/.lefa/`, carpeta PDF configurada).
- Fugas de información sensible en logs, copias de seguridad ZIP o exportaciones VeriFactu.
- Dependencias de Python con vulnerabilidades conocidas que afecten al entorno de ejecución.
- Comportamientos inseguros al generar XML Facturae, registros VeriFactu o al enviar correo.

**Fuera de alcance habitual:** Disponibilidad de servidores SMTP de terceros (Gmail, Outlook, etc.), cambios en las especificaciones AEAT/FACe, o el uso de LEFA en entornos *headless* sin llavero gráfico (ver README).

## Cómo reportar una vulnerabilidad

1. **No** abras un issue público con detalles del fallo de seguridad.
2. Usa [GitHub Security Advisories](https://github.com/entreunosyceros/lefa/security/advisories/new) (**Report a vulnerability**) si la opción está habilitada en este repositorio.
3. Si no puedes usar Advisories, abre un issue con el título `SECURITY (sin detalles)` y solicita un canal de comunicación privado; no incluyas pasos de explotación en el tablón público.

Incluye, en la medida de lo posible:

- Descripción del problema y componente afectado (p. ej. `email_service`, `database`, exportación ZIP).
- Pasos detallados para reproducir el fallo.
- Impacto estimado (solo local, otros usuarios del equipo, red).
- Versión o commit afectado.
- Sugerencia de mitigación, si dispones de ella.

## Qué esperar

- **Acuse de recibo:** Evaluación inicial en un plazo razonable de pocos días.
- **Resolución:** Parche, mitigación o refactorización del componente afectado en una versión posterior si procede.
- **Créditos:** Reconocimiento público al informante en las notas de la release, salvo que se solicite expresamente el anonimato.

## Buenas prácticas para usuarios

- **Datos locales:** La carpeta `~/.lefa/` contiene información fiscal sensible. Protege el equipo y haz copias de seguridad cifradas si las almacenas fuera de tu máquina.
- **SMTP:** Usa contraseñas de aplicación cuando el proveedor lo exija; la contraseña se guarda en el llavero del sistema, no en el ZIP de backup.
- **Entorno de escritorio:** El envío de correo requiere un entorno gráfico con llavero activo (no suele funcionar por SSH sin D-Bus).
- **Actualizaciones:** Mantén Python y las dependencias actualizadas (`pip install -r requirements.txt --upgrade`).
- **Origen seguro:** Descarga el código y los releases únicamente desde el [repositorio oficial de LEFA](https://github.com/entreunosyceros/lefa).

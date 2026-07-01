# Guía de contribución

¡Gracias por interesarte en **LEFA** (Local & Eficiente Facturación para Autónomos)! Este proyecto es software libre ([GPL-3.0](LICENSE)) para facturación de escritorio con datos 100 % locales. Cualquier mejora bien planteada es bienvenida.

> **Estado del proyecto:** LEFA está en fase de desarrollo y pruebas. No se recomienda aún para facturación real en producción.

## Antes de empezar

- Lee el [README](README.md) para entender el alcance: facturas, presupuestos, VeriFactu, Facturae, clientes y envío por correo.
- Revisa las [issues abiertas](https://github.com/entreunosyceros/lefa/issues) por si alguien ya trabaja en lo mismo.
- Consulta el [Código de conducta](CODE_OF_CONDUCT.md).
- Para vulnerabilidades, sigue [SECURITY.md](SECURITY.md) (no abras issues públicas con detalles de explotación).

## Cómo puedes ayudar

- **Reportar errores** en la interfaz, emisión de facturas, PDF, VeriFactu, Facturae o envío SMTP.
- **Proponer mejoras** explicando el caso de uso del autónomo y el impacto esperado.
- **Enviar pull requests** acotados y probados manualmente.
- **Mejorar documentación** (README, Ayuda rápida en la app, comentarios en código).
- **Probar en Linux y Windows** si tu cambio afecta a la UI o al arranque.

## Entorno de desarrollo

Requisitos: **Python 3.10+**, entorno de escritorio (PyQt6) y, para probar correo, un llavero del sistema (GNOME Keyring, KWallet, etc.).

```bash
git clone https://github.com/entreunosyceros/lefa.git
cd lefa
python3 run_app.py
```

`run_app.py` crea el entorno virtual si no existe, instala dependencias y arranca la aplicación.

### Arranque manual (opcional)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Datos locales

La aplicación guarda todo en `~/.lefa/` (en Windows: `%USERPROFILE%\.lefa\`). No subas esa carpeta ni archivos de backup con datos reales a issues o PRs.

## Áreas del código

| Área | Ubicación habitual |
|------|-------------------|
| Ventana principal / pestañas | `lefa/ui/main_window.py`, `inicio_tab.py`, `nueva_factura_tab.py` |
| Listados y presupuestos | `lefa/ui/listado_tab.py`, `listado_presupuestos_tab.py` |
| Lógica de facturación | `lefa/services/factura_service.py` |
| Presupuestos | `lefa/services/presupuesto_service.py` |
| PDF y Facturae | `lefa/services/pdf_service.py`, `facturae_service.py` |
| VeriFactu | `lefa/verifactu/` |
| Clientes y preferencias | `lefa/services/cliente_service.py`, `preferencias_service.py` |
| Correo SMTP | `lefa/services/email_service.py` |
| Modelos ORM | `lefa/models/` |
| Base de datos / migraciones | `lefa/database/` |

## Estilo de código

- Sigue el estilo del código existente (nombres, imports, nivel de comentarios).
- Cambios **mínimos y enfocados**: no mezcles varias funcionalidades en un mismo PR.
- Los textos visibles para el usuario van en **español**, con tono claro y directo.
- No incluyas secretos (contraseñas SMTP, `.env`), rutas personales ni datos fiscales reales en commits o issues.
- La UI se maqueta **solo por código** (PyQt6), sin archivos `.ui`.

## Pull requests

1. Crea una rama descriptiva desde `main` (por ejemplo `fix/verifactu-cadena` o `feat/listado-vencimiento`).
2. Describe **qué** cambias y **por qué**.
3. Indica cómo lo has probado (pasos manuales, capturas o comandos).
4. Si tocas VeriFactu o Facturae, indica el escenario probado (serie, rectificativa, etc.).
5. Actualiza el README solo si el cambio lo requiere.

Usa la [plantilla de pull request](.github/pull_request_template.md) al abrir el PR.

## Reportar problemas

- **Bugs y mejoras:** plantillas de [GitHub Issues](https://github.com/entreunosyceros/lefa/issues/new/choose).
- **Seguridad:** [SECURITY.md](SECURITY.md).

## Licencia

Al contribuir, aceptas que tu aportación se publique bajo la misma licencia del proyecto: [GNU General Public License v3.0](LICENSE).

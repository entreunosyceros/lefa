# Arquitectura del proyecto

[← Índice](README.md) · [Instalación](instalacion.md) · [VeriFactu y SIF](verifactu.md)

<p align="center">
<img width="1916" height="1048" alt="Estructura del proyecto" src="https://github.com/user-attachments/assets/7f270575-930e-4f23-bdf5-6b613e9d4a2d" />
</p>

## Stack

- **UI:** PyQt6 (maquetación 100% por código, sin archivos `.ui`)
- **BD:** SQLite + SQLAlchemy
- **PDF:** FPDF2 + QR tributario (qrcode)
- **Correo:** smtplib + keyring (contraseña en llavero del sistema)

## Estructura de carpetas

```
LEFA/
├── main.py                 # Punto de entrada directo (con venv activo)
├── run_app.py              # Arranque con gestión automática del entorno
├── requirements.txt
├── LICENSE                 # GNU GPL v3.0
├── docs/                   # Documentación del repositorio
├── img/
│   └── logo.png            # Icono de ventana, bandeja y diálogo "Sobre"
└── lefa/
    ├── config.py           # Rutas, constantes y datos del emisor
    ├── resources.py        # Rutas a recursos e icono de la aplicación
    ├── database/           # Engine y sesiones SQLite
    ├── models/             # Cliente, Factura, Presupuesto, Servicio, plantillas…
    ├── services/           # Negocio, PDF, Facturae, presupuestos, email…
    ├── verifactu/          # Hash, QR, registro y exportación (SIF España)
    ├── workers/            # PDF factura/presupuesto, SMTP
    ├── ui/
    │   ├── main_window.py
    │   ├── nueva_factura_tab.py
    │   ├── nuevo_presupuesto_tab.py
    │   ├── listado_tab.py
    │   ├── listado_presupuestos_tab.py
    │   ├── clientes_tab.py
    │   ├── servicios_dialog.py
    │   ├── plantillas_factura_dialog.py
    │   └── …
    └── utils/
```

## Ver también

- [VeriFactu y SIF](verifactu.md)
- [Instalación](instalacion.md)

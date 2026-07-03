# Interfaz

[← Índice](README.md) · [Flujos operativos](flujos-operativos.md) · [Preferencias y plantillas](preferencias-y-plantillas.md)

## Pestañas

| Pestaña | Descripción |
|---------|-------------|
| **Inicio** | Flujo visual lineal: el camino recto para facturar o presupuestar (sin laberinto de ventanas). |
| **Nueva Factura** | Cliente, serie, vencimiento, líneas con plantillas/servicios, IVA/IRPF. *Guardar*, *Emitir*, *Abrir carpeta PDFs* (tras emitir) y *Enviar por email*. |
| **Nuevo Presupuesto** | Crear, emitir y **convertir en factura** presupuestos comerciales. |
| **Listado presupuestos** | *Aceptar*, *Convertir en factura*, *Rechazar*, *Ver factura asociada*. |
| **Facturas/Borradores** | Estado, **envío**, **vencimiento**. **Guardar PDF…** (una o varias), **Abrir carpeta**, **Duplicar**, **Rectificar**, *Marcar como Cobrada*. |
| **Clientes** | **Buscar** por nombre, NIF o email. Al editar: historial de facturas y total facturado. |

## Menú superior

| Menú | Opciones |
|------|----------|
| **Archivo** | Crear copia de seguridad… · Salir (`Ctrl+Q`) |
| **Clientes** | Nuevo cliente… · Gestionar clientes |
| **Herramientas** | Correo · Preferencias · Plantillas · Plantillas de factura · Catálogo de servicios · Exportar VeriFactu |
| **Ayuda** | Ayuda rápida… (`F1`) · Sobre… (logo, versión y enlace a GitHub) |

## Bandeja del sistema

- Al arrancar aparece el icono `img/logo.png` en la bandeja (si el entorno de escritorio lo soporta).
- **Clic derecho:** menú contextual con las mismas opciones que el menú superior.
- **Doble clic** (o clic simple en algunos entornos): restaura la ventana principal.

## Cierre de la aplicación

| Acción | Comportamiento |
|--------|----------------|
| **X** en la ventana (con bandeja) | Oculta la ventana; LEFA sigue en la bandeja. Notificación: *"LEFA sigue ejecutándose en la bandeja del sistema."* |
| **Archivo → Salir** | Cierra la aplicación por completo. |
| **Salir** en la bandeja | Cierra la aplicación por completo. |
| **X** sin bandeja disponible | Cierra la aplicación (comportamiento estándar). |
| **Ctrl+C** en la terminal | Cierra la aplicación de forma segura. |

## Ver también

- [Flujos operativos](flujos-operativos.md)
- [Correo SMTP](correo-smtp.md)

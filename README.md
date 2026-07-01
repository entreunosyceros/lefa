# LEFA — Local & Eficiente Facturación para Autónomos
<p align="center">
<img width="1200" height="655" alt="logo" src="https://github.com/user-attachments/assets/d3e52c55-7abb-4cc4-bb1f-cf7640292f74" />
</p>

Aplicación de escritorio para facturación de autónomos con control total local. Compatible con **Linux** y **Windows**.

## ¿Por qué?

LEFA nace tras hablar con un pequeño autónomo que estaba cansado de tener que trabajar con ERP muy complejos para realizar tareas tan sencillas como emitir una factura o enviarla a un cliente.

El objetivo de este proyecto es ofrecer una herramienta de escritorio sencilla, rápida y totalmente local, pensada para aquellos profesionales que únicamente necesitan gestionar sus clientes y emitir facturas sin tener que aprender a utilizar decenas de módulos que nunca llegarán a usar.

Al funcionar completamente en local, no requiere suscripciones mensuales, servicios en la nube ni depender de un proveedor externo para acceder a la información.

> **⚠ Estado del proyecto**
>
> LEFA se encuentra actualmente en fase de desarrollo y pruebas. Aunque muchas funcionalidades ya están implementadas, todavía no se recomienda su uso en entornos de producción ni para la gestión de la facturación real de un negocio.
>
> LEFA no pretende competir con un ERP. Pretende evitar que un pequeño autónomo necesite uno para realizar su trabajo diario.

## Stack

- **UI:** PyQt6 (maquetación 100% por código, sin archivos `.ui`)
- **BD:** SQLite + SQLAlchemy
- **PDF:** FPDF2 + QR tributario (qrcode)
- **Correo:** smtplib + keyring (contraseña en llavero del sistema)

## Ejecución rápida (recomendada)

`run_app.py` crea el entorno virtual si no existe, instala dependencias y arranca la aplicación:

```bash
cd LEFA
python3 run_app.py
```

En Windows:

```powershell
cd LEFA
python run_app.py
```

## Instalación manual

```bash
cd LEFA
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Datos locales

| Recurso              | Ubicación                      |
|----------------------|--------------------------------|
| Base de datos        | `~/.lefa/lefa.db`              |
| PDFs de facturas     | `~/.lefa/facturas_pdf/`        |
| PDFs de presupuestos | `~/.lefa/presupuestos_pdf/`    |
| Facturae (XML)       | `~/.lefa/facturas_xml/`        |
| Registros VeriFactu  | `~/.lefa/verifactu/registros/` |
| Configuración SMTP   | `~/.lefa/smtp_config.json`     |
| Preferencias         | `~/.lefa/preferencias.json`    |
| Contraseña SMTP      | Llavero del sistema (keyring)  |

> **Nota:** Requiere un entorno de escritorio activo para interactuar con el llavero del sistema de forma segura. En Linux, si ejecuta LEFA por SSH o en un servidor sin interfaz gráfica (*headless*), `keyring` puede fallar al no encontrar el demonio de D-Bus de la sesión (p. ej. GNOME Keyring o KWallet).

Al primer arranque se crean **3 clientes de ejemplo** si la base de datos está vacía.

## Estructura del proyecto
<p align="center">
<img width="1916" height="1048" alt="2026-07-01_13-19" src="https://github.com/user-attachments/assets/7f270575-930e-4f23-bdf5-6b613e9d4a2d" />
</p>

```
LEFA/
├── main.py                 # Punto de entrada directo (con venv activo)
├── run_app.py              # Arranque con gestión automática del entorno
├── requirements.txt
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

## Interfaz

### Pestañas

| Pestaña         | Descripción |
|-----------------|-------------|
| **Inicio** | Flujo visual lineal: el camino recto para facturar o presupuestar (sin laberinto de ventanas). |
| **Nueva Factura** | Cliente (se recuerda el último usado), **serie**, **vencimiento**, líneas con plantillas, IVA/IRPF. Botones *Guardar*, *Emitir* y *Enviar por email*. |
| **Nuevo Presupuesto** | Crear y emitir presupuestos comerciales (sin validez fiscal). |
| **Listado presupuestos** | *Aceptar*, *Convertir en factura*, *Rechazar*. |
| **Listado**       | Estado, **envío**, **vencimiento**. **Duplicar**, **Rectificar**, *Marcar como Cobrada*. |
| **Clientes**      | **Buscar** por nombre, NIF o email. Al editar: historial de facturas y total facturado. |

### Menú superior

| Menú           | Opciones |
|----------------|----------|
| **Archivo**    | Crear copia de seguridad… · Salir (`Ctrl+Q`) |
| **Clientes**   | Nuevo cliente… · Gestionar clientes |
| **Herramientas** | Correo · Preferencias · Plantillas · Plantillas de factura · Catálogo de servicios · Exportar VeriFactu |
| **Ayuda**      | Ayuda rápida… (`F1`) · Sobre… (logo, versión y enlace a GitHub) |

### Bandeja del sistema

- Al arrancar aparece el icono `img/logo.png` en la bandeja (si el entorno de escritorio lo soporta).
- **Clic derecho:** menú contextual con las mismas opciones que el menú superior.
- **Doble clic** (o clic simple en algunos entornos): restaura la ventana principal.

## Configuración de correo (SMTP)

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

## Presupuestos

Flujo pensado para el día a día:

1. **Nuevo Presupuesto** — cliente, líneas, *Emitir presupuesto* (PDF en `~/.lefa/presupuestos_pdf/`).
2. **Aceptar** — en *Listado presupuestos*, cuando el cliente dice que sí.
3. **Convertir en factura** — en *Listado presupuestos*, pulse el botón homónimo. Se crea un borrador y **se abre automáticamente en *Nueva Factura*** con cliente, líneas e impuestos ya cargados; solo revise y pulse **Emitir**.

Si el presupuesto está emitido pero aún no marcado como aceptado, *Convertir en factura* lo acepta automáticamente.

Estados del presupuesto: *Borrador* → *Emitido* → *Aceptado* → *Convertido* (o *Rechazado*).

Al convertir, LEFA guarda en la base de datos el `factura_id` del borrador creado. Meses después, en *Listado presupuestos*, un presupuesto *Convertido* muestra la factura vinculada en la columna **Factura** y el botón **Ver factura asociada** abre esa factura en *Nueva Factura*. La trazabilidad es bidireccional: la factura conserva `presupuesto_origen_id`.

## Facturas rectificativas

En el **Listado**, seleccione una factura emitida o cobrada y pulse **Rectificar**. Se crea un borrador en serie **RECT**, se **abre en *Nueva Factura*** y queda vinculado a la original. Ajuste las líneas (use **importes negativos** si debe devolver dinero) y emita. El PDF indica qué factura rectifica.

## VeriFactu (preparado para España)

Arquitectura en `lefa/verifactu/`:

| Módulo | Función |
|--------|---------|
| `hash.py` | Hash SHA-256 encadenado (cadena única para todas las series) |
| `registro.py` | Registro inmutable al emitir (JSON local) |
| `qr.py` | URL de cotejo AEAT (NIF, número de factura, fecha e importe) y generación del QR tributario |
| `export.py` | Exportación ZIP de registros |

Al **emitir**, LEFA genera el registro encadenado, guarda el hash en la factura e imprime el **QR tributario** en el PDF. El módulo `qr.py` construye la URL con el **formato oficial de la AEAT** (parámetros `nif`, `numserie`, fecha en `DD-MM-AAAA` e importe con punto decimal). **Generación de código QR conforme a las especificaciones de la resolución de la AEAT.** Modalidad actual: *No-VeriFactu* (cotejo sin envío automático a AEAT). El envío oficial se podrá activar sin reescribir la aplicación.

**Cadena de hashes:** el hilo VeriFactu es **único e ininterrumpido** para todo el programa. Una factura rectificativa (serie `RECT`) enlaza con la **última factura emitida cronológicamente** en el sistema (p. ej. una `FACT`), no con la rectificativa anterior. El orden se determina por fecha de emisión e ID, sin filtrar por serie.

**Herramientas → Exportar registros VeriFactu…** empaqueta todos los registros para auditoría.

## Facturae (XML)

Al emitir una factura, LEFA genera automáticamente:

- `Factura.pdf` en la carpeta de PDFs
- `Factura.xml` en `~/.lefa/facturas_xml/`

Sin pasos extra: *Emitir factura* y listo.

**Requisitos FACe (administración pública):** el XML incluye medio de pago (por defecto `04` = transferencia), **IBAN del emisor** (en *Preferencias → Empresa emisora*) y, si el cliente es una administración, los códigos **DIR3** (oficina contable, órgano gestor, unidad tramitadora) configurables en la ficha del cliente. Sin IBAN o sin DIR3 cuando FACe los exige, la plataforma del Estado rechazará el fichero aunque el XML esté bien formado.

| Dónde configurarlo | Campo |
|--------------------|-------|
| Preferencias | IBAN emisor, forma de pago por defecto (`04`) |
| Cliente → Facturae / FACe | DIR3, IBAN cliente (opcional), forma de pago |

## Catálogo de servicios

**Herramientas → Catálogo de servicios…** — servicios con descripción, precio e IVA (ej. Desarrollo web 40 €/h al 21 %). En *Nueva Factura*, **Añadir servicio** rellena la línea y el IVA.

## Plantillas de factura completa

**Herramientas → Plantillas de factura…** — facturas enteras reutilizables (cliente, líneas, IVA, serie). **Nueva factura desde plantilla** crea un borrador listo para emitir.

## Preferencias

En **Herramientas → Preferencias…** puede configurar valores por defecto que se aplican a nuevas facturas y al PDF:

| Opción | Descripción |
|--------|-------------|
| IVA / IRPF por defecto | Valores al crear una factura nueva |
| Vencimiento por defecto | Días desde la emisión (p. ej. 30) |
| Empresa emisora | Nombre, NIF, dirección, teléfono, email, **IBAN** (necesario para Facturae/FACe) |
| Forma de pago Facturae | Código por defecto (`04` = transferencia bancaria) |
| Logotipo | Aparece en el PDF y como icono de la aplicación |
| Formato de número | `FACT-2026-0001`, `2026-001`, `0001/2026`, `WEB-001`, etc. |
| Series de facturación | Varias series con correlativo independiente (`FACT, WEB, MANT`) |
| Carpeta PDFs | Dónde se guardan los PDF generados |

## Plantillas de líneas

No son plantillas de PDF, sino **conceptos reutilizables** para facturas recurrentes.

En **Herramientas → Plantillas de líneas…** puede crear, editar o eliminar plantillas (descripción, cantidad y precio). Al facturar, elija una en el desplegable de *Nueva Factura* y pulse **Añadir plantilla**.

Al instalar por primera vez se incluyen dos ejemplos:

- Mantenimiento informático mensual — 250 €
- Desarrollo software — 8 h × 35 €/h

## Historial de envío

Cada factura guarda si ya se envió por correo:

| Campo | Descripción |
|-------|-------------|
| `enviada` | `true` tras un envío correcto |
| `fecha_envio` | Cuándo se envió |
| `destinatario` | A qué email |

En el **Listado**, la columna **Envío** muestra *✓ Enviada (fecha)* o *Pendiente de enviar*. Así, meses después, sigue siendo evidente si esa factura ya salió por correo.

## Duplicar factura

En el **Listado**, seleccione una factura emitida o cobrada y pulse **Duplicar**. Se crea un **borrador** con el mismo cliente, líneas, serie e impuestos, el **vencimiento recalculado desde hoy** y se **abre en *Nueva Factura***.

## Vencimiento

Cada factura puede tener **fecha de vencimiento**. En el listado verá:

- *Pendiente*
- *Vence en 5 días*
- *Vencida*
- *Cobrada*

Sin automatismos: solo información clara para saber qué está pendiente de cobro.

## Copia de seguridad

**Archivo → Crear copia de seguridad…** genera un ZIP (`backup_2026-06-18.zip`) con:

- `lefa.db`
- `preferencias.json`
- `smtp_config.json`
- `facturas_pdf/`
- `presupuestos_pdf/`
- `facturas_xml/` (Facturae)
- `verifactu/registros/`

> La contraseña SMTP está en el llavero del sistema y **no** se incluye en el ZIP.

## Flujo operativo

### Factura directa

1. Configure **preferencias** (IVA, emisor, carpeta PDF) y el **correo SMTP** (menú *Herramientas*).
2. Cree o seleccione un **cliente** con NIF y, si enviará por email, con dirección de correo.
3. En **Nueva Factura**, añada líneas (manual, **servicio**, **plantilla de línea** o **plantilla de factura**).
4. **Guardar como Borrador** o **Emitir Factura** (genera PDF, XML Facturae y registro VeriFactu).
5. **Enviar por email** si procede; consulte el **Listado** (envío, vencimiento, cobro).

### Presupuesto → factura

1. Pestaña **Nuevo Presupuesto** → crear y **Emitir presupuesto** (PDF al cliente).
2. Pestaña **Listado presupuestos** → **Aceptar** cuando el cliente confirme.
3. **Convertir en factura** → se abre **Nueva Factura** con todo cargado → **Emitir**.

### Otras acciones útiles

- **Duplicar** o **Rectificar** desde el Listado (abren *Nueva Factura* automáticamente).
- **Archivo → Crear copia de seguridad** de vez en cuando.

## Estados de factura

| Estado    | Color en listado | Descripción |
|-----------|------------------|-------------|
| Borrador  | Gris claro       | Editable, sin número oficial |
| Emitida   | Naranja claro    | Numerada y bloqueada |
| Cobrada   | Verde claro      | Emitida y marcada como cobrada |

## Variables de entorno (opcionales)

| Variable            | Descripción |
|---------------------|-------------|
| `LEFA_PROJECT_DIR`  | Raíz del proyecto (p. ej. instalaciones empaquetadas) |
| `LEFA_VENV`         | Ruta explícita al entorno virtual |

## Respaldos (manual)

También puede copiar la carpeta `~/.lefa` a un pendrive:

```bash
cp -a ~/.lefa /ruta/a/tu/pendrive/lefa-backup-$(date +%Y%m%d)
```

En Windows, copie la carpeta `%USERPROFILE%\.lefa` a un USB o disco externo.

| Contenido              | Archivo / carpeta              |
|------------------------|--------------------------------|
| Base de datos          | `lefa.db`                      |
| Facturas en PDF        | `facturas_pdf/`                |
| Presupuestos en PDF    | `presupuestos_pdf/`            |
| Facturae (XML)         | `facturas_xml/`                |
| VeriFactu (registros)  | `verifactu/registros/`         |
| Configuración SMTP     | `smtp_config.json`             |
| Preferencias           | `preferencias.json`            |
| Contraseña de correo   | Llavero del sistema (keyring)  |

> **Recomendación:** haga copias periódicas (semanal o mensual). Si restaura en otro equipo, copie la carpeta de vuelta a `~/.lefa` y reconfigure la contraseña SMTP si el llavero no se transfiere.

## Cierre de la aplicación

| Acción | Comportamiento |
|--------|----------------|
| **X** en la ventana (con bandeja) | Oculta la ventana; LEFA sigue en la bandeja. Notificación: *"LEFA sigue ejecutándose en la bandeja del sistema."* |
| **Archivo → Salir** | Cierra la aplicación por completo. |
| **Salir** en la bandeja | Cierra la aplicación por completo. |
| **X** sin bandeja disponible | Cierra la aplicación (comportamiento estándar). |
| **Ctrl+C** en la terminal | Cierra la aplicación de forma segura. |

## Repositorio

[https://github.com/entreunosyceros/lefa](https://github.com/entreunosyceros/lefa)

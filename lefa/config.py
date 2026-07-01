"""
Configuración centralizada de rutas y constantes de la aplicación.

Toda la persistencia es local: base de datos SQLite y PDFs en carpetas
dentro del directorio de datos del usuario.
"""

from pathlib import Path

# Directorio raíz de datos de la aplicación (~/.lefa)
APP_DATA_DIR = Path.home() / ".lefa"
DATABASE_PATH = APP_DATA_DIR / "lefa.db"
PDF_OUTPUT_DIR = APP_DATA_DIR / "facturas_pdf"
PRESUPUESTOS_PDF_DIR = APP_DATA_DIR / "presupuestos_pdf"
SMTP_CONFIG_PATH = APP_DATA_DIR / "smtp_config.json"
PREFERENCIAS_PATH = APP_DATA_DIR / "preferencias.json"
VERIFACTU_REGISTROS_DIR = APP_DATA_DIR / "verifactu" / "registros"
FACTURAE_OUTPUT_DIR = APP_DATA_DIR / "facturas_xml"

# VeriFactu — URL base AEAT (producción; usar prewww2.aeat.es en pruebas)
VERIFACTU_URL_BASE = "https://www2.agenciatributaria.gob.es"
VERIFACTU_MODO_VERIFACTU = False  # No-Verifactu hasta activar envío a AEAT

# Tipos de IVA e IRPF habituales en España
IVA_OPCIONES = (21.0, 10.0, 4.0, 0.0)
IRPF_OPCIONES = (15.0, 7.0, 0.0)

# Series por defecto
SERIE_PRESUPUESTO = "PRES"
SERIES_POR_DEFECTO = ("FACT", "PRES", "PROFORMA", "RECT")

# Identificador para almacenar la contraseña SMTP en el llavero del sistema
KEYRING_SERVICE = "lefa-smtp"
KEYRING_USER = "password"

# Valores por defecto de impuestos para autónomos en España
DEFAULT_IVA_PORCENTAJE = 21.0
DEFAULT_IRPF_PORCENTAJE = 15.0

# Prefijo de la serie de facturación (correlativo anual)
SERIE_FACTURA_PREFIX = "FACT"

# Datos del emisor (autónomo) — editables en futuras versiones
EMISOR_RAZON_SOCIAL = "Mi Empresa Autónoma S.L."
EMISOR_CIF = "B12345678"
EMISOR_DIRECCION = "Calle Ejemplo 1, 28001 Madrid"
EMISOR_EMAIL = "facturacion@miempresa.es"


def ensure_directories() -> None:
    """Crea las carpetas necesarias si no existen."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRESUPUESTOS_PDF_DIR.mkdir(parents=True, exist_ok=True)
    VERIFACTU_REGISTROS_DIR.mkdir(parents=True, exist_ok=True)
    FACTURAE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

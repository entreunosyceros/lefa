"""
Código QR tributario para facturas (VeriFactu / No-VeriFactu).

Especificaciones AEAT (Orden HAC/1177/2024): tamaño impreso 30–40 mm,
leyenda obligatoria junto al QR y URL de cotejo según modalidad.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import quote

from lefa.config import VERIFACTU_MODO_VERIFACTU, VERIFACTU_URL_BASE

# PNG intermedio: resolución suficiente para impresión (≈85–113 px a 72 dpi)
QR_PX = 100

# Tamaño físico en el PDF (FPDF usa milímetros, no píxeles)
QR_MM = 35.0

# Rótulos legales obligatorios junto al código QR (RD facturación / SIF)
TEXTO_LEGAL_VERIFACTU = "VERI*FACTU"
TEXTO_LEGAL_NO_VERIFACTU = "SISTEMA INFORMÁTICO NO VERIFICADO"


def texto_legal_qr(modo_verifactu: bool | None = None) -> str:
    """Leyenda que debe figurar al lado o debajo del QR en la factura impresa."""
    if modo_verifactu is None:
        modo_verifactu = VERIFACTU_MODO_VERIFACTU
    return TEXTO_LEGAL_VERIFACTU if modo_verifactu else TEXTO_LEGAL_NO_VERIFACTU


def hash_para_url(hash_registro: str | None) -> str:
    """
    Normaliza el hash SHA-256 para el parámetro ``hash`` de la URL AEAT.

    Según las especificaciones técnicas del código QR (v0.5.x), en modalidad
    VERI*FACTU se incluye la huella completa de 64 caracteres hexadecimales
    en minúsculas. Si la AEAT publicara otro tramo, centralizar el ajuste aquí.
    """
    if not hash_registro:
        return ""
    return hash_registro.strip().lower()


def url_verificacion(
    nif_emisor: str,
    numero_factura: str,
    fecha_emision: date,
    importe_total: float,
    hash_registro: str | None = None,
    modo_verifactu: bool | None = None,
) -> str:
    """
    Construye la URL de cotejo en la sede electrónica de la AEAT.

    Parámetros: nif, numserie, fecha (DD-MM-AAAA), importe (punto decimal).
    En modalidad VERI*FACTU se añade el hash del registro (64 hex en minúsculas).
    """
    if modo_verifactu is None:
        modo_verifactu = VERIFACTU_MODO_VERIFACTU

    endpoint = "ValidarQR" if modo_verifactu else "ValidarQRNoVerifactu"
    base = VERIFACTU_URL_BASE.rstrip("/")
    fecha = fecha_emision.strftime("%d-%m-%Y")
    importe = f"{importe_total:.2f}"

    params = [
        f"nif={quote(nif_emisor.strip().upper())}",
        f"numserie={quote(numero_factura.strip())}",
        f"fecha={fecha}",
        f"importe={importe}",
    ]
    hash_url = hash_para_url(hash_registro)
    if modo_verifactu and hash_url:
        params.append(f"hash={quote(hash_url)}")

    return f"{base}/wlpl/TIKE-CONT/{endpoint}?{'&'.join(params)}"


def generar_qr_png(url: str, ruta_destino: Path, size_px: int = QR_PX) -> Path:
    """Genera una imagen PNG del código QR con la URL de verificación."""
    import qrcode

    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(version=None, box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size_px, size_px))
    img.save(str(ruta_destino))
    return ruta_destino

"""
Código QR tributario para facturas (VeriFactu / No-VeriFactu).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import quote

from lefa.config import VERIFACTU_MODO_VERIFACTU, VERIFACTU_URL_BASE

# Tamaño recomendado AEAT: 30–40 mm ≈ 85–113 px a 72 dpi; usamos 100 px
QR_PX = 100


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
    En modalidad VERI*FACTU se añade el hash del registro.
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
    if modo_verifactu and hash_registro:
        params.append(f"hash={hash_registro}")

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

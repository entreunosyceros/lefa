"""
VeriFactu — registro, hash encadenado, QR y exportación.

Arquitectura preparada para cumplimiento SIF en España.
La implementación actual cubre QR y registro local; el envío a AEAT
se añadirá cuando proceda sin cambiar la interfaz pública.
"""

from lefa.verifactu.export import VerifactuExport
from lefa.verifactu.hash import calcular_hash_registro
from lefa.verifactu.qr import (
    QR_MM,
    TEXTO_LEGAL_NO_VERIFACTU,
    TEXTO_LEGAL_VERIFACTU,
    generar_qr_png,
    hash_para_url,
    texto_legal_qr,
    url_verificacion,
)
from lefa.verifactu.registro import RegistroVerifactu, RegistroVerifactuService

__all__ = [
    "QR_MM",
    "RegistroVerifactu",
    "RegistroVerifactuService",
    "TEXTO_LEGAL_NO_VERIFACTU",
    "TEXTO_LEGAL_VERIFACTU",
    "VerifactuExport",
    "calcular_hash_registro",
    "generar_qr_png",
    "hash_para_url",
    "texto_legal_qr",
    "url_verificacion",
]

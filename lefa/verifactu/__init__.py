"""
VeriFactu — registro, hash encadenado, QR y exportación.

Arquitectura preparada para cumplimiento SIF en España.
La implementación actual cubre QR y registro local; el envío a AEAT
se añadirá cuando proceda sin cambiar la interfaz pública.
"""

from lefa.verifactu.export import VerifactuExport
from lefa.verifactu.hash import calcular_hash_registro
from lefa.verifactu.qr import generar_qr_png, url_verificacion
from lefa.verifactu.registro import RegistroVerifactu, RegistroVerifactuService

__all__ = [
    "RegistroVerifactu",
    "RegistroVerifactuService",
    "VerifactuExport",
    "calcular_hash_registro",
    "generar_qr_png",
    "url_verificacion",
]

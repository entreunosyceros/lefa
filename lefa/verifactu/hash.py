"""
Hash SHA-256 encadenado para registros de facturación (VeriFactu).

Cada registro incorpora el hash del anterior para garantizar inmutabilidad.
La cadena es **única para todo el SIF**: FACT, RECT y cualquier otra serie
comparten el mismo hilo; una rectificativa enlaza con la última factura emitida
cronológicamente, no con la rectificativa anterior.
"""

from __future__ import annotations

import hashlib
from datetime import date


def calcular_hash_registro(
    nif_emisor: str,
    numero_factura: str,
    fecha_emision: date,
    importe_total: float,
    hash_anterior: str = "",
) -> str:
    """
    Calcula el hash del registro de facturación.

    El formato del payload sigue un esquema estable para poder alinearse
    con las especificaciones AEAT cuando se active el envío oficial.
    """
    fecha_str = fecha_emision.strftime("%d-%m-%Y")
    importe_str = f"{importe_total:.2f}"
    payload = "|".join(
        [
            nif_emisor.strip().upper(),
            numero_factura.strip(),
            fecha_str,
            importe_str,
            hash_anterior.strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

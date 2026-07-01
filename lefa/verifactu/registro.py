"""
Registro de facturación VeriFactu — generación y persistencia local.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select

from lefa.config import VERIFACTU_REGISTROS_DIR, ensure_directories
from lefa.models import Factura
from lefa.services.preferencias_service import PreferenciasService
from lefa.verifactu.hash import calcular_hash_registro


@dataclass
class RegistroVerifactu:
    """Registro inmutable de una factura emitida."""

    factura_id: int
    numero_factura: str
    serie: str
    nif_emisor: str
    fecha_emision: str
    importe_total: float
    hash_registro: str
    hash_anterior: str
    timestamp: str
    tipo: str = "alta"
    factura_rectificada_id: int | None = None


class RegistroVerifactuService:
    """Crea y almacena registros encadenados en disco y en la BD."""

    @staticmethod
    def _ultimo_hash_global(session, excluir_factura_id: int | None = None) -> str:
        """
        Hash del último registro emitido en el sistema (todas las series).

        Orden cronológico por fecha de emisión y, a igualdad, por ID.
        Las rectificativas (RECT) enlazan aquí, no en una cadena aparte.
        """
        consulta = (
            select(Factura)
            .where(Factura.verifactu_hash.isnot(None))
            .order_by(Factura.fecha_emision.desc(), Factura.id.desc())
        )
        if excluir_factura_id is not None:
            consulta = consulta.where(Factura.id != excluir_factura_id)

        factura = session.scalar(consulta.limit(1))
        return factura.verifactu_hash if factura and factura.verifactu_hash else ""

    @staticmethod
    def crear_registro_emision(session, factura: Factura) -> RegistroVerifactu:
        """
        Genera el registro y asigna hashes a la factura (dentro de la transacción).

        Debe llamarse antes del commit de la emisión.
        """
        prefs = PreferenciasService.cargar()
        hash_anterior = RegistroVerifactuService._ultimo_hash_global(
            session, excluir_factura_id=factura.id
        )

        importe = round(factura.calcular_total(), 2)
        numero = factura.numero_factura or ""
        fecha = factura.fecha_emision or date.today()
        tipo = "rectificativa" if factura.factura_rectificada_id else "alta"

        hash_registro = calcular_hash_registro(
            prefs.emisor_cif,
            numero,
            fecha,
            importe,
            hash_anterior,
        )

        registro = RegistroVerifactu(
            factura_id=factura.id,
            numero_factura=numero,
            serie=factura.serie,
            nif_emisor=prefs.emisor_cif,
            fecha_emision=fecha.isoformat(),
            importe_total=importe,
            hash_registro=hash_registro,
            hash_anterior=hash_anterior,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            tipo=tipo,
            factura_rectificada_id=factura.factura_rectificada_id,
        )

        factura.verifactu_hash = hash_registro
        factura.verifactu_hash_anterior = hash_anterior or None

        RegistroVerifactuService._guardar_json(registro)
        return registro

    @staticmethod
    def _guardar_json(registro: RegistroVerifactu) -> Path:
        ensure_directories()
        VERIFACTU_REGISTROS_DIR.mkdir(parents=True, exist_ok=True)
        nombre = f"{registro.factura_id}_{registro.numero_factura.replace('/', '-')}.json"
        ruta = VERIFACTU_REGISTROS_DIR / nombre
        ruta.write_text(
            json.dumps(asdict(registro), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return ruta

    @staticmethod
    def ruta_registro(factura_id: int, numero_factura: str) -> Path:
        nombre = f"{factura_id}_{numero_factura.replace('/', '-')}.json"
        return VERIFACTU_REGISTROS_DIR / nombre

"""
Registro de facturación VeriFactu — generación y persistencia local.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from lefa.config import VERIFACTU_REGISTROS_DIR, ensure_directories
from lefa.database import begin_immediate
from lefa.models import EstadoFactura, Factura
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
    def _ultima_factura_emitida(
        session: Session,
        excluir_factura_id: int | None = None,
    ) -> Factura | None:
        """
        Última factura emitida del sistema (todas las series).

        Orden cronológico por fecha de emisión y, a igualdad, por ID.
        Debe ejecutarse dentro de la misma transacción que asigna el nuevo hash.
        """
        consulta = (
            select(Factura)
            .where(Factura.estado != EstadoFactura.BORRADOR)
            .where(Factura.verifactu_hash.isnot(None))
            .order_by(Factura.fecha_emision.desc(), Factura.id.desc())
        )
        if excluir_factura_id is not None:
            consulta = consulta.where(Factura.id != excluir_factura_id)

        return session.scalar(consulta.limit(1))

    @staticmethod
    def _ultimo_hash_global(
        session: Session,
        excluir_factura_id: int | None = None,
    ) -> str:
        """Hash del último registro emitido (cadena única FACT/RECT/…)."""
        factura = RegistroVerifactuService._ultima_factura_emitida(
            session, excluir_factura_id=excluir_factura_id
        )
        return factura.verifactu_hash if factura and factura.verifactu_hash else ""

    @staticmethod
    def crear_registro_emision(
        session: Session,
        factura: Factura,
        *,
        persistir_json: bool = False,
    ) -> RegistroVerifactu:
        """
        Genera el registro y asigna hashes a la factura.

        Debe llamarse dentro de ``session_scope_immediate()`` junto con la
        numeración correlativa, sin commit intermedio:

        1. SELECT última factura emitida → ``hash_anterior``
        2. ``calcular_hash_registro`` para la factura actual
        3. UPDATE de la factura con ``verifactu_hash`` / ``verifactu_hash_anterior``
        4. commit de la transacción (en el servicio de emisión)

        El JSON en disco se escribe tras el commit salvo ``persistir_json=True``.
        """
        # Blindaje transaccional (ver ``lefa.database.begin_immediate``).
        begin_immediate(session)

        ultima = RegistroVerifactuService._ultima_factura_emitida(
            session, excluir_factura_id=factura.id
        )
        hash_anterior = ultima.verifactu_hash if ultima and ultima.verifactu_hash else ""

        prefs = PreferenciasService.cargar()
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

        if persistir_json:
            RegistroVerifactuService.guardar_json(registro)
        return registro

    @staticmethod
    def guardar_json(registro: RegistroVerifactu) -> Path:
        """Persiste el registro en disco (llamar tras commit exitoso de emisión)."""
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

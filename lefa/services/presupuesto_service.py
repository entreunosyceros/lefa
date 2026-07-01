"""
Servicio de presupuestos — oferta, aceptación y conversión a factura.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import and_, extract, select
from sqlalchemy.orm import joinedload

from lefa.config import SERIE_PRESUPUESTO
from lefa.database import session_scope
from lefa.models import EstadoPresupuesto, LineaPresupuesto, Presupuesto
from lefa.services.factura_service import FacturaService, LineaFacturaDTO
from lefa.services.numeracion_service import NumeracionService
from lefa.services.preferencias_service import PreferenciasService


@dataclass
class LineaPresupuestoDTO:
    descripcion: str
    cantidad: float
    precio_unitario: float


class PresupuestoService:
    """CRUD y flujo presupuesto → factura."""

    @staticmethod
    def listar_todos() -> list[Presupuesto]:
        with session_scope() as session:
            return list(
                session.scalars(
                    select(Presupuesto)
                    .options(joinedload(Presupuesto.cliente), joinedload(Presupuesto.lineas))
                    .order_by(Presupuesto.id.desc())
                ).unique()
            )

    @staticmethod
    def obtener_por_id(presupuesto_id: int) -> Presupuesto | None:
        with session_scope() as session:
            return session.scalar(
                select(Presupuesto)
                .options(joinedload(Presupuesto.cliente), joinedload(Presupuesto.lineas))
                .where(Presupuesto.id == presupuesto_id)
            )

    @staticmethod
    def guardar_borrador(
        cliente_id: int,
        lineas: list[LineaPresupuestoDTO],
        porc_iva: float,
        porc_irpf: float,
        presupuesto_id: int | None = None,
        validez_hasta: date | None = None,
    ) -> Presupuesto:
        if not lineas:
            raise ValueError("El presupuesto debe tener al menos una línea.")

        with session_scope() as session:
            if presupuesto_id:
                presupuesto = session.get(Presupuesto, presupuesto_id)
                if presupuesto is None:
                    raise ValueError(f"Presupuesto {presupuesto_id} no encontrado.")
                if presupuesto.estado != EstadoPresupuesto.BORRADOR:
                    raise ValueError("Solo se pueden editar presupuestos en borrador.")
                for linea in list(presupuesto.lineas):
                    session.delete(linea)
            else:
                presupuesto = Presupuesto(
                    numero_presupuesto=None,
                    serie=SERIE_PRESUPUESTO,
                    cliente_id=cliente_id,
                    estado=EstadoPresupuesto.BORRADOR,
                    porc_iva=porc_iva,
                    porc_irpf=porc_irpf,
                )
                session.add(presupuesto)

            presupuesto.cliente_id = cliente_id
            presupuesto.porc_iva = porc_iva
            presupuesto.porc_irpf = porc_irpf
            presupuesto.validez_hasta = validez_hasta

            for dto in lineas:
                presupuesto.lineas.append(
                    LineaPresupuesto(
                        descripcion=dto.descripcion,
                        cantidad=dto.cantidad,
                        precio_unitario=dto.precio_unitario,
                    )
                )

            session.flush()
            session.refresh(presupuesto)
            _ = presupuesto.cliente
            _ = presupuesto.lineas
            session.expunge(presupuesto)
            PreferenciasService.guardar_ultimo_cliente(cliente_id)
            return presupuesto

    @staticmethod
    def emitir_presupuesto(presupuesto_id: int) -> Presupuesto:
        """Asigna número y fecha; genera PDF aparte."""
        with session_scope() as session:
            presupuesto = session.get(Presupuesto, presupuesto_id)
            if presupuesto is None:
                raise ValueError(f"Presupuesto {presupuesto_id} no encontrado.")
            if presupuesto.estado != EstadoPresupuesto.BORRADOR:
                raise ValueError("Solo se pueden emitir presupuestos en borrador.")
            if not presupuesto.lineas:
                raise ValueError("El presupuesto no tiene líneas.")

            prefs = PreferenciasService.cargar()
            anio = date.today().year
            serie = presupuesto.serie.strip() or SERIE_PRESUPUESTO
            secuencia = NumeracionService.siguiente_secuencia_presupuesto(
                session, serie, anio, prefs.formato_numeracion, prefs.digitos_secuencia
            )
            presupuesto.numero_presupuesto = NumeracionService.formatear_numero(
                serie, anio, secuencia, prefs.formato_numeracion, prefs.digitos_secuencia
            )
            presupuesto.fecha_emision = date.today()
            if presupuesto.validez_hasta is None:
                presupuesto.validez_hasta = date.today() + timedelta(days=30)
            presupuesto.estado = EstadoPresupuesto.EMITIDO

            session.flush()
            session.refresh(presupuesto)
            _ = presupuesto.cliente
            _ = presupuesto.lineas
            session.expunge(presupuesto)
            return presupuesto

    @staticmethod
    def aceptar(presupuesto_id: int) -> Presupuesto:
        with session_scope() as session:
            presupuesto = session.get(Presupuesto, presupuesto_id)
            if presupuesto is None:
                raise ValueError(f"Presupuesto {presupuesto_id} no encontrado.")
            if presupuesto.estado != EstadoPresupuesto.EMITIDO:
                raise ValueError("Solo se pueden aceptar presupuestos emitidos.")
            presupuesto.estado = EstadoPresupuesto.ACEPTADO
            session.flush()
            session.refresh(presupuesto)
            _ = presupuesto.cliente
            _ = presupuesto.lineas
            session.expunge(presupuesto)
            return presupuesto

    @staticmethod
    def rechazar(presupuesto_id: int) -> Presupuesto:
        with session_scope() as session:
            presupuesto = session.get(Presupuesto, presupuesto_id)
            if presupuesto is None:
                raise ValueError(f"Presupuesto {presupuesto_id} no encontrado.")
            if presupuesto.estado not in (
                EstadoPresupuesto.EMITIDO,
                EstadoPresupuesto.ACEPTADO,
            ):
                raise ValueError("No se puede rechazar este presupuesto.")
            presupuesto.estado = EstadoPresupuesto.RECHAZADO
            session.flush()
            session.refresh(presupuesto)
            session.expunge(presupuesto)
            return presupuesto

    @staticmethod
    def convertir_a_factura(presupuesto_id: int) -> int:
        """
        Crea un borrador de factura con los mismos datos y marca el presupuesto.

        Acepta automáticamente si aún está solo emitido.
        """
        with session_scope() as session:
            presupuesto = session.scalar(
                select(Presupuesto)
                .options(joinedload(Presupuesto.lineas))
                .where(Presupuesto.id == presupuesto_id)
            )
            if presupuesto is None:
                raise ValueError(f"Presupuesto {presupuesto_id} no encontrado.")
            if presupuesto.estado == EstadoPresupuesto.CONVERTIDO:
                raise ValueError("Este presupuesto ya se convirtió en factura.")
            if presupuesto.estado == EstadoPresupuesto.RECHAZADO:
                raise ValueError("No se puede facturar un presupuesto rechazado.")
            if presupuesto.estado == EstadoPresupuesto.BORRADOR:
                raise ValueError("Emita el presupuesto antes de convertirlo.")
            if presupuesto.estado == EstadoPresupuesto.EMITIDO:
                presupuesto.estado = EstadoPresupuesto.ACEPTADO

            lineas = [
                LineaFacturaDTO(
                    descripcion=l.descripcion,
                    cantidad=l.cantidad,
                    precio_unitario=l.precio_unitario,
                )
                for l in presupuesto.lineas
            ]
            cliente_id = presupuesto.cliente_id
            porc_iva = presupuesto.porc_iva
            porc_irpf = presupuesto.porc_irpf
            presupuesto_id_val = presupuesto.id

        prefs = PreferenciasService.cargar()
        fecha_venc = None
        if prefs.dias_vencimiento > 0:
            fecha_venc = date.today() + timedelta(days=prefs.dias_vencimiento)

        factura = FacturaService.guardar_borrador(
            cliente_id=cliente_id,
            lineas=lineas,
            porc_iva=porc_iva,
            porc_irpf=porc_irpf,
            serie=PreferenciasService.obtener_serie_prefix(),
            fecha_vencimiento=fecha_venc,
            presupuesto_origen_id=presupuesto_id_val,
        )

        with session_scope() as session:
            presupuesto = session.get(Presupuesto, presupuesto_id_val)
            if presupuesto:
                presupuesto.estado = EstadoPresupuesto.CONVERTIDO
                presupuesto.factura_id = factura.id

        return factura.id

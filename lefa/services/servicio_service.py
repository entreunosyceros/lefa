"""
Servicio del catálogo de servicios.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from lefa.database import session_scope
from lefa.models import Servicio


@dataclass
class ServicioDTO:
    nombre: str
    descripcion: str
    cantidad: float
    precio_unitario: float
    porc_iva: float


class ServicioService:
    """CRUD del catálogo de servicios."""

    @staticmethod
    def listar_todos() -> list[Servicio]:
        with session_scope() as session:
            return list(session.scalars(select(Servicio).order_by(Servicio.nombre)))

    @staticmethod
    def crear(datos: ServicioDTO) -> Servicio:
        ServicioService._validar(datos)
        with session_scope() as session:
            servicio = Servicio(
                nombre=datos.nombre.strip(),
                descripcion=datos.descripcion.strip(),
                cantidad=datos.cantidad,
                precio_unitario=datos.precio_unitario,
                porc_iva=datos.porc_iva,
            )
            session.add(servicio)
            session.flush()
            session.refresh(servicio)
            session.expunge(servicio)
            return servicio

    @staticmethod
    def actualizar(servicio_id: int, datos: ServicioDTO) -> Servicio:
        ServicioService._validar(datos)
        with session_scope() as session:
            servicio = session.get(Servicio, servicio_id)
            if servicio is None:
                raise ValueError(f"Servicio {servicio_id} no encontrado.")
            servicio.nombre = datos.nombre.strip()
            servicio.descripcion = datos.descripcion.strip()
            servicio.cantidad = datos.cantidad
            servicio.precio_unitario = datos.precio_unitario
            servicio.porc_iva = datos.porc_iva
            session.flush()
            session.refresh(servicio)
            session.expunge(servicio)
            return servicio

    @staticmethod
    def eliminar(servicio_id: int) -> None:
        with session_scope() as session:
            servicio = session.get(Servicio, servicio_id)
            if servicio is None:
                raise ValueError(f"Servicio {servicio_id} no encontrado.")
            session.delete(servicio)

    @staticmethod
    def _validar(datos: ServicioDTO) -> None:
        if not datos.nombre.strip():
            raise ValueError("El nombre del servicio es obligatorio.")
        if not datos.descripcion.strip():
            raise ValueError("La descripción es obligatoria.")

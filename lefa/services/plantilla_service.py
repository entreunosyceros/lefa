"""
Servicio de plantillas de líneas de factura.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from lefa.database import session_scope
from lefa.models import PlantillaLinea


@dataclass
class PlantillaLineaDTO:
    nombre: str
    descripcion: str
    cantidad: float
    precio_unitario: float


class PlantillaService:
    """CRUD de plantillas de líneas."""

    @staticmethod
    def listar_todas() -> list[PlantillaLinea]:
        with session_scope() as session:
            return list(
                session.scalars(select(PlantillaLinea).order_by(PlantillaLinea.nombre))
            )

    @staticmethod
    def crear(datos: PlantillaLineaDTO) -> PlantillaLinea:
        PlantillaService._validar(datos)
        with session_scope() as session:
            plantilla = PlantillaLinea(
                nombre=datos.nombre.strip(),
                descripcion=datos.descripcion.strip(),
                cantidad=datos.cantidad,
                precio_unitario=datos.precio_unitario,
            )
            session.add(plantilla)
            session.flush()
            session.refresh(plantilla)
            session.expunge(plantilla)
            return plantilla

    @staticmethod
    def actualizar(plantilla_id: int, datos: PlantillaLineaDTO) -> PlantillaLinea:
        PlantillaService._validar(datos)
        with session_scope() as session:
            plantilla = session.get(PlantillaLinea, plantilla_id)
            if plantilla is None:
                raise ValueError(f"Plantilla {plantilla_id} no encontrada.")
            plantilla.nombre = datos.nombre.strip()
            plantilla.descripcion = datos.descripcion.strip()
            plantilla.cantidad = datos.cantidad
            plantilla.precio_unitario = datos.precio_unitario
            session.flush()
            session.refresh(plantilla)
            session.expunge(plantilla)
            return plantilla

    @staticmethod
    def eliminar(plantilla_id: int) -> None:
        with session_scope() as session:
            plantilla = session.get(PlantillaLinea, plantilla_id)
            if plantilla is None:
                raise ValueError(f"Plantilla {plantilla_id} no encontrada.")
            session.delete(plantilla)

    @staticmethod
    def _validar(datos: PlantillaLineaDTO) -> None:
        if not datos.nombre.strip():
            raise ValueError("El nombre de la plantilla es obligatorio.")
        if not datos.descripcion.strip():
            raise ValueError("La descripción es obligatoria.")

"""
Modelo PlantillaLinea — conceptos reutilizables en facturas recurrentes.
"""

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from lefa.models.base import Base


class PlantillaLinea(Base):
    """Plantilla de línea de factura (descripción, cantidad y precio)."""

    __tablename__ = "plantillas_linea"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return f"<PlantillaLinea(id={self.id}, nombre='{self.nombre}')>"

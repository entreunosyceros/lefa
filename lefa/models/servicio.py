"""
Modelo Servicio — catálogo de conceptos con precio e IVA.
"""

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from lefa.models.base import Base


class Servicio(Base):
    """Servicio del catálogo para rellenar líneas de factura con un clic."""

    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    porc_iva: Mapped[float] = mapped_column(Float, nullable=False, default=21.0)

    def __repr__(self) -> str:
        return f"<Servicio(id={self.id}, nombre='{self.nombre}')>"

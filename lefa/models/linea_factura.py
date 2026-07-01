"""
Modelo LineaFactura — concepto individual dentro de una factura.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.factura import Factura


class LineaFactura(Base):
    """Línea de detalle con descripción, cantidad y precio."""

    __tablename__ = "lineas_factura"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    factura: Mapped[Factura] = relationship("Factura", back_populates="lineas")

    @property
    def subtotal(self) -> float:
        return round(self.cantidad * self.precio_unitario, 2)

    def __repr__(self) -> str:
        return f"<LineaFactura(id={self.id}, desc='{self.descripcion[:30]}...')>"

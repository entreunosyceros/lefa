"""
Línea de detalle de un presupuesto.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.presupuesto import Presupuesto


class LineaPresupuesto(Base):
    """Concepto dentro de un presupuesto."""

    __tablename__ = "lineas_presupuesto"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    presupuesto_id: Mapped[int] = mapped_column(ForeignKey("presupuestos.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    presupuesto: Mapped[Presupuesto] = relationship("Presupuesto", back_populates="lineas")

    @property
    def subtotal(self) -> float:
        return round(self.cantidad * self.precio_unitario, 2)

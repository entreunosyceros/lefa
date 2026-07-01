"""
Modelo PlantillaFactura — factura completa reutilizable (mensual, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.cliente import Cliente


class PlantillaFactura(Base):
    """Plantilla con varias líneas, cliente opcional e impuestos."""

    __tablename__ = "plantillas_factura"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    serie: Mapped[str] = mapped_column(String(20), nullable=False, default="FACT")
    porc_iva: Mapped[float] = mapped_column(Float, nullable=False, default=21.0)
    porc_irpf: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)

    cliente: Mapped[Cliente | None] = relationship("Cliente")
    lineas: Mapped[list[PlantillaFacturaLinea]] = relationship(
        "PlantillaFacturaLinea",
        back_populates="plantilla",
        cascade="all, delete-orphan",
        order_by="PlantillaFacturaLinea.id",
    )

    def __repr__(self) -> str:
        return f"<PlantillaFactura(id={self.id}, nombre='{self.nombre}')>"


class PlantillaFacturaLinea(Base):
    """Línea incluida en una plantilla de factura completa."""

    __tablename__ = "plantillas_factura_lineas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plantilla_id: Mapped[int] = mapped_column(
        ForeignKey("plantillas_factura.id"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    plantilla: Mapped[PlantillaFactura] = relationship(
        "PlantillaFactura", back_populates="lineas"
    )

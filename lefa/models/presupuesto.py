"""
Modelo Presupuesto — oferta previa convertible en factura.
"""

from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.cliente import Cliente
    from lefa.models.linea_presupuesto import LineaPresupuesto


class EstadoPresupuesto(str, enum.Enum):
    """Ciclo de vida del presupuesto."""

    BORRADOR = "Borrador"
    EMITIDO = "Emitido"
    ACEPTADO = "Aceptado"
    CONVERTIDO = "Convertido"
    RECHAZADO = "Rechazado"


class Presupuesto(Base):
    """Presupuesto comercial sin validez fiscal hasta convertirse en factura."""

    __tablename__ = "presupuestos"
    __table_args__ = (UniqueConstraint("numero_presupuesto", name="uq_numero_presupuesto"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_presupuesto: Mapped[str | None] = mapped_column(String(30), nullable=True)
    serie: Mapped[str] = mapped_column(String(20), nullable=False, default="PRES")
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    fecha_emision: Mapped[date | None] = mapped_column(Date, nullable=True)
    validez_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoPresupuesto] = mapped_column(
        Enum(EstadoPresupuesto), nullable=False, default=EstadoPresupuesto.BORRADOR
    )
    porc_iva: Mapped[float] = mapped_column(Float, nullable=False, default=21.0)
    porc_irpf: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)
    factura_id: Mapped[int | None] = mapped_column(ForeignKey("facturas.id"), nullable=True)

    cliente: Mapped[Cliente] = relationship("Cliente", back_populates="presupuestos")
    lineas: Mapped[list[LineaPresupuesto]] = relationship(
        "LineaPresupuesto",
        back_populates="presupuesto",
        cascade="all, delete-orphan",
        order_by="LineaPresupuesto.id",
    )

    def calcular_subtotal(self) -> float:
        return sum(linea.subtotal for linea in self.lineas)

    def calcular_iva(self) -> float:
        return self.calcular_subtotal() * (self.porc_iva / 100.0)

    def calcular_irpf(self) -> float:
        return self.calcular_subtotal() * (self.porc_irpf / 100.0)

    def calcular_total(self) -> float:
        subtotal = self.calcular_subtotal()
        return subtotal + self.calcular_iva() - self.calcular_irpf()

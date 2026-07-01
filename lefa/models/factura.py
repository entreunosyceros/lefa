"""
Modelo Factura — documento de facturación con estados de ciclo de vida.
"""

from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.cliente import Cliente
    from lefa.models.linea_factura import LineaFactura


class EstadoFactura(str, enum.Enum):
    """Estados posibles de una factura en el flujo operativo."""

    BORRADOR = "Borrador"
    EMITIDA = "Emitida"
    COBRADA = "Cobrada"


class Factura(Base):
    """
    Factura emitida o en borrador.

    numero_factura es NULL mientras la factura permanece en borrador,
    permitiendo ediciones sin comprometer la numeración oficial.
    """

    __tablename__ = "facturas"
    __table_args__ = (UniqueConstraint("numero_factura", name="uq_numero_factura"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_factura: Mapped[str | None] = mapped_column(String(30), nullable=True)
    serie: Mapped[str] = mapped_column(String(20), nullable=False, default="FACT")
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    fecha_emision: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoFactura] = mapped_column(
        Enum(EstadoFactura), nullable=False, default=EstadoFactura.BORRADOR
    )
    porc_iva: Mapped[float] = mapped_column(Float, nullable=False, default=21.0)
    porc_irpf: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)

    # Historial de envío por correo
    enviada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_envio: Mapped[date | None] = mapped_column(Date, nullable=True)
    destinatario: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # VeriFactu — hash encadenado (inmutable tras emisión)
    verifactu_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verifactu_hash_anterior: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Rectificativa: referencia a la factura que corrige
    factura_rectificada_id: Mapped[int | None] = mapped_column(
        ForeignKey("facturas.id"), nullable=True
    )
    # Presupuesto del que proviene (si se convirtió)
    presupuesto_origen_id: Mapped[int | None] = mapped_column(
        ForeignKey("presupuestos.id"), nullable=True
    )

    cliente: Mapped[Cliente] = relationship("Cliente", back_populates="facturas")
    factura_rectificada: Mapped[Factura | None] = relationship(
        "Factura",
        remote_side="Factura.id",
        foreign_keys=[factura_rectificada_id],
    )
    lineas: Mapped[list[LineaFactura]] = relationship(
        "LineaFactura",
        back_populates="factura",
        cascade="all, delete-orphan",
        order_by="LineaFactura.id",
    )

    def __repr__(self) -> str:
        return (
            f"<Factura(id={self.id}, numero='{self.numero_factura}', "
            f"estado={self.estado.value})>"
        )

    @property
    def es_editable(self) -> bool:
        """Solo los borradores pueden modificarse."""
        return self.estado == EstadoFactura.BORRADOR

    def calcular_subtotal(self) -> float:
        """Suma de todas las líneas (cantidad × precio unitario)."""
        return sum(linea.subtotal for linea in self.lineas)

    def calcular_iva(self) -> float:
        return self.calcular_subtotal() * (self.porc_iva / 100.0)

    def calcular_irpf(self) -> float:
        return self.calcular_subtotal() * (self.porc_irpf / 100.0)

    def calcular_total(self) -> float:
        subtotal = self.calcular_subtotal()
        return subtotal + self.calcular_iva() - self.calcular_irpf()

    @property
    def es_rectificativa(self) -> bool:
        return self.factura_rectificada_id is not None

    def texto_estado_envio(self) -> str:
        """Texto legible del estado de envío por correo."""
        if self.estado == EstadoFactura.BORRADOR:
            return "—"
        if self.enviada:
            fecha = (
                self.fecha_envio.strftime("%d/%m/%Y") if self.fecha_envio else "?"
            )
            return f"✓ Enviada ({fecha})"
        return "Pendiente de enviar"

    def texto_estado_vencimiento(self) -> str:
        """Estado de cobro según fecha de vencimiento (sin automatismos)."""
        if self.estado == EstadoFactura.BORRADOR:
            return "—"
        if self.estado == EstadoFactura.COBRADA:
            return "Cobrada"
        if self.fecha_vencimiento is None:
            return "Pendiente"
        hoy = date.today()
        if self.fecha_vencimiento < hoy:
            return "Vencida"
        dias = (self.fecha_vencimiento - hoy).days
        if dias == 0:
            return "Vence hoy"
        if dias <= 5:
            return f"Vence en {dias} días"
        return "Pendiente"

"""
Modelo Cliente — destinatario de las facturas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lefa.models.base import Base

if TYPE_CHECKING:
    from lefa.models.factura import Factura
    from lefa.models.presupuesto import Presupuesto


class Cliente(Base):
    """Representa un cliente del autónomo."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    cif_nif: Mapped[str] = mapped_column(String(20), nullable=False)
    direccion: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    telefono: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    # Facturae / FACe (administración pública)
    iban: Mapped[str] = mapped_column(String(34), nullable=False, default="")
    forma_pago: Mapped[str] = mapped_column(
        String(2), nullable=False, default="04"
    )  # 04 = transferencia bancaria
    dir3_oficina: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    dir3_organo: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    dir3_unidad: Mapped[str] = mapped_column(String(20), nullable=False, default="")

    facturas: Mapped[list[Factura]] = relationship(
        "Factura", back_populates="cliente", cascade="all, delete-orphan"
    )
    presupuestos: Mapped[list[Presupuesto]] = relationship(
        "Presupuesto", back_populates="cliente", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, razon_social='{self.razon_social}')>"

"""
Plantillas de factura completa — varias líneas listas para emitir.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from lefa.database import session_scope
from lefa.models import PlantillaFactura, PlantillaFacturaLinea
from lefa.services.factura_service import FacturaService, LineaFacturaDTO


@dataclass
class PlantillaFacturaLineaDTO:
    descripcion: str
    cantidad: float
    precio_unitario: float


@dataclass
class PlantillaFacturaDTO:
    nombre: str
    serie: str
    porc_iva: float
    porc_irpf: float
    cliente_id: int | None
    lineas: list[PlantillaFacturaLineaDTO]


class PlantillaFacturaService:
    """CRUD y creación de borradores desde plantillas completas."""

    @staticmethod
    def listar_todas() -> list[PlantillaFactura]:
        with session_scope() as session:
            return list(
                session.scalars(
                    select(PlantillaFactura)
                    .options(
                        joinedload(PlantillaFactura.lineas),
                        joinedload(PlantillaFactura.cliente),
                    )
                    .order_by(PlantillaFactura.nombre)
                ).unique()
            )

    @staticmethod
    def crear(datos: PlantillaFacturaDTO) -> PlantillaFactura:
        PlantillaFacturaService._validar(datos)
        with session_scope() as session:
            plantilla = PlantillaFactura(
                nombre=datos.nombre.strip(),
                cliente_id=datos.cliente_id,
                serie=datos.serie.strip() or "FACT",
                porc_iva=datos.porc_iva,
                porc_irpf=datos.porc_irpf,
            )
            for linea in datos.lineas:
                plantilla.lineas.append(
                    PlantillaFacturaLinea(
                        descripcion=linea.descripcion.strip(),
                        cantidad=linea.cantidad,
                        precio_unitario=linea.precio_unitario,
                    )
                )
            session.add(plantilla)
            session.flush()
            session.refresh(plantilla)
            _ = plantilla.lineas
            session.expunge(plantilla)
            return plantilla

    @staticmethod
    def eliminar(plantilla_id: int) -> None:
        with session_scope() as session:
            plantilla = session.get(PlantillaFactura, plantilla_id)
            if plantilla is None:
                raise ValueError(f"Plantilla {plantilla_id} no encontrada.")
            session.delete(plantilla)

    @staticmethod
    def crear_borrador_desde_plantilla(plantilla_id: int) -> int:
        """Crea un borrador y devuelve su ID."""
        with session_scope() as session:
            plantilla = session.scalar(
                select(PlantillaFactura)
                .options(joinedload(PlantillaFactura.lineas))
                .where(PlantillaFactura.id == plantilla_id)
            )
            if plantilla is None:
                raise ValueError(f"Plantilla {plantilla_id} no encontrada.")
            if not plantilla.lineas:
                raise ValueError("La plantilla no tiene líneas.")
            if plantilla.cliente_id is None:
                raise ValueError("La plantilla debe tener un cliente asignado.")

            lineas = [
                LineaFacturaDTO(
                    descripcion=linea.descripcion,
                    cantidad=linea.cantidad,
                    precio_unitario=linea.precio_unitario,
                )
                for linea in plantilla.lineas
            ]
            cliente_id = plantilla.cliente_id
            porc_iva = plantilla.porc_iva
            porc_irpf = plantilla.porc_irpf
            serie = plantilla.serie

        factura = FacturaService.guardar_borrador(
            cliente_id=cliente_id,
            lineas=lineas,
            porc_iva=porc_iva,
            porc_irpf=porc_irpf,
            serie=serie,
        )
        return factura.id

    @staticmethod
    def _validar(datos: PlantillaFacturaDTO) -> None:
        if not datos.nombre.strip():
            raise ValueError("El nombre de la plantilla es obligatorio.")
        if not datos.lineas:
            raise ValueError("Añada al menos una línea a la plantilla.")

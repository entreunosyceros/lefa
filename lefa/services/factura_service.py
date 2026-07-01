"""
Servicio de facturación — núcleo de la lógica de negocio.

Gestiona borradores, emisión con numeración correlativa y consultas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from lefa.database import session_scope
from lefa.models import EstadoFactura, Factura, LineaFactura
from lefa.services.numeracion_service import NumeracionService
from lefa.services.preferencias_service import PreferenciasService
from lefa.verifactu.registro import RegistroVerifactuService


@dataclass
class LineaFacturaDTO:
    """Objeto de transferencia para líneas desde la UI."""

    descripcion: str
    cantidad: float
    precio_unitario: float


@dataclass
class TotalesFactura:
    """Resultado del cálculo de importes."""

    subtotal: float
    iva: float
    irpf: float
    total: float


@dataclass
class ResumenHoy:
    """Tres cifras para la pantalla de inicio — sin BI, solo lo esencial."""

    facturas_emitidas_hoy: int
    pendientes_cobrar: int
    importe_pendiente: float


class FacturaService:
    """Operaciones transaccionales sobre facturas."""

    @staticmethod
    def calcular_totales(
        lineas: list[LineaFacturaDTO], porc_iva: float, porc_irpf: float
    ) -> TotalesFactura:
        """Cálculo puro en memoria — sin acceso a BD (respuesta instantánea en UI)."""
        subtotal = round(
            sum(l.cantidad * l.precio_unitario for l in lineas),
            2,
        )
        iva = round(subtotal * (porc_iva / 100.0), 2)
        irpf = round(subtotal * (porc_irpf / 100.0), 2)
        total = round(subtotal + iva - irpf, 2)
        return TotalesFactura(subtotal=subtotal, iva=iva, irpf=irpf, total=total)

    @staticmethod
    def listar_todas() -> list[Factura]:
        with session_scope() as session:
            facturas = session.scalars(
                select(Factura)
                .options(joinedload(Factura.cliente), joinedload(Factura.lineas))
                .order_by(Factura.id.desc())
            ).unique().all()
            return list(facturas)

    @staticmethod
    def resumen_hoy() -> ResumenHoy:
        """Facturas de hoy, pendientes de cobro e importe por cobrar."""
        hoy = date.today()
        with session_scope() as session:
            emitidas_hoy = session.scalar(
                select(func.count(Factura.id))
                .where(Factura.estado != EstadoFactura.BORRADOR)
                .where(Factura.fecha_emision == hoy)
            )
            pendientes = session.scalars(
                select(Factura)
                .options(joinedload(Factura.lineas))
                .where(Factura.estado == EstadoFactura.EMITIDA)
            ).unique().all()

        importe = round(sum(f.calcular_total() for f in pendientes), 2)
        return ResumenHoy(
            facturas_emitidas_hoy=int(emitidas_hoy or 0),
            pendientes_cobrar=len(pendientes),
            importe_pendiente=importe,
        )

    @staticmethod
    def listar_por_cliente(cliente_id: int) -> list[Factura]:
        with session_scope() as session:
            facturas = session.scalars(
                select(Factura)
                .options(joinedload(Factura.lineas))
                .where(Factura.cliente_id == cliente_id)
                .where(Factura.estado != EstadoFactura.BORRADOR)
                .order_by(Factura.fecha_emision.desc(), Factura.id.desc())
            ).unique().all()
            return list(facturas)

    @staticmethod
    def total_facturado_cliente(cliente_id: int) -> float:
        """Suma de totales de facturas emitidas y cobradas."""
        facturas = FacturaService.listar_por_cliente(cliente_id)
        return round(sum(f.calcular_total() for f in facturas), 2)

    @staticmethod
    def obtener_por_id(factura_id: int) -> Factura | None:
        with session_scope() as session:
            factura = session.scalar(
                select(Factura)
                .options(
                    joinedload(Factura.cliente),
                    joinedload(Factura.lineas),
                    joinedload(Factura.factura_rectificada),
                )
                .where(Factura.id == factura_id)
            )
            return factura

    @staticmethod
    def guardar_borrador(
        cliente_id: int,
        lineas: list[LineaFacturaDTO],
        porc_iva: float,
        porc_irpf: float,
        factura_id: int | None = None,
        serie: str | None = None,
        fecha_vencimiento: date | None = None,
        factura_rectificada_id: int | None = None,
        presupuesto_origen_id: int | None = None,
    ) -> Factura:
        """
        Crea o actualiza un borrador sin asignar número oficial.

        numero_factura permanece NULL hasta la emisión.
        """
        if not lineas:
            raise ValueError("La factura debe tener al menos una línea.")

        serie = (serie or PreferenciasService.obtener_serie_prefix()).strip() or "FACT"
        if factura_rectificada_id is not None:
            serie = "RECT"

        with session_scope() as session:
            if factura_id:
                factura = session.get(Factura, factura_id)
                if factura is None:
                    raise ValueError(f"Factura {factura_id} no encontrada.")
                if factura.estado != EstadoFactura.BORRADOR:
                    raise ValueError("Solo se pueden editar facturas en borrador.")
                for linea in list(factura.lineas):
                    session.delete(linea)
            else:
                factura = Factura(
                    numero_factura=None,
                    serie=serie,
                    cliente_id=cliente_id,
                    fecha_emision=None,
                    fecha_vencimiento=fecha_vencimiento,
                    estado=EstadoFactura.BORRADOR,
                    porc_iva=porc_iva,
                    porc_irpf=porc_irpf,
                    factura_rectificada_id=factura_rectificada_id,
                    presupuesto_origen_id=presupuesto_origen_id,
                )
                session.add(factura)

            factura.cliente_id = cliente_id
            factura.serie = serie
            factura.porc_iva = porc_iva
            factura.porc_irpf = porc_irpf
            factura.fecha_vencimiento = fecha_vencimiento
            if factura_rectificada_id is not None:
                factura.factura_rectificada_id = factura_rectificada_id
                factura.serie = "RECT"
            if presupuesto_origen_id is not None:
                factura.presupuesto_origen_id = presupuesto_origen_id

            for dto in lineas:
                factura.lineas.append(
                    LineaFactura(
                        descripcion=dto.descripcion,
                        cantidad=dto.cantidad,
                        precio_unitario=dto.precio_unitario,
                    )
                )

            session.flush()
            session.refresh(factura)
            _ = factura.cliente
            _ = factura.lineas
            session.expunge(factura)
            PreferenciasService.guardar_ultimo_cliente(cliente_id)
            return factura

    @staticmethod
    def emitir_factura(factura_id: int) -> Factura:
        """
        Transacción atómica de emisión:
        1. Valida que sea borrador.
        2. Asigna número según formato configurado.
        3. Fija fecha de emisión al día actual.
        4. Cambia estado a Emitida.
        """
        with session_scope() as session:
            factura = session.get(Factura, factura_id)
            if factura is None:
                raise ValueError(f"Factura {factura_id} no encontrada.")
            if factura.estado != EstadoFactura.BORRADOR:
                raise ValueError("Solo se pueden emitir facturas en borrador.")
            if not factura.lineas:
                raise ValueError("No se puede emitir una factura sin líneas.")

            prefs = PreferenciasService.cargar()
            anio = date.today().year
            serie = factura.serie.strip() or PreferenciasService.obtener_serie_prefix()
            secuencia = NumeracionService.siguiente_secuencia(
                session,
                serie,
                anio,
                prefs.formato_numeracion,
                prefs.digitos_secuencia,
            )

            factura.numero_factura = NumeracionService.formatear_numero(
                serie,
                anio,
                secuencia,
                prefs.formato_numeracion,
                prefs.digitos_secuencia,
            )
            factura.fecha_emision = date.today()
            if factura.fecha_vencimiento is None and prefs.dias_vencimiento > 0:
                factura.fecha_vencimiento = factura.fecha_emision + timedelta(
                    days=prefs.dias_vencimiento
                )
            factura.estado = EstadoFactura.EMITIDA
            factura.enviada = False
            factura.fecha_envio = None
            factura.destinatario = None

            RegistroVerifactuService.crear_registro_emision(session, factura)

            session.flush()
            session.refresh(factura)
            _ = factura.cliente
            _ = factura.lineas
            session.expunge(factura)
            PreferenciasService.guardar_ultimo_cliente(factura.cliente_id)
            return factura

    @staticmethod
    def marcar_enviada(factura_id: int, destinatario: str) -> Factura:
        """Registra el envío exitoso de una factura por correo."""
        with session_scope() as session:
            factura = session.get(Factura, factura_id)
            if factura is None:
                raise ValueError(f"Factura {factura_id} no encontrada.")
            factura.enviada = True
            factura.fecha_envio = date.today()
            factura.destinatario = destinatario.strip()
            session.flush()
            session.refresh(factura)
            _ = factura.cliente
            _ = factura.lineas
            session.expunge(factura)
            return factura

    @staticmethod
    def duplicar_factura(factura_id: int) -> Factura:
        """
        Crea un borrador nuevo copiando cliente, líneas e impuestos.

        Sin número ni historial de envío; el usuario solo emite con la fecha actual.
        """
        origen = FacturaService.obtener_por_id(factura_id)
        if origen is None:
            raise ValueError(f"Factura {factura_id} no encontrada.")
        if origen.estado == EstadoFactura.BORRADOR:
            raise ValueError("Duplique una factura ya emitida o cobrada.")

        lineas = [
            LineaFacturaDTO(
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
            )
            for linea in origen.lineas
        ]
        prefs = PreferenciasService.cargar()
        fecha_vencimiento = None
        if prefs.dias_vencimiento > 0:
            fecha_vencimiento = date.today() + timedelta(days=prefs.dias_vencimiento)

        return FacturaService.guardar_borrador(
            cliente_id=origen.cliente_id,
            lineas=lineas,
            porc_iva=origen.porc_iva,
            porc_irpf=origen.porc_irpf,
            serie=origen.serie,
            fecha_vencimiento=fecha_vencimiento,
        )

    @staticmethod
    def rectificar_factura(factura_id: int) -> Factura:
        """
        Crea un borrador rectificativo (serie RECT) vinculado a la factura original.

        Copia líneas; use importes negativos si debe devolver importe al cliente.
        """
        origen = FacturaService.obtener_por_id(factura_id)
        if origen is None:
            raise ValueError(f"Factura {factura_id} no encontrada.")
        if origen.estado not in (EstadoFactura.EMITIDA, EstadoFactura.COBRADA):
            raise ValueError("Solo se pueden rectificar facturas emitidas o cobradas.")
        if origen.es_rectificativa:
            raise ValueError("No se puede rectificar una factura que ya es rectificativa.")

        lineas = [
            LineaFacturaDTO(
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
            )
            for linea in origen.lineas
        ]
        prefs = PreferenciasService.cargar()
        fecha_venc = None
        if prefs.dias_vencimiento > 0:
            fecha_venc = date.today() + timedelta(days=prefs.dias_vencimiento)

        return FacturaService.guardar_borrador(
            cliente_id=origen.cliente_id,
            lineas=lineas,
            porc_iva=origen.porc_iva,
            porc_irpf=origen.porc_irpf,
            serie="RECT",
            fecha_vencimiento=fecha_venc,
            factura_rectificada_id=origen.id,
        )

    @staticmethod
    def marcar_cobrada(factura_id: int) -> Factura:
        """Cambia el estado de una factura emitida a Cobrada."""
        with session_scope() as session:
            factura = session.get(Factura, factura_id)
            if factura is None:
                raise ValueError(f"Factura {factura_id} no encontrada.")
            if factura.estado != EstadoFactura.EMITIDA:
                raise ValueError("Solo se pueden cobrar facturas emitidas.")
            factura.estado = EstadoFactura.COBRADA
            session.flush()
            session.refresh(factura)
            _ = factura.cliente
            _ = factura.lineas
            session.expunge(factura)
            return factura

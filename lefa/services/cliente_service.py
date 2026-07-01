"""
Servicio de gestión de clientes.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from lefa.database import session_scope
from lefa.models import Cliente


@dataclass
class ClienteDTO:
    """Datos de cliente para alta y edición."""

    razon_social: str
    cif_nif: str
    direccion: str = ""
    email: str = ""
    telefono: str = ""
    iban: str = ""
    forma_pago: str = "04"
    dir3_oficina: str = ""
    dir3_organo: str = ""
    dir3_unidad: str = ""


class ClienteService:
    """Operaciones sobre la tabla de clientes."""

    @staticmethod
    def listar_todos() -> list[Cliente]:
        with session_scope() as session:
            return list(session.scalars(select(Cliente).order_by(Cliente.razon_social)))

    @staticmethod
    def buscar(termino: str) -> list[Cliente]:
        """Filtra por razón social, NIF o email (sin distinguir mayúsculas)."""
        texto = termino.strip()
        if not texto:
            return ClienteService.listar_todos()
        patron = f"%{texto}%"
        with session_scope() as session:
            return list(
                session.scalars(
                    select(Cliente)
                    .where(
                        (Cliente.razon_social.ilike(patron))
                        | (Cliente.cif_nif.ilike(patron))
                        | (Cliente.email.ilike(patron))
                    )
                    .order_by(Cliente.razon_social)
                )
            )

    @staticmethod
    def obtener_por_id(cliente_id: int) -> Cliente | None:
        with session_scope() as session:
            return session.get(Cliente, cliente_id)

    @staticmethod
    def crear(datos: ClienteDTO) -> Cliente:
        ClienteService._validar_datos(datos)
        with session_scope() as session:
            cliente = Cliente(
                razon_social=datos.razon_social.strip(),
                cif_nif=datos.cif_nif.strip().upper(),
                direccion=datos.direccion.strip(),
                email=datos.email.strip(),
                telefono=datos.telefono.strip(),
                iban=datos.iban.strip().replace(" ", ""),
                forma_pago=datos.forma_pago.strip() or "04",
                dir3_oficina=datos.dir3_oficina.strip(),
                dir3_organo=datos.dir3_organo.strip(),
                dir3_unidad=datos.dir3_unidad.strip(),
            )
            session.add(cliente)
            session.flush()
            session.refresh(cliente)
            session.expunge(cliente)
            return cliente

    @staticmethod
    def actualizar(cliente_id: int, datos: ClienteDTO) -> Cliente:
        ClienteService._validar_datos(datos)
        with session_scope() as session:
            cliente = session.get(Cliente, cliente_id)
            if cliente is None:
                raise ValueError(f"Cliente {cliente_id} no encontrado.")
            cliente.razon_social = datos.razon_social.strip()
            cliente.cif_nif = datos.cif_nif.strip().upper()
            cliente.direccion = datos.direccion.strip()
            cliente.email = datos.email.strip()
            cliente.telefono = datos.telefono.strip()
            cliente.iban = datos.iban.strip().replace(" ", "")
            cliente.forma_pago = datos.forma_pago.strip() or "04"
            cliente.dir3_oficina = datos.dir3_oficina.strip()
            cliente.dir3_organo = datos.dir3_organo.strip()
            cliente.dir3_unidad = datos.dir3_unidad.strip()
            session.flush()
            session.refresh(cliente)
            session.expunge(cliente)
            return cliente

    @staticmethod
    def _validar_datos(datos: ClienteDTO) -> None:
        if not datos.razon_social.strip():
            raise ValueError("La razón social es obligatoria.")
        if not datos.cif_nif.strip():
            raise ValueError("El CIF/NIF es obligatorio.")

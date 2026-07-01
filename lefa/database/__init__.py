"""
Gestión de sesiones y motor SQLite.

Centraliza la creación del engine y el ciclo de vida de la sesión ORM.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker

from lefa.config import DATABASE_PATH, SERIES_POR_DEFECTO, ensure_directories
from lefa.models import Base, Cliente, PlantillaLinea, Servicio

# Motor SQLite con soporte multi-hilo para workers en segundo plano
_engine = None
_SessionLocal = None


def get_engine():
    """Inicializa lazy el motor de base de datos."""
    global _engine, _SessionLocal
    if _engine is None:
        ensure_directories()
        _engine = create_engine(
            f"sqlite:///{DATABASE_PATH}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _engine


def _migrar_esquema(engine) -> None:
    """Añade columnas nuevas en bases de datos existentes sin perder datos."""
    inspector = inspect(engine)
    alteraciones = []

    if inspector.has_table("facturas"):
        columnas = {col["name"] for col in inspector.get_columns("facturas")}
        if "enviada" not in columnas:
            alteraciones.append(
                "ALTER TABLE facturas ADD COLUMN enviada BOOLEAN NOT NULL DEFAULT 0"
            )
        if "fecha_envio" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN fecha_envio DATE")
        if "destinatario" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN destinatario VARCHAR(150)")
        if "serie" not in columnas:
            alteraciones.append(
                "ALTER TABLE facturas ADD COLUMN serie VARCHAR(20) NOT NULL DEFAULT 'FACT'"
            )
        if "fecha_vencimiento" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN fecha_vencimiento DATE")
        if "verifactu_hash" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN verifactu_hash VARCHAR(64)")
        if "verifactu_hash_anterior" not in columnas:
            alteraciones.append(
                "ALTER TABLE facturas ADD COLUMN verifactu_hash_anterior VARCHAR(64)"
            )
        if "factura_rectificada_id" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN factura_rectificada_id INTEGER")
        if "presupuesto_origen_id" not in columnas:
            alteraciones.append("ALTER TABLE facturas ADD COLUMN presupuesto_origen_id INTEGER")

    if inspector.has_table("clientes"):
        cols_cliente = {col["name"] for col in inspector.get_columns("clientes")}
        if "telefono" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN telefono VARCHAR(30) NOT NULL DEFAULT ''"
            )
        if "iban" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN iban VARCHAR(34) NOT NULL DEFAULT ''"
            )
        if "forma_pago" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN forma_pago VARCHAR(2) NOT NULL DEFAULT '04'"
            )
        if "dir3_oficina" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN dir3_oficina VARCHAR(20) NOT NULL DEFAULT ''"
            )
        if "dir3_organo" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN dir3_organo VARCHAR(20) NOT NULL DEFAULT ''"
            )
        if "dir3_unidad" not in cols_cliente:
            alteraciones.append(
                "ALTER TABLE clientes ADD COLUMN dir3_unidad VARCHAR(20) NOT NULL DEFAULT ''"
            )

    if inspector.has_table("presupuestos"):
        cols_pres = {col["name"] for col in inspector.get_columns("presupuestos")}
        if "factura_id" not in cols_pres:
            alteraciones.append("ALTER TABLE presupuestos ADD COLUMN factura_id INTEGER")

    if alteraciones:
        with engine.begin() as conn:
            for sql in alteraciones:
                conn.execute(text(sql))


def init_database() -> None:
    """
    Crea las tablas, aplica migraciones y siembra datos iniciales si procede.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _migrar_esquema(engine)

    with session_scope() as session:
        existe = session.scalar(select(Cliente).limit(1))
        if existe is None:
            session.add_all(
                [
                    Cliente(
                        razon_social="Tech Solutions S.L.",
                        cif_nif="B87654321",
                        direccion="Av. Innovación 42, 08001 Barcelona",
                        email="admin@techsolutions.es",
                    ),
                    Cliente(
                        razon_social="Consultoría Martínez",
                        cif_nif="12345678Z",
                        direccion="Plaza Mayor 3, 46001 Valencia",
                        email="info@martinezconsulting.es",
                    ),
                    Cliente(
                        razon_social="Distribuciones Norte S.A.",
                        cif_nif="A11223344",
                        direccion="Polígono Industrial 7, 33001 Oviedo",
                        email="compras@distnorte.es",
                    ),
                ]
            )

        existe_plantilla = session.scalar(select(PlantillaLinea).limit(1))
        if existe_plantilla is None:
            session.add_all(
                [
                    PlantillaLinea(
                        nombre="Mantenimiento mensual",
                        descripcion="Mantenimiento informático mensual",
                        cantidad=1.0,
                        precio_unitario=250.0,
                    ),
                    PlantillaLinea(
                        nombre="Desarrollo software",
                        descripcion="Desarrollo software",
                        cantidad=8.0,
                        precio_unitario=35.0,
                    ),
                ]
            )

        existe_servicio = session.scalar(select(Servicio).limit(1))
        if existe_servicio is None:
            session.add_all(
                [
                    Servicio(
                        nombre="Desarrollo web",
                        descripcion="Desarrollo web",
                        cantidad=1.0,
                        precio_unitario=40.0,
                        porc_iva=21.0,
                    ),
                    Servicio(
                        nombre="Mantenimiento",
                        descripcion="Mantenimiento informático",
                        cantidad=1.0,
                        precio_unitario=50.0,
                        porc_iva=21.0,
                    ),
                ]
            )


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager que garantiza commit/rollback y cierre de sesión.

    Uso recomendado en servicios para transacciones atómicas.
    """
    if _SessionLocal is None:
        get_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

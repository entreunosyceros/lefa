"""
Preferencias de la aplicación persistidas en JSON local.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lefa.config import (
    DEFAULT_IRPF_PORCENTAJE,
    DEFAULT_IVA_PORCENTAJE,
    EMISOR_CIF,
    EMISOR_DIRECCION,
    EMISOR_EMAIL,
    EMISOR_RAZON_SOCIAL,
    PDF_OUTPUT_DIR,
    PREFERENCIAS_PATH,
    SERIE_FACTURA_PREFIX,
    SERIES_POR_DEFECTO,
    ensure_directories,
)
from lefa.resources import get_logo_path


@dataclass
class Preferencias:
    """Opciones configurables por el autónomo."""

    iva_porcentaje: float = DEFAULT_IVA_PORCENTAJE
    irpf_porcentaje: float = DEFAULT_IRPF_PORCENTAJE
    carpeta_pdf: str = ""
    emisor_razon_social: str = EMISOR_RAZON_SOCIAL
    emisor_cif: str = EMISOR_CIF
    emisor_direccion: str = EMISOR_DIRECCION
    emisor_email: str = EMISOR_EMAIL
    emisor_telefono: str = ""
    emisor_iban: str = ""
    serie_factura_prefix: str = SERIE_FACTURA_PREFIX
    series_facturacion: list[str] = field(
        default_factory=lambda: list(SERIES_POR_DEFECTO)
    )
    formato_numeracion: str = "fact_anio_4"
    digitos_secuencia: int = 4
    dias_vencimiento: int = 30
    ruta_logotipo: str = ""
    pie_factura: str = ""
    ultimo_cliente_id: int | None = None
    facturae_forma_pago: str = "04"  # Transferencia bancaria (Facturae)
    mostrar_bienvenida: bool = True


class PreferenciasService:
    """Carga y guarda preferencias en ~/.lefa/preferencias.json."""

    _cache: Preferencias | None = None

    @classmethod
    def cargar(cls) -> Preferencias:
        if cls._cache is not None:
            return cls._cache

        ensure_directories()
        if not PREFERENCIAS_PATH.is_file():
            cls._cache = Preferencias()
            return cls._cache

        datos = json.loads(PREFERENCIAS_PATH.read_text(encoding="utf-8"))
        series = datos.get("series_facturacion")
        if not series:
            series = list(SERIES_POR_DEFECTO)

        ultimo = datos.get("ultimo_cliente_id")
        cls._cache = Preferencias(
            iva_porcentaje=float(datos.get("iva_porcentaje", DEFAULT_IVA_PORCENTAJE)),
            irpf_porcentaje=float(datos.get("irpf_porcentaje", DEFAULT_IRPF_PORCENTAJE)),
            carpeta_pdf=datos.get("carpeta_pdf", ""),
            emisor_razon_social=datos.get("emisor_razon_social", EMISOR_RAZON_SOCIAL),
            emisor_cif=datos.get("emisor_cif", EMISOR_CIF),
            emisor_direccion=datos.get("emisor_direccion", EMISOR_DIRECCION),
            emisor_email=datos.get("emisor_email", EMISOR_EMAIL),
            emisor_telefono=datos.get("emisor_telefono", ""),
            emisor_iban=datos.get("emisor_iban", ""),
            serie_factura_prefix=datos.get("serie_factura_prefix", SERIE_FACTURA_PREFIX),
            series_facturacion=[s.strip() for s in series if str(s).strip()],
            formato_numeracion=datos.get("formato_numeracion", "fact_anio_4"),
            digitos_secuencia=int(datos.get("digitos_secuencia", 4)),
            dias_vencimiento=int(datos.get("dias_vencimiento", 30)),
            ruta_logotipo=datos.get("ruta_logotipo", ""),
            pie_factura=datos.get("pie_factura", ""),
            ultimo_cliente_id=int(ultimo) if ultimo is not None else None,
            facturae_forma_pago=datos.get("facturae_forma_pago", "04"),
            mostrar_bienvenida=bool(datos.get("mostrar_bienvenida", True)),
        )
        if not cls._cache.series_facturacion:
            cls._cache.series_facturacion = list(SERIES_POR_DEFECTO)
        return cls._cache

    @classmethod
    def guardar(cls, prefs: Preferencias) -> None:
        ensure_directories()
        PREFERENCIAS_PATH.write_text(
            json.dumps(asdict(prefs), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        cls._cache = prefs
        prefs.carpeta_pdf_path().mkdir(parents=True, exist_ok=True)

    @classmethod
    def invalidar_cache(cls) -> None:
        cls._cache = None

    @classmethod
    def obtener_serie_prefix(cls) -> str:
        series = cls.cargar().series_facturacion
        if series:
            return series[0].strip() or SERIE_FACTURA_PREFIX
        return cls.cargar().serie_factura_prefix.strip() or SERIE_FACTURA_PREFIX

    @classmethod
    def obtener_series(cls) -> list[str]:
        prefs = cls.cargar()
        series = [s.strip() for s in prefs.series_facturacion if s.strip()]
        if series:
            return series
        prefijo = prefs.serie_factura_prefix.strip() or SERIE_FACTURA_PREFIX
        return [prefijo]

    @classmethod
    def guardar_ultimo_cliente(cls, cliente_id: int | None) -> None:
        prefs = cls.cargar()
        prefs.ultimo_cliente_id = cliente_id
        cls.guardar(prefs)

    @classmethod
    def obtener_carpeta_pdf(cls) -> Path:
        return cls.cargar().carpeta_pdf_path()

    @classmethod
    def obtener_logotipo(cls) -> Path:
        prefs = cls.cargar()
        if prefs.ruta_logotipo.strip():
            return Path(prefs.ruta_logotipo.strip())
        return get_logo_path()


def _carpeta_pdf_path(self: Preferencias) -> Path:
    if self.carpeta_pdf.strip():
        return Path(self.carpeta_pdf.strip()).expanduser()
    return PDF_OUTPUT_DIR


Preferencias.carpeta_pdf_path = _carpeta_pdf_path  # type: ignore[method-assign]

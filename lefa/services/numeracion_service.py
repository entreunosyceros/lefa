"""
Formato y correlativos de numeración de facturas.

Plantillas predefinidas para que el autónomo mantenga su numeración habitual.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import and_, extract, select
from sqlalchemy.orm import Session

from lefa.models import Factura, Presupuesto

# id → plantilla con marcadores {serie}, {anio}, {seq}
FORMATOS_NUMERACION: dict[str, str] = {
    "fact_anio_4": "{serie}-{anio}-{seq}",
    "anio_3": "{anio}-{seq}",
    "serie_anio_3": "{serie}-{anio}-{seq}",
    "serie_anio_compact": "{serie}{anio}-{seq}",
    "seq4_anio": "{seq}/{anio}",
    "serie_seq3": "{serie}-{seq}",
}

ETIQUETAS_FORMATO: dict[str, str] = {
    "fact_anio_4": "FACT-2026-0001 (serie-año-4 dígitos)",
    "anio_3": "2026-001",
    "serie_anio_3": "F-2026-001",
    "serie_anio_compact": "FAC2026-001",
    "seq4_anio": "0001/2026",
    "serie_seq3": "WEB-001 (serie sin año)",
}


@dataclass(frozen=True)
class ContextoNumeracion:
    serie: str
    anio: int
    secuencia: int
    digitos: int = 4

    def formatear(self, plantilla: str) -> str:
        seq = f"{self.secuencia:0{self.digitos}d}"
        return (
            plantilla.replace("{serie}", self.serie)
            .replace("{anio}", str(self.anio))
            .replace("{seq}", seq)
        )


class NumeracionService:
    """Genera números de factura y calcula el siguiente correlativo."""

    @staticmethod
    def plantilla(formato_id: str) -> str:
        return FORMATOS_NUMERACION.get(formato_id, FORMATOS_NUMERACION["fact_anio_4"])

    @staticmethod
    def usa_serie(formato_id: str) -> bool:
        return "{serie}" in NumeracionService.plantilla(formato_id)

    @staticmethod
    def usa_anio(formato_id: str) -> bool:
        return "{anio}" in NumeracionService.plantilla(formato_id)

    @staticmethod
    def formatear_numero(
        serie: str,
        anio: int,
        secuencia: int,
        formato_id: str,
        digitos: int = 4,
    ) -> str:
        ctx = ContextoNumeracion(
            serie=serie.strip() or "FACT",
            anio=anio,
            secuencia=secuencia,
            digitos=digitos,
        )
        return ctx.formatear(NumeracionService.plantilla(formato_id))

    @staticmethod
    def _plantilla_a_regex(plantilla: str, serie: str, anio: int, digitos: int) -> re.Pattern:
        """Convierte la plantilla en regex para extraer la secuencia."""
        partes: list[str] = []
        resto = plantilla
        while resto:
            idx = resto.find("{")
            if idx == -1:
                partes.append(re.escape(resto))
                break
            if idx > 0:
                partes.append(re.escape(resto[:idx]))
            resto = resto[idx:]
            if resto.startswith("{serie}"):
                partes.append(re.escape(serie))
                resto = resto[7:]
            elif resto.startswith("{anio}"):
                partes.append(str(anio))
                resto = resto[6:]
            elif resto.startswith("{seq}"):
                partes.append(rf"(\d{{{digitos}}})")
                resto = resto[5:]
            else:
                partes.append(re.escape(resto[0]))
                resto = resto[1:]
        return re.compile("^" + "".join(partes) + "$")

    @staticmethod
    def extraer_secuencia(
        numero: str,
        formato_id: str,
        serie: str,
        anio: int,
        digitos: int,
    ) -> int | None:
        plantilla = NumeracionService.plantilla(formato_id)
        regex = NumeracionService._plantilla_a_regex(plantilla, serie, anio, digitos)
        match = regex.match(numero)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def siguiente_secuencia(
        session: Session,
        serie: str,
        anio: int,
        formato_id: str,
        digitos: int = 4,
    ) -> int:
        """Correlativo por serie y, si el formato incluye año, por ejercicio."""
        serie = serie.strip() or "FACT"
        condiciones = [Factura.numero_factura.isnot(None)]
        if NumeracionService.usa_serie(formato_id):
            condiciones.append(Factura.serie == serie)
        if NumeracionService.usa_anio(formato_id):
            condiciones.append(Factura.fecha_emision.isnot(None))
            condiciones.append(extract("year", Factura.fecha_emision) == anio)

        numeros = session.scalars(
            select(Factura.numero_factura).where(and_(*condiciones))
        ).all()

        max_seq = 0
        for numero in numeros:
            if not numero:
                continue
            seq = NumeracionService.extraer_secuencia(
                numero, formato_id, serie if NumeracionService.usa_serie(formato_id) else "",
                anio,
                digitos,
            )
            if seq is not None and seq > max_seq:
                max_seq = seq
        return max_seq + 1

    @staticmethod
    def siguiente_secuencia_presupuesto(
        session: Session,
        serie: str,
        anio: int,
        formato_id: str,
        digitos: int = 4,
    ) -> int:
        """Correlativo de presupuestos (tabla separada de facturas)."""
        serie = serie.strip() or "PRES"
        condiciones = [Presupuesto.numero_presupuesto.isnot(None)]
        if NumeracionService.usa_serie(formato_id):
            condiciones.append(Presupuesto.serie == serie)
        if NumeracionService.usa_anio(formato_id):
            condiciones.append(Presupuesto.fecha_emision.isnot(None))
            condiciones.append(extract("year", Presupuesto.fecha_emision) == anio)

        numeros = session.scalars(
            select(Presupuesto.numero_presupuesto).where(and_(*condiciones))
        ).all()

        max_seq = 0
        for numero in numeros:
            if not numero:
                continue
            seq = NumeracionService.extraer_secuencia(
                numero,
                formato_id,
                serie if NumeracionService.usa_serie(formato_id) else "",
                anio,
                digitos,
            )
            if seq is not None and seq > max_seq:
                max_seq = seq
        return max_seq + 1

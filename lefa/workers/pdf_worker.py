"""
Worker para generación de documentos de factura en segundo plano.

Genera PDF (con QR tributario), XML Facturae y registra archivos locales.
"""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from lefa.models import EstadoFactura
from lefa.services.factura_service import FacturaService
from lefa.services.facturae_service import FacturaeService
from lefa.services.pdf_service import PDFService


class PDFWorker(QThread):
    """
    Hilo dedicado a generar PDF y Facturae de una factura.

    Señales:
        finished_ok(dict): rutas {pdf, xml?}.
        finished_error(str): mensaje de error.
    """

    finished_ok = pyqtSignal(object)
    finished_error = pyqtSignal(str)

    def __init__(self, factura_id: int, parent=None):
        super().__init__(parent)
        self._factura_id = factura_id

    def run(self) -> None:
        try:
            factura = FacturaService.obtener_por_id(self._factura_id)
            if factura is None:
                raise ValueError(f"Factura {self._factura_id} no encontrada.")

            ruta_pdf = PDFService.generar(factura)
            resultado = {"pdf": ruta_pdf, "xml": None}

            if factura.estado != EstadoFactura.BORRADOR and factura.numero_factura:
                resultado["xml"] = FacturaeService.generar(factura)

            self.finished_ok.emit(resultado)
        except Exception as exc:
            self.finished_error.emit(str(exc))

"""Worker para generar PDF de presupuesto en segundo plano."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from lefa.services.presupuesto_pdf_service import PresupuestoPDFService
from lefa.services.presupuesto_service import PresupuestoService


class PresupuestoPDFWorker(QThread):
    finished_ok = pyqtSignal(object)
    finished_error = pyqtSignal(str)

    def __init__(self, presupuesto_id: int, parent=None):
        super().__init__(parent)
        self._presupuesto_id = presupuesto_id

    def run(self) -> None:
        try:
            presupuesto = PresupuestoService.obtener_por_id(self._presupuesto_id)
            if presupuesto is None:
                raise ValueError(f"Presupuesto {self._presupuesto_id} no encontrado.")
            ruta = PresupuestoPDFService.generar(presupuesto)
            self.finished_ok.emit(ruta)
        except Exception as exc:
            self.finished_error.emit(str(exc))

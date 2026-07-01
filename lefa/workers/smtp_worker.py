"""
Worker para envío de facturas por correo en segundo plano.
"""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from lefa.services.email_service import EmailService


class SMTPWorker(QThread):
    """
    Hilo dedicado al envío SMTP de una factura con PDF adjunto.

    Señales:
        finished_ok(str): mensaje de confirmación.
        finished_error(str): mensaje de error.
    """

    finished_ok = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, factura_id: int, parent=None):
        super().__init__(parent)
        self._factura_id = factura_id

    def run(self) -> None:
        try:
            mensaje = EmailService.enviar_factura(self._factura_id)
            self.finished_ok.emit(mensaje)
        except Exception as exc:
            self.finished_error.emit(str(exc))

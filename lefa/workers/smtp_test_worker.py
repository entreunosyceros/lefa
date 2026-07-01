"""
Worker para probar la configuración SMTP sin bloquear la UI.
"""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from lefa.services.email_service import EmailService
from lefa.services.smtp_config_service import SmtpConfig


class SmtpTestWorker(QThread):
    """Prueba la conexión SMTP en un hilo separado."""

    finished_ok = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(
        self,
        config: SmtpConfig,
        contrasena: str,
        destino_prueba: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._contrasena = contrasena
        self._destino_prueba = destino_prueba

    def run(self) -> None:
        try:
            mensaje = EmailService.probar_conexion(
                self._config,
                self._contrasena,
                self._destino_prueba,
            )
            self.finished_ok.emit(mensaje)
        except Exception as exc:
            self.finished_error.emit(str(exc))

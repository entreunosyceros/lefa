"""
Diálogo 'Sobre LEFA' — información de la aplicación.

Muestra logo, descripción breve y enlace al repositorio en GitHub.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from lefa import __app_name__, __version__
from lefa.resources import GITHUB_URL, get_logo_path

# Tamaño máximo de visualización del logo (respeta proporción original).
LOGO_ANCHO_MAXIMO = 480


class AboutDialog(QDialog):
    """Ventana modal con datos del programa y acceso al repositorio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Sobre {__app_name__}")
        self.setMinimumSize(620, 560)
        self.resize(680, 600)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 24)

        # Logo desde img/logo.png en la raíz del proyecto
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        logo_path = get_logo_path()
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaledToWidth(
                        LOGO_ANCHO_MAXIMO,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if logo_label.pixmap() is None:
            logo_label.setText(f"No se encontró el logo en:\n{logo_path}")
            logo_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(logo_label)

        # Título y versión
        titulo = QLabel(
            f"<span style='font-size: 18px;'>"
            f"<b>{__app_name__}</b> — Local &amp; Eficiente Facturación para Autónomos"
            f"</span>"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setWordWrap(True)
        layout.addWidget(titulo)

        version = QLabel(f"Versión {__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(version)

        # Descripción
        descripcion = QLabel(
            "LEFA es una aplicación de escritorio pensada para autónomos que "
            "necesitan facturar con rapidez y mantener el control total de sus "
            "datos en local. Gestiona clientes, borradores, emisión de facturas, "
            "generación automática de PDF y seguimiento de cobros sin depender "
            "de servicios en la nube."
        )
        descripcion.setWordWrap(True)
        descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuente_desc = QFont()
        fuente_desc.setPointSize(11)
        descripcion.setFont(fuente_desc)
        descripcion.setStyleSheet("padding: 0 12px;")
        layout.addWidget(descripcion)

        layout.addStretch()

        # Botón GitHub (abre el navegador predeterminado — Linux y Windows)
        btn_github = QPushButton("Ver en GitHub")
        btn_github.setMinimumWidth(180)
        btn_github.setMinimumHeight(36)
        btn_github.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_github.clicked.connect(self._abrir_github)
        layout.addWidget(btn_github, alignment=Qt.AlignmentFlag.AlignCenter)

        # Cerrar
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _abrir_github(self) -> None:
        """Abre la URL del repositorio con el navegador del sistema."""
        QDesktopServices.openUrl(QUrl(GITHUB_URL))

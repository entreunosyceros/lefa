"""
Diálogo de bienvenida — presenta el flujo lineal en el primer arranque.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from lefa import __app_name__
from lefa.resources import get_logo_path

_PASOS = (
    ("1", "Cliente", "#1565c0"),
    ("2", "Líneas", "#1565c0"),
    ("3", "Emitir", "#1565c0"),
    ("4", "Listo", "#2e7d32"),
)


class BienvenidaDialog(QDialog):
    """Bienvenida breve con el camino recto frente al laberinto ERP."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Bienvenido a {__app_name__}")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._chk_no_mostrar = QCheckBox("No volver a mostrar")
        self._setup_ui()

    def no_volver_a_mostrar(self) -> bool:
        return self._chk_no_mostrar.isChecked()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 20)

        logo_path = get_logo_path()
        if logo_path.is_file():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo = QLabel()
                logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo.setPixmap(pix.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation))
                layout.addWidget(logo)

        titulo = QLabel(
            "<span style='font-size: 17px;'><b>Facturar sin laberintos</b></span>"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        texto = QLabel(
            f"{__app_name__} está pensado para ir <b>en línea recta</b>: "
            "cliente, líneas, emitir y listo — en una sola pestaña, "
            "sin abrir cinco ventanas como en un ERP tradicional."
        )
        texto.setWordWrap(True)
        texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(texto)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        for i, (num, nombre, color) in enumerate(_PASOS):
            celda = QVBoxLayout()
            circulo = QLabel(num)
            circulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circulo.setFixedSize(32, 32)
            circulo.setStyleSheet(
                f"background-color: {color}; color: white; border-radius: 16px;"
                "font-weight: bold;"
            )
            celda.addWidget(circulo, alignment=Qt.AlignmentFlag.AlignHCenter)
            lbl = QLabel(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 11px;")
            celda.addWidget(lbl)
            fila.addLayout(celda)
            if i < len(_PASOS) - 1:
                flecha = QLabel("→")
                flecha.setStyleSheet("font-size: 22px; color: #1565c0;")
                flecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fila.addWidget(flecha)
        layout.addLayout(fila)

        layout.addWidget(self._chk_no_mostrar)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Empezar")
        botones.accepted.connect(self.accept)
        layout.addWidget(botones)

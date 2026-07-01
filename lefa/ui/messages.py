"""
Diálogos con estilo legible en temas claros y oscuros del sistema.
"""

from PyQt6.QtWidgets import QMessageBox, QWidget

_ESTILO_MENSAJE = """
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #212121;
    min-width: 300px;
}
QMessageBox QPushButton {
    color: #212121;
    background-color: #eeeeee;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 6px 18px;
    min-width: 72px;
}
"""


def _preparar(parent: QWidget | None, titulo: str, texto: str, icono) -> QMessageBox:
    box = QMessageBox(icono, titulo, texto, QMessageBox.StandardButton.Ok, parent)
    box.setStyleSheet(_ESTILO_MENSAJE)
    return box


def aviso(parent: QWidget | None, titulo: str, texto: str) -> None:
    _preparar(parent, titulo, texto, QMessageBox.Icon.Warning).exec()


def informacion(parent: QWidget | None, titulo: str, texto: str) -> None:
    _preparar(parent, titulo, texto, QMessageBox.Icon.Information).exec()


def error(parent: QWidget | None, titulo: str, texto: str) -> None:
    _preparar(parent, titulo, texto, QMessageBox.Icon.Critical).exec()

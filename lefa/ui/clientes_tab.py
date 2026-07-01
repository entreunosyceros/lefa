"""
Pestaña 'Clientes' — alta y consulta de clientes.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lefa.services.cliente_service import ClienteService
from lefa.ui.cliente_dialog import ClienteDialog
from lefa.ui.messages import aviso

COLOR_TEXTO = QColor(33, 33, 33)
COLOR_FILA = QColor(245, 245, 245)

COL_ID = 0
COL_RAZON = 1
COL_CIF = 2
COL_DIRECCION = 3
COL_EMAIL = 4
COL_TELEFONO = 5


class ClientesTab(QWidget):
    """Listado y gestión de clientes del autónomo."""

    clientes_actualizados = pyqtSignal()
    estado_mensaje = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        buscar_layout = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, NIF o email…")
        self.txt_buscar.textChanged.connect(self.refrescar)
        buscar_layout.addWidget(self.txt_buscar)
        layout.addLayout(buscar_layout)

        toolbar = QHBoxLayout()
        self.btn_nuevo = QPushButton("+ Nuevo cliente")
        self.btn_nuevo.clicked.connect(self._nuevo_cliente)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self._editar_cliente)
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.clicked.connect(self.refrescar)
        toolbar.addWidget(self.btn_nuevo)
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_refrescar)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Razón social", "CIF/NIF", "Dirección", "Email", "Teléfono"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self._editar_cliente)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_CIF, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_RAZON, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_DIRECCION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_EMAIL, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_TELEFONO, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setStyleSheet(
            "QTableWidget::item:selected {"
            "  background-color: #90CAF9;"
            "  color: #212121;"
            "}"
        )
        layout.addWidget(self.tabla)

    def refrescar(self) -> None:
        termino = self.txt_buscar.text().strip()
        clientes = (
            ClienteService.buscar(termino)
            if termino
            else ClienteService.listar_todos()
        )
        self.tabla.setRowCount(0)
        brush_fondo = QBrush(COLOR_FILA)
        brush_texto = QBrush(COLOR_TEXTO)

        for cliente in clientes:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [
                str(cliente.id),
                cliente.razon_social,
                cliente.cif_nif,
                cliente.direccion,
                cliente.email,
                cliente.telefono,
            ]
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setBackground(brush_fondo)
                item.setForeground(brush_texto)
                if col == COL_ID:
                    item.setData(Qt.ItemDataRole.UserRole, cliente.id)
                self.tabla.setItem(fila, col, item)

    def _cliente_seleccionado_id(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        item = self.tabla.item(fila, COL_ID)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _nuevo_cliente(self) -> None:
        dialogo = ClienteDialog(self)
        if dialogo.exec() and dialogo.cliente_id is not None:
            self.refrescar()
            self.clientes_actualizados.emit()
            self.estado_mensaje.emit("Cliente creado correctamente.")

    def _editar_cliente(self) -> None:
        cliente_id = self._cliente_seleccionado_id()
        if cliente_id is None:
            aviso(self, "Selección", "Seleccione un cliente de la lista.")
            return
        cliente = ClienteService.obtener_por_id(cliente_id)
        if cliente is None:
            aviso(self, "Error", "Cliente no encontrado.")
            self.refrescar()
            return

        dialogo = ClienteDialog(self, cliente=cliente)
        if dialogo.exec() and dialogo.cliente_id is not None:
            self.refrescar()
            self.clientes_actualizados.emit()
            self.estado_mensaje.emit("Cliente actualizado correctamente.")

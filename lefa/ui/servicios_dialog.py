"""
Gestión del catálogo de servicios.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from lefa.config import IVA_OPCIONES
from lefa.services.servicio_service import ServicioDTO, ServicioService
from lefa.ui.messages import aviso, error, informacion

COLOR_TEXTO = QColor(33, 33, 33)
COLOR_FILA = QColor(245, 245, 245)


class ServiciosDialog(QDialog):
    """CRUD del catálogo de servicios."""

    servicios_actualizados = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catálogo de servicios")
        self.setMinimumSize(700, 420)
        self.setModal(True)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        for texto, slot in [
            ("+ Nuevo servicio", self._nuevo),
            ("Editar", self._editar),
            ("Eliminar", self._eliminar),
        ]:
            btn = QPushButton(texto)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Nombre", "Descripción", "Cantidad", "Precio", "IVA %"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self._editar)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.accept)
        layout.addWidget(botones)

    def refrescar(self) -> None:
        servicios = ServicioService.listar_todos()
        self.tabla.setRowCount(0)
        brush_fondo = QBrush(COLOR_FILA)
        brush_texto = QBrush(COLOR_TEXTO)
        for s in servicios:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            for col, texto in enumerate(
                [
                    s.nombre,
                    s.descripcion,
                    f"{s.cantidad:.2f}",
                    f"{s.precio_unitario:.2f} €",
                    f"{s.porc_iva:g} %",
                ]
            ):
                item = QTableWidgetItem(texto)
                item.setBackground(brush_fondo)
                item.setForeground(brush_texto)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, s.id)
                self.tabla.setItem(fila, col, item)

    def _seleccionado_id(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        item = self.tabla.item(fila, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _nuevo(self) -> None:
        if ServicioFormDialog(self).exec():
            self.refrescar()
            self.servicios_actualizados.emit()

    def _editar(self) -> None:
        sid = self._seleccionado_id()
        if sid is None:
            aviso(self, "Selección", "Seleccione un servicio.")
            return
        servicios = {s.id: s for s in ServicioService.listar_todos()}
        if servicios.get(sid) and ServicioFormDialog(self, servicios[sid]).exec():
            self.refrescar()
            self.servicios_actualizados.emit()

    def _eliminar(self) -> None:
        sid = self._seleccionado_id()
        if sid is None:
            aviso(self, "Selección", "Seleccione un servicio.")
            return
        try:
            ServicioService.eliminar(sid)
            self.refrescar()
            self.servicios_actualizados.emit()
        except Exception as exc:
            error(self, "Error", str(exc))


class ServicioFormDialog(QDialog):
    def __init__(self, parent=None, servicio=None):
        super().__init__(parent)
        self._servicio_id = servicio.id if servicio else None
        self.setWindowTitle("Editar servicio" if servicio else "Nuevo servicio")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.txt_nombre = QLineEdit(servicio.nombre if servicio else "")
        form.addRow("Nombre *:", self.txt_nombre)
        self.txt_descripcion = QLineEdit(servicio.descripcion if servicio else "")
        form.addRow("Descripción *:", self.txt_descripcion)
        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setValue(servicio.cantidad if servicio else 1.0)
        form.addRow("Cantidad:", self.spin_cantidad)
        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setRange(0, 9999999)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setSuffix(" €")
        self.spin_precio.setValue(servicio.precio_unitario if servicio else 0.0)
        form.addRow("Precio unitario:", self.spin_precio)
        self.combo_iva = QComboBox()
        for v in IVA_OPCIONES:
            self.combo_iva.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        if servicio:
            idx = self.combo_iva.findData(servicio.porc_iva)
            if idx >= 0:
                self.combo_iva.setCurrentIndex(idx)
        form.addRow("IVA:", self.combo_iva)
        layout.addLayout(form)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _guardar(self) -> None:
        datos = ServicioDTO(
            nombre=self.txt_nombre.text(),
            descripcion=self.txt_descripcion.text(),
            cantidad=self.spin_cantidad.value(),
            precio_unitario=self.spin_precio.value(),
            porc_iva=float(self.combo_iva.currentData()),
        )
        try:
            if self._servicio_id is None:
                ServicioService.crear(datos)
            else:
                ServicioService.actualizar(self._servicio_id, datos)
            informacion(self, "Guardado", "Servicio guardado.")
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

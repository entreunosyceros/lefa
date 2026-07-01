"""
Gestión de plantillas de líneas de factura.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
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

from lefa.services.plantilla_service import PlantillaLineaDTO, PlantillaService
from lefa.ui.messages import aviso, error, informacion

COLOR_TEXTO = QColor(33, 33, 33)
COLOR_FILA = QColor(245, 245, 245)


class PlantillasDialog(QDialog):
    """CRUD de plantillas para añadir líneas con dos clics."""

    plantillas_actualizadas = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plantillas de líneas")
        self.setMinimumSize(640, 420)
        self.setModal(True)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_nueva = QPushButton("+ Nueva plantilla")
        self.btn_nueva.clicked.connect(self._nueva_plantilla)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self._editar_plantilla)
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.clicked.connect(self._eliminar_plantilla)
        toolbar.addWidget(self.btn_nueva)
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_eliminar)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(
            ["Nombre", "Descripción", "Cantidad", "Precio unitario"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self._editar_plantilla)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tabla)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.accept)
        layout.addWidget(botones)

    def refrescar(self) -> None:
        plantillas = PlantillaService.listar_todas()
        self.tabla.setRowCount(0)
        brush_fondo = QBrush(COLOR_FILA)
        brush_texto = QBrush(COLOR_TEXTO)

        for p in plantillas:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            for col, texto in enumerate(
                [p.nombre, p.descripcion, f"{p.cantidad:.2f}", f"{p.precio_unitario:.2f} €"]
            ):
                item = QTableWidgetItem(texto)
                item.setBackground(brush_fondo)
                item.setForeground(brush_texto)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.tabla.setItem(fila, col, item)

    def _seleccionada_id(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        item = self.tabla.item(fila, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _nueva_plantilla(self) -> None:
        if PlantillaFormDialog(self).exec():
            self.refrescar()
            self.plantillas_actualizadas.emit()

    def _editar_plantilla(self) -> None:
        pid = self._seleccionada_id()
        if pid is None:
            aviso(self, "Selección", "Seleccione una plantilla.")
            return
        plantillas = {p.id: p for p in PlantillaService.listar_todas()}
        plantilla = plantillas.get(pid)
        if plantilla and PlantillaFormDialog(self, plantilla).exec():
            self.refrescar()
            self.plantillas_actualizadas.emit()

    def _eliminar_plantilla(self) -> None:
        pid = self._seleccionada_id()
        if pid is None:
            aviso(self, "Selección", "Seleccione una plantilla.")
            return
        try:
            PlantillaService.eliminar(pid)
            self.refrescar()
            self.plantillas_actualizadas.emit()
        except Exception as exc:
            error(self, "Error", str(exc))


class PlantillaFormDialog(QDialog):
    """Formulario de alta/edición de una plantilla."""

    def __init__(self, parent=None, plantilla=None):
        super().__init__(parent)
        self._plantilla_id = plantilla.id if plantilla else None
        self.setWindowTitle("Editar plantilla" if plantilla else "Nueva plantilla")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_nombre = QLineEdit(plantilla.nombre if plantilla else "")
        form.addRow("Nombre *:", self.txt_nombre)

        self.txt_descripcion = QLineEdit(plantilla.descripcion if plantilla else "")
        form.addRow("Descripción *:", self.txt_descripcion)

        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setValue(plantilla.cantidad if plantilla else 1.0)
        form.addRow("Cantidad:", self.spin_cantidad)

        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setRange(0, 9999999)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setSuffix(" €")
        self.spin_precio.setValue(plantilla.precio_unitario if plantilla else 0.0)
        form.addRow("Precio unitario:", self.spin_precio)

        layout.addLayout(form)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _guardar(self) -> None:
        datos = PlantillaLineaDTO(
            nombre=self.txt_nombre.text(),
            descripcion=self.txt_descripcion.text(),
            cantidad=self.spin_cantidad.value(),
            precio_unitario=self.spin_precio.value(),
        )
        try:
            if self._plantilla_id is None:
                PlantillaService.crear(datos)
            else:
                PlantillaService.actualizar(self._plantilla_id, datos)
            informacion(self, "Guardado", "Plantilla guardada.")
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

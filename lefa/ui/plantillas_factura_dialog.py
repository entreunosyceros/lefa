"""
Plantillas de factura completa — nueva factura desde plantilla mensual.
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

from lefa.config import IRPF_OPCIONES, IVA_OPCIONES
from lefa.services.cliente_service import ClienteService
from lefa.services.plantilla_factura_service import (
    PlantillaFacturaDTO,
    PlantillaFacturaLineaDTO,
    PlantillaFacturaService,
)
from lefa.services.preferencias_service import PreferenciasService
from lefa.ui.messages import aviso, error, informacion

COLOR_TEXTO = QColor(33, 33, 33)
COLOR_FILA = QColor(245, 245, 245)


class PlantillasFacturaDialog(QDialog):
    """Gestiona plantillas de factura completa y crea borradores."""

    plantilla_usada = pyqtSignal(int)  # factura_id del borrador creado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plantillas de factura")
        self.setMinimumSize(720, 440)
        self.setModal(True)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.btn_nueva = QPushButton("+ Nueva plantilla")
        self.btn_nueva.clicked.connect(self._nueva)
        self.btn_usar = QPushButton("Nueva factura desde plantilla")
        self.btn_usar.clicked.connect(self._usar_plantilla)
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.clicked.connect(self._eliminar)
        toolbar.addWidget(self.btn_nueva)
        toolbar.addWidget(self.btn_usar)
        toolbar.addWidget(self.btn_eliminar)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Nombre", "Cliente", "Serie", "IVA", "Líneas"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self._usar_plantilla)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.accept)
        layout.addWidget(botones)

    def refrescar(self) -> None:
        plantillas = PlantillaFacturaService.listar_todas()
        self.tabla.setRowCount(0)
        brush_fondo = QBrush(COLOR_FILA)
        brush_texto = QBrush(COLOR_TEXTO)
        for p in plantillas:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            cliente = p.cliente.razon_social if p.cliente else "—"
            valores = [
                p.nombre,
                cliente,
                p.serie,
                f"{p.porc_iva:g} %",
                str(len(p.lineas)),
            ]
            for col, texto in enumerate(valores):
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

    def _nueva(self) -> None:
        if PlantillaFacturaFormDialog(self).exec():
            self.refrescar()

    def _usar_plantilla(self) -> None:
        pid = self._seleccionada_id()
        if pid is None:
            aviso(self, "Selección", "Seleccione una plantilla.")
            return
        try:
            factura_id = PlantillaFacturaService.crear_borrador_desde_plantilla(pid)
            self.plantilla_usada.emit(factura_id)
            informacion(
                self,
                "Plantilla aplicada",
                "Se creó un borrador. Revíselo en Nueva Factura y emita.",
            )
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

    def _eliminar(self) -> None:
        pid = self._seleccionada_id()
        if pid is None:
            aviso(self, "Selección", "Seleccione una plantilla.")
            return
        try:
            PlantillaFacturaService.eliminar(pid)
            self.refrescar()
        except Exception as exc:
            error(self, "Error", str(exc))


class PlantillaFacturaFormDialog(QDialog):
    """Alta rápida de plantilla con una línea (ampliable después)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva plantilla de factura")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. Mantenimiento mensual")
        form.addRow("Nombre *:", self.txt_nombre)

        self.combo_cliente = QComboBox()
        for c in ClienteService.listar_todos():
            self.combo_cliente.addItem(f"{c.razon_social} ({c.cif_nif})", c.id)
        form.addRow("Cliente *:", self.combo_cliente)

        self.combo_serie = QComboBox()
        for s in PreferenciasService.obtener_series():
            self.combo_serie.addItem(s)
        form.addRow("Serie:", self.combo_serie)

        self.combo_iva = QComboBox()
        for v in IVA_OPCIONES:
            self.combo_iva.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        form.addRow("IVA:", self.combo_iva)

        self.combo_irpf = QComboBox()
        for v in IRPF_OPCIONES:
            self.combo_irpf.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        form.addRow("IRPF:", self.combo_irpf)

        self.txt_descripcion = QLineEdit()
        self.txt_descripcion.setPlaceholderText("Concepto de la línea")
        form.addRow("Descripción *:", self.txt_descripcion)

        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setRange(0.01, 99999)
        self.spin_cantidad.setValue(1.0)
        form.addRow("Cantidad:", self.spin_cantidad)

        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setRange(0, 9999999)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setSuffix(" €")
        form.addRow("Precio unitario:", self.spin_precio)

        layout.addLayout(form)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _guardar(self) -> None:
        cliente_id = self.combo_cliente.currentData()
        if cliente_id is None:
            aviso(self, "Validación", "Seleccione un cliente.")
            return
        datos = PlantillaFacturaDTO(
            nombre=self.txt_nombre.text(),
            serie=self.combo_serie.currentText(),
            porc_iva=float(self.combo_iva.currentData()),
            porc_irpf=float(self.combo_irpf.currentData()),
            cliente_id=int(cliente_id),
            lineas=[
                PlantillaFacturaLineaDTO(
                    descripcion=self.txt_descripcion.text(),
                    cantidad=self.spin_cantidad.value(),
                    precio_unitario=self.spin_precio.value(),
                )
            ],
        )
        try:
            PlantillaFacturaService.crear(datos)
            informacion(self, "Guardado", "Plantilla creada.")
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

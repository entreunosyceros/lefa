"""
Listado de presupuestos — aceptar y convertir en factura.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lefa.models import EstadoPresupuesto
from lefa.services.factura_service import FacturaService
from lefa.services.presupuesto_service import PresupuestoService
from lefa.ui.messages import aviso, error, informacion
from lefa.utils import formato_moneda

COLOR_BORRADOR = QColor(240, 240, 240)
COLOR_EMITIDO = QColor(187, 222, 251)
COLOR_ACEPTADO = QColor(200, 230, 201)
COLOR_CONVERTIDO = QColor(220, 220, 220)
COLOR_RECHAZADO = QColor(255, 205, 210)
COLOR_TEXTO = QColor(33, 33, 33)

ROLE_PRESUPUESTO_ID = Qt.ItemDataRole.UserRole
ROLE_FACTURA_ID = Qt.ItemDataRole.UserRole + 1
ROLE_ESTADO = Qt.ItemDataRole.UserRole + 2


class ListadoPresupuestosTab(QWidget):
    editar_borrador = pyqtSignal(int)
    convertido_en_factura = pyqtSignal(int)
    ver_factura_asociada = pyqtSignal(int)
    estado_mensaje = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.clicked.connect(self.refrescar)
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_aceptar.clicked.connect(self._aceptar)
        self.btn_convertir = QPushButton("Convertir en factura")
        self.btn_convertir.setStyleSheet("font-weight: bold;")
        self.btn_convertir.clicked.connect(self._convertir)
        self.btn_ver_factura = QPushButton("Ver factura asociada")
        self.btn_ver_factura.clicked.connect(self._ver_factura_asociada)
        self.btn_ver_factura.setEnabled(False)
        self.btn_rechazar = QPushButton("Rechazar")
        self.btn_rechazar.clicked.connect(self._rechazar)
        for w in (
            self.btn_refrescar,
            self.btn_aceptar,
            self.btn_convertir,
            self.btn_ver_factura,
            self.btn_rechazar,
        ):
            bar.addWidget(w)
        bar.addStretch()
        layout.addLayout(bar)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            [
                "ID",
                "Número",
                "Cliente",
                "Fecha",
                "Estado",
                "Válido hasta",
                "Factura",
                "Total",
            ]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self._doble_clic)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        h = self.tabla.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

    def refrescar(self) -> None:
        presupuestos = PresupuestoService.listar_todos()
        self.tabla.setRowCount(0)
        for p in presupuestos:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            color = self._color(p.estado)
            brush = QBrush(color)
            texto = QBrush(COLOR_TEXTO)
            factura_txt = "—"
            if p.factura_id:
                factura = FacturaService.obtener_por_id(p.factura_id)
                if factura and factura.numero_factura:
                    factura_txt = factura.numero_factura
                elif factura:
                    factura_txt = f"Borrador #{factura.id}"
                else:
                    factura_txt = f"ID {p.factura_id}"
            vals = [
                str(p.id),
                p.numero_presupuesto or "—",
                p.cliente.razon_social,
                p.fecha_emision.strftime("%d/%m/%Y") if p.fecha_emision else "—",
                p.estado.value,
                p.validez_hasta.strftime("%d/%m/%Y") if p.validez_hasta else "—",
                factura_txt,
                formato_moneda(p.calcular_total()),
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setBackground(brush)
                item.setForeground(texto)
                if col == 0:
                    item.setData(ROLE_PRESUPUESTO_ID, p.id)
                    item.setData(ROLE_FACTURA_ID, p.factura_id)
                    item.setData(ROLE_ESTADO, p.estado.value)
                self.tabla.setItem(fila, col, item)
        self._actualizar_botones()

    @staticmethod
    def _color(estado: EstadoPresupuesto) -> QColor:
        return {
            EstadoPresupuesto.BORRADOR: COLOR_BORRADOR,
            EstadoPresupuesto.EMITIDO: COLOR_EMITIDO,
            EstadoPresupuesto.ACEPTADO: COLOR_ACEPTADO,
            EstadoPresupuesto.CONVERTIDO: COLOR_CONVERTIDO,
            EstadoPresupuesto.RECHAZADO: COLOR_RECHAZADO,
        }.get(estado, COLOR_BORRADOR)

    def _fila_seleccionada(self) -> tuple[int | None, int | None, str | None]:
        f = self.tabla.currentRow()
        if f < 0:
            return None, None, None
        item = self.tabla.item(f, 0)
        if not item:
            return None, None, None
        pid = item.data(ROLE_PRESUPUESTO_ID)
        fid = item.data(ROLE_FACTURA_ID)
        estado = item.data(ROLE_ESTADO)
        return (
            int(pid) if pid is not None else None,
            int(fid) if fid is not None else None,
            str(estado) if estado else None,
        )

    def _actualizar_botones(self) -> None:
        _, factura_id, estado = self._fila_seleccionada()
        convertido = estado == EstadoPresupuesto.CONVERTIDO.value
        puede_convertir = estado in (
            EstadoPresupuesto.EMITIDO.value,
            EstadoPresupuesto.ACEPTADO.value,
        )
        self.btn_ver_factura.setEnabled(convertido and factura_id is not None)
        self.btn_convertir.setEnabled(puede_convertir)
        self.btn_convertir.setToolTip(
            "Crea un borrador de factura con las mismas líneas"
            if puede_convertir
            else "Solo presupuestos emitidos o aceptados (no borradores ni rechazados)"
        )
        self.btn_aceptar.setEnabled(estado == EstadoPresupuesto.EMITIDO.value)
        self.btn_rechazar.setEnabled(
            estado
            in (
                EstadoPresupuesto.EMITIDO.value,
                EstadoPresupuesto.ACEPTADO.value,
            )
        )

    def _doble_clic(self) -> None:
        pid, _, _ = self._fila_seleccionada()
        if pid:
            self.editar_borrador.emit(pid)

    def _aceptar(self) -> None:
        pid, _, _ = self._fila_seleccionada()
        if pid is None:
            aviso(self, "Selección", "Seleccione un presupuesto.")
            return
        try:
            p = PresupuestoService.aceptar(pid)
            self.refrescar()
            self.estado_mensaje.emit(f"Presupuesto {p.numero_presupuesto} aceptado.")
            informacion(
                self,
                "Aceptado",
                "Presupuesto marcado como aceptado.\n"
                "Pulse «Convertir en factura» cuando quiera facturar.",
            )
        except Exception as exc:
            error(self, "Error", str(exc))

    def _convertir(self) -> None:
        pid, _, _ = self._fila_seleccionada()
        if pid is None:
            aviso(self, "Selección", "Seleccione un presupuesto.")
            return
        try:
            factura_id = PresupuestoService.convertir_a_factura(pid)
            self.refrescar()
            self.convertido_en_factura.emit(factura_id)
            self.estado_mensaje.emit(
                "Presupuesto convertido — abriendo borrador en Nueva Factura…"
            )
        except Exception as exc:
            error(self, "Error", str(exc))

    def _ver_factura_asociada(self) -> None:
        _, factura_id, estado = self._fila_seleccionada()
        if factura_id is None:
            aviso(self, "Sin factura", "Este presupuesto no tiene factura asociada.")
            return
        if estado != EstadoPresupuesto.CONVERTIDO.value:
            aviso(
                self,
                "No convertido",
                "Solo los presupuestos en estado Convertido tienen factura vinculada.",
            )
            return
        self.ver_factura_asociada.emit(factura_id)
        self.estado_mensaje.emit("Abriendo factura asociada al presupuesto…")

    def _rechazar(self) -> None:
        pid, _, _ = self._fila_seleccionada()
        if pid is None:
            aviso(self, "Selección", "Seleccione un presupuesto.")
            return
        try:
            PresupuestoService.rechazar(pid)
            self.refrescar()
            self.estado_mensaje.emit("Presupuesto rechazado.")
        except Exception as exc:
            error(self, "Error", str(exc))

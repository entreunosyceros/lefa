"""
Pestaña de creación y edición de presupuestos.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemDelegate,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lefa.config import IRPF_OPCIONES, IVA_OPCIONES
from lefa.models import EstadoPresupuesto
from lefa.services.cliente_service import ClienteService
from lefa.services.presupuesto_service import LineaPresupuestoDTO, PresupuestoService
from lefa.services.preferencias_service import PreferenciasService
from lefa.ui.cliente_dialog import ClienteDialog
from lefa.ui.messages import aviso, error, informacion
from lefa.utils import formato_moneda
from lefa.workers.presupuesto_pdf_worker import PresupuestoPDFWorker

COL_DESCRIPCION, COL_CANTIDAD, COL_PRECIO, COL_SUBTOTAL = 0, 1, 2, 3


class NuevoPresupuestoTab(QWidget):
    presupuesto_guardado = pyqtSignal(int)
    presupuesto_emitido = pyqtSignal(int)
    estado_mensaje = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._presupuesto_id: int | None = None
        self._congelado = False
        self._pdf_worker: PresupuestoPDFWorker | None = None
        self._setup_ui()
        self._cargar_clientes()
        self._aplicar_preferencias()
        self._agregar_linea_vacia()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        cabecera = QGroupBox("Datos del presupuesto")
        form = QFormLayout(cabecera)

        self.combo_cliente = QComboBox()
        cliente_row = QHBoxLayout()
        cliente_row.addWidget(self.combo_cliente, 1)
        btn_nuevo = QPushButton("+ Nuevo")
        btn_nuevo.clicked.connect(self._nuevo_cliente)
        cliente_row.addWidget(btn_nuevo)
        form.addRow("Cliente:", cliente_row)

        self.date_validez = QDateEdit()
        self.date_validez.setCalendarPopup(True)
        self.date_validez.setDisplayFormat("dd/MM/yyyy")
        self.date_validez.setDate(QDate.currentDate().addDays(30))
        form.addRow("Válido hasta:", self.date_validez)

        imp_row = QHBoxLayout()
        self.combo_iva = QComboBox()
        for v in IVA_OPCIONES:
            self.combo_iva.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        self.combo_irpf = QComboBox()
        for v in IRPF_OPCIONES:
            self.combo_irpf.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        imp_row.addWidget(QLabel("IVA:"))
        imp_row.addWidget(self.combo_iva)
        imp_row.addSpacing(16)
        imp_row.addWidget(QLabel("IRPF:"))
        imp_row.addWidget(self.combo_irpf)
        imp_row.addStretch()
        form.addRow("Impuestos:", imp_row)
        layout.addWidget(cabecera)

        lineas_g = QGroupBox("Líneas")
        lineas_l = QVBoxLayout(lineas_g)
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(
            ["Descripción", "Cantidad", "Precio Unitario (€)", "Subtotal"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            COL_DESCRIPCION, QHeaderView.ResizeMode.Stretch
        )
        self.tabla.cellChanged.connect(self._on_celda_cambiada)
        lineas_l.addWidget(self.tabla)
        btns = QHBoxLayout()
        btn_add = QPushButton("+ Añadir línea")
        btn_add.clicked.connect(self._agregar_linea_vacia)
        btn_del = QPushButton("− Eliminar línea")
        btn_del.clicked.connect(self._eliminar_linea)
        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        btns.addStretch()
        lineas_l.addLayout(btns)
        layout.addWidget(lineas_g)

        self.lbl_total = QLabel("TOTAL: 0,00 €")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_total)

        acciones = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo presupuesto")
        self.btn_nuevo.clicked.connect(self.reiniciar)
        self.btn_guardar = QPushButton("Guardar borrador")
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_emitir = QPushButton("Emitir presupuesto")
        self.btn_emitir.setStyleSheet(
            "QPushButton { background-color: #5C6BC0; color: white; padding: 8px 16px; "
            "font-weight: bold; border-radius: 4px; }"
        )
        self.btn_emitir.clicked.connect(self._emitir)
        acciones.addWidget(self.btn_nuevo)
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar)
        acciones.addWidget(self.btn_emitir)
        layout.addLayout(acciones)

        self.lbl_estado = QLabel("")
        layout.addWidget(self.lbl_estado)

    def _aplicar_preferencias(self) -> None:
        prefs = PreferenciasService.cargar()
        idx = self.combo_iva.findData(prefs.iva_porcentaje)
        if idx >= 0:
            self.combo_iva.setCurrentIndex(idx)
        idx = self.combo_irpf.findData(prefs.irpf_porcentaje)
        if idx >= 0:
            self.combo_irpf.setCurrentIndex(idx)

    def _cargar_clientes(self, seleccionar_id: int | None = None) -> None:
        sid = seleccionar_id or self._cliente_id()
        self.combo_cliente.clear()
        for c in ClienteService.listar_todos():
            self.combo_cliente.addItem(f"{c.razon_social} ({c.cif_nif})", c.id)
        if sid:
            for i in range(self.combo_cliente.count()):
                if self.combo_cliente.itemData(i) == sid:
                    self.combo_cliente.setCurrentIndex(i)
                    break

    def recargar_clientes(self, seleccionar_id: int | None = None) -> None:
        self._cargar_clientes(seleccionar_id)

    def _cliente_id(self) -> int | None:
        d = self.combo_cliente.currentData(Qt.ItemDataRole.UserRole)
        return int(d) if d is not None else None

    def _iva(self) -> float:
        return float(self.combo_iva.currentData(Qt.ItemDataRole.UserRole))

    def _irpf(self) -> float:
        return float(self.combo_irpf.currentData(Qt.ItemDataRole.UserRole))

    def _validez(self):
        from datetime import date

        qd = self.date_validez.date()
        return date(qd.year(), qd.month(), qd.day())

    def _bloquear_tabla(self, b: bool) -> None:
        self.tabla.blockSignals(b)

    def _agregar_linea_vacia(self) -> None:
        if self._congelado:
            return
        f = self.tabla.rowCount()
        self._bloquear_tabla(True)
        self.tabla.insertRow(f)
        self.tabla.setItem(f, COL_DESCRIPCION, QTableWidgetItem(""))
        self.tabla.setItem(f, COL_CANTIDAD, QTableWidgetItem("1"))
        self.tabla.setItem(f, COL_PRECIO, QTableWidgetItem("0.00"))
        sub = QTableWidgetItem("0,00 €")
        sub.setFlags(sub.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.tabla.setItem(f, COL_SUBTOTAL, sub)
        self._bloquear_tabla(False)
        self._recalcular()

    def _eliminar_linea(self) -> None:
        if self._congelado:
            return
        r = self.tabla.currentRow()
        if r >= 0:
            self.tabla.removeRow(r)
            self._recalcular()

    def _leer_float(self, fila: int, col: int, default: float = 0.0) -> float:
        item = self.tabla.item(fila, col)
        if not item or not item.text().strip():
            return default
        try:
            return float(item.text().strip().replace(",", "."))
        except ValueError:
            return default

    def _leer_lineas(self) -> list[LineaPresupuestoDTO]:
        lineas = []
        for f in range(self.tabla.rowCount()):
            desc = self.tabla.item(f, COL_DESCRIPCION)
            d = desc.text().strip() if desc else ""
            if not d:
                continue
            lineas.append(
                LineaPresupuestoDTO(
                    d,
                    self._leer_float(f, COL_CANTIDAD, 1.0),
                    self._leer_float(f, COL_PRECIO, 0.0),
                )
            )
        return lineas

    def _on_celda_cambiada(self, fila: int, col: int) -> None:
        if col in (COL_CANTIDAD, COL_PRECIO, COL_DESCRIPCION):
            c = self._leer_float(fila, COL_CANTIDAD)
            p = self._leer_float(fila, COL_PRECIO)
            self._bloquear_tabla(True)
            item = self.tabla.item(fila, COL_SUBTOTAL)
            if item:
                item.setText(formato_moneda(c * p))
            self._bloquear_tabla(False)
            self._recalcular()

    def _recalcular(self) -> None:
        from lefa.services.factura_service import FacturaService, LineaFacturaDTO

        dtos = [
            LineaFacturaDTO(l.descripcion, l.cantidad, l.precio_unitario)
            for l in self._leer_lineas()
        ]
        t = FacturaService.calcular_totales(dtos, self._iva(), self._irpf())
        self.lbl_total.setText(f"TOTAL: {formato_moneda(t.total)}")

    def _commit_tabla(self) -> None:
        idx = self.tabla.currentIndex()
        if idx.isValid():
            d = self.tabla.itemDelegate(idx)
            w = self.tabla.indexWidget(idx)
            if w:
                d.commitData(w)
                d.closeEditor(w, QAbstractItemDelegate.EndEditHint.NoHint)
        app = QApplication.instance()
        if app:
            app.processEvents()

    def _validar(self) -> bool:
        self._commit_tabla()
        if self._cliente_id() is None:
            aviso(self, "Validación", "Seleccione un cliente.")
            return False
        if not self._leer_lineas():
            aviso(self, "Validación", "Añada al menos una línea con descripción.")
            return False
        return True

    def _guardar(self) -> None:
        if self._congelado or not self._validar():
            return
        try:
            p = PresupuestoService.guardar_borrador(
                self._cliente_id(),
                self._leer_lineas(),
                self._iva(),
                self._irpf(),
                self._presupuesto_id,
                self._validez(),
            )
            self._presupuesto_id = p.id
            self.lbl_estado.setText(f"Borrador guardado (ID: {p.id})")
            self.presupuesto_guardado.emit(p.id)
            self._generar_pdf(p.id)
        except Exception as exc:
            error(self, "Error", str(exc))

    def _emitir(self) -> None:
        if self._congelado or not self._validar():
            return
        try:
            self._commit_tabla()
            p = PresupuestoService.guardar_borrador(
                self._cliente_id(),
                self._leer_lineas(),
                self._iva(),
                self._irpf(),
                self._presupuesto_id,
                self._validez(),
            )
            self._presupuesto_id = p.id
            emitido = PresupuestoService.emitir_presupuesto(p.id)
            self._congelar(emitido.numero_presupuesto or "")
            self.presupuesto_emitido.emit(emitido.id)
            self._generar_pdf(emitido.id)
            informacion(
                self,
                "Presupuesto emitido",
                f"Presupuesto {emitido.numero_presupuesto} listo.\n"
                "Cuando el cliente lo acepte, conviértalo en factura desde el listado.",
            )
        except Exception as exc:
            error(self, "Error", str(exc))

    def _congelar(self, numero: str) -> None:
        self._congelado = True
        self.combo_cliente.setEnabled(False)
        self.date_validez.setEnabled(False)
        self.combo_iva.setEnabled(False)
        self.combo_irpf.setEnabled(False)
        self.tabla.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.btn_emitir.setEnabled(False)
        self.lbl_estado.setText(f"Presupuesto {numero} emitido")

    def reiniciar(self) -> None:
        self._presupuesto_id = None
        self._congelado = False
        self.combo_cliente.setEnabled(True)
        self.date_validez.setEnabled(True)
        self.combo_iva.setEnabled(True)
        self.combo_irpf.setEnabled(True)
        self.tabla.setEnabled(True)
        self.btn_guardar.setEnabled(True)
        self.btn_emitir.setEnabled(True)
        self.tabla.setRowCount(0)
        self._aplicar_preferencias()
        self.date_validez.setDate(QDate.currentDate().addDays(30))
        prefs = PreferenciasService.cargar()
        if prefs.ultimo_cliente_id:
            self._cargar_clientes(prefs.ultimo_cliente_id)
        self.lbl_estado.setText("")
        self._agregar_linea_vacia()

    def cargar_presupuesto(self, presupuesto_id: int) -> None:
        p = PresupuestoService.obtener_por_id(presupuesto_id)
        if not p:
            aviso(self, "Error", "Presupuesto no encontrado.")
            return
        self.reiniciar()
        self._presupuesto_id = p.id
        for i in range(self.combo_cliente.count()):
            if self.combo_cliente.itemData(i) == p.cliente_id:
                self.combo_cliente.setCurrentIndex(i)
                break
        idx = self.combo_iva.findData(p.porc_iva)
        if idx >= 0:
            self.combo_iva.setCurrentIndex(idx)
        idx = self.combo_irpf.findData(p.porc_irpf)
        if idx >= 0:
            self.combo_irpf.setCurrentIndex(idx)
        if p.validez_hasta:
            v = p.validez_hasta
            self.date_validez.setDate(QDate(v.year, v.month, v.day))
        self.tabla.setRowCount(0)
        for linea in p.lineas:
            self._agregar_linea_vacia()
            f = self.tabla.rowCount() - 1
            self.tabla.item(f, COL_DESCRIPCION).setText(linea.descripcion)
            self.tabla.item(f, COL_CANTIDAD).setText(str(linea.cantidad))
            self.tabla.item(f, COL_PRECIO).setText(f"{linea.precio_unitario:.2f}")
            self._on_celda_cambiada(f, COL_PRECIO)
        if p.estado != EstadoPresupuesto.BORRADOR:
            self._congelar(p.numero_presupuesto or "")

    def _nuevo_cliente(self) -> None:
        dlg = ClienteDialog(self)
        if dlg.exec() and dlg.cliente_id:
            self.recargar_clientes(dlg.cliente_id)

    def _generar_pdf(self, presupuesto_id: int) -> None:
        if self._pdf_worker and self._pdf_worker.isRunning():
            self._pdf_worker.wait(3000)
        self.estado_mensaje.emit("Generando PDF del presupuesto…")
        self._pdf_worker = PresupuestoPDFWorker(presupuesto_id, self)
        self._pdf_worker.finished_ok.connect(
            lambda r: self.estado_mensaje.emit(f"PDF presupuesto: {r.name}")
        )
        self._pdf_worker.finished_error.connect(
            lambda m: self.estado_mensaje.emit(f"Error PDF: {m}")
        )
        self._pdf_worker.start()

    def detener_workers(self) -> None:
        if self._pdf_worker and self._pdf_worker.isRunning():
            self._pdf_worker.wait(2000)

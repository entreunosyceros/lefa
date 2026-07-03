"""
Pestaña 'Nueva Factura' — formulario operativo de alta/edición.

Prioriza velocidad: totales recalculados en tiempo real sin bloquear la UI.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QDate, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemDelegate,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
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
from lefa.models import EstadoFactura
from lefa.services.cliente_service import ClienteService
from lefa.services.factura_service import FacturaService, LineaFacturaDTO
from lefa.services.plantilla_service import PlantillaService
from lefa.services.preferencias_service import PreferenciasService
from lefa.services.servicio_service import ServicioService
from lefa.ui.cliente_dialog import ClienteDialog
from lefa.ui.messages import aviso, error, informacion
from lefa.ui.plantillas_dialog import PlantillasDialog
from lefa.ui.servicios_dialog import ServiciosDialog
from lefa.ui.smtp_config_dialog import SmtpConfigDialog
from lefa.utils import formato_moneda
from lefa.workers.pdf_worker import PDFWorker
from lefa.workers.smtp_worker import SMTPWorker

# Índices de columnas en la tabla de líneas
COL_DESCRIPCION = 0
COL_CANTIDAD = 1
COL_PRECIO = 2
COL_SUBTOTAL = 3


class NuevaFacturaTab(QWidget):
    """
    Formulario de creación y edición de facturas en borrador.

    Emite señales hacia la ventana principal para refrescar el listado
    y coordinar workers en segundo plano.
    """

    factura_guardada = pyqtSignal(int)  # factura_id
    factura_emitida = pyqtSignal(int)  # factura_id
    factura_enviada = pyqtSignal(int)  # factura_id
    estado_mensaje = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._factura_id: int | None = None
        self._congelada = False
        self._pdf_worker: PDFWorker | None = None
        self._smtp_worker: SMTPWorker | None = None
        self._setup_ui()
        self._cargar_clientes()
        self._cargar_plantillas()
        self._cargar_servicios()
        self.aplicar_preferencias()
        self._seleccionar_ultimo_cliente()
        self._agregar_linea_vacia()
        self._recalcular_totales()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Cabecera: cliente e impuestos ---
        cabecera = QGroupBox("Datos generales")
        form = QFormLayout(cabecera)

        self.combo_cliente = QComboBox()
        self.combo_cliente.setMinimumWidth(300)
        cliente_layout = QHBoxLayout()
        cliente_layout.addWidget(self.combo_cliente, stretch=1)
        self.btn_nuevo_cliente = QPushButton("+ Nuevo")
        self.btn_nuevo_cliente.setToolTip("Crear un cliente nuevo")
        self.btn_nuevo_cliente.clicked.connect(self._nuevo_cliente)
        cliente_layout.addWidget(self.btn_nuevo_cliente)
        form.addRow("Cliente:", cliente_layout)

        self.combo_serie = QComboBox()
        self._cargar_series()
        form.addRow("Serie:", self.combo_serie)

        self.date_vencimiento = QDateEdit()
        self.date_vencimiento.setCalendarPopup(True)
        self.date_vencimiento.setDisplayFormat("dd/MM/yyyy")
        self.date_vencimiento.setSpecialValueText("Sin vencimiento")
        self.date_vencimiento.setMinimumDate(QDate(2000, 1, 1))
        self._aplicar_vencimiento_por_defecto()
        form.addRow("Vencimiento:", self.date_vencimiento)

        impuestos_layout = QHBoxLayout()
        self.combo_iva = QComboBox()
        for v in IVA_OPCIONES:
            self.combo_iva.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        self.combo_iva.currentIndexChanged.connect(self._recalcular_totales)

        self.combo_irpf = QComboBox()
        for v in IRPF_OPCIONES:
            self.combo_irpf.addItem(f"{int(v) if v == int(v) else v:g} %", v)
        self.combo_irpf.currentIndexChanged.connect(self._recalcular_totales)

        impuestos_layout.addWidget(QLabel("IVA:"))
        impuestos_layout.addWidget(self.combo_iva)
        impuestos_layout.addSpacing(20)
        impuestos_layout.addWidget(QLabel("IRPF:"))
        impuestos_layout.addWidget(self.combo_irpf)
        impuestos_layout.addStretch()
        form.addRow("Impuestos:", impuestos_layout)

        layout.addWidget(cabecera)

        # --- Tabla dinámica de líneas ---
        lineas_group = QGroupBox("Líneas de factura")
        lineas_layout = QVBoxLayout(lineas_group)

        self.tabla_lineas = QTableWidget(0, 4)
        self.tabla_lineas.setHorizontalHeaderLabels(
            ["Descripción", "Cantidad", "Precio Unitario (€)", "Subtotal"]
        )
        header = self.tabla_lineas.horizontalHeader()
        header.setSectionResizeMode(COL_DESCRIPCION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_CANTIDAD, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_PRECIO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_SUBTOTAL, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_lineas.cellChanged.connect(self._on_celda_cambiada)
        lineas_layout.addWidget(self.tabla_lineas)

        btn_lineas = QHBoxLayout()
        self.combo_servicio = QComboBox()
        self.combo_servicio.setMinimumWidth(180)
        self.btn_aplicar_servicio = QPushButton("Añadir servicio")
        self.btn_aplicar_servicio.clicked.connect(self._aplicar_servicio)
        self.btn_gestionar_servicios = QPushButton("Gestionar servicios…")
        self.btn_gestionar_servicios.setToolTip(
            "Crear, editar o eliminar servicios del catálogo"
        )
        self.btn_gestionar_servicios.clicked.connect(self._gestionar_servicios)
        self.combo_plantilla = QComboBox()
        self.combo_plantilla.setMinimumWidth(220)
        self.btn_aplicar_plantilla = QPushButton("Añadir plantilla")
        self.btn_aplicar_plantilla.clicked.connect(self._aplicar_plantilla)
        self.btn_gestionar_plantillas = QPushButton("Gestionar plantillas…")
        self.btn_gestionar_plantillas.setToolTip(
            "Crear, editar o eliminar plantillas de líneas"
        )
        self.btn_gestionar_plantillas.clicked.connect(self._gestionar_plantillas)
        self.btn_agregar_linea = QPushButton("+ Añadir línea")
        self.btn_agregar_linea.clicked.connect(self._agregar_linea_vacia)
        self.btn_eliminar_linea = QPushButton("− Eliminar línea")
        self.btn_eliminar_linea.clicked.connect(self._eliminar_linea_seleccionada)
        btn_lineas.addWidget(self.combo_servicio)
        btn_lineas.addWidget(self.btn_aplicar_servicio)
        btn_lineas.addWidget(self.btn_gestionar_servicios)
        btn_lineas.addWidget(self.combo_plantilla)
        btn_lineas.addWidget(self.btn_aplicar_plantilla)
        btn_lineas.addWidget(self.btn_gestionar_plantillas)
        btn_lineas.addWidget(self.btn_agregar_linea)
        btn_lineas.addWidget(self.btn_eliminar_linea)
        btn_lineas.addStretch()
        lineas_layout.addLayout(btn_lineas)

        layout.addWidget(lineas_group)

        # --- Totales grandes (actualización instantánea) ---
        totales_group = QGroupBox("Resumen")
        totales_layout = QHBoxLayout(totales_group)

        font_grande = QFont()
        font_grande.setPointSize(14)
        font_grande.setBold(True)

        self.lbl_subtotal = self._crear_label_total("Subtotal:", font_grande)
        self.lbl_iva = self._crear_label_total("IVA:", font_grande)
        self.lbl_irpf = self._crear_label_total("IRPF:", font_grande)
        self.lbl_total = self._crear_label_total("TOTAL:", font_grande)

        totales_layout.addWidget(self.lbl_subtotal)
        totales_layout.addWidget(self.lbl_iva)
        totales_layout.addWidget(self.lbl_irpf)
        totales_layout.addStretch()
        totales_layout.addWidget(self.lbl_total)

        layout.addWidget(totales_group)

        # --- Botones de acción ---
        acciones = QHBoxLayout()
        self.btn_nueva = QPushButton("Nueva factura")
        self.btn_nueva.clicked.connect(self.reiniciar_formulario)

        self.btn_guardar = QPushButton("Guardar como Borrador")
        self.btn_guardar.setStyleSheet(
            "QPushButton { background-color: #78909C; color: white; padding: 10px 20px; "
            "font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #607D8B; }"
        )
        self.btn_guardar.clicked.connect(self._guardar_borrador)

        self.btn_emitir = QPushButton("Emitir Factura")
        self.btn_emitir.setStyleSheet(
            "QPushButton { background-color: #FF8F00; color: white; padding: 10px 20px; "
            "font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.btn_emitir.clicked.connect(self._emitir_factura)

        self.btn_enviar_email = QPushButton("Enviar por email")
        self.btn_enviar_email.clicked.connect(self._enviar_email)
        self.btn_enviar_email.setEnabled(False)

        self.btn_abrir_carpeta = QPushButton("Abrir carpeta PDFs")
        self.btn_abrir_carpeta.setToolTip(
            "Abre la carpeta donde LEFA guarda los PDF de facturas emitidas"
        )
        self.btn_abrir_carpeta.clicked.connect(self._abrir_carpeta_pdfs)
        self.btn_abrir_carpeta.setEnabled(False)

        acciones.addWidget(self.btn_nueva)
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar)
        acciones.addWidget(self.btn_emitir)
        acciones.addWidget(self.btn_abrir_carpeta)
        acciones.addWidget(self.btn_enviar_email)

        layout.addLayout(acciones)

        self.lbl_estado_form = QLabel("")
        self.lbl_estado_form.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_estado_form)

    @staticmethod
    def _crear_label_total(prefijo: str, font: QFont) -> QLabel:
        lbl = QLabel(f"{prefijo} 0,00 €")
        lbl.setFont(font)
        return lbl

    def _obtener_iva(self) -> float:
        v = self.combo_iva.currentData(Qt.ItemDataRole.UserRole)
        return float(v) if v is not None else 21.0

    def _obtener_irpf(self) -> float:
        v = self.combo_irpf.currentData(Qt.ItemDataRole.UserRole)
        return float(v) if v is not None else 15.0

    def _establecer_iva(self, valor: float) -> None:
        idx = self.combo_iva.findData(valor)
        if idx >= 0:
            self.combo_iva.setCurrentIndex(idx)

    def _establecer_irpf(self, valor: float) -> None:
        idx = self.combo_irpf.findData(valor)
        if idx >= 0:
            self.combo_irpf.setCurrentIndex(idx)

    def _cargar_servicios(self) -> None:
        self.combo_servicio.clear()
        self.combo_servicio.addItem("- Servicio -", None)
        for servicio in ServicioService.listar_todos():
            self.combo_servicio.addItem(
                f"{servicio.nombre} ({servicio.precio_unitario:.2f} €)",
                servicio.id,
            )

    def _gestionar_servicios(self) -> None:
        dlg = ServiciosDialog(self)
        dlg.servicios_actualizados.connect(self._cargar_servicios)
        dlg.exec()

    def _aplicar_servicio(self) -> None:
        if self._congelada:
            return
        servicio_id = self.combo_servicio.currentData(Qt.ItemDataRole.UserRole)
        if servicio_id is None:
            aviso(self, "Servicio", "Seleccione un servicio del catálogo.")
            return
        servicios = {s.id: s for s in ServicioService.listar_todos()}
        servicio = servicios.get(servicio_id)
        if servicio is None:
            return

        self._establecer_iva(servicio.porc_iva)
        fila = self.tabla_lineas.rowCount()
        self._bloquear_senales_tabla(True)
        self.tabla_lineas.insertRow(fila)
        self.tabla_lineas.setItem(fila, COL_DESCRIPCION, QTableWidgetItem(servicio.descripcion))
        self.tabla_lineas.setItem(fila, COL_CANTIDAD, QTableWidgetItem(str(servicio.cantidad)))
        self.tabla_lineas.setItem(
            fila, COL_PRECIO, QTableWidgetItem(f"{servicio.precio_unitario:.2f}")
        )
        subtotal_item = QTableWidgetItem(
            formato_moneda(servicio.cantidad * servicio.precio_unitario)
        )
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.tabla_lineas.setItem(fila, COL_SUBTOTAL, subtotal_item)
        self._bloquear_senales_tabla(False)
        self._recalcular_totales()
        self.combo_servicio.setCurrentIndex(0)

    def _cargar_series(self) -> None:
        serie_actual = self.combo_serie.currentText() if self.combo_serie.count() else None
        self.combo_serie.clear()
        for serie in PreferenciasService.obtener_series():
            self.combo_serie.addItem(serie)
        if serie_actual:
            idx = self.combo_serie.findText(serie_actual)
            if idx >= 0:
                self.combo_serie.setCurrentIndex(idx)

    def _aplicar_vencimiento_por_defecto(self) -> None:
        prefs = PreferenciasService.cargar()
        if prefs.dias_vencimiento > 0:
            self.date_vencimiento.setDate(
                QDate.currentDate().addDays(prefs.dias_vencimiento)
            )
            self.date_vencimiento.setEnabled(True)
        else:
            self.date_vencimiento.setDate(QDate.currentDate())
            self.date_vencimiento.setEnabled(True)

    def _leer_fecha_vencimiento(self):
        from datetime import date

        qd = self.date_vencimiento.date()
        if not qd.isValid():
            return None
        return date(qd.year(), qd.month(), qd.day())

    def _seleccionar_ultimo_cliente(self) -> None:
        prefs = PreferenciasService.cargar()
        if prefs.ultimo_cliente_id is not None:
            self._seleccionar_cliente(prefs.ultimo_cliente_id)

    def _cargar_clientes(self, seleccionar_id: int | None = None) -> None:
        seleccion_actual = seleccionar_id or self._obtener_cliente_id()
        self.combo_cliente.clear()
        for cliente in ClienteService.listar_todos():
            self.combo_cliente.addItem(
                f"{cliente.razon_social} ({cliente.cif_nif})",
                int(cliente.id),
            )
        if seleccion_actual is not None:
            self._seleccionar_cliente(seleccion_actual)

    def recargar_clientes(self, seleccionar_id: int | None = None) -> None:
        """Actualiza el combo tras crear o editar clientes."""
        self._cargar_clientes(seleccionar_id=seleccionar_id)

    def _seleccionar_cliente(self, cliente_id: int) -> None:
        for i in range(self.combo_cliente.count()):
            if self.combo_cliente.itemData(i, Qt.ItemDataRole.UserRole) == cliente_id:
                self.combo_cliente.setCurrentIndex(i)
                break

    def aplicar_preferencias(self) -> None:
        """Aplica IVA/IRPF por defecto y series desde preferencias."""
        prefs = PreferenciasService.cargar()
        self._establecer_iva(prefs.iva_porcentaje)
        self._establecer_irpf(prefs.irpf_porcentaje)
        self._cargar_series()
        if self._factura_id is None and not self._congelada:
            self._aplicar_vencimiento_por_defecto()

    def _cargar_plantillas(self) -> None:
        self.combo_plantilla.clear()
        self.combo_plantilla.addItem("- Seleccionar plantilla -", None)
        for plantilla in PlantillaService.listar_todas():
            self.combo_plantilla.addItem(plantilla.nombre, plantilla.id)

    def _gestionar_plantillas(self) -> None:
        dlg = PlantillasDialog(self)
        dlg.plantillas_actualizadas.connect(self._cargar_plantillas)
        dlg.exec()

    def _aplicar_plantilla(self) -> None:
        if self._congelada:
            return
        plantilla_id = self.combo_plantilla.currentData(Qt.ItemDataRole.UserRole)
        if plantilla_id is None:
            aviso(self, "Plantilla", "Seleccione una plantilla de la lista.")
            return
        plantillas = {p.id: p for p in PlantillaService.listar_todas()}
        plantilla = plantillas.get(plantilla_id)
        if plantilla is None:
            return

        fila = self.tabla_lineas.rowCount()
        self._bloquear_senales_tabla(True)
        self.tabla_lineas.insertRow(fila)
        self.tabla_lineas.setItem(fila, COL_DESCRIPCION, QTableWidgetItem(plantilla.descripcion))
        self.tabla_lineas.setItem(fila, COL_CANTIDAD, QTableWidgetItem(str(plantilla.cantidad)))
        self.tabla_lineas.setItem(
            fila, COL_PRECIO, QTableWidgetItem(f"{plantilla.precio_unitario:.2f}")
        )
        subtotal_item = QTableWidgetItem(formato_moneda(plantilla.cantidad * plantilla.precio_unitario))
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.tabla_lineas.setItem(fila, COL_SUBTOTAL, subtotal_item)
        self._bloquear_senales_tabla(False)
        self._recalcular_totales()
        self.combo_plantilla.setCurrentIndex(0)

    def _nuevo_cliente(self) -> None:
        dialogo = ClienteDialog(self)
        if dialogo.exec() and dialogo.cliente_id is not None:
            self.recargar_clientes(seleccionar_id=dialogo.cliente_id)
            self.estado_mensaje.emit("Cliente creado y seleccionado.")

    def _commit_edicion_tabla(self) -> None:
        """
        Confirma el texto del editor de celda abierto antes de leer la tabla.

        Si el usuario pulsa Guardar/Emitir mientras edita una celda, Qt puede
        no haber volcado aún el texto al QTableWidgetItem.
        """
        index = self.tabla_lineas.currentIndex()
        if index.isValid():
            delegate = self.tabla_lineas.itemDelegateForIndex(index)
            editor = self.tabla_lineas.indexWidget(index)
            if editor is None:
                editor = self.tabla_lineas.focusWidget()
                if editor is self.tabla_lineas:
                    editor = None
            if editor is not None:
                delegate.commitData(editor)
                delegate.closeEditor(
                    editor,
                    QAbstractItemDelegate.EndEditHint.SubmitModelCache,
                )
        self.tabla_lineas.clearFocus()
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def _bloquear_senales_tabla(self, bloquear: bool) -> None:
        if bloquear:
            self.tabla_lineas.blockSignals(True)
        else:
            self.tabla_lineas.blockSignals(False)

    def _agregar_linea_vacia(self) -> None:
        if self._congelada:
            return
        fila = self.tabla_lineas.rowCount()
        self._bloquear_senales_tabla(True)
        self.tabla_lineas.insertRow(fila)

        self.tabla_lineas.setItem(fila, COL_DESCRIPCION, QTableWidgetItem(""))
        self.tabla_lineas.setItem(fila, COL_CANTIDAD, QTableWidgetItem("1"))
        self.tabla_lineas.setItem(fila, COL_PRECIO, QTableWidgetItem("0.00"))

        subtotal_item = QTableWidgetItem("0,00 €")
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.tabla_lineas.setItem(fila, COL_SUBTOTAL, subtotal_item)

        self._bloquear_senales_tabla(False)
        self._recalcular_totales()

    def _eliminar_linea_seleccionada(self) -> None:
        if self._congelada:
            return
        fila = self.tabla_lineas.currentRow()
        if fila >= 0:
            self.tabla_lineas.removeRow(fila)
            self._recalcular_totales()

    def _on_celda_cambiada(self, fila: int, columna: int) -> None:
        if columna in (COL_CANTIDAD, COL_PRECIO, COL_DESCRIPCION):
            self._actualizar_subtotal_fila(fila)
            self._recalcular_totales()

    def _actualizar_subtotal_fila(self, fila: int) -> None:
        cantidad = self._leer_float_celda(fila, COL_CANTIDAD, default=0.0)
        precio = self._leer_float_celda(fila, COL_PRECIO, default=0.0)
        subtotal = round(cantidad * precio, 2)

        self._bloquear_senales_tabla(True)
        item = self.tabla_lineas.item(fila, COL_SUBTOTAL)
        if item is None:
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_lineas.setItem(fila, COL_SUBTOTAL, item)
        item.setText(formato_moneda(subtotal))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._bloquear_senales_tabla(False)

    def _leer_float_celda(self, fila: int, columna: int, default: float = 0.0) -> float:
        item = self.tabla_lineas.item(fila, columna)
        if item is None or not item.text().strip():
            return default
        texto = item.text().strip().replace("€", "").replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return default

    def _leer_lineas_formulario(self) -> list[LineaFacturaDTO]:
        lineas: list[LineaFacturaDTO] = []
        for fila in range(self.tabla_lineas.rowCount()):
            desc_item = self.tabla_lineas.item(fila, COL_DESCRIPCION)
            descripcion = desc_item.text().strip() if desc_item else ""
            if not descripcion:
                continue
            lineas.append(
                LineaFacturaDTO(
                    descripcion=descripcion,
                    cantidad=self._leer_float_celda(fila, COL_CANTIDAD, 1.0),
                    precio_unitario=self._leer_float_celda(fila, COL_PRECIO, 0.0),
                )
            )
        return lineas

    def _recalcular_totales(self) -> None:
        """Cálculo en memoria — O(n) sobre líneas, sin I/O."""
        lineas = self._leer_lineas_formulario()
        totales = FacturaService.calcular_totales(
            lineas, self._obtener_iva(), self._obtener_irpf()
        )
        self.lbl_subtotal.setText(f"Subtotal: {formato_moneda(totales.subtotal)}")
        self.lbl_iva.setText(f"IVA: {formato_moneda(totales.iva)}")
        self.lbl_irpf.setText(f"IRPF: −{formato_moneda(totales.irpf)}")
        self.lbl_total.setText(f"TOTAL: {formato_moneda(totales.total)}")

    def _obtener_cliente_id(self) -> int | None:
        cliente_id = self.combo_cliente.currentData(Qt.ItemDataRole.UserRole)
        if cliente_id is None:
            return None
        return int(cliente_id)

    def _mostrar_error_validacion(self, mensaje: str) -> None:
        """Feedback visible en el formulario y en la barra de estado."""
        self.lbl_estado_form.setStyleSheet("color: #c62828; font-weight: bold;")
        self.lbl_estado_form.setText(mensaje)
        self.estado_mensaje.emit(mensaje)
        aviso(self, "Validación", mensaje)

    def _validar_formulario(self) -> bool:
        self._commit_edicion_tabla()
        if self._obtener_cliente_id() is None:
            self._mostrar_error_validacion("Seleccione un cliente.")
            return False
        lineas = self._leer_lineas_formulario()
        if not lineas:
            self._mostrar_error_validacion(
                "Añada al menos una línea con descripción."
            )
            return False
        self.lbl_estado_form.setStyleSheet("color: #666; font-style: italic;")
        return True

    def _guardar_borrador(self) -> None:
        if self._congelada:
            informacion(
                self,
                "Factura congelada",
                "Esta factura ya fue emitida y no puede modificarse.",
            )
            return
        if not self._validar_formulario():
            return

        try:
            self._commit_edicion_tabla()
            factura = FacturaService.guardar_borrador(
                cliente_id=self._obtener_cliente_id(),
                lineas=self._leer_lineas_formulario(),
                porc_iva=self._obtener_iva(),
                porc_irpf=self._obtener_irpf(),
                factura_id=self._factura_id,
                serie=self.combo_serie.currentText(),
                fecha_vencimiento=self._leer_fecha_vencimiento(),
            )
            self._factura_id = factura.id
            self.lbl_estado_form.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self.lbl_estado_form.setText(f"Borrador guardado (ID: {factura.id})")
            self.estado_mensaje.emit("Borrador guardado correctamente.")
            self.factura_guardada.emit(factura.id)
            self._iniciar_generacion_pdf(factura.id)
        except Exception as exc:
            error(self, "Error", str(exc))

    def _emitir_factura(self) -> None:
        if self._congelada:
            informacion(
                self,
                "Factura congelada",
                "Esta factura ya fue emitida y no puede volver a emitirse.",
            )
            return
        if not self._validar_formulario():
            return

        try:
            # Primero persistir borrador, luego emitir en transacción separada
            self._commit_edicion_tabla()
            factura = FacturaService.guardar_borrador(
                cliente_id=self._obtener_cliente_id(),
                lineas=self._leer_lineas_formulario(),
                porc_iva=self._obtener_iva(),
                porc_irpf=self._obtener_irpf(),
                factura_id=self._factura_id,
                serie=self.combo_serie.currentText(),
                fecha_vencimiento=self._leer_fecha_vencimiento(),
            )
            self._factura_id = factura.id

            factura_emitida = FacturaService.emitir_factura(factura.id)
            self._congelar_formulario(factura_emitida.numero_factura)
            self.lbl_estado_form.setText(
                f"Factura emitida: {factura_emitida.numero_factura}"
            )
            self.estado_mensaje.emit(
                f"Factura {factura_emitida.numero_factura} emitida correctamente."
            )
            self.factura_emitida.emit(factura_emitida.id)
            self._iniciar_generacion_pdf(factura_emitida.id)
        except Exception as exc:
            error(self, "Error al emitir", str(exc))

    def _congelar_formulario(self, numero_factura: str) -> None:
        """Deshabilita todos los controles tras la emisión."""
        self._congelada = True
        self.combo_cliente.setEnabled(False)
        self.combo_serie.setEnabled(False)
        self.date_vencimiento.setEnabled(False)
        self.combo_iva.setEnabled(False)
        self.combo_irpf.setEnabled(False)
        self.tabla_lineas.setEnabled(False)
        self.combo_servicio.setEnabled(False)
        self.btn_aplicar_servicio.setEnabled(False)
        self.btn_gestionar_servicios.setEnabled(False)
        self.combo_plantilla.setEnabled(False)
        self.btn_aplicar_plantilla.setEnabled(False)
        self.btn_gestionar_plantillas.setEnabled(False)
        self.btn_agregar_linea.setEnabled(False)
        self.btn_eliminar_linea.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.btn_emitir.setEnabled(False)
        self.btn_abrir_carpeta.setEnabled(True)
        self.btn_enviar_email.setEnabled(True)
        self.lbl_estado_form.setText(
            f"Factura {numero_factura} emitida - formulario bloqueado"
        )

    def reiniciar_formulario(self) -> None:
        """Limpia el formulario para crear una nueva factura."""
        self._factura_id = None
        self._congelada = False
        self.combo_cliente.setEnabled(True)
        self.combo_serie.setEnabled(True)
        self.date_vencimiento.setEnabled(True)
        self.combo_iva.setEnabled(True)
        self.combo_irpf.setEnabled(True)
        self.aplicar_preferencias()
        self.tabla_lineas.setEnabled(True)
        self.tabla_lineas.setRowCount(0)
        self.combo_servicio.setEnabled(True)
        self.btn_aplicar_servicio.setEnabled(True)
        self.btn_gestionar_servicios.setEnabled(True)
        self.combo_plantilla.setEnabled(True)
        self.btn_aplicar_plantilla.setEnabled(True)
        self.btn_gestionar_plantillas.setEnabled(True)
        self.btn_agregar_linea.setEnabled(True)
        self.btn_eliminar_linea.setEnabled(True)
        self.btn_guardar.setEnabled(True)
        self.btn_emitir.setEnabled(True)
        self.btn_abrir_carpeta.setEnabled(False)
        self.btn_enviar_email.setEnabled(False)
        self.lbl_estado_form.setText("")
        self._aplicar_vencimiento_por_defecto()
        self._seleccionar_ultimo_cliente()
        self._agregar_linea_vacia()

    def cargar_factura(self, factura_id: int) -> None:
        """Carga una factura existente en el formulario (solo borradores editables)."""
        factura = FacturaService.obtener_por_id(factura_id)
        if factura is None:
            aviso(self, "Error", "Factura no encontrada.")
            return

        self.reiniciar_formulario()
        self._factura_id = factura.id

        # Seleccionar cliente
        for i in range(self.combo_cliente.count()):
            if self.combo_cliente.itemData(i) == factura.cliente_id:
                self.combo_cliente.setCurrentIndex(i)
                break

        self._establecer_iva(factura.porc_iva)
        self._establecer_irpf(factura.porc_irpf)

        idx_serie = self.combo_serie.findText(factura.serie)
        if idx_serie >= 0:
            self.combo_serie.setCurrentIndex(idx_serie)
        elif factura.serie:
            self.combo_serie.addItem(factura.serie)
            self.combo_serie.setCurrentText(factura.serie)

        if factura.fecha_vencimiento:
            fv = factura.fecha_vencimiento
            self.date_vencimiento.setDate(QDate(fv.year, fv.month, fv.day))
        else:
            self._aplicar_vencimiento_por_defecto()

        self.tabla_lineas.setRowCount(0)
        for linea in factura.lineas:
            fila = self.tabla_lineas.rowCount()
            self._bloquear_senales_tabla(True)
            self.tabla_lineas.insertRow(fila)
            self.tabla_lineas.setItem(fila, COL_DESCRIPCION, QTableWidgetItem(linea.descripcion))
            self.tabla_lineas.setItem(fila, COL_CANTIDAD, QTableWidgetItem(str(linea.cantidad)))
            self.tabla_lineas.setItem(
                fila, COL_PRECIO, QTableWidgetItem(f"{linea.precio_unitario:.2f}")
            )
            subtotal_item = QTableWidgetItem(formato_moneda(linea.subtotal))
            subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            subtotal_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabla_lineas.setItem(fila, COL_SUBTOTAL, subtotal_item)
            self._bloquear_senales_tabla(False)

        self._recalcular_totales()

        if factura.estado == EstadoFactura.BORRADOR:
            if factura.es_rectificativa and factura.factura_rectificada:
                orig = factura.factura_rectificada
                self.lbl_estado_form.setStyleSheet("color: #c62828; font-weight: bold;")
                self.lbl_estado_form.setText(
                    f"Rectificativa de {orig.numero_factura} — ajuste líneas y emita"
                )
            else:
                self.lbl_estado_form.setText(f"Editando borrador (ID: {factura.id})")
        elif factura.estado == EstadoFactura.EMITIDA:
            self._congelar_formulario(factura.numero_factura or "")
            self.btn_enviar_email.setEnabled(True)
        elif factura.estado == EstadoFactura.COBRADA:
            self._congelar_formulario(factura.numero_factura or "")
            self.btn_enviar_email.setEnabled(False)

    # --- Workers asíncronos ---

    def _iniciar_generacion_pdf(self, factura_id: int) -> None:
        if self._pdf_worker and self._pdf_worker.isRunning():
            self._pdf_worker.wait(5_000)

        self.estado_mensaje.emit("Generando PDF en segundo plano...")
        self._pdf_worker = PDFWorker(factura_id, self)
        self._pdf_worker.finished_ok.connect(self._on_pdf_generado)
        self._pdf_worker.finished_error.connect(self._on_pdf_error)
        self._pdf_worker.start()

    def _on_pdf_generado(self, resultado) -> None:
        if isinstance(resultado, dict):
            mensaje = f"PDF: {resultado['pdf'].name}"
            if resultado.get("xml"):
                mensaje += f" | Facturae: {resultado['xml'].name}"
        else:
            mensaje = f"PDF guardado: {resultado}"
        self.estado_mensaje.emit(mensaje)

    def _on_pdf_error(self, mensaje: str) -> None:
        self.estado_mensaje.emit(f"Error PDF: {mensaje}")

    def _abrir_carpeta_pdfs(self) -> None:
        try:
            carpeta = PreferenciasService.obtener_carpeta_pdf()
            carpeta.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(carpeta)))
        except Exception as exc:
            error(self, "No se pudo abrir la carpeta", str(exc))

    def _enviar_email(self) -> None:
        if self._factura_id is None:
            return
        if not SmtpConfigDialog.esta_configurado():
            aviso(
                self,
                "Correo no configurado",
                "Configure una cuenta SMTP antes de enviar facturas.",
            )
            dialogo = SmtpConfigDialog(self)
            if not dialogo.exec():
                return
            if not SmtpConfigDialog.esta_configurado():
                return

        if self._smtp_worker and self._smtp_worker.isRunning():
            return

        self.estado_mensaje.emit("Enviando factura por correo electrónico…")
        self.btn_enviar_email.setEnabled(False)
        self._smtp_worker = SMTPWorker(self._factura_id, self)
        self._smtp_worker.finished_ok.connect(self._on_email_enviado)
        self._smtp_worker.finished_error.connect(self._on_email_error)
        self._smtp_worker.start()

    def _on_email_enviado(self, mensaje: str) -> None:
        self.estado_mensaje.emit(mensaje)
        self.btn_enviar_email.setEnabled(True)
        if self._factura_id is not None:
            self.factura_enviada.emit(self._factura_id)
        informacion(self, "Correo enviado", mensaje)

    def _on_email_error(self, mensaje: str) -> None:
        self.estado_mensaje.emit(f"Error email: {mensaje}")
        self.btn_enviar_email.setEnabled(True)
        error(self, "Error al enviar", mensaje)

    def detener_workers(self) -> None:
        """Detiene hilos en segundo plano antes de cerrar la aplicación."""
        for worker in (self._pdf_worker, self._smtp_worker):
            if worker is None or not worker.isRunning():
                continue
            worker.wait(2_000)
            if worker.isRunning():
                worker.terminate()
                worker.wait(1_000)

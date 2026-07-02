"""
Pestaña 'Listado' — vista consolidada de todas las facturas.

Codificación cromática sutil según el estado del ciclo de vida.
"""

from __future__ import annotations

from pathlib import Path
from shutil import copy2

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QFileDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QUrl

from lefa.models import EstadoFactura
from lefa.services.factura_service import FacturaService
from lefa.services.pdf_service import PDFService
from lefa.services.preferencias_service import PreferenciasService
from lefa.ui.messages import aviso, error, informacion
from lefa.utils import formato_moneda

COLOR_BORRADOR = QColor(240, 240, 240)
COLOR_EMITIDA = QColor(255, 224, 178)
COLOR_COBRADA = QColor(200, 230, 201)
COLOR_TEXTO = QColor(33, 33, 33)

COL_ID = 0
COL_NUMERO = 1
COL_CLIENTE = 2
COL_FECHA = 3
COL_ESTADO = 4
COL_ENVIO = 5
COL_VENCIMIENTO = 6
COL_SUBTOTAL = 7
COL_TOTAL = 8


class ListadoTab(QWidget):
    """Tabla de facturas con acciones de refresco, cobro y duplicado."""

    editar_borrador = pyqtSignal(int)
    factura_duplicada = pyqtSignal(int)
    factura_rectificada = pyqtSignal(int)
    estado_mensaje = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.clicked.connect(self.refrescar)
        self.btn_guardar_pdf = QPushButton("Guardar PDF…")
        self.btn_guardar_pdf.clicked.connect(self._guardar_pdf)
        self.btn_abrir_carpeta = QPushButton("Abrir carpeta")
        self.btn_abrir_carpeta.clicked.connect(self._abrir_carpeta_pdfs)
        self.btn_duplicar = QPushButton("Duplicar")
        self.btn_duplicar.clicked.connect(self._duplicar_factura)
        self.btn_rectificar = QPushButton("Rectificar")
        self.btn_rectificar.clicked.connect(self._rectificar_factura)
        self.btn_marcar_cobrada = QPushButton("Marcar como Cobrada")
        self.btn_marcar_cobrada.clicked.connect(self._marcar_cobrada)
        toolbar.addWidget(self.btn_refrescar)
        toolbar.addWidget(self.btn_guardar_pdf)
        toolbar.addWidget(self.btn_abrir_carpeta)
        toolbar.addWidget(self.btn_duplicar)
        toolbar.addWidget(self.btn_rectificar)
        toolbar.addWidget(self.btn_marcar_cobrada)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tabla = QTableWidget(0, 9)
        self.tabla.setHorizontalHeaderLabels(
            [
                "ID",
                "Número",
                "Cliente",
                "Fecha",
                "Estado",
                "Envío",
                "Vencimiento",
                "Subtotal",
                "Total",
            ]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.doubleClicked.connect(self._on_doble_clic)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_NUMERO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_CLIENTE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_FECHA, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_ESTADO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_ENVIO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_VENCIMIENTO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_SUBTOTAL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_TOTAL, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setStyleSheet(
            "QTableWidget::item:selected {"
            "  background-color: #90CAF9;"
            "  color: #212121;"
            "}"
        )
        layout.addWidget(self.tabla)

        leyenda = QHBoxLayout()
        for color, texto in [
            (COLOR_BORRADOR, "Borrador"),
            (COLOR_EMITIDA, "Emitida"),
            (COLOR_COBRADA, "Cobrada"),
        ]:
            indicador = QLabel(f"  {texto}  ")
            indicador.setStyleSheet(
                f"background-color: {color.name()};"
                f" color: {COLOR_TEXTO.name()};"
                " border-radius: 3px;"
                " padding: 2px 8px;"
            )
            leyenda.addWidget(indicador)
        leyenda.addStretch()
        layout.addLayout(leyenda)

    def refrescar(self) -> None:
        facturas = FacturaService.listar_todas()
        self.tabla.setRowCount(0)

        for factura in facturas:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            color = self._color_por_estado(factura.estado)
            brush_fondo = QBrush(color)
            brush_texto = QBrush(COLOR_TEXTO)
            texto_envio = factura.texto_estado_envio()
            texto_venc = factura.texto_estado_vencimiento()
            valores = [
                str(factura.id),
                ("↳ " if factura.es_rectificativa else "") + (factura.numero_factura or "—"),
                factura.cliente.razon_social,
                factura.fecha_emision.strftime("%d/%m/%Y") if factura.fecha_emision else "—",
                factura.estado.value,
                texto_envio,
                texto_venc,
                formato_moneda(factura.calcular_subtotal()),
                formato_moneda(factura.calcular_total()),
            ]

            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setBackground(brush_fondo)
                item.setForeground(brush_texto)
                if col == COL_ID:
                    item.setData(Qt.ItemDataRole.UserRole, factura.id)
                if col == COL_ENVIO and factura.enviada and factura.destinatario:
                    item.setToolTip(f"Enviada a {factura.destinatario}")
                if col == COL_VENCIMIENTO and factura.fecha_vencimiento:
                    item.setToolTip(
                        f"Vence el {factura.fecha_vencimiento.strftime('%d/%m/%Y')}"
                    )
                self.tabla.setItem(fila, col, item)

    @staticmethod
    def _color_por_estado(estado: EstadoFactura) -> QColor:
        if estado == EstadoFactura.BORRADOR:
            return COLOR_BORRADOR
        if estado == EstadoFactura.EMITIDA:
            return COLOR_EMITIDA
        return COLOR_COBRADA

    def _factura_seleccionada_id(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        item = self.tabla.item(fila, COL_ID)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _facturas_seleccionadas_ids(self) -> list[int]:
        filas = sorted({idx.row() for idx in self.tabla.selectionModel().selectedRows()})
        ids: list[int] = []
        for fila in filas:
            item = self.tabla.item(fila, COL_ID)
            if item is None:
                continue
            val = item.data(Qt.ItemDataRole.UserRole)
            if val is None:
                continue
            ids.append(int(val))
        return ids

    def _on_doble_clic(self) -> None:
        factura_id = self._factura_seleccionada_id()
        if factura_id is None:
            return
        self.editar_borrador.emit(factura_id)

    def _duplicar_factura(self) -> None:
        factura_id = self._factura_seleccionada_id()
        if factura_id is None:
            aviso(self, "Selección", "Seleccione una factura para duplicar.")
            return
        try:
            nueva = FacturaService.duplicar_factura(factura_id)
            self.refrescar()
            self.factura_duplicada.emit(nueva.id)
            self.estado_mensaje.emit(
                f"Factura duplicada como borrador (ID: {nueva.id}). Revise y emita."
            )
            informacion(
                self,
                "Factura duplicada",
                "Se creó un borrador con las mismas líneas.\n"
                "Revíselo en Nueva Factura y pulse Emitir para asignar fecha y número.",
            )
        except Exception as exc:
            error(self, "No se pudo duplicar", str(exc))

    def _guardar_pdf(self) -> None:
        ids = self._facturas_seleccionadas_ids()
        if not ids:
            aviso(self, "Selección", "Seleccione una o varias facturas para guardar sus PDFs.")
            return

        # Caso 1: una sola factura → elegir fichero
        if len(ids) == 1:
            factura_id = ids[0]
            factura = FacturaService.obtener_por_id(factura_id)
            if factura is None:
                error(self, "No encontrada", f"Factura {factura_id} no encontrada.")
                return

            sugerida = PDFService.ruta_pdf_factura(factura).name
            ruta_destino, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF de factura",
                sugerida,
                "PDF (*.pdf)",
            )
            if not ruta_destino:
                return

            destino = Path(ruta_destino)
            if destino.suffix.lower() != ".pdf":
                destino = destino.with_suffix(".pdf")

            try:
                origen = PDFService.obtener_o_generar(factura)
                copy2(origen, destino)
                informacion(self, "PDF guardado", f"Se guardó el PDF en:\n{destino}")
                self.estado_mensaje.emit(f"PDF guardado: {destino.name}")
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(destino.parent)))
            except Exception as exc:
                error(self, "No se pudo guardar el PDF", str(exc))
            return

        # Caso 2: varias facturas → elegir carpeta y exportar todas
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Elegir carpeta destino para PDFs",
            "",
        )
        if not carpeta:
            return
        destino_dir = Path(carpeta)

        guardados = 0
        errores: list[str] = []
        for factura_id in ids:
            factura = FacturaService.obtener_por_id(factura_id)
            if factura is None:
                errores.append(f"Factura {factura_id}: no encontrada")
                continue
            try:
                origen = PDFService.obtener_o_generar(factura)
                nombre = PDFService.ruta_pdf_factura(factura).name
                copy2(origen, destino_dir / nombre)
                guardados += 1
            except Exception as exc:
                errores.append(f"Factura {factura_id}: {exc}")

        if guardados:
            self.estado_mensaje.emit(f"PDFs guardados: {guardados}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(destino_dir)))
        if errores:
            error(self, "Algunos PDFs no se pudieron guardar", "\n".join(errores))
        else:
            informacion(self, "PDFs guardados", f"Se guardaron {guardados} PDFs en:\n{destino_dir}")

    def _abrir_carpeta_pdfs(self) -> None:
        try:
            carpeta = PreferenciasService.obtener_carpeta_pdf()
            carpeta.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(carpeta)))
        except Exception as exc:
            error(self, "No se pudo abrir la carpeta", str(exc))

    def _rectificar_factura(self) -> None:
        factura_id = self._factura_seleccionada_id()
        if factura_id is None:
            aviso(self, "Selección", "Seleccione una factura para rectificar.")
            return
        try:
            nueva = FacturaService.rectificar_factura(factura_id)
            self.refrescar()
            self.factura_rectificada.emit(nueva.id)
            self.estado_mensaje.emit(
                f"Rectificativa creada como borrador (ID: {nueva.id})."
            )
            informacion(
                self,
                "Factura rectificativa",
                "Se creó un borrador en serie RECT.\n\n"
                "Ajuste las líneas (use importes negativos si debe "
                "devolver dinero al cliente) y emita.",
            )
        except Exception as exc:
            error(self, "No se pudo rectificar", str(exc))

    def _marcar_cobrada(self) -> None:
        factura_id = self._factura_seleccionada_id()
        if factura_id is None:
            aviso(self, "Selección", "Seleccione una factura.")
            return
        try:
            factura = FacturaService.marcar_cobrada(factura_id)
            self.estado_mensaje.emit(
                f"Factura {factura.numero_factura} marcada como Cobrada."
            )
            self.refrescar()
        except Exception as exc:
            error(self, "No se pudo marcar", str(exc))

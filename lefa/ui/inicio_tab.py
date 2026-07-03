"""
Pestaña Inicio — flujo visual lineal (camino recto frente al laberinto ERP).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lefa import __app_name__
from lefa.services.factura_service import FacturaService
from lefa.utils import formato_moneda


class _PasoFlujo(QFrame):
    """Tarjeta de un paso en el camino lineal."""

    def __init__(
        self,
        numero: int,
        titulo: str,
        descripcion: str,
        texto_boton: str,
        *,
        fondo: str = "#e3f2fd",
        borde: str = "#90caf9",
        acento: str = "#1565c0",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {fondo};
                border: 1px solid {borde};
                border-radius: 8px;
            }}
            """
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        num = QLabel(str(numero))
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setFixedSize(28, 28)
        num.setStyleSheet(
            f"background-color: {acento}; color: white; border-radius: 14px;"
            "font-weight: bold; font-size: 14px;"
        )
        layout.addWidget(num, alignment=Qt.AlignmentFlag.AlignHCenter)

        lbl_titulo = QLabel(f"<b>{titulo}</b>")
        lbl_titulo.setWordWrap(True)
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        lbl_desc = QLabel(descripcion)
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("color: #424242; font-size: 12px;")
        layout.addWidget(lbl_desc)

        self.btn = QPushButton(texto_boton)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn)


class _Flecha(QWidget):
    """Conector visual entre pasos."""

    def __init__(self, color: str = "#1565c0", parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(36)
        lbl = QLabel("→")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"font-size: 28px; color: {color}; font-weight: bold;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch()
        lay.addWidget(lbl)
        lay.addStretch()


class InicioTab(QWidget):
    """
    Pantalla de inicio con el flujo operativo en línea recta.

    Contrasta con ERPs que obligan a saltar entre muchas ventanas.
    """

    ir_nueva_factura = pyqtSignal()
    ir_nuevo_cliente = pyqtSignal()
    ir_clientes = pyqtSignal()
    ir_listado = pyqtSignal()
    ir_presupuesto = pyqtSignal()
    ir_listado_presupuestos = pyqtSignal()
    ir_preferencias = pyqtSignal()
    ir_servicios = pyqtSignal()
    ir_plantillas = pyqtSignal()
    ir_documentacion = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 20, 24, 24)

        titulo = QLabel(
            f"<span style='font-size: 22px;'><b>{__app_name__}</b></span>"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "<span style='font-size: 15px;'>Rapidez y cero complicaciones — "
            "<b>un camino recto</b>, no un laberinto de ventanas.</span>"
        )
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #37474f; padding: 0 12px;")
        layout.addWidget(subtitulo)

        self._caja_resumen = QFrame()
        self._caja_resumen.setFrameShape(QFrame.Shape.StyledPanel)
        self._caja_resumen.setStyleSheet(
            """
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            """
        )
        resumen_layout = QVBoxLayout(self._caja_resumen)
        resumen_layout.setContentsMargins(20, 16, 20, 16)
        resumen_layout.setSpacing(10)

        lbl_hoy = QLabel("<b>Hoy</b>")
        lbl_hoy.setStyleSheet("font-size: 15px; color: #212121;")
        resumen_layout.addWidget(lbl_hoy)

        self._lbl_emitidas = QLabel()
        self._lbl_pendientes = QLabel()
        self._lbl_importe = QLabel()
        for lbl in (self._lbl_emitidas, self._lbl_pendientes, self._lbl_importe):
            lbl.setStyleSheet("font-size: 14px; color: #424242;")
            resumen_layout.addWidget(lbl)

        layout.addWidget(self._caja_resumen)
        self.refrescar_resumen()

        btn_principal = QPushButton("Nueva factura")
        btn_principal.setMinimumHeight(44)
        btn_principal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_principal.setStyleSheet(
            """
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:pressed { background-color: #1b5e20; }
            """
        )
        btn_principal.clicked.connect(self.ir_nueva_factura.emit)
        layout.addWidget(btn_principal, alignment=Qt.AlignmentFlag.AlignHCenter)

        # —— Flujo factura ——
        seccion_factura = QLabel("<b>Tu factura en cuatro pasos — todo en la misma pestaña</b>")
        seccion_factura.setStyleSheet("font-size: 14px; color: #1565c0; margin-top: 8px;")
        layout.addWidget(seccion_factura)

        fila_factura = QHBoxLayout()
        fila_factura.setSpacing(4)

        paso1 = _PasoFlujo(
            1,
            "Cliente",
            "Elija uno existente o créelo al vuelo.",
            "Nuevo cliente…",
        )
        paso1.btn.clicked.connect(self.ir_nuevo_cliente.emit)

        paso2 = _PasoFlujo(
            2,
            "Líneas",
            "Conceptos, servicios o plantillas con un clic.",
            "Añadir líneas",
        )
        paso2.btn.clicked.connect(self.ir_nueva_factura.emit)

        paso3 = _PasoFlujo(
            3,
            "Emitir",
            "PDF, Facturae y VeriFactu automáticos.",
            "Ir a emitir",
        )
        paso3.btn.clicked.connect(self.ir_nueva_factura.emit)

        paso4 = _PasoFlujo(
            4,
            "Listo",
            "Email al cliente o consulta en el listado.",
            "Ver listado",
        )
        paso4.btn.clicked.connect(self.ir_listado.emit)

        for i, paso in enumerate((paso1, paso2, paso3, paso4)):
            fila_factura.addWidget(paso, stretch=1)
            if i < 3:
                fila_factura.addWidget(_Flecha())

        layout.addLayout(fila_factura)

        nota_erp = QLabel(
            "<i>En un ERP tradicional suele hacer falta abrir clientes, catálogo, "
            "productos y facturas en ventanas separadas. En LEFA va todo seguido "
            "en <b>Nueva Factura</b>.</i>"
        )
        nota_erp.setWordWrap(True)
        nota_erp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nota_erp.setStyleSheet(
            "background-color: #f5f5f5; border-radius: 6px; padding: 12px; color: #616161;"
        )
        layout.addWidget(nota_erp)

        # —— Flujo presupuesto ——
        seccion_pres = QLabel("<b>¿Presupuesto antes? Otro camino recto</b>")
        seccion_pres.setStyleSheet("font-size: 14px; color: #6a1b9a;")
        layout.addWidget(seccion_pres)

        fila_pres = QHBoxLayout()
        fila_pres.setSpacing(4)

        pres1 = _PasoFlujo(
            1,
            "Presupuesto",
            "Oferta al cliente (PDF).",
            "Crear",
            fondo="#f3e5f5",
            borde="#ce93d8",
            acento="#6a1b9a",
        )
        pres1.btn.clicked.connect(self.ir_presupuesto.emit)

        pres2 = _PasoFlujo(
            2,
            "Aceptar",
            "El cliente dice que sí.",
            "Listado presup.",
            fondo="#f3e5f5",
            borde="#ce93d8",
            acento="#6a1b9a",
        )
        pres2.btn.clicked.connect(self.ir_listado_presupuestos.emit)

        pres3 = _PasoFlujo(
            3,
            "Convertir",
            "Un clic → borrador de factura.",
            "Convertir",
            fondo="#f3e5f5",
            borde="#ce93d8",
            acento="#6a1b9a",
        )
        pres3.btn.clicked.connect(self.ir_listado_presupuestos.emit)

        pres4 = _PasoFlujo(
            4,
            "Emitir",
            "Revise y facture.",
            "Nueva Factura",
            fondo="#f3e5f5",
            borde="#ce93d8",
            acento="#6a1b9a",
        )
        pres4.btn.clicked.connect(self.ir_nueva_factura.emit)

        for i, paso in enumerate((pres1, pres2, pres3, pres4)):
            fila_pres.addWidget(paso, stretch=1)
            if i < 3:
                fila_pres.addWidget(_Flecha("#6a1b9a"))

        layout.addLayout(fila_pres)

        # —— Accesos rápidos ——
        barra = QHBoxLayout()
        barra.setSpacing(12)

        btn_clientes = QPushButton("Clientes")
        btn_clientes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clientes.clicked.connect(self.ir_clientes.emit)
        barra.addWidget(btn_clientes)

        btn_preferencias = QPushButton("Preferencias")
        btn_preferencias.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_preferencias.clicked.connect(self.ir_preferencias.emit)
        barra.addWidget(btn_preferencias)

        btn_servicios = QPushButton("Servicios")
        btn_servicios.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_servicios.setToolTip("Catálogo de servicios con precio e IVA")
        btn_servicios.clicked.connect(self.ir_servicios.emit)
        barra.addWidget(btn_servicios)

        btn_plantillas = QPushButton("Plantillas")
        btn_plantillas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plantillas.setToolTip("Plantillas de líneas reutilizables")
        btn_plantillas.clicked.connect(self.ir_plantillas.emit)
        barra.addWidget(btn_plantillas)

        btn_documentacion = QPushButton("Ayuda rápida")
        btn_documentacion.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_documentacion.clicked.connect(self.ir_documentacion.emit)
        barra.addWidget(btn_documentacion)

        barra.addStretch()
        layout.addLayout(barra)

        layout.addStretch()

        scroll.setWidget(contenido)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.refrescar_resumen()

    def refrescar_resumen(self) -> None:
        """Actualiza las tres cifras del día."""
        r = FacturaService.resumen_hoy()
        self._lbl_emitidas.setText(f"Facturas emitidas: <b>{r.facturas_emitidas_hoy}</b>")
        self._lbl_pendientes.setText(f"Pendientes de cobrar: <b>{r.pendientes_cobrar}</b>")
        self._lbl_importe.setText(
            f"Importe pendiente: <b>{formato_moneda(r.importe_pendiente)}</b>"
        )

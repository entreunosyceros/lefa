"""
Diálogo de alta y edición de clientes.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from lefa.models import Cliente
from lefa.services.cliente_service import ClienteDTO, ClienteService
from lefa.services.factura_service import FacturaService
from lefa.ui.messages import aviso, error
from lefa.utils import formato_moneda

COLOR_TEXTO = QColor(33, 33, 33)
COLOR_FILA = QColor(245, 245, 245)


class ClienteDialog(QDialog):
    """Formulario modal para crear o editar un cliente."""

    def __init__(self, parent=None, cliente: Cliente | None = None):
        super().__init__(parent)
        self._cliente_id = cliente.id if cliente else None
        self._cliente_guardado_id: int | None = None
        self.setWindowTitle("Editar cliente" if cliente else "Nuevo cliente")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._setup_ui(cliente)

    @property
    def cliente_id(self) -> int | None:
        return self._cliente_guardado_id

    def _setup_ui(self, cliente: Cliente | None) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.txt_razon_social = QLineEdit()
        self.txt_razon_social.setPlaceholderText("Ej. Tech Solutions S.L.")
        form.addRow("Nombre *:", self.txt_razon_social)

        self.txt_cif_nif = QLineEdit()
        self.txt_cif_nif.setPlaceholderText("Ej. B12345678")
        form.addRow("NIF/CIF *:", self.txt_cif_nif)

        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Calle, número, CP, ciudad")
        form.addRow("Dirección:", self.txt_direccion)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("cliente@empresa.es")
        form.addRow("Email:", self.txt_email)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional")
        form.addRow("Teléfono:", self.txt_telefono)

        layout.addLayout(form)

        grupo_face = QGroupBox("Facturae / FACe (opcional — administración pública)")
        form_face = QFormLayout(grupo_face)
        self.txt_iban = QLineEdit()
        self.txt_iban.setPlaceholderText("Solo si difiere del IBAN del emisor")
        form_face.addRow("IBAN cliente:", self.txt_iban)

        self.txt_forma_pago = QLineEdit("04")
        self.txt_forma_pago.setPlaceholderText("04 = transferencia bancaria")
        self.txt_forma_pago.setToolTip(
            "Código Facturae del medio de pago. 04 = transferencia bancaria."
        )
        form_face.addRow("Forma de pago:", self.txt_forma_pago)

        self.txt_dir3_oficina = QLineEdit()
        self.txt_dir3_oficina.setPlaceholderText("Oficina contable (DIR3)")
        form_face.addRow("DIR3 oficina:", self.txt_dir3_oficina)

        self.txt_dir3_organo = QLineEdit()
        self.txt_dir3_organo.setPlaceholderText("Órgano gestor (DIR3)")
        form_face.addRow("DIR3 órgano:", self.txt_dir3_organo)

        self.txt_dir3_unidad = QLineEdit()
        self.txt_dir3_unidad.setPlaceholderText("Unidad tramitadora (DIR3)")
        form_face.addRow("DIR3 unidad:", self.txt_dir3_unidad)

        layout.addWidget(grupo_face)

        if cliente is not None:
            self.txt_razon_social.setText(cliente.razon_social)
            self.txt_cif_nif.setText(cliente.cif_nif)
            self.txt_direccion.setText(cliente.direccion)
            self.txt_email.setText(cliente.email)
            self.txt_telefono.setText(cliente.telefono)
            self.txt_iban.setText(cliente.iban)
            self.txt_forma_pago.setText(cliente.forma_pago or "04")
            self.txt_dir3_oficina.setText(cliente.dir3_oficina)
            self.txt_dir3_organo.setText(cliente.dir3_organo)
            self.txt_dir3_unidad.setText(cliente.dir3_unidad)
            self._añadir_historial(cliente.id)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _añadir_historial(self, cliente_id: int) -> None:
        facturas = FacturaService.listar_por_cliente(cliente_id)
        if not facturas:
            return

        grupo = QGroupBox("Facturas de este cliente")
        vbox = QVBoxLayout(grupo)

        total = FacturaService.total_facturado_cliente(cliente_id)
        lbl_total = QLabel(f"Total facturado: {formato_moneda(total)}")
        lbl_total.setStyleSheet("font-weight: bold;")
        vbox.addWidget(lbl_total)

        tabla = QTableWidget(len(facturas), 4)
        tabla.setHorizontalHeaderLabels(["Número", "Fecha", "Estado", "Total"])
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setMaximumHeight(180)

        brush_fondo = QBrush(COLOR_FILA)
        brush_texto = QBrush(COLOR_TEXTO)
        for fila, factura in enumerate(facturas):
            valores = [
                factura.numero_factura or "—",
                factura.fecha_emision.strftime("%d/%m/%Y") if factura.fecha_emision else "—",
                factura.estado.value,
                formato_moneda(factura.calcular_total()),
            ]
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setBackground(brush_fondo)
                item.setForeground(brush_texto)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(fila, col, item)

        vbox.addWidget(tabla)
        self.layout().insertWidget(1, grupo)

    def _guardar(self) -> None:
        datos = ClienteDTO(
            razon_social=self.txt_razon_social.text(),
            cif_nif=self.txt_cif_nif.text(),
            direccion=self.txt_direccion.text(),
            email=self.txt_email.text(),
            telefono=self.txt_telefono.text(),
            iban=self.txt_iban.text(),
            forma_pago=self.txt_forma_pago.text() or "04",
            dir3_oficina=self.txt_dir3_oficina.text(),
            dir3_organo=self.txt_dir3_organo.text(),
            dir3_unidad=self.txt_dir3_unidad.text(),
        )
        if not datos.razon_social.strip():
            aviso(self, "Validación", "La razón social es obligatoria.")
            return
        if not datos.cif_nif.strip():
            aviso(self, "Validación", "El CIF/NIF es obligatorio.")
            return

        try:
            if self._cliente_id is None:
                cliente = ClienteService.crear(datos)
            else:
                cliente = ClienteService.actualizar(self._cliente_id, datos)
            self._cliente_guardado_id = cliente.id
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

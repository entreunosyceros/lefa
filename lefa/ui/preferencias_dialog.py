"""
Diálogo de preferencias generales de LEFA.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from lefa.services.numeracion_service import ETIQUETAS_FORMATO
from lefa.services.preferencias_service import Preferencias, PreferenciasService
from lefa.ui.messages import informacion


class PreferenciasDialog(QDialog):
    """IVA/IRPF, emisor, numeración, series y carpeta PDF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias")
        self.setMinimumWidth(560)
        self.setModal(True)
        self._prefs = PreferenciasService.cargar()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        impuestos = QGroupBox("Impuestos y vencimiento")
        form_imp = QFormLayout(impuestos)
        self.spin_iva = QDoubleSpinBox()
        self.spin_iva.setRange(0, 100)
        self.spin_iva.setSuffix(" %")
        self.spin_iva.setValue(self._prefs.iva_porcentaje)
        form_imp.addRow("IVA por defecto:", self.spin_iva)

        self.spin_irpf = QDoubleSpinBox()
        self.spin_irpf.setRange(0, 100)
        self.spin_irpf.setSuffix(" %")
        self.spin_irpf.setValue(self._prefs.irpf_porcentaje)
        form_imp.addRow("IRPF por defecto:", self.spin_irpf)

        self.spin_dias_venc = QSpinBox()
        self.spin_dias_venc.setRange(0, 365)
        self.spin_dias_venc.setSuffix(" días")
        self.spin_dias_venc.setValue(self._prefs.dias_vencimiento)
        self.spin_dias_venc.setToolTip(
            "Días desde la emisión hasta el vencimiento (0 = sin vencimiento automático)"
        )
        form_imp.addRow("Vencimiento por defecto:", self.spin_dias_venc)
        layout.addWidget(impuestos)

        emisor = QGroupBox("Empresa emisora")
        form_em = QFormLayout(emisor)
        self.txt_emisor_nombre = QLineEdit(self._prefs.emisor_razon_social)
        form_em.addRow("Nombre:", self.txt_emisor_nombre)
        self.txt_emisor_cif = QLineEdit(self._prefs.emisor_cif)
        form_em.addRow("NIF/CIF:", self.txt_emisor_cif)
        self.txt_emisor_direccion = QLineEdit(self._prefs.emisor_direccion)
        form_em.addRow("Dirección:", self.txt_emisor_direccion)
        self.txt_emisor_telefono = QLineEdit(self._prefs.emisor_telefono)
        form_em.addRow("Teléfono:", self.txt_emisor_telefono)
        self.txt_emisor_email = QLineEdit(self._prefs.emisor_email)
        form_em.addRow("Email:", self.txt_emisor_email)
        self.txt_emisor_iban = QLineEdit(self._prefs.emisor_iban)
        self.txt_emisor_iban.setPlaceholderText("ES00 0000 0000 0000 0000 0000")
        form_em.addRow("IBAN:", self.txt_emisor_iban)

        self.txt_facturae_forma_pago = QLineEdit(self._prefs.facturae_forma_pago or "04")
        self.txt_facturae_forma_pago.setPlaceholderText("04 = transferencia bancaria")
        self.txt_facturae_forma_pago.setToolTip(
            "Código Facturae del medio de pago por defecto en el XML."
        )
        form_em.addRow("Forma de pago Facturae:", self.txt_facturae_forma_pago)

        logo_layout = QHBoxLayout()
        self.txt_logotipo = QLineEdit(self._prefs.ruta_logotipo)
        self.txt_logotipo.setPlaceholderText("Vacío = img/logo.png del proyecto (solo PDF)")
        btn_logo = QPushButton("…")
        btn_logo.clicked.connect(self._elegir_logotipo)
        logo_layout.addWidget(self.txt_logotipo)
        logo_layout.addWidget(btn_logo)
        form_em.addRow("Logotipo (PDF):", logo_layout)

        self.txt_pie_factura = QTextEdit()
        self.txt_pie_factura.setPlainText(self._prefs.pie_factura or "")
        self.txt_pie_factura.setPlaceholderText(
            "Opcional. Se imprime al final del PDF (puede tener varias líneas)."
        )
        self.txt_pie_factura.setFixedHeight(70)
        form_em.addRow("Pie de factura (PDF):", self.txt_pie_factura)
        layout.addWidget(emisor)

        numeracion = QGroupBox("Numeración y series")
        form_num = QFormLayout(numeracion)
        self.combo_formato = QComboBox()
        for clave, etiqueta in ETIQUETAS_FORMATO.items():
            self.combo_formato.addItem(etiqueta, clave)
        idx = self.combo_formato.findData(self._prefs.formato_numeracion)
        if idx >= 0:
            self.combo_formato.setCurrentIndex(idx)
        form_num.addRow("Formato de número:", self.combo_formato)

        self.spin_digitos = QSpinBox()
        self.spin_digitos.setRange(2, 6)
        self.spin_digitos.setValue(self._prefs.digitos_secuencia)
        form_num.addRow("Dígitos correlativo:", self.spin_digitos)

        self.txt_series = QLineEdit(", ".join(self._prefs.series_facturacion))
        self.txt_series.setPlaceholderText("Ej. FACT, WEB, MANT")
        self.txt_series.setToolTip("Series separadas por comas. Cada una lleva su propio correlativo.")
        form_num.addRow("Series de facturación:", self.txt_series)

        carpeta_layout = QHBoxLayout()
        self.txt_carpeta_pdf = QLineEdit(self._prefs.carpeta_pdf)
        self.txt_carpeta_pdf.setPlaceholderText("Vacío = ~/.lefa/facturas_pdf/")
        btn_carpeta = QPushButton("…")
        btn_carpeta.clicked.connect(self._elegir_carpeta_pdf)
        carpeta_layout.addWidget(self.txt_carpeta_pdf)
        carpeta_layout.addWidget(btn_carpeta)
        form_num.addRow("Carpeta PDFs:", carpeta_layout)
        layout.addWidget(numeracion)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _elegir_carpeta_pdf(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Carpeta de PDFs")
        if ruta:
            self.txt_carpeta_pdf.setText(ruta)

    def _elegir_logotipo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar logotipo", "", "Imágenes (*.png *.jpg *.jpeg)"
        )
        if ruta:
            self.txt_logotipo.setText(ruta)

    def _guardar(self) -> None:
        series = [
            s.strip()
            for s in self.txt_series.text().split(",")
            if s.strip()
        ]
        if not series:
            series = ["FACT"]

        prefs = Preferencias(
            iva_porcentaje=self.spin_iva.value(),
            irpf_porcentaje=self.spin_irpf.value(),
            carpeta_pdf=self.txt_carpeta_pdf.text().strip(),
            emisor_razon_social=self.txt_emisor_nombre.text().strip(),
            emisor_cif=self.txt_emisor_cif.text().strip(),
            emisor_direccion=self.txt_emisor_direccion.text().strip(),
            emisor_email=self.txt_emisor_email.text().strip(),
            emisor_telefono=self.txt_emisor_telefono.text().strip(),
            emisor_iban=self.txt_emisor_iban.text().strip(),
            facturae_forma_pago=self.txt_facturae_forma_pago.text().strip() or "04",
            serie_factura_prefix=series[0],
            series_facturacion=series,
            formato_numeracion=self.combo_formato.currentData(),
            digitos_secuencia=self.spin_digitos.value(),
            dias_vencimiento=self.spin_dias_venc.value(),
            ruta_logotipo=self.txt_logotipo.text().strip(),
            pie_factura=self.txt_pie_factura.toPlainText().strip(),
            ultimo_cliente_id=self._prefs.ultimo_cliente_id,
        )
        PreferenciasService.guardar(prefs)
        informacion(self, "Preferencias", "Preferencias guardadas correctamente.")
        self.accept()

"""
Diálogo de configuración de la cuenta de correo SMTP.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from lefa.services.smtp_config_service import (
    SeguridadSMTP,
    SmtpConfig,
    SmtpConfigService,
)
from lefa.ui.messages import aviso, error, informacion
from lefa.workers.smtp_test_worker import SmtpTestWorker


class SmtpConfigDialog(QDialog):
    """Formulario para configurar el envío real de facturas por email."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_guardada = SmtpConfigService.cargar()
        self._test_worker: SmtpTestWorker | None = None
        self.setWindowTitle("Configurar correo electrónico")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._setup_ui()
        self._cargar_datos()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        ayuda = QLabel(
            "Configure su cuenta SMTP para enviar facturas en PDF a los clientes. "
            "La contraseña se guarda de forma segura en el llavero del sistema."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #555; margin-bottom: 8px;")
        layout.addWidget(ayuda)

        form = QFormLayout()

        self.txt_servidor = QLineEdit()
        self.txt_servidor.setPlaceholderText("Ej. smtp.gmail.com")
        form.addRow("Servidor SMTP *:", self.txt_servidor)

        self.spin_puerto = QSpinBox()
        self.spin_puerto.setRange(1, 65535)
        self.spin_puerto.setValue(587)
        form.addRow("Puerto *:", self.spin_puerto)

        self.combo_seguridad = QComboBox()
        self.combo_seguridad.addItem("STARTTLS (recomendado, puerto 587)", SeguridadSMTP.STARTTLS)
        self.combo_seguridad.addItem("SSL/TLS (puerto 465)", SeguridadSMTP.SSL)
        self.combo_seguridad.addItem("Sin cifrado (no recomendado)", SeguridadSMTP.NINGUNA)
        self.combo_seguridad.currentIndexChanged.connect(self._ajustar_puerto_sugerido)
        form.addRow("Seguridad:", self.combo_seguridad)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("usuario@dominio.com")
        form.addRow("Usuario *:", self.txt_usuario)

        self.txt_contrasena = QLineEdit()
        self.txt_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_contrasena.setPlaceholderText("Dejar vacío para mantener la actual")
        form.addRow("Contraseña *:", self.txt_contrasena)

        self.txt_remitente = QLineEdit()
        self.txt_remitente.setPlaceholderText("correo@dominio.com")
        form.addRow("Correo remitente *:", self.txt_remitente)

        self.txt_nombre_remitente = QLineEdit()
        self.txt_nombre_remitente.setPlaceholderText("Ej. Mi Empresa Autónoma")
        form.addRow("Nombre remitente:", self.txt_nombre_remitente)

        layout.addLayout(form)

        self.chk_enviar_prueba = QCheckBox("Enviar correo de prueba al remitente al probar conexión")
        layout.addWidget(self.chk_enviar_prueba)

        pruebas = QHBoxLayout()
        self.btn_probar = QPushButton("Probar conexión")
        self.btn_probar.clicked.connect(self._probar_conexion)
        pruebas.addWidget(self.btn_probar)
        pruebas.addStretch()
        layout.addLayout(pruebas)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setWordWrap(True)
        layout.addWidget(self.lbl_estado)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _cargar_datos(self) -> None:
        cfg = self._config_guardada
        self.txt_servidor.setText(cfg.servidor)
        self.spin_puerto.setValue(cfg.puerto or cfg.puerto_por_defecto())
        index = self.combo_seguridad.findData(cfg.seguridad)
        if index >= 0:
            self.combo_seguridad.setCurrentIndex(index)
        self.txt_usuario.setText(cfg.usuario)
        self.txt_remitente.setText(cfg.remitente)
        self.txt_nombre_remitente.setText(cfg.nombre_remitente)

        if SmtpConfigService.tiene_contrasena_guardada():
            self.txt_contrasena.setPlaceholderText("••••••••  (dejar vacío para mantener)")

    def _ajustar_puerto_sugerido(self) -> None:
        seguridad = self.combo_seguridad.currentData()
        if seguridad == SeguridadSMTP.SSL:
            self.spin_puerto.setValue(465)
        elif seguridad == SeguridadSMTP.STARTTLS:
            self.spin_puerto.setValue(587)

    def _leer_config(self) -> SmtpConfig:
        return SmtpConfig(
            servidor=self.txt_servidor.text(),
            puerto=self.spin_puerto.value(),
            seguridad=self.combo_seguridad.currentData(),
            usuario=self.txt_usuario.text(),
            remitente=self.txt_remitente.text(),
            nombre_remitente=self.txt_nombre_remitente.text(),
        )

    def _obtener_contrasena_efectiva(self) -> str | None:
        texto = self.txt_contrasena.text()
        if texto:
            return texto
        return SmtpConfigService.obtener_contrasena()

    def _validar_campos(self) -> bool:
        config = self._leer_config()
        if not config.servidor.strip():
            aviso(self, "Validación", "Indique el servidor SMTP.")
            return False
        if not config.usuario.strip():
            aviso(self, "Validación", "Indique el usuario SMTP.")
            return False
        if not config.remitente.strip():
            aviso(self, "Validación", "Indique el correo remitente.")
            return False
        if not self._obtener_contrasena_efectiva():
            aviso(self, "Validación", "Indique la contraseña SMTP.")
            return False
        return True

    def _guardar(self) -> None:
        if not self._validar_campos():
            return

        config = self._leer_config()
        contrasena_nueva = self.txt_contrasena.text()
        try:
            SmtpConfigService.guardar(
                config,
                contrasena=contrasena_nueva or SmtpConfigService.obtener_contrasena(),
            )
            informacion(self, "Configuración guardada", "La cuenta de correo se guardó correctamente.")
            self.accept()
        except Exception as exc:
            error(self, "Error", str(exc))

    def _probar_conexion(self) -> None:
        if not self._validar_campos():
            return
        if self._test_worker and self._test_worker.isRunning():
            return

        config = self._leer_config()
        contrasena = self._obtener_contrasena_efectiva()
        if not contrasena:
            aviso(self, "Validación", "Indique la contraseña para probar la conexión.")
            return

        destino = config.remitente if self.chk_enviar_prueba.isChecked() else None
        self.lbl_estado.setText("Probando conexión SMTP…")
        self.lbl_estado.setStyleSheet("color: #666;")
        self.btn_probar.setEnabled(False)

        self._test_worker = SmtpTestWorker(config, contrasena, destino, self)
        self._test_worker.finished_ok.connect(self._on_prueba_ok)
        self._test_worker.finished_error.connect(self._on_prueba_error)
        self._test_worker.start()

    def _on_prueba_ok(self, mensaje: str) -> None:
        self.lbl_estado.setText(mensaje)
        self.lbl_estado.setStyleSheet("color: #2e7d32; font-weight: bold;")
        self.btn_probar.setEnabled(True)

    def _on_prueba_error(self, mensaje: str) -> None:
        self.lbl_estado.setText(mensaje)
        self.lbl_estado.setStyleSheet("color: #c62828; font-weight: bold;")
        self.btn_probar.setEnabled(True)

    @staticmethod
    def esta_configurado() -> bool:
        return SmtpConfigService.cargar().esta_configurada()

"""
Ventana principal de LEFA.

Orquesta las pestañas y la barra de estado; punto de entrada de la UI.
"""

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lefa import __app_name__, __version__
from lefa.resources import get_app_icon
from lefa.services.backup_service import BackupService
from lefa.services.preferencias_service import PreferenciasService
from lefa.ui.about_dialog import AboutDialog
from lefa.ui.bienvenida_dialog import BienvenidaDialog
from lefa.ui.cliente_dialog import ClienteDialog
from lefa.ui.clientes_tab import ClientesTab
from lefa.ui.documentacion_dialog import DocumentacionDialog
from lefa.ui.inicio_tab import InicioTab
from lefa.ui.listado_presupuestos_tab import ListadoPresupuestosTab
from lefa.ui.listado_tab import ListadoTab
from lefa.ui.messages import informacion
from lefa.ui.nuevo_presupuesto_tab import NuevoPresupuestoTab
from lefa.ui.nueva_factura_tab import NuevaFacturaTab
from lefa.ui.plantillas_dialog import PlantillasDialog
from lefa.ui.plantillas_factura_dialog import PlantillasFacturaDialog
from lefa.ui.preferencias_dialog import PreferenciasDialog
from lefa.ui.servicios_dialog import ServiciosDialog
from lefa.ui.smtp_config_dialog import SmtpConfigDialog
from lefa.ui.system_tray import SystemTray
from lefa.verifactu.export import VerifactuExport


class MainWindow(QMainWindow):
    """
    Contenedor principal con QTabWidget.

    Arquitectura:
        - NuevaFacturaTab: flujo operativo de alta/emisión.
        - ListadoTab: consulta y gestión de estados.
        - ClientesTab: gestión de clientes.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} — Local & Eficiente Facturación para Autónomos")
        self.setMinimumSize(960, 680)
        self.setWindowIcon(get_app_icon())
        self._cierre_preparado = False
        self._salida_definitiva = False
        self._tray: SystemTray | None = None
        self._acciones: dict[str, QAction] = {}
        self._crear_acciones()
        self._setup_menu()
        self._setup_ui()
        self._setup_tray()
        QTimer.singleShot(150, self._arranque_inicial)

    def _crear_acciones(self) -> None:
        """Acciones compartidas entre la barra de menú y la bandeja del sistema."""
        self._acciones["backup"] = QAction("Crear &copia de seguridad…", self)
        self._acciones["backup"].setStatusTip(
            "Genera un ZIP con la base de datos, PDFs y configuración"
        )
        self._acciones["backup"].triggered.connect(self._crear_backup)

        self._acciones["salir"] = QAction("&Salir", self)
        self._acciones["salir"].setShortcut(QKeySequence.StandardKey.Quit)
        self._acciones["salir"].setStatusTip("Cerrar la aplicación por completo")
        self._acciones["salir"].triggered.connect(self._salir_aplicacion)

        self._acciones["nuevo_cliente"] = QAction("&Nuevo cliente…", self)
        self._acciones["nuevo_cliente"].setStatusTip("Crear un cliente nuevo")
        self._acciones["nuevo_cliente"].triggered.connect(self._nuevo_cliente)

        self._acciones["gestionar_clientes"] = QAction("&Gestionar clientes", self)
        self._acciones["gestionar_clientes"].setStatusTip("Abrir la pestaña de clientes")
        self._acciones["gestionar_clientes"].triggered.connect(self._ir_a_clientes)

        self._acciones["sobre"] = QAction("&Sobre…", self)
        self._acciones["sobre"].setStatusTip(f"Información sobre {__app_name__}")
        self._acciones["sobre"].triggered.connect(self._mostrar_sobre)

        self._acciones["documentacion"] = QAction("&Ayuda rápida…", self)
        self._acciones["documentacion"].setShortcut(QKeySequence("F1"))
        self._acciones["documentacion"].setText("&Ayuda rápida…")
        self._acciones["documentacion"].setStatusTip(
            "Guía rápida: qué puede hacer con LEFA y cómo hacerlo"
        )
        self._acciones["documentacion"].triggered.connect(self._mostrar_documentacion)

        self._acciones["config_correo"] = QAction("&Configurar correo electrónico…", self)
        self._acciones["config_correo"].setStatusTip("Configurar cuenta SMTP para envío de facturas")
        self._acciones["config_correo"].triggered.connect(self._configurar_correo)

        self._acciones["preferencias"] = QAction("&Preferencias…", self)
        self._acciones["preferencias"].setStatusTip("IVA, emisor, carpeta PDF y numeración")
        self._acciones["preferencias"].triggered.connect(self._mostrar_preferencias)

        self._acciones["plantillas"] = QAction("&Plantillas de líneas…", self)
        self._acciones["plantillas"].setStatusTip("Gestionar plantillas de conceptos recurrentes")
        self._acciones["plantillas"].triggered.connect(self._mostrar_plantillas)

        self._acciones["plantillas_factura"] = QAction("&Plantillas de factura…", self)
        self._acciones["plantillas_factura"].setStatusTip(
            "Facturas completas reutilizables (mensual, etc.)"
        )
        self._acciones["plantillas_factura"].triggered.connect(self._mostrar_plantillas_factura)

        self._acciones["servicios"] = QAction("&Catálogo de servicios…", self)
        self._acciones["servicios"].setStatusTip("Servicios con precio e IVA para añadir con un clic")
        self._acciones["servicios"].triggered.connect(self._mostrar_servicios)

        self._acciones["export_verifactu"] = QAction("E&xportar registros VeriFactu…", self)
        self._acciones["export_verifactu"].setStatusTip(
            "Exporta los registros de facturación encadenados (ZIP)"
        )
        self._acciones["export_verifactu"].triggered.connect(self._exportar_verifactu)

    def _setup_menu(self) -> None:
        """Barra de menú superior."""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        menu_archivo = menu_bar.addMenu("&Archivo")
        menu_archivo.addAction(self._acciones["backup"])
        menu_archivo.addSeparator()
        menu_archivo.addAction(self._acciones["salir"])

        menu_clientes = menu_bar.addMenu("&Clientes")
        menu_clientes.addAction(self._acciones["nuevo_cliente"])
        menu_clientes.addAction(self._acciones["gestionar_clientes"])

        menu_herramientas = menu_bar.addMenu("&Herramientas")
        menu_herramientas.addAction(self._acciones["config_correo"])
        menu_herramientas.addAction(self._acciones["preferencias"])
        menu_herramientas.addAction(self._acciones["plantillas"])
        menu_herramientas.addAction(self._acciones["plantillas_factura"])
        menu_herramientas.addAction(self._acciones["servicios"])
        menu_herramientas.addSeparator()
        menu_herramientas.addAction(self._acciones["export_verifactu"])

        menu_ayuda = menu_bar.addMenu("A&yuda")
        menu_ayuda.addAction(self._acciones["documentacion"])
        menu_ayuda.addSeparator()
        menu_ayuda.addAction(self._acciones["sobre"])

    def _setup_tray(self) -> None:
        """Muestra el icono en la bandeja del sistema (Linux y Windows)."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        app = QApplication.instance()
        if app is not None:
            # La X de la ventana oculta; solo Archivo → Salir cierra el proceso.
            app.setQuitOnLastWindowClosed(False)
        self._tray = SystemTray(self, self._acciones, self)
        self._tray.show()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        self.tab_inicio = InicioTab()
        self.tab_nueva = NuevaFacturaTab()
        self.tab_presupuesto = NuevoPresupuestoTab()
        self.tab_listado_pres = ListadoPresupuestosTab()
        self.tab_listado = ListadoTab()
        self.tab_clientes = ClientesTab()

        self.tabs.addTab(self.tab_inicio, "Inicio")
        self.tabs.addTab(self.tab_nueva, "Nueva Factura")
        self.tabs.addTab(self.tab_presupuesto, "Nuevo Presupuesto")
        self.tabs.addTab(self.tab_listado_pres, "Listado presupuestos")
        self.tabs.addTab(self.tab_listado, "Listado")
        self.tabs.addTab(self.tab_clientes, "Clientes")
        layout.addWidget(self.tabs)

        # Conexiones entre pestañas
        self.tab_inicio.ir_nueva_factura.connect(self._ir_a_nueva_factura)
        self.tab_inicio.ir_nuevo_cliente.connect(self._nuevo_cliente)
        self.tab_inicio.ir_clientes.connect(self._ir_a_clientes)
        self.tab_inicio.ir_listado.connect(self._ir_a_listado)
        self.tab_inicio.ir_presupuesto.connect(self._ir_a_presupuesto)
        self.tab_inicio.ir_listado_presupuestos.connect(self._ir_a_listado_presupuestos)
        self.tab_inicio.ir_preferencias.connect(self._mostrar_preferencias)
        self.tab_inicio.ir_documentacion.connect(self._mostrar_documentacion)
        self.tab_nueva.factura_guardada.connect(self._on_factura_cambiada)
        self.tab_nueva.factura_emitida.connect(self._on_factura_cambiada)
        self.tab_nueva.estado_mensaje.connect(self._mostrar_estado)
        self.tab_listado.editar_borrador.connect(self._abrir_factura)
        self.tab_listado.factura_duplicada.connect(self._abrir_factura_duplicada)
        self.tab_listado.factura_rectificada.connect(self._abrir_factura)
        self.tab_listado.estado_mensaje.connect(self._mostrar_estado)
        self.tab_nueva.factura_enviada.connect(self._on_factura_cambiada)
        self.tab_presupuesto.presupuesto_guardado.connect(self._on_presupuesto_cambiado)
        self.tab_presupuesto.presupuesto_emitido.connect(self._on_presupuesto_cambiado)
        self.tab_presupuesto.estado_mensaje.connect(self._mostrar_estado)
        self.tab_listado_pres.editar_borrador.connect(self._abrir_presupuesto)
        self.tab_listado_pres.convertido_en_factura.connect(self._abrir_factura_desde_presupuesto)
        self.tab_listado_pres.ver_factura_asociada.connect(self._abrir_factura)
        self.tab_listado_pres.estado_mensaje.connect(self._mostrar_estado)
        self.tab_clientes.clientes_actualizados.connect(self.tab_nueva.recargar_clientes)
        self.tab_clientes.clientes_actualizados.connect(self.tab_presupuesto.recargar_clientes)
        self.tab_clientes.estado_mensaje.connect(self._mostrar_estado)

        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._mostrar_estado("Listo — LEFA v" + __version__)

    def _activar_ventana(self) -> None:
        """
        Lleva el foco a la ventana sin desmaximizar ni cambiar el tamaño.

        Solo restaura si estaba oculta (bandeja) o minimizada.
        """
        estado = self.windowState()
        if not self.isVisible() or (estado & Qt.WindowState.WindowMinimized):
            self.setWindowState(
                (estado & ~Qt.WindowState.WindowMinimized)
                | Qt.WindowState.WindowActive
            )
            if not self.isVisible():
                self.show()
        self.raise_()
        self.activateWindow()

    def _arranque_inicial(self) -> None:
        """Pestaña Inicio y bienvenida opcional en el primer arranque."""
        self.tabs.setCurrentWidget(self.tab_inicio)
        prefs = PreferenciasService.cargar()
        if not prefs.mostrar_bienvenida:
            return
        dlg = BienvenidaDialog(self)
        if dlg.exec() and dlg.no_volver_a_mostrar():
            prefs.mostrar_bienvenida = False
            PreferenciasService.guardar(prefs)

    def _ir_a_nueva_factura(self) -> None:
        self.tabs.setCurrentWidget(self.tab_nueva)

    def _ir_a_listado(self) -> None:
        self.tabs.setCurrentWidget(self.tab_listado)

    def _ir_a_presupuesto(self) -> None:
        self.tabs.setCurrentWidget(self.tab_presupuesto)

    def _ir_a_listado_presupuestos(self) -> None:
        self.tabs.setCurrentWidget(self.tab_listado_pres)

    def _on_presupuesto_cambiado(self, _id: int) -> None:
        self.tab_listado_pres.refrescar()

    def _abrir_presupuesto(self, presupuesto_id: int) -> None:
        self.tabs.setCurrentWidget(self.tab_presupuesto)
        self.tab_presupuesto.cargar_presupuesto(presupuesto_id)

    def _on_factura_cambiada(self, _factura_id: int) -> None:
        self.tab_listado.refrescar()
        self.tab_inicio.refrescar_resumen()

    def _abrir_factura(self, factura_id: int) -> None:
        """Abre un borrador en Nueva Factura y lleva el foco a la ventana."""
        self.tabs.setCurrentWidget(self.tab_nueva)
        self.tab_nueva.cargar_factura(factura_id)
        self.tab_listado.refrescar()

    def _abrir_factura_duplicada(self, factura_id: int) -> None:
        self._abrir_factura(factura_id)

    def _abrir_factura_desde_presupuesto(self, factura_id: int) -> None:
        """Tras convertir presupuesto: abre el borrador listo para emitir."""
        self._abrir_factura(factura_id)
        self._mostrar_estado(
            "Presupuesto convertido — revise la factura en esta pestaña y pulse Emitir."
        )

    def _mostrar_estado(self, mensaje: str) -> None:
        self.status_bar.showMessage(mensaje, 8000)

    def _salir_aplicacion(self) -> None:
        """Cierra la aplicación por completo (Linux y Windows)."""
        self._salida_definitiva = True
        self._preparar_cierre()
        if self._tray is not None:
            self._tray.hide()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Con bandeja activa, la X oculta la ventana y deja LEFA en segundo plano.
        El cierre real solo ocurre con Archivo → Salir o desde la bandeja.
        """
        if self._tray is not None and not self._salida_definitiva:
            event.ignore()
            self.hide()
            self._tray.notificar_minimizado()
            return

        self._preparar_cierre()
        if self._tray is not None:
            self._tray.hide()
        event.accept()

    def _preparar_cierre(self) -> None:
        """Detiene tareas asíncronas antes de salir."""
        if self._cierre_preparado:
            return
        self._cierre_preparado = True
        self.tab_nueva.detener_workers()
        self.tab_presupuesto.detener_workers()

    def _mostrar_sobre(self) -> None:
        """Muestra el diálogo 'Sobre LEFA'."""
        self._activar_ventana()
        AboutDialog(self).exec()

    def _mostrar_documentacion(self) -> None:
        """Abre la guía de uso integrada."""
        self._activar_ventana()
        DocumentacionDialog(self).exec()

    def _ir_a_clientes(self) -> None:
        self.tabs.setCurrentWidget(self.tab_clientes)

    def _nuevo_cliente(self) -> None:
        dialogo = ClienteDialog(self)
        if dialogo.exec() and dialogo.cliente_id is not None:
            self.tab_clientes.refrescar()
            self.tab_nueva.recargar_clientes(seleccionar_id=dialogo.cliente_id)
            self.tab_presupuesto.recargar_clientes(seleccionar_id=dialogo.cliente_id)
            self._mostrar_estado("Cliente creado correctamente.")

    def _configurar_correo(self) -> None:
        self._activar_ventana()
        if SmtpConfigDialog(self).exec():
            self._mostrar_estado("Configuración de correo actualizada.")

    def _mostrar_preferencias(self) -> None:
        self._activar_ventana()
        if PreferenciasDialog(self).exec():
            self.tab_nueva.aplicar_preferencias()
            self._mostrar_estado("Preferencias actualizadas.")

    def _crear_backup(self) -> None:
        self._activar_ventana()
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar copia de seguridad",
            f"backup_{date.today().isoformat()}.zip",
            "Archivo ZIP (*.zip)",
        )
        if not ruta:
            return
        try:
            destino = BackupService.crear_backup(Path(ruta))
            informacion(
                self,
                "Copia de seguridad",
                f"Copia creada correctamente:\n{destino}\n\n"
                "Nota: la contraseña SMTP está en el llavero del sistema "
                "y no se incluye en el ZIP.",
            )
            self._mostrar_estado(f"Copia de seguridad: {destino.name}")
        except Exception as exc:
            from lefa.ui.messages import error

            error(self, "Error al crear copia", str(exc))

    def _mostrar_plantillas(self) -> None:
        self._activar_ventana()
        dlg = PlantillasDialog(self)
        dlg.plantillas_actualizadas.connect(self.tab_nueva._cargar_plantillas)
        dlg.exec()

    def _mostrar_plantillas_factura(self) -> None:
        self._activar_ventana()
        dlg = PlantillasFacturaDialog(self)
        dlg.plantilla_usada.connect(self._abrir_factura)
        dlg.exec()

    def _mostrar_servicios(self) -> None:
        self._activar_ventana()
        dlg = ServiciosDialog(self)
        dlg.servicios_actualizados.connect(self.tab_nueva._cargar_servicios)
        dlg.exec()

    def _exportar_verifactu(self) -> None:
        self._activar_ventana()
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar registros VeriFactu",
            f"verifactu_export_{date.today().isoformat()}.zip",
            "Archivo ZIP (*.zip)",
        )
        if not ruta:
            return
        try:
            destino = VerifactuExport.exportar_zip(Path(ruta))
            informacion(self, "VeriFactu", f"Registros exportados:\n{destino}")
            self._mostrar_estado(f"VeriFactu: {destino.name}")
        except Exception as exc:
            from lefa.ui.messages import error

            error(self, "Error al exportar", str(exc))

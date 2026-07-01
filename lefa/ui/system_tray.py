"""
Icono en la bandeja del sistema con menú contextual.

Replica las opciones del menú superior de la ventana principal.
"""

from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from lefa import __app_name__
from lefa.resources import get_app_icon


class SystemTray(QSystemTrayIcon):
    """Bandeja del sistema con menú contextual y acceso rápido a la ventana."""

    def __init__(self, ventana, acciones: dict[str, QAction], parent=None):
        super().__init__(parent)
        self._ventana = ventana
        self.setIcon(get_app_icon())
        self.setToolTip(__app_name__)
        self.setContextMenu(self._crear_menu_contextual(acciones))
        self.activated.connect(self._on_activated)

    def _crear_menu_contextual(self, acciones: dict[str, QAction]) -> QMenu:
        """Construye el menú de clic derecho con la misma estructura que la barra superior."""
        menu = QMenu()

        menu_archivo = menu.addMenu("&Archivo")
        menu_archivo.addAction(acciones["backup"])
        menu_archivo.addSeparator()
        menu_archivo.addAction(acciones["salir"])

        menu_clientes = menu.addMenu("&Clientes")
        menu_clientes.addAction(acciones["nuevo_cliente"])
        menu_clientes.addAction(acciones["gestionar_clientes"])

        menu_herramientas = menu.addMenu("&Herramientas")
        menu_herramientas.addAction(acciones["config_correo"])
        menu_herramientas.addAction(acciones["preferencias"])
        menu_herramientas.addAction(acciones["plantillas"])
        menu_herramientas.addAction(acciones["plantillas_factura"])
        menu_herramientas.addAction(acciones["servicios"])
        menu_herramientas.addSeparator()
        menu_herramientas.addAction(acciones["export_verifactu"])

        menu_ayuda = menu.addMenu("A&yuda")
        menu_ayuda.addAction(acciones["documentacion"])
        menu_ayuda.addSeparator()
        menu_ayuda.addAction(acciones["sobre"])

        return menu

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Doble clic (o clic simple en algunos entornos) restaura la ventana principal."""
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self._mostrar_ventana()

    def _mostrar_ventana(self) -> None:
        self._ventana._activar_ventana()

    def notificar_minimizado(self) -> None:
        """Avisa al usuario de que la aplicación sigue activa en la bandeja."""
        self.showMessage(
            __app_name__,
            "LEFA sigue ejecutándose en la bandeja del sistema.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

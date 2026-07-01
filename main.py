#!/usr/bin/env python3
"""
LEFA — Local & Eficiente Facturación para Autónomos.

Punto de entrada de la aplicación de escritorio.

Arquitectura en capas:
    ┌─────────────────────────────────────────┐
    │  UI (PyQt6)          main_window, tabs  │
    ├─────────────────────────────────────────┤
    │  Workers (QThread) pdf_worker, smtp     │
    ├─────────────────────────────────────────┤
    │  Services            factura, pdf, cli  │
    ├─────────────────────────────────────────┤
    │  Models (SQLAlchemy) Cliente, Factura   │
    ├─────────────────────────────────────────┤
    │  Database (SQLite)   ~/.lefa/lefa.db    │
    └─────────────────────────────────────────┘

Ejecución:
    pip install -r requirements.txt
    python main.py
"""

import os
import signal
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from lefa.database import init_database
from lefa.ui import MainWindow


def _configurar_cierre_por_terminal(app: QApplication, ventana: MainWindow) -> None:
    """
    Permite cerrar la aplicación con Ctrl+C en la terminal.

    La señal se encola en el hilo principal de Qt (no llamar a quit() desde
    el manejador de señales directamente). Compatible con Linux y Windows.
    """
    cerrando = {"activo": False}

    def _solicitar_cierre(_signum, _frame) -> None:
        if cerrando["activo"]:
            # Segundo Ctrl+C: salida inmediata sin volcar traceback.
            os._exit(0)
        cerrando["activo"] = True
        ventana._salida_definitiva = True
        QTimer.singleShot(0, app.quit)

    signal.signal(signal.SIGINT, _solicitar_cierre)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _solicitar_cierre)

    timer = QTimer(app)
    timer.timeout.connect(lambda: None)
    timer.start(250)


def main() -> int:
    # Inicializar persistencia local antes de mostrar la UI
    init_database()

    app = QApplication(sys.argv)
    app.setApplicationName("LEFA")
    app.setOrganizationName("LEFA")

    ventana = MainWindow()
    _configurar_cierre_por_terminal(app, ventana)
    app.setWindowIcon(ventana.windowIcon())
    app.aboutToQuit.connect(ventana._preparar_cierre)
    ventana.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

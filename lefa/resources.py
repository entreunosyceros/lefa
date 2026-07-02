"""
Rutas a recursos estáticos (imágenes, etc.).

Resuelve rutas de forma portable en Linux y Windows, tanto en desarrollo
como cuando el proyecto se instala en un directorio de solo lectura.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QPixmap

# Raíz del paquete lefa/ y del proyecto (contiene img/, main.py, etc.)
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent

# URL pública del repositorio
GITHUB_URL = "https://github.com/entreunosyceros/lefa"


def get_project_dir() -> Path:
    """
    Directorio base del proyecto.

    Prioridad:
    1. Variable de entorno LEFA_PROJECT_DIR (instalaciones empaquetadas).
    2. Carpeta padre del paquete lefa (desarrollo y ejecución desde fuente).
    """
    import os

    override = os.environ.get("LEFA_PROJECT_DIR")
    if override:
        return Path(override)
    return PROJECT_DIR


def get_logo_path() -> Path:
    """Ruta absoluta a ``<raíz_del_proyecto>/img/logo.png``."""
    return get_project_dir() / "img" / "logo.png"


def get_app_icon() -> QIcon:
    """Icono de la aplicación escalado para ventana y bandeja del sistema."""
    # El icono de la aplicación (ventana/bandeja) debe ser estable y NO depender
    # del logotipo configurable del PDF. Así evitamos que cambiar el logo de factura
    # afecte a la identidad visual del programa en el sistema.
    logo_path = get_logo_path()

    if not logo_path.is_file():
        logo_path = get_logo_path()
        return QIcon()

    # Evita crashes en contextos sin aplicación Qt inicializada (p. ej. scripts).
    if QGuiApplication.instance() is None:
        return QIcon(str(logo_path))

    pixmap = QPixmap(str(logo_path))
    if pixmap.isNull():
        return QIcon()

    icon = QIcon()
    for size in (16, 24, 32, 48, 64):
        icon.addPixmap(
            pixmap.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    return icon

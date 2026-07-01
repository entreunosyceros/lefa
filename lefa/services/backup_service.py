"""
Copias de seguridad locales en ZIP.
"""

from __future__ import annotations

import zipfile
from datetime import date
from pathlib import Path

from lefa.config import (
    APP_DATA_DIR,
    DATABASE_PATH,
    FACTURAE_OUTPUT_DIR,
    PDF_OUTPUT_DIR,
    PREFERENCIAS_PATH,
    PRESUPUESTOS_PDF_DIR,
    SMTP_CONFIG_PATH,
    VERIFACTU_REGISTROS_DIR,
    ensure_directories,
)


class BackupService:
    """Empaqueta la base de datos, PDFs y configuración en un archivo ZIP."""

    @staticmethod
    def crear_backup(ruta_destino: Path | None = None) -> Path:
        ensure_directories()
        if ruta_destino is None:
            nombre = f"backup_{date.today().isoformat()}.zip"
            ruta_destino = APP_DATA_DIR / nombre
        else:
            ruta_destino = Path(ruta_destino)

        if ruta_destino.suffix.lower() != ".zip":
            ruta_destino = ruta_destino.with_suffix(".zip")

        with zipfile.ZipFile(ruta_destino, "w", zipfile.ZIP_DEFLATED) as zf:
            if DATABASE_PATH.is_file():
                zf.write(DATABASE_PATH, "lefa.db")
            if PREFERENCIAS_PATH.is_file():
                zf.write(PREFERENCIAS_PATH, "preferencias.json")
            if SMTP_CONFIG_PATH.is_file():
                zf.write(SMTP_CONFIG_PATH, "smtp_config.json")
            if VERIFACTU_REGISTROS_DIR.is_dir():
                for reg in VERIFACTU_REGISTROS_DIR.glob("*.json"):
                    zf.write(reg, f"verifactu/registros/{reg.name}")
            if FACTURAE_OUTPUT_DIR.is_dir():
                for xml in FACTURAE_OUTPUT_DIR.rglob("*.xml"):
                    zf.write(xml, f"facturas_xml/{xml.relative_to(FACTURAE_OUTPUT_DIR)}")
            if PDF_OUTPUT_DIR.is_dir():
                for pdf in PDF_OUTPUT_DIR.rglob("*.pdf"):
                    zf.write(pdf, f"facturas_pdf/{pdf.relative_to(PDF_OUTPUT_DIR)}")
            if PRESUPUESTOS_PDF_DIR.is_dir():
                for pdf in PRESUPUESTOS_PDF_DIR.rglob("*.pdf"):
                    zf.write(pdf, f"presupuestos_pdf/{pdf.relative_to(PRESUPUESTOS_PDF_DIR)}")

        return ruta_destino

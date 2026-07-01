"""
Exportación de registros VeriFactu para auditoría o envío futuro a AEAT.
"""

from __future__ import annotations

import json
import zipfile
from datetime import date
from pathlib import Path

from lefa.config import VERIFACTU_REGISTROS_DIR, ensure_directories


class VerifactuExport:
    """Empaqueta los registros JSON en un ZIP legible por máquinas."""

    @staticmethod
    def exportar_zip(ruta_destino: Path | None = None) -> Path:
        ensure_directories()
        if ruta_destino is None:
            ruta_destino = (
                VERIFACTU_REGISTROS_DIR.parent
                / f"verifactu_export_{date.today().isoformat()}.zip"
            )
        else:
            ruta_destino = Path(ruta_destino)
            if ruta_destino.suffix.lower() != ".zip":
                ruta_destino = ruta_destino.with_suffix(".zip")

        registros = list(VERIFACTU_REGISTROS_DIR.glob("*.json")) if VERIFACTU_REGISTROS_DIR.is_dir() else []

        with zipfile.ZipFile(ruta_destino, "w", zipfile.ZIP_DEFLATED) as zf:
            for registro in registros:
                zf.write(registro, f"registros/{registro.name}")
            indice = [json.loads(r.read_text(encoding="utf-8")) for r in registros]
            zf.writestr(
                "indice.json",
                json.dumps(indice, indent=2, ensure_ascii=False),
            )

        return ruta_destino

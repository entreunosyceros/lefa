"""
PDF de presupuestos (sin QR tributario ni Facturae).
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from lefa.config import PRESUPUESTOS_PDF_DIR, ensure_directories
from lefa.models import EstadoPresupuesto, Presupuesto
from lefa.services.preferencias_service import PreferenciasService


class PresupuestoPDFService:
    @staticmethod
    def generar(presupuesto: Presupuesto) -> Path:
        ensure_directories()
        prefs = PreferenciasService.cargar()
        pdf_dir = PRESUPUESTOS_PDF_DIR
        pdf_dir.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        logo_path = PreferenciasService.obtener_logotipo()
        y_inicio = 10
        if logo_path.is_file():
            try:
                pdf.image(str(logo_path), x=10, y=y_inicio, h=22)
                y_inicio = 36
            except Exception:
                pass

        pdf.set_y(y_inicio)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "PRESUPUESTO", ln=True, align="R")
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, prefs.emisor_razon_social, ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.cell(0, 5, f"CIF: {prefs.emisor_cif}", ln=True)
        pdf.cell(0, 5, prefs.emisor_direccion, ln=True)
        pdf.cell(0, 5, prefs.emisor_email, ln=True)
        pdf.ln(8)

        numero = presupuesto.numero_presupuesto or f"BORRADOR #{presupuesto.id}"
        fecha_str = (
            presupuesto.fecha_emision.strftime("%d/%m/%Y")
            if presupuesto.fecha_emision
            else "Pendiente"
        )
        validez = (
            presupuesto.validez_hasta.strftime("%d/%m/%Y")
            if presupuesto.validez_hasta
            else "—"
        )

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(95, 6, "Datos del presupuesto", border=0)
        pdf.cell(95, 6, "Cliente", border=0, ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.cell(95, 5, f"Número: {numero}")
        pdf.cell(95, 5, presupuesto.cliente.razon_social, ln=True)
        pdf.cell(95, 5, f"Fecha: {fecha_str}")
        pdf.cell(95, 5, f"NIF: {presupuesto.cliente.cif_nif}", ln=True)
        pdf.cell(95, 5, f"Válido hasta: {validez}")
        pdf.cell(95, 5, presupuesto.cliente.email, ln=True)
        pdf.ln(8)

        col_widths = [80, 25, 35, 35]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for i, h in enumerate(["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]):
            pdf.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", size=9)
        for linea in presupuesto.lineas:
            pdf.cell(col_widths[0], 7, linea.descripcion[:60], border=1)
            pdf.cell(col_widths[1], 7, f"{linea.cantidad:.2f}", border=1, align="R")
            pdf.cell(col_widths[2], 7, f"{linea.precio_unitario:.2f} EUR", border=1, align="R")
            pdf.cell(col_widths[3], 7, f"{linea.subtotal:.2f} EUR", border=1, align="R")
            pdf.ln()

        pdf.ln(6)
        subtotal = presupuesto.calcular_subtotal()
        iva = presupuesto.calcular_iva()
        irpf = presupuesto.calcular_irpf()
        total = presupuesto.calcular_total()
        x = 120
        pdf.set_x(x)
        pdf.cell(40, 6, "Subtotal:", align="R")
        pdf.cell(30, 6, f"{subtotal:.2f} EUR", align="R", ln=True)
        pdf.set_x(x)
        pdf.cell(40, 6, f"IVA ({presupuesto.porc_iva:.0f}%):", align="R")
        pdf.cell(30, 6, f"{iva:.2f} EUR", align="R", ln=True)
        pdf.set_x(x)
        pdf.cell(40, 6, f"IRPF ({presupuesto.porc_irpf:.0f}%):", align="R")
        pdf.cell(30, 6, f"-{irpf:.2f} EUR", align="R", ln=True)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(x)
        pdf.cell(40, 8, "TOTAL:", align="R")
        pdf.cell(30, 8, f"{total:.2f} EUR", align="R", ln=True)

        if presupuesto.estado == EstadoPresupuesto.BORRADOR:
            pdf.ln(8)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "BORRADOR — Sin validez comercial", ln=True, align="C")
            pdf.set_text_color(0, 0, 0)

        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(
            0,
            4,
            "Este documento es un presupuesto informativo. No sustituye a una factura.",
        )

        if presupuesto.numero_presupuesto:
            nombre = f"{presupuesto.numero_presupuesto.replace('/', '-')}.pdf"
        else:
            nombre = f"PRES_BORRADOR_{presupuesto.id}.pdf"
        ruta = pdf_dir / nombre
        pdf.output(str(ruta))
        return ruta

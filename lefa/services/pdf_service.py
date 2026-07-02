"""
Generación de PDFs de factura con FPDF2.

Renderizado nativo sin dependencias de navegador ni LaTeX.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from lefa.config import ensure_directories
from lefa.models import EstadoFactura, Factura
from lefa.services.preferencias_service import PreferenciasService
from lefa.verifactu.qr import QR_MM, generar_qr_png, texto_legal_qr, url_verificacion


class PDFService:
    """Construye documentos PDF profesionales a partir de una Factura ORM."""

    @staticmethod
    def _texto_pdf_safe(texto: str) -> str:
        """
        Normaliza caracteres problemáticos para las fuentes core (Helvetica).

        FPDF con fuentes core no soporta algunos símbolos Unicode como “—”.
        """
        return (
            (texto or "")
            .replace("\u2014", "-")  # em dash —
            .replace("\u2013", "-")  # en dash –
            .replace("\u2212", "-")  # minus sign −
        )

    @staticmethod
    def generar(factura: Factura) -> Path:
        """
        Genera el PDF y devuelve la ruta del archivo creado.

        El nombre del archivo depende del estado:
        - Borrador: BORRADOR_{id}.pdf
        - Emitida/Cobrada: {numero_factura}.pdf
        """
        ensure_directories()
        prefs = PreferenciasService.cargar()
        pdf_dir = PreferenciasService.obtener_carpeta_pdf()
        pdf_dir.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        # Reservar columna derecha para QR (evita solapar el título "FACTURA")
        qr_reserva_mm = 0.0

        # --- QR tributario (facturas emitidas) ---
        if factura.numero_factura and factura.fecha_emision:
            url_qr = url_verificacion(
                prefs.emisor_cif,
                factura.numero_factura,
                factura.fecha_emision,
                factura.calcular_total(),
                hash_registro=factura.verifactu_hash,
            )
            qr_tmp = pdf_dir / f".qr_{factura.id}.png"
            try:
                generar_qr_png(url_qr, qr_tmp)
                # Colocación relativa a la página (sin hardcodear 158mm)
                qr_gap = 4.0
                qr_x = pdf.w - pdf.r_margin - QR_MM
                qr_y = 10.0
                pdf.image(str(qr_tmp), x=qr_x, y=qr_y, w=QR_MM, h=QR_MM)
                pdf.set_xy(qr_x - 2, qr_y + QR_MM + 1)
                pdf.set_font("Helvetica", "B", size=6)
                pdf.multi_cell(
                    QR_MM + 4,
                    3,
                    texto_legal_qr(),
                    align="C",
                )
                qr_reserva_mm = QR_MM + qr_gap
            finally:
                if qr_tmp.is_file():
                    qr_tmp.unlink(missing_ok=True)
            pdf.set_font("Helvetica", size=10)

        # --- Logotipo (esquina superior izquierda) ---
        logo_path = PreferenciasService.obtener_logotipo()
        y_inicio = 10
        if logo_path.is_file():
            try:
                pdf.image(str(logo_path), x=10, y=y_inicio, h=22)
                y_inicio = 36
            except Exception:
                y_inicio = 10

        # --- Cabecera emisor ---
        pdf.set_y(y_inicio)
        titulo = "FACTURA RECTIFICATIVA" if factura.es_rectificativa else "FACTURA"
        pdf.set_font("Helvetica", "B", 18)
        # Imprimir el título alineado a la derecha, pero sin invadir la columna del QR
        ancho_util = pdf.w - pdf.l_margin - pdf.r_margin
        ancho_titulo = max(0.0, ancho_util - qr_reserva_mm)
        pdf.cell(ancho_titulo, 10, titulo, ln=True, align="R")
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(ancho_titulo, 6, prefs.emisor_razon_social, ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.cell(ancho_titulo, 5, f"CIF: {prefs.emisor_cif}", ln=True)
        pdf.cell(ancho_titulo, 5, prefs.emisor_direccion, ln=True)
        if prefs.emisor_telefono.strip():
            pdf.cell(ancho_titulo, 5, f"Tel: {prefs.emisor_telefono.strip()}", ln=True)
        pdf.cell(ancho_titulo, 5, prefs.emisor_email, ln=True)
        if prefs.emisor_iban.strip():
            pdf.cell(ancho_titulo, 5, f"IBAN: {prefs.emisor_iban.strip()}", ln=True)
        pdf.ln(8)

        # --- Datos factura y cliente ---
        numero = factura.numero_factura or f"BORRADOR #{factura.id}"
        fecha_str = (
            factura.fecha_emision.strftime("%d/%m/%Y")
            if factura.fecha_emision
            else "Pendiente de emisión"
        )
        venc_str = (
            factura.fecha_vencimiento.strftime("%d/%m/%Y")
            if factura.fecha_vencimiento
            else "-"
        )

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(95, 6, "Datos de la factura", border=0)
        pdf.cell(95, 6, "Cliente", border=0, ln=True)
        pdf.set_font("Helvetica", size=9)

        pdf.cell(95, 5, f"Número: {numero}")
        pdf.cell(95, 5, factura.cliente.razon_social, ln=True)
        pdf.cell(95, 5, f"Fecha emisión: {fecha_str}")
        pdf.cell(95, 5, f"CIF/NIF: {factura.cliente.cif_nif}", ln=True)
        pdf.cell(95, 5, f"Vencimiento: {venc_str}")
        pdf.cell(95, 5, factura.cliente.direccion, ln=True)
        pdf.cell(95, 5, f"Estado: {factura.estado.value}")
        pdf.cell(95, 5, factura.cliente.email, ln=True)
        if factura.es_rectificativa and factura.factura_rectificada:
            orig = factura.factura_rectificada
            fecha_orig = (
                orig.fecha_emision.strftime("%d/%m/%Y") if orig.fecha_emision else "?"
            )
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(180, 0, 0)
            pdf.cell(
                0,
                5,
                f"Rectifica factura {orig.numero_factura} de {fecha_orig}",
                ln=True,
            )
            pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

        # --- Tabla de líneas ---
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        col_widths = [80, 25, 35, 35]
        headers = ["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", size=9)
        for linea in factura.lineas:
            pdf.cell(col_widths[0], 7, linea.descripcion[:60], border=1)
            pdf.cell(col_widths[1], 7, f"{linea.cantidad:.2f}", border=1, align="R")
            pdf.cell(
                col_widths[2], 7, f"{linea.precio_unitario:.2f} EUR", border=1, align="R"
            )
            pdf.cell(col_widths[3], 7, f"{linea.subtotal:.2f} EUR", border=1, align="R")
            pdf.ln()

        pdf.ln(6)

        # --- Totales ---
        subtotal = factura.calcular_subtotal()
        iva = factura.calcular_iva()
        irpf = factura.calcular_irpf()
        total = factura.calcular_total()

        x_totales = 120
        pdf.set_x(x_totales)
        pdf.cell(40, 6, "Subtotal:", align="R")
        pdf.cell(30, 6, f"{subtotal:.2f} EUR", align="R", ln=True)
        pdf.set_x(x_totales)
        pdf.cell(40, 6, f"IVA ({factura.porc_iva:.0f}%):", align="R")
        pdf.cell(30, 6, f"{iva:.2f} EUR", align="R", ln=True)
        pdf.set_x(x_totales)
        pdf.cell(40, 6, f"IRPF ({factura.porc_irpf:.0f}%):", align="R")
        pdf.cell(30, 6, f"-{irpf:.2f} EUR", align="R", ln=True)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(x_totales)
        pdf.cell(40, 8, "TOTAL:", align="R")
        pdf.cell(30, 8, f"{total:.2f} EUR", align="R", ln=True)

        if factura.estado == EstadoFactura.BORRADOR:
            pdf.ln(10)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "DOCUMENTO EN BORRADOR - Sin validez fiscal", ln=True, align="C")
            pdf.set_text_color(0, 0, 0)

        pie = (prefs.pie_factura or "").strip()
        if pie:
            pdf.ln(8)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(90, 90, 90)
            pdf.multi_cell(0, 4, PDFService._texto_pdf_safe(pie))
            pdf.set_text_color(0, 0, 0)

        # --- Guardar archivo ---
        if factura.numero_factura:
            nombre = f"{factura.numero_factura.replace('/', '-')}.pdf"
        else:
            nombre = f"BORRADOR_{factura.id}.pdf"

        ruta = pdf_dir / nombre
        pdf.output(str(ruta))
        return ruta

    @staticmethod
    def ruta_pdf_factura(factura: Factura) -> Path:
        """Devuelve la ruta esperada del PDF sin generarlo."""
        if factura.numero_factura:
            nombre = f"{factura.numero_factura.replace('/', '-')}.pdf"
        else:
            nombre = f"BORRADOR_{factura.id}.pdf"
        return PreferenciasService.obtener_carpeta_pdf() / nombre

    @staticmethod
    def obtener_o_generar(factura: Factura) -> Path:
        """Devuelve el PDF existente o lo genera si aún no está en disco."""
        ruta = PDFService.ruta_pdf_factura(factura)
        if ruta.is_file():
            return ruta
        return PDFService.generar(factura)

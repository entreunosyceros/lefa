"""
Generación de facturas electrónicas Facturae 3.2 (XML).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from lefa.config import FACTURAE_OUTPUT_DIR, ensure_directories
from lefa.models import Factura
from lefa.services.preferencias_service import PreferenciasService

NS = "http://www.facturae.gob.es/formato/Versiones/Facturaev3_2_2.xml"
ET.register_namespace("", NS)

# Facturae: 04 = transferencia bancaria
FORMA_PAGO_TRANSFERENCIA = "04"
UNIDAD_MEDIDA_UNIDADES = "01"


class FacturaeService:
    """Genera XML Facturae al emitir facturas."""

    @staticmethod
    def _sub(parent, tag: str, text: str | None = None):
        el = ET.SubElement(parent, f"{{{NS}}}{tag}")
        if text is not None:
            el.text = text
        return el

    @staticmethod
    def _añadir_centros_dir3(legal_entity, cliente) -> None:
        """Códigos DIR3 obligatorios en FACe para administraciones públicas."""
        centros = [
            (cliente.dir3_oficina, "01"),  # Oficina contable
            (cliente.dir3_organo, "02"),  # Órgano gestor
            (cliente.dir3_unidad, "03"),  # Unidad tramitadora
        ]
        for codigo, rol in centros:
            if not codigo.strip():
                continue
            centro = ET.SubElement(legal_entity, f"{{{NS}}}AdministrativeCentre")
            FacturaeService._sub(centro, "CentreCode", codigo.strip())
            FacturaeService._sub(centro, "RoleTypeCode", rol)
            FacturaeService._sub(centro, "Name", cliente.razon_social)

    @staticmethod
    def generar(factura: Factura) -> Path:
        if not factura.numero_factura or not factura.fecha_emision:
            raise ValueError("Solo se genera Facturae para facturas emitidas.")

        ensure_directories()
        prefs = PreferenciasService.cargar()
        FACTURAE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        cliente = factura.cliente
        forma_pago = (
            cliente.forma_pago.strip()
            or prefs.facturae_forma_pago.strip()
            or FORMA_PAGO_TRANSFERENCIA
        )
        iban = prefs.emisor_iban.strip().replace(" ", "")
        if not iban and cliente.iban.strip():
            iban = cliente.iban.strip().replace(" ", "")

        root = ET.Element(f"{{{NS}}}Facturae")
        inv = ET.SubElement(root, f"{{{NS}}}Invoices")
        invoice = ET.SubElement(inv, f"{{{NS}}}Invoice")

        header = ET.SubElement(invoice, f"{{{NS}}}InvoiceHeader")
        FacturaeService._sub(header, "InvoiceNumber", factura.numero_factura)
        doc_type = "R1" if factura.es_rectificativa else "FC"
        FacturaeService._sub(header, "InvoiceDocumentType", doc_type)
        FacturaeService._sub(header, "InvoiceClass", "OO")

        issue = ET.SubElement(invoice, f"{{{NS}}}InvoiceIssueData")
        FacturaeService._sub(issue, "IssueDate", factura.fecha_emision.isoformat())
        FacturaeService._sub(issue, "InvoiceCurrencyCode", "EUR")
        if factura.fecha_vencimiento:
            FacturaeService._sub(issue, "TaxCurrencyCode", "EUR")
            FacturaeService._sub(
                issue, "LanguageName", "es"
            )

        parties = ET.SubElement(invoice, f"{{{NS}}}Parties")
        seller = ET.SubElement(parties, f"{{{NS}}}SellerParty")
        seller_tax = ET.SubElement(seller, f"{{{NS}}}TaxIdentification")
        FacturaeService._sub(seller_tax, "PersonTypeCode", "J")
        FacturaeService._sub(seller_tax, "ResidenceTypeCode", "R")
        FacturaeService._sub(seller_tax, "TaxIdentificationNumber", prefs.emisor_cif)
        seller_legal = ET.SubElement(seller, f"{{{NS}}}LegalEntity")
        FacturaeService._sub(seller_legal, "CorporateName", prefs.emisor_razon_social)
        addr_s = ET.SubElement(seller_legal, f"{{{NS}}}AddressInSpain")
        FacturaeService._sub(addr_s, "Address", prefs.emisor_direccion)

        buyer = ET.SubElement(parties, f"{{{NS}}}BuyerParty")
        buyer_tax = ET.SubElement(buyer, f"{{{NS}}}TaxIdentification")
        FacturaeService._sub(buyer_tax, "PersonTypeCode", "J")
        FacturaeService._sub(buyer_tax, "ResidenceTypeCode", "R")
        FacturaeService._sub(buyer_tax, "TaxIdentificationNumber", cliente.cif_nif)
        buyer_legal = ET.SubElement(buyer, f"{{{NS}}}LegalEntity")
        FacturaeService._sub(buyer_legal, "CorporateName", cliente.razon_social)
        addr_b = ET.SubElement(buyer_legal, f"{{{NS}}}AddressInSpain")
        FacturaeService._sub(addr_b, "Address", cliente.direccion or "-")
        FacturaeService._añadir_centros_dir3(buyer_legal, cliente)

        items = ET.SubElement(invoice, f"{{{NS}}}Items")
        for linea in factura.lineas:
            line = ET.SubElement(items, f"{{{NS}}}InvoiceLine")
            FacturaeService._sub(line, "ItemDescription", linea.descripcion)
            FacturaeService._sub(line, "Quantity", f"{linea.cantidad:.2f}")
            FacturaeService._sub(line, "UnitOfMeasure", UNIDAD_MEDIDA_UNIDADES)
            FacturaeService._sub(
                line, "UnitPriceWithoutTax", f"{linea.precio_unitario:.2f}"
            )
            FacturaeService._sub(line, "TotalCost", f"{linea.subtotal:.2f}")
            taxes = ET.SubElement(line, f"{{{NS}}}TaxesOutputs")
            tax = ET.SubElement(taxes, f"{{{NS}}}Tax")
            FacturaeService._sub(tax, "TaxTypeCode", "01")
            FacturaeService._sub(tax, "TaxRate", f"{factura.porc_iva:.2f}")

        totals = ET.SubElement(invoice, f"{{{NS}}}InvoiceTotals")
        FacturaeService._sub(
            totals, "TotalGrossAmount", f"{factura.calcular_subtotal():.2f}"
        )
        FacturaeService._sub(totals, "TotalGeneralDiscounts", "0.00")
        FacturaeService._sub(
            totals,
            "TotalGrossAmountBeforeTaxes",
            f"{factura.calcular_subtotal():.2f}",
        )
        FacturaeService._sub(
            totals, "TotalTaxOutputs", f"{factura.calcular_iva():.2f}"
        )
        FacturaeService._sub(
            totals, "TotalTaxesWithheld", f"{factura.calcular_irpf():.2f}"
        )
        FacturaeService._sub(totals, "InvoiceTotal", f"{factura.calcular_total():.2f}")
        FacturaeService._sub(
            totals,
            "TotalOutstandingAmount",
            f"{factura.calcular_total():.2f}",
        )
        FacturaeService._sub(
            totals,
            "TotalExecutableAmount",
            f"{factura.calcular_total():.2f}",
        )

        total = f"{factura.calcular_total():.2f}"
        vencimiento = (
            factura.fecha_vencimiento.isoformat()
            if factura.fecha_vencimiento
            else factura.fecha_emision.isoformat()
        )
        payment_details = ET.SubElement(invoice, f"{{{NS}}}PaymentDetails")
        installment = ET.SubElement(payment_details, f"{{{NS}}}Installment")
        FacturaeService._sub(installment, "InstallmentDueDate", vencimiento)
        FacturaeService._sub(installment, "InstallmentAmount", total)
        FacturaeService._sub(installment, "PaymentMeans", forma_pago)
        if iban:
            account = ET.SubElement(installment, f"{{{NS}}}AccountToBeCredited")
            FacturaeService._sub(account, "IBAN", iban)

        tree = ET.ElementTree(root)
        nombre = f"{factura.numero_factura.replace('/', '-')}.xml"
        ruta = FACTURAE_OUTPUT_DIR / nombre
        tree.write(str(ruta), encoding="UTF-8", xml_declaration=True)
        return ruta

    @staticmethod
    def ruta_facturae(factura: Factura) -> Path:
        if not factura.numero_factura:
            raise ValueError("Factura sin número.")
        nombre = f"{factura.numero_factura.replace('/', '-')}.xml"
        return FACTURAE_OUTPUT_DIR / nombre

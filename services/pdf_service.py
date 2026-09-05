"""
PDF Service providing server-side PDF compilation with dual-engine support:
Primary: WeasyPrint (HTML to PDF)
Fallback: ReportLab (Pure Python PDF generator for environments missing native C libraries)
"""
from io import BytesIO
import logging
from flask import render_template
from utils.formatting import format_indian_currency, format_date_display, sanitize_filename

logger = logging.getLogger(__name__)

# Attempt to import WeasyPrint
try:
    import weasyprint
    HAS_WEASYPRINT = True
except Exception as e:
    logger.warning(f"WeasyPrint unavailable: {e}")
    HAS_WEASYPRINT = False

# Attempt to import ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    HAS_REPORTLAB = True
except Exception as e:
    logger.warning(f"ReportLab unavailable: {e}")
    HAS_REPORTLAB = False


class PDFService:
    @classmethod
    def generate_quotation_pdf(cls, quotation_data: dict) -> tuple[bytes, str]:
        """
        Generate quotation PDF using WeasyPrint with ReportLab fallback.
        Returns (pdf_bytes, suggested_filename).
        """
        customer = quotation_data.get('customer', {})
        cust_name = customer.get('name', 'Customer').strip()
        clean_cust = sanitize_filename(cust_name)
        filename = f"Quotation_{clean_cust}.pdf"

        # Try WeasyPrint first
        if HAS_WEASYPRINT:
            try:
                pdf_bytes = cls._generate_quotation_weasyprint(quotation_data)
                return pdf_bytes, filename
            except Exception as err:
                logger.error(f"WeasyPrint PDF generation failed, falling back to ReportLab: {err}")

        # Fallback to ReportLab
        if HAS_REPORTLAB:
            try:
                pdf_bytes = cls._generate_quotation_reportlab(quotation_data)
                return pdf_bytes, filename
            except Exception as err:
                logger.error(f"ReportLab PDF generation failed: {err}")
                raise err

        raise RuntimeError("Neither WeasyPrint nor ReportLab is operational for PDF generation.")

    @classmethod
    def generate_invoice_pdf(cls, invoice_data: dict) -> tuple[bytes, str]:
        """
        Generate invoice PDF using WeasyPrint with ReportLab fallback.
        Returns (pdf_bytes, suggested_filename).
        """
        customer = invoice_data.get('customer', {})
        cust_name = customer.get('name', 'Customer').strip()
        clean_cust = sanitize_filename(cust_name)
        filename = f"Invoice_{clean_cust}.pdf"


        if HAS_WEASYPRINT:
            try:
                pdf_bytes = cls._generate_invoice_weasyprint(invoice_data)
                return pdf_bytes, filename
            except Exception as err:
                logger.error(f"WeasyPrint PDF generation failed, falling back to ReportLab: {err}")

        if HAS_REPORTLAB:
            try:
                pdf_bytes = cls._generate_invoice_reportlab(invoice_data)
                return pdf_bytes, filename
            except Exception as err:
                logger.error(f"ReportLab PDF generation failed: {err}")
                raise err

        raise RuntimeError("Neither WeasyPrint nor ReportLab is operational for PDF generation.")

    @staticmethod
    def _generate_quotation_weasyprint(quotation_data: dict) -> bytes:
        company = quotation_data.get('companySnapshot', {})
        customer = quotation_data.get('customer', {})
        items = quotation_data.get('items', [])
        tax = quotation_data.get('tax', {})
        subtotal = quotation_data.get('subtotal', 0)
        grand_total = quotation_data.get('grandTotal', 0)
        scope = quotation_data.get('scope', [])
        q_no = quotation_data.get('quotationNo', 'QTN-2026-000')
        date_str = quotation_data.get('date', '')

        formatted_items = []
        for it in items:
            formatted_items.append({
                'item': it.get('item', ''),
                'qty': it.get('qty', 1),
                'unit': it.get('unit', 'Units') if it.get('unit') else 'Units',
                'rate': format_indian_currency(it.get('rate', 0), include_symbol=True, suffix_dash=False),
                'amount': format_indian_currency(it.get('amount', 0), include_symbol=True, suffix_dash=True)
            })

        sgst_rate = tax.get('sgstRate', 9.0)
        cgst_rate = tax.get('cgstRate', 9.0)
        sgst_amount = tax.get('sgstAmount', 0)
        cgst_amount = tax.get('cgstAmount', 0)

        context = {
            'q_no': q_no,
            'date_display': format_date_display(date_str),
            'company': company,
            'customer': customer,
            'items': formatted_items,
            'sgst_rate_str': f"{sgst_rate:g}%" if isinstance(sgst_rate, (int, float)) else f"{sgst_rate}%",
            'cgst_rate_str': f"{cgst_rate:g}%" if isinstance(cgst_rate, (int, float)) else f"{cgst_rate}%",
            'sgst_amount': format_indian_currency(sgst_amount, include_symbol=True, suffix_dash=True),
            'cgst_amount': format_indian_currency(cgst_amount, include_symbol=True, suffix_dash=True),
            'subtotal': format_indian_currency(subtotal, include_symbol=True, suffix_dash=True),
            'grand_total': format_indian_currency(grand_total, include_symbol=True, suffix_dash=True),
            'scope': scope
        }

        html_content = render_template('quotation_pdf.html', **context)
        return weasyprint.HTML(string=html_content).write_pdf()

    @staticmethod
    def _generate_invoice_weasyprint(invoice_data: dict) -> bytes:
        company = invoice_data.get('companySnapshot', {})
        customer = invoice_data.get('customer', {})
        items = invoice_data.get('items', [])
        tax = invoice_data.get('tax', {})
        subtotal = invoice_data.get('subtotal', 0)
        grand_total = invoice_data.get('grandTotal', 0)
        scope = invoice_data.get('scope', [])
        notes = invoice_data.get('notes', [])
        inv_no = invoice_data.get('invoiceNo', 'INV-2026-000')
        date_str = invoice_data.get('date', '')

        formatted_items = []
        for it in items:
            formatted_items.append({
                'item': it.get('item', ''),
                'qty': it.get('qty', 1),
                'unit': it.get('unit', 'Units') if it.get('unit') else 'Units',
                'rate': format_indian_currency(it.get('rate', 0), include_symbol=True, suffix_dash=False),
                'amount': format_indian_currency(it.get('amount', 0), include_symbol=True, suffix_dash=True)
            })

        sgst_rate = tax.get('sgstRate', 9.0)
        cgst_rate = tax.get('cgstRate', 9.0)
        sgst_amount = tax.get('sgstAmount', 0)
        cgst_amount = tax.get('cgstAmount', 0)

        context = {
            'inv_no': inv_no,
            'date_display': format_date_display(date_str),
            'company': company,
            'customer': customer,
            'items': formatted_items,
            'sgst_rate_str': f"{sgst_rate:g}%" if isinstance(sgst_rate, (int, float)) else f"{sgst_rate}%",
            'cgst_rate_str': f"{cgst_rate:g}%" if isinstance(cgst_rate, (int, float)) else f"{cgst_rate}%",
            'sgst_amount': format_indian_currency(sgst_amount, include_symbol=True, suffix_dash=True),
            'cgst_amount': format_indian_currency(cgst_amount, include_symbol=True, suffix_dash=True),
            'subtotal': format_indian_currency(subtotal, include_symbol=True, suffix_dash=True),
            'grand_total': format_indian_currency(grand_total, include_symbol=True, suffix_dash=True),
            'scope': scope,
            'notes': notes
        }

        html_content = render_template('invoice_pdf.html', **context)
        return weasyprint.HTML(string=html_content).write_pdf()

    @classmethod
    def _generate_quotation_reportlab(cls, quotation_data: dict) -> bytes:
        return cls._build_reportlab_pdf(quotation_data, is_invoice=False)

    @classmethod
    def _generate_invoice_reportlab(cls, invoice_data: dict) -> bytes:
        return cls._build_reportlab_pdf(invoice_data, is_invoice=True)

    @staticmethod
    def _build_reportlab_pdf(data: dict, is_invoice: bool = False) -> bytes:
        """Pure-Python A4 PDF compilation using ReportLab."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0F2A4A'),
            spaceAfter=10
        )

        header_right_style = ParagraphStyle(
            'HeaderRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#333333')
        )

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#0F2A4A'),
            spaceBefore=12,
            spaceAfter=6
        )

        normal_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1A1A1A')
        )

        bold_style = ParagraphStyle(
            'BodyBold',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )

        company = data.get('companySnapshot', {})
        customer = data.get('customer', {})
        items = data.get('items', [])
        tax = data.get('tax', {})
        grand_total = data.get('grandTotal', 0)
        scope = data.get('scope', [])
        notes = data.get('notes', [])
        date_display = format_date_display(data.get('date', ''))

        # Header Top Right
        header_text = f"<b>Win Spares</b><br/>{date_display}"
        story.append(Paragraph(header_text, header_right_style))
        story.append(Spacer(1, 8))

        # Title
        default_title = 'Invoice' if is_invoice else 'Quotation'
        doc_title = company.get('invoiceTitle' if is_invoice else 'quotationTitle') or default_title
        story.append(Paragraph(doc_title, title_style))

        # Divider line
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CCCCCC'), spaceAfter=12))


        # FROM & CUSTOMER Table
        from_lines = [
            f"<b>FROM</b>",
            f"<b>{company.get('name', 'Win Spares')}</b>",
            company.get('address', '').replace('\n', '<br/>'),
            f"Ph.no: {company.get('phone', '')}"
        ]
        if company.get('gstin'):
            from_lines.append(f"GSTIN: {company.get('gstin')}")

        cust_lines = [
            f"<b>CUSTOMER</b>",
            f"<b>{customer.get('name', '')}</b>",
            customer.get('address', '').replace('\n', '<br/>')
        ]
        if customer.get('contactPerson'):
            cust_lines.append(f"Attn: {customer.get('contactPerson')}")
        if customer.get('phone'):
            cust_lines.append(f"Ph: {customer.get('phone')}")
        if customer.get('gstin'):
            cust_lines.append(f"GSTIN: {customer.get('gstin')}")

        party_table_data = [
            [
                Paragraph("<br/>".join(from_lines), normal_style),
                Paragraph("<br/>".join(cust_lines), normal_style)
            ]
        ]
        party_table = Table(party_table_data, colWidths=[260, 260])
        party_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0F2A4A')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#0F2A4A')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(party_table)
        story.append(Spacer(1, 14))

        # Section 1: Estimate Calculation
        story.append(Paragraph("1. Estimate Calculation", section_style))

        # Table Header
        price_header = "Price" if is_invoice else "Rate"
        table_rows = [
            [
                Paragraph("<b>Item</b>", bold_style),
                Paragraph("<b>Qty</b>", bold_style),
                Paragraph(f"<b>{price_header}</b>", bold_style),
                Paragraph("<b>Amount</b>", bold_style)
            ]
        ]

        for it in items:
            qty_str = f"{it.get('qty', 1)} {it.get('unit', 'Units') if it.get('unit') else 'Units'}"
            rate_str = format_indian_currency(it.get('rate', 0), include_symbol=True, suffix_dash=False)
            amount_str = format_indian_currency(it.get('amount', 0), include_symbol=True, suffix_dash=True)
            table_rows.append([
                Paragraph(it.get('item', ''), normal_style),
                Paragraph(qty_str, normal_style),
                Paragraph(rate_str, normal_style),
                Paragraph(amount_str, normal_style)
            ])

        sgst_rate = tax.get('sgstRate', 9.0)
        cgst_rate = tax.get('cgstRate', 9.0)
        sgst_amount = tax.get('sgstAmount', 0)
        cgst_amount = tax.get('cgstAmount', 0)

        sgst_str = format_indian_currency(sgst_amount, include_symbol=True, suffix_dash=True)
        cgst_str = format_indian_currency(cgst_amount, include_symbol=True, suffix_dash=True)
        grand_total_str = format_indian_currency(grand_total, include_symbol=True, suffix_dash=True)

        sgst_label = f"SGST ({sgst_rate:g}%)" if is_invoice else f"SGST {sgst_rate:g}%"
        cgst_label = f"CGST ({cgst_rate:g}%)" if is_invoice else f"CGST {cgst_rate:g}%"

        table_rows.append([Paragraph(sgst_label, bold_style), "", "", Paragraph(sgst_str, normal_style)])
        table_rows.append([Paragraph(cgst_label, bold_style), "", "", Paragraph(cgst_str, normal_style)])
        table_rows.append([Paragraph("<b>Grand Total</b>", bold_style), "", "", Paragraph(f"<b>{grand_total_str}</b>", bold_style)])

        calc_table = Table(table_rows, colWidths=[220, 90, 100, 110])
        calc_table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2A4A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0F2A4A')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('SPAN', (0, -3), (2, -3)),
            ('SPAN', (0, -2), (2, -2)),
            ('SPAN', (0, -1), (2, -1)),
            ('ALIGN', (0, -3), (-1, -1), 'RIGHT'),
        ]
        calc_table.setStyle(TableStyle(calc_table_styles))
        story.append(calc_table)
        story.append(Spacer(1, 14))

        # Section 2: Scope of Service
        if scope:
            story.append(Paragraph("2. Scope of Service", section_style))
            for sc in scope:
                story.append(Paragraph(f"• {sc}", normal_style))
            story.append(Spacer(1, 10))

        # Section 3: Important Notes (Invoices)
        if is_invoice and notes:
            story.append(Paragraph("Important Note:", section_style))
            for n in notes:
                story.append(Paragraph(f"• {n}", normal_style))
            story.append(Spacer(1, 10))

        # Footer
        story.append(Spacer(1, 16))
        greeting = company.get('greeting', 'Greetings from WIN SPARES!')
        default_closing = 'Thank you for allowing us to serve you. Please find our invoice for your requirements below.<br/>We appreciate the opportunity to serve you.' if is_invoice else 'Thank you for allowing us to serve you. Please find our quotation for your requirements below.'
        closing = company.get('closingText', default_closing)

        center_style = ParagraphStyle('CenterFooter', parent=normal_style, alignment=TA_CENTER)
        story.append(Paragraph(f"<b>** {greeting} **</b>", center_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(closing, center_style))


        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


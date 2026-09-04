"""
PDF Service for WeasyPrint server-side PDF compilation matching VRF_Quotation.pdf.
"""
from io import BytesIO
import weasyprint
from flask import render_template
from utils.formatting import format_indian_currency, format_date_display, sanitize_filename


class PDFService:
    @staticmethod
    def generate_quotation_pdf(quotation_data: dict) -> tuple[bytes, str]:
        """
        Render templates/quotation_pdf.html with quotation context and compile
        into searchable, high-fidelity PDF bytes.
        Returns (pdf_bytes, suggested_filename).
        """
        company = quotation_data.get('companySnapshot', {})
        customer = quotation_data.get('customer', {})
        items = quotation_data.get('items', [])
        tax = quotation_data.get('tax', {})
        subtotal = quotation_data.get('subtotal', 0)
        grand_total = quotation_data.get('grandTotal', 0)
        scope = quotation_data.get('scope', [])
        q_no = quotation_data.get('quotationNo', 'QTN-2026-000')
        date_str = quotation_data.get('date', '')

        # Format totals and currency for template rendering
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

        # Render HTML template
        html_content = render_template('quotation_pdf.html', **context)

        # Generate PDF using WeasyPrint
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

        # Filename format: QTN-2026-001_Visesha-Silk-Sarees-LLP.pdf
        clean_cust = sanitize_filename(customer.get('name', 'Customer'))
        filename = f"{q_no}_{clean_cust}.pdf"

        return pdf_bytes, filename

    @staticmethod
    def generate_invoice_pdf(invoice_data: dict) -> tuple[bytes, str]:
        """
        Render templates/invoice_pdf.html with invoice context and compile
        into searchable, high-fidelity PDF bytes.
        Returns (pdf_bytes, suggested_filename).
        """
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
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

        clean_cust = sanitize_filename(customer.get('name', 'Customer'))
        filename = f"{inv_no}_{clean_cust}.pdf"

        return pdf_bytes, filename

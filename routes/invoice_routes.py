"""
Invoice Routes Blueprint
Handles Invoice creation, previewing, saving, history, PDF downloading, and customer autocomplete APIs.
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from services.invoice_service import InvoiceService
from services.pdf_service import PDFService
from services.firebase_service import FirebaseService
from utils.formatting import format_indian_currency, format_date_display

logger = logging.getLogger(__name__)

invoice_bp = Blueprint('invoice', __name__)
inv_service = InvoiceService()
fb_service = FirebaseService()


def parse_invoice_form_payload(req) -> dict:
    """Helper to parse raw HTML form inputs or JSON payload into invoice data dict."""
    if req.content_type == 'application/json':
        return req.get_json() or {}

    if 'invoice_data_json' in req.form:
        try:
            return json.loads(req.form['invoice_data_json'])
        except Exception:
            pass

    date_str = req.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    service_type = req.form.get('serviceType', 'vrf_amc')
    invoice_no = req.form.get('invoiceNo', '')

    customer = {
        'name': req.form.get('customer[name]', '').strip(),
        'address': req.form.get('customer[address]', '').strip(),
        'contactPerson': req.form.get('customer[contactPerson]', '').strip(),
        'phone': req.form.get('customer[phone]', '').strip(),
        'email': req.form.get('customer[email]', '').strip(),
        'gstin': req.form.get('customer[gstin]', '').strip()
    }

    # Extract items array
    items_dict = {}
    for key, value in req.form.items():
        if key.startswith('items['):
            try:
                parts = key.replace('items[', '').split(']')
                idx = int(parts[0])
                field = parts[1].replace('[', '')
                if idx not in items_dict:
                    items_dict[idx] = {}
                items_dict[idx][field] = value
            except (ValueError, IndexError):
                pass

    items = []
    for idx in sorted(items_dict.keys()):
        item_obj = items_dict[idx]
        if item_obj.get('item'):
            qty = float(item_obj.get('qty', 1)) if item_obj.get('qty') else 1.0
            rate = float(item_obj.get('rate', 0)) if item_obj.get('rate') else 0.0
            items.append({
                'item': item_obj.get('item', '').strip(),
                'qty': qty,
                'rate': rate,
                'amount': qty * rate,
                'unit': 'Units'
            })

    # Tax details
    sgst_rate = float(req.form.get('tax[sgstRate]', 9.0))
    cgst_rate = float(req.form.get('tax[cgstRate]', 9.0))
    tax = {'sgstRate': sgst_rate, 'cgstRate': cgst_rate}

    # Scope of service items array
    scope = req.form.getlist('scope[]')
    if not scope:
        scope_dict = {}
        for key, value in req.form.items():
            if key.startswith('scope['):
                try:
                    idx = int(key.replace('scope[', '').replace(']', ''))
                    scope_dict[idx] = value
                except ValueError:
                    pass
        scope = [scope_dict[i] for i in sorted(scope_dict.keys())]

    # Important notes
    notes_raw = req.form.get('notes', '')
    notes = [n.strip() for n in notes_raw.split('\n') if n and n.strip()]

    return {
        'date': date_str,
        'invoiceNo': invoice_no,
        'serviceType': service_type,
        'customer': customer,
        'items': items,
        'tax': tax,
        'scope': scope,
        'notes': notes
    }


@invoice_bp.route('/invoice/new', methods=['GET', 'POST'])
def new_invoice():
    """Render Create Invoice Form, pre-populated with template or edit data."""
    initial_data = {}
    if request.method == 'POST':
        initial_data = parse_invoice_form_payload(request)

    service_templates = fb_service.get_all_service_templates()

    initial_date = initial_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    initial_customer = initial_data.get('customer')
    initial_items = initial_data.get('items')
    initial_tax = initial_data.get('tax')
    initial_scope = initial_data.get('scope')
    initial_notes = initial_data.get('notes')

    if not initial_customer:
        customers = fb_service.get_customers()
        initial_customer = customers[0] if customers else None

    next_inv_no = fb_service.get_next_invoice_number(initial_date.split('-')[0])

    return render_template(
        'invoice_form.html',
        service_templates=service_templates,
        initial_date=initial_date,
        next_inv_no=next_inv_no,
        initial_customer=initial_customer,
        initial_items=initial_items,
        initial_tax=initial_tax,
        initial_scope=initial_scope,
        initial_notes=initial_notes
    )


@invoice_bp.route('/invoice/preview', methods=['POST'])
def preview_invoice():
    """Process form data, calculate totals, and render A4 Preview matching reference invoice sample."""
    raw_data = parse_invoice_form_payload(request)

    processed_payload, errors = inv_service.process_and_prepare(raw_data, generate_number=False)
    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('invoice.new_invoice'))

    formatted_items = []
    for it in processed_payload['items']:
        formatted_items.append({
            'item': it['item'],
            'qty': it['qty'],
            'unit': it.get('unit', 'Units'),
            'rate_formatted': format_indian_currency(it['rate'], include_symbol=True, suffix_dash=False),
            'amount_formatted': format_indian_currency(it['amount'], include_symbol=True, suffix_dash=True)
        })

    tax = processed_payload['tax']
    sgst_rate = tax.get('sgstRate', 9.0)
    cgst_rate = tax.get('cgstRate', 9.0)

    context = {
        'raw_data_json': json.dumps(raw_data),
        'company': processed_payload['companySnapshot'],
        'customer': processed_payload['customer'],
        'items': formatted_items,
        'sgst_rate_str': f"{sgst_rate:g}%" if isinstance(sgst_rate, (int, float)) else f"{sgst_rate}%",
        'cgst_rate_str': f"{cgst_rate:g}%" if isinstance(cgst_rate, (int, float)) else f"{cgst_rate}%",
        'sgst_amount_formatted': format_indian_currency(tax.get('sgstAmount', 0), include_symbol=True, suffix_dash=True),
        'cgst_amount_formatted': format_indian_currency(tax.get('cgstAmount', 0), include_symbol=True, suffix_dash=True),
        'subtotal_formatted': format_indian_currency(processed_payload['subtotal'], include_symbol=True, suffix_dash=True),
        'grand_total_formatted': format_indian_currency(processed_payload['grandTotal'], include_symbol=True, suffix_dash=True),
        'scope': processed_payload['scope'],
        'notes': processed_payload.get('notes', []),
        'date_display': format_date_display(processed_payload['date'])
    }

    return render_template('invoice_preview.html', **context)


@invoice_bp.route('/invoice/save', methods=['POST'])
def save_invoice():
    """Save invoice to Firestore and return generated WeasyPrint PDF download."""
    raw_data = parse_invoice_form_payload(request)

    created_invoice, errors = inv_service.create_invoice(raw_data)
    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('invoice.new_invoice'))

    pdf_bytes, filename = PDFService.generate_invoice_pdf(created_invoice)

    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@invoice_bp.route('/invoices')
def invoice_history():
    """Display table of generated invoices with search filter."""
    search_query = request.args.get('q', '').strip()
    invoices = inv_service.list_invoices(search_query)
    return render_template('invoice_history.html', invoices=invoices, search_query=search_query)


@invoice_bp.route('/invoice/<inv_id>')
def view_invoice(inv_id):
    """View saved invoice details."""
    inv = inv_service.get_invoice_by_id(inv_id)
    if not inv:
        flash('Invoice not found.', 'error')
        return redirect(url_for('invoice.invoice_history'))

    formatted_items = []
    for it in inv.get('items', []):
        formatted_items.append({
            'item': it.get('item', ''),
            'qty': it.get('qty', 1),
            'unit': it.get('unit', 'Units'),
            'rate_formatted': format_indian_currency(it.get('rate', 0), include_symbol=True, suffix_dash=False),
            'amount_formatted': format_indian_currency(it.get('amount', 0), include_symbol=True, suffix_dash=True)
        })

    tax = inv.get('tax', {})
    sgst_rate = tax.get('sgstRate', 9.0)
    cgst_rate = tax.get('cgstRate', 9.0)

    context = {
        'inv_id': inv_id,
        'inv_no': inv.get('invoiceNo', ''),
        'company': inv.get('companySnapshot', {}),
        'customer': inv.get('customer', {}),
        'items': formatted_items,
        'sgst_rate_str': f"{sgst_rate:g}%" if isinstance(sgst_rate, (int, float)) else f"{sgst_rate}%",
        'cgst_rate_str': f"{cgst_rate:g}%" if isinstance(cgst_rate, (int, float)) else f"{cgst_rate}%",
        'sgst_amount_formatted': format_indian_currency(tax.get('sgstAmount', 0), include_symbol=True, suffix_dash=True),
        'cgst_amount_formatted': format_indian_currency(tax.get('cgstAmount', 0), include_symbol=True, suffix_dash=True),
        'grand_total_formatted': format_indian_currency(inv.get('grandTotal', 0), include_symbol=True, suffix_dash=True),
        'scope': inv.get('scope', []),
        'notes': inv.get('notes', []),
        'date_display': format_date_display(inv.get('date', ''))
    }

    return render_template('invoice_view.html', **context)


@invoice_bp.route('/invoice/<inv_id>/pdf')
def download_pdf(inv_id):
    """Download PDF for an existing saved invoice."""
    inv = inv_service.get_invoice_by_id(inv_id)
    if not inv:
        flash('Invoice not found.', 'error')
        return redirect(url_for('invoice.invoice_history'))

    pdf_bytes, filename = PDFService.generate_invoice_pdf(inv)

    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@invoice_bp.route('/invoice/<inv_id>/duplicate')
def duplicate_invoice(inv_id):
    """Duplicate an existing invoice."""
    original = inv_service.get_invoice_by_id(inv_id)
    if not original:
        flash('Original invoice not found.', 'error')
        return redirect(url_for('invoice.invoice_history'))

    service_templates = fb_service.get_all_service_templates()
    today_str = datetime.now().strftime('%Y-%m-%d')
    next_inv_no = fb_service.get_next_invoice_number(datetime.now().year)

    return render_template(
        'invoice_form.html',
        service_templates=service_templates,
        initial_date=today_str,
        next_inv_no=next_inv_no,
        initial_customer=original.get('customer'),
        initial_items=original.get('items'),
        initial_tax=original.get('tax'),
        initial_scope=original.get('scope'),
        initial_notes=original.get('notes', [])
    )

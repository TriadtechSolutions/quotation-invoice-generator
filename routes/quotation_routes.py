"""
Quotation Routes Blueprint
Handles Quotation creation, previewing, saving, history, PDF downloading, and customer APIs.
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from services.quotation_service import QuotationService
from services.pdf_service import PDFService
from services.firebase_service import FirebaseService
from utils.formatting import format_indian_currency, format_date_display

logger = logging.getLogger(__name__)

quotation_bp = Blueprint('quotation', __name__)
q_service = QuotationService()
fb_service = FirebaseService()


def parse_form_payload(req) -> dict:
    """Helper to parse raw HTML form inputs or JSON payload into quotation data dict."""
    if req.content_type == 'application/json':
        return req.get_json() or {}

    # Check if raw JSON was posted in hidden input (e.g. from preview/edit actions)
    if 'quotation_data_json' in req.form:
        try:
            return json.loads(req.form['quotation_data_json'])
        except Exception:
            pass

    date_str = req.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    service_type = req.form.get('serviceType', 'vrf_amc')
    quotation_no = req.form.get('quotationNo', '')

    customer = {
        'name': req.form.get('customer[name]', '').strip(),
        'address': req.form.get('customer[address]', '').strip(),
        'contactPerson': req.form.get('customer[contactPerson]', '').strip(),
        'phone': req.form.get('customer[phone]', '').strip(),
        'email': req.form.get('customer[email]', '').strip()
    }

    # Extract items array from form keys like items[0][item], items[0][qty], items[0][rate]
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
        # Fallback if submitted as scope[0], scope[1]
        scope_dict = {}
        for key, value in req.form.items():
            if key.startswith('scope['):
                try:
                    idx = int(key.replace('scope[', '').replace(']', ''))
                    scope_dict[idx] = value
                except ValueError:
                    pass
        scope = [scope_dict[i] for i in sorted(scope_dict.keys())]

    return {
        'date': date_str,
        'quotationNo': quotation_no,
        'serviceType': service_type,
        'customer': customer,
        'items': items,
        'tax': tax,
        'scope': scope
    }


@quotation_bp.route('/quotation/new', methods=['GET', 'POST'])
def new_quotation():
    """Render Create Quotation Form, pre-populated with template or edit data."""
    initial_data = {}
    if request.method == 'POST':
        initial_data = parse_form_payload(request)

    service_templates = fb_service.get_all_service_templates()
    default_tpl = fb_service.get_service_template('vrf_amc')

    initial_date = initial_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    initial_customer = initial_data.get('customer')
    initial_items = initial_data.get('items')
    initial_tax = initial_data.get('tax')
    initial_scope = initial_data.get('scope')

    # Seed sample customer if none specified yet
    if not initial_customer:
        customers = fb_service.get_customers()
        initial_customer = customers[0] if customers else None

    next_q_no = fb_service.get_next_quotation_number(initial_date.split('-')[0])

    return render_template(
        'quotation_form.html',
        service_templates=service_templates,
        initial_date=initial_date,
        next_q_no=next_q_no,
        initial_customer=initial_customer,
        initial_items=initial_items,
        initial_tax=initial_tax,
        initial_scope=initial_scope,
        default_scope=default_tpl.get('scope', [])
    )


@quotation_bp.route('/quotation/preview', methods=['POST'])
def preview_quotation():
    """Process form data, calculate totals, and render A4 Preview matching VRF_Quotation.pdf."""
    raw_data = parse_form_payload(request)

    processed_payload, errors = q_service.process_and_prepare(raw_data, generate_number=False)
    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('quotation.new_quotation'))

    # Format numbers for preview template
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
        'date_display': format_date_display(processed_payload['date'])
    }

    return render_template('quotation_preview.html', **context)


@quotation_bp.route('/quotation/save', methods=['POST'])
def save_quotation():
    """Save quotation to data store and return generated PDF download or JSON fallback."""
    raw_data = parse_form_payload(request)

    created_quotation, errors = q_service.create_quotation(raw_data)
    if errors:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('quotation.new_quotation'))

    try:
        pdf_bytes, filename = PDFService.generate_quotation_pdf(created_quotation)
        response = Response(pdf_bytes, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['X-Quotation-ID'] = created_quotation.get('id', '')
        return response
    except Exception as err:
        logger.error(f"Server-side PDF generation error for quotation {created_quotation.get('id')}: {err}")
        # Return JSON signaling client-side PDF generation fallback
        q_id = created_quotation.get('id', '')
        clean_cust = created_quotation.get('customer', {}).get('name', 'Customer')
        q_no = created_quotation.get('quotationNo', 'QTN-2026-000')
        fallback_filename = f"{q_no}_{clean_cust}.pdf"
        return jsonify({
            'success': True,
            'fallback_client_pdf': True,
            'quotation_id': q_id,
            'filename': fallback_filename,
            'message': 'Quotation saved successfully. Utilizing browser-native PDF engine.'
        }), 200



@quotation_bp.route('/quotations')
def history():
    """Display table of generated quotations with search filter."""
    search_query = request.args.get('q', '').strip()
    quotations = q_service.list_quotations(search_query)
    return render_template('quotation_history.html', quotations=quotations, search_query=search_query)


@quotation_bp.route('/quotation/<q_id>')
def view_quotation(q_id):
    """View saved quotation details."""
    q = q_service.get_quotation_by_id(q_id)
    if not q:
        flash('Quotation not found.', 'error')
        return redirect(url_for('quotation.history'))

    # Format numbers for view
    formatted_items = []
    for it in q.get('items', []):
        formatted_items.append({
            'item': it.get('item', ''),
            'qty': it.get('qty', 1),
            'unit': it.get('unit', 'Units'),
            'rate_formatted': format_indian_currency(it.get('rate', 0), include_symbol=True, suffix_dash=False),
            'amount_formatted': format_indian_currency(it.get('amount', 0), include_symbol=True, suffix_dash=True)
        })

    tax = q.get('tax', {})
    sgst_rate = tax.get('sgstRate', 9.0)
    cgst_rate = tax.get('cgstRate', 9.0)

    context = {
        'q': q,
        'company': q.get('companySnapshot', {}),
        'customer': q.get('customer', {}),
        'items': formatted_items,
        'sgst_rate_str': f"{sgst_rate:g}%" if isinstance(sgst_rate, (int, float)) else f"{sgst_rate}%",
        'cgst_rate_str': f"{cgst_rate:g}%" if isinstance(cgst_rate, (int, float)) else f"{cgst_rate}%",
        'sgst_amount_formatted': format_indian_currency(tax.get('sgstAmount', 0), include_symbol=True, suffix_dash=True),
        'cgst_amount_formatted': format_indian_currency(tax.get('cgstAmount', 0), include_symbol=True, suffix_dash=True),
        'grand_total_formatted': format_indian_currency(q.get('grandTotal', 0), include_symbol=True, suffix_dash=True),
        'scope': q.get('scope', []),
        'date_display': format_date_display(q.get('date', ''))
    }

    return render_template('quotation_view.html', **context)


@quotation_bp.route('/quotation/<q_id>/pdf')
def download_pdf(q_id):
    """Download PDF for an existing saved quotation using historical snapshot data."""
    q = q_service.get_quotation_by_id(q_id)
    if not q:
        flash('Quotation not found.', 'error')
        return redirect(url_for('quotation.history'))

    try:
        pdf_bytes, filename = PDFService.generate_quotation_pdf(q)
        response = Response(pdf_bytes, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as err:
        logger.error(f"Error downloading quotation PDF {q_id}: {err}")
        flash('Unable to compile PDF server-side. Viewing quotation preview instead.', 'warning')
        return redirect(url_for('quotation.view_quotation', q_id=q_id))



@quotation_bp.route('/quotation/<q_id>/duplicate')
def duplicate_quotation(q_id):
    """Duplicate an existing quotation: pre-fill form with new date and new quotation number."""
    original = q_service.get_quotation_by_id(q_id)
    if not original:
        flash('Original quotation not found.', 'error')
        return redirect(url_for('quotation.history'))

    service_templates = fb_service.get_all_service_templates()
    today_str = datetime.now().strftime('%Y-%m-%d')
    next_q_no = fb_service.get_next_quotation_number(datetime.now().year)

    return render_template(
        'quotation_form.html',
        service_templates=service_templates,
        initial_date=today_str,
        next_q_no=next_q_no,
        initial_customer=original.get('customer'),
        initial_items=original.get('items'),
        initial_tax=original.get('tax'),
        initial_scope=original.get('scope'),
        default_scope=[]
    )


@quotation_bp.route('/api/customers')
def api_customers():
    """API endpoint for customer autocomplete."""
    q = request.args.get('q', '')
    customers = fb_service.get_customers(q)
    return jsonify(customers)

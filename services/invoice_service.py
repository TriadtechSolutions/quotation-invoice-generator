"""
Invoice Service Layer
Handles business calculations, validation, Firestore persistence, and historical snapshots for Invoices.
"""
from datetime import datetime
from services.firebase_service import FirebaseService
from utils.formatting import format_indian_currency


class InvoiceService:
    def __init__(self):
        self.fb = FirebaseService()

    def process_and_prepare(self, raw_data: dict, generate_number: bool = False) -> tuple[dict, list[str]]:
        """
        Validate raw input data and calculate tax and totals.
        Returns (processed_payload, list_of_errors).
        """
        errors = []

        date_str = raw_data.get('date', '').strip()
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        invoice_no = raw_data.get('invoiceNo', '').strip()
        if generate_number or not invoice_no:
            year = date_str.split('-')[0] if '-' in date_str else str(datetime.now().year)
            invoice_no = self.fb.get_next_invoice_number(year)

        customer = raw_data.get('customer', {})
        if not customer.get('name', '').strip():
            errors.append("Customer name is required.")

        raw_items = raw_data.get('items', [])
        processed_items = []
        subtotal = 0.0

        for idx, item in enumerate(raw_items):
            item_name = item.get('item', '').strip()
            if not item_name:
                continue

            try:
                qty = float(item.get('qty', 1))
            except (ValueError, TypeError):
                qty = 1.0

            try:
                rate = float(item.get('rate', 0.0))
            except (ValueError, TypeError):
                rate = 0.0

            amount = round(qty * rate, 2)
            subtotal += amount

            processed_items.append({
                'item': item_name,
                'qty': int(qty) if qty.is_integer() else qty,
                'rate': rate,
                'amount': amount,
                'unit': item.get('unit', 'Units')
            })

        if not processed_items:
            errors.append("At least one valid item line is required.")

        # Tax calculations
        tax = raw_data.get('tax', {})
        sgst_rate = float(tax.get('sgstRate', 9.0))
        cgst_rate = float(tax.get('cgstRate', 9.0))

        sgst_amount = round((subtotal * sgst_rate) / 100.0, 2)
        cgst_amount = round((subtotal * cgst_rate) / 100.0, 2)
        grand_total = round(subtotal + sgst_amount + cgst_amount, 2)

        # Process Scope of Service
        scope = [s.strip() for s in raw_data.get('scope', []) if s and s.strip()]

        # Process Important Notes (can be list or multiline string)
        raw_notes = raw_data.get('notes', raw_data.get('importantNotes', []))
        if isinstance(raw_notes, str):
            notes = [n.strip() for n in raw_notes.split('\n') if n.strip()]
        elif isinstance(raw_notes, list):
            notes = [str(n).strip() for n in raw_notes if str(n).strip()]
        else:
            notes = []

        company_snapshot = self.fb.get_company_settings()

        payload = {
            'invoiceNo': invoice_no,
            'date': date_str,
            'serviceType': raw_data.get('serviceType', 'vrf_amc'),
            'customer': {
                'name': customer.get('name', '').strip(),
                'address': customer.get('address', '').strip(),
                'contactPerson': customer.get('contactPerson', '').strip(),
                'phone': customer.get('phone', '').strip(),
                'email': customer.get('email', '').strip(),
                'gstin': customer.get('gstin', '').strip()
            },
            'companySnapshot': company_snapshot,
            'items': processed_items,
            'subtotal': subtotal,
            'tax': {
                'sgstRate': sgst_rate,
                'cgstRate': cgst_rate,
                'sgstAmount': sgst_amount,
                'cgstAmount': cgst_amount
            },
            'grandTotal': grand_total,
            'scope': scope,
            'notes': notes
        }

        return payload, errors

    def create_invoice(self, raw_data: dict) -> tuple[dict, list[str]]:
        """Process, validate, save customer, and persist invoice."""
        payload, errors = self.process_and_prepare(raw_data, generate_number=True)
        if errors:
            return {}, errors

        # Save customer if new
        cust_id = self.fb.save_customer_if_new(payload['customer'])
        if cust_id:
            payload['customer']['id'] = cust_id

        inv_id = self.fb.save_invoice(payload)
        payload['id'] = inv_id
        return payload, []

    def get_invoice_by_id(self, inv_id: str) -> dict:
        return self.fb.get_invoice(inv_id)

    def list_invoices(self, search_query: str = "") -> list[dict]:
        return self.fb.get_all_invoices(search_query)

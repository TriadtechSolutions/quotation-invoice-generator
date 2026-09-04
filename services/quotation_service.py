"""
Quotation Service handling quotation lifecycle: payload preparation,
authoritative server-side calculations, snapshot embedding, and DB persistence.
"""
from datetime import datetime
from services.firebase_service import FirebaseService
from utils.calculations import calculate_quotation_totals
from utils.validators import validate_quotation_data


class QuotationService:
    def __init__(self):
        self.fb_service = FirebaseService()

    def process_and_prepare(self, raw_data: dict, generate_number: bool = True) -> tuple[dict, list[str]]:
        """
        Validate, recalculate authoritative numbers, attach company snapshot,
        and generate quotation number if required.
        """
        is_valid, errors = validate_quotation_data(raw_data)
        if not is_valid:
            return {}, errors

        date_str = raw_data.get('date', '').strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        year_str = date_str.split('-')[0] if '-' in date_str else str(datetime.now().year)

        # Company snapshot (for historical immutability)
        company_info = self.fb_service.get_company_settings()

        # Recalculate totals authoritatively
        tax = raw_data.get('tax', {})
        sgst_rate = float(tax.get('sgstRate', 9.0))
        cgst_rate = float(tax.get('cgstRate', 9.0))

        raw_items = raw_data.get('items', [])
        totals = calculate_quotation_totals(raw_items, sgst_rate, cgst_rate)

        # Customer information
        customer_info = raw_data.get('customer', {})

        # Scope of service items
        scope_items = [str(s).strip() for s in raw_data.get('scope', []) if str(s).strip()]

        # Generate quotation number if new
        q_no = raw_data.get('quotationNo', '')
        if generate_number or not q_no:
            q_no = self.fb_service.get_next_quotation_number(year_str)

        quotation_payload = {
            "quotationNo": q_no,
            "date": date_str,
            "serviceType": raw_data.get('serviceType', 'vrf_amc'),
            "companySnapshot": company_info,
            "customer": {
                "name": str(customer_info.get('name', '')).strip(),
                "address": str(customer_info.get('address', '')).strip(),
                "contactPerson": str(customer_info.get('contactPerson', '')).strip(),
                "phone": str(customer_info.get('phone', '')).strip(),
                "email": str(customer_info.get('email', '')).strip()
            },
            "items": totals['items'],
            "tax": totals['tax'],
            "subtotal": totals['subtotal'],
            "grandTotal": totals['grandTotal'],
            "scope": scope_items,
            "status": "generated"
        }

        return quotation_payload, []

    def create_quotation(self, raw_data: dict) -> tuple[dict, list[str]]:
        """Process, validate, save new customer if needed, and save quotation."""
        payload, errors = self.process_and_prepare(raw_data, generate_number=True)
        if errors:
            return {}, errors

        # Save customer if new
        self.fb_service.save_customer_if_new(payload['customer'])

        # Save quotation doc
        q_id = self.fb_service.save_quotation(payload)
        payload['id'] = q_id
        return payload, []

    def get_quotation_by_id(self, quotation_id: str) -> dict:
        return self.fb_service.get_quotation(quotation_id)

    def list_quotations(self, query: str = "") -> list[dict]:
        return self.fb_service.get_all_quotations(query)

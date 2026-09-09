"""
Firebase Service Layer providing structured CRUD methods for settings, templates,
customers, and quotations with automatic seeding on startup.
"""
from datetime import datetime
from firebase.firebase_config import get_firestore_db


class FirebaseService:
    def __init__(self):
        self.db, self.is_mock = get_firestore_db()
        self.seed_defaults_if_needed()

    def seed_defaults_if_needed(self):
        """Seed initial company settings, VRF AMC template, and sample customer if missing."""
        # 1. Company Settings
        company_ref = self.db.collection('settings').document('company')
        doc = company_ref.get()
        if not doc.exists:
            company_ref.set({
                "name": "Win Spares",
                "address": "No: 70, Dr. Alagappa Road, near Six Corner Road\nTatabad, Coimbatore - 641012",
                "phone": "93617 62191",
                "gstin": "33DWFPK5792D1ZG",
                "quotationTitle": "Quotation",
                "invoiceTitle": "Invoice",
                "greeting": "Greetings from WIN SPARES!",
                "closingText": "Thank you for allowing us to serve you. Please find our quotation for your requirements below.",
                "serviceFooter": ""
            })

        # 2. Service Template: VRF AMC
        tpl_ref = self.db.collection('service_templates').document('vrf_amc')
        tpl_doc = tpl_ref.get()
        if not tpl_doc.exists:
            tpl_ref.set({
                "name": "VRF Annual Maintenance Contract",
                "quotationTitle": "Quotation",
                "defaultSGST": 9.0,
                "defaultCGST": 9.0,
                "scope": [
                    "6 VRF Units",
                    "AC performance & operating condition checking",
                    "Indoor & outdoor unit inspection",
                    "Electrical connection & safety checking",
                    "Drain line / drain system checking",
                    "Refrigerant pressure & leakage inspection",
                    "Temperature / performance checking",
                    "Preventive maintenance report"
                ],
                "active": True
            })

        # 3. Sample Customer: Visesha Silk Sarees LLP
        cust_ref = self.db.collection('customers').document('visesha_silk_sarees')
        cust_doc = cust_ref.get()
        if not cust_doc.exists:
            cust_ref.set({
                "name": "Visesha Silk Sarees LLP",
                "address": "Shop No 1, 1216, Shri Hari Building, Nava India\nAvinashi Road, Coimbatore – 641004",
                "contactPerson": "",
                "phone": "",
                "email": "",
                "createdAt": datetime.now().isoformat()
            })

    def get_company_settings(self) -> dict:
        """Fetch company settings."""
        doc = self.db.collection('settings').document('company').get()
        if doc.exists:
            return doc.to_dict()
        return {
            "name": "Win Spares",
            "address": "No: 70, Dr. Alagappa Road, near Six Corner Road\nTatabad, Coimbatore - 641012",
            "phone": "93617 62191",
            "gstin": "33DWFPK5792D1ZG",
            "quotationTitle": "Quotation",
            "invoiceTitle": "Invoice",
            "greeting": "Greetings from WIN SPARES!",
            "closingText": "Thank you for allowing us to serve you. Please find our quotation for your requirements below.",
            "serviceFooter": ""
        }


    def get_service_template(self, template_id: str = "vrf_amc") -> dict:
        """Fetch service template details."""
        doc = self.db.collection('service_templates').document(template_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return {}

    def get_all_service_templates(self) -> list[dict]:
        """Get all active service templates."""
        docs = self.db.collection('service_templates').get()
        templates = []
        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            if data.get('active', True):
                templates.append(data)
        return templates

    def get_customers(self, query: str = "") -> list[dict]:
        """Fetch customers, optionally filtered by name."""
        docs = self.db.collection('customers').get()
        customers = []
        query_lower = query.lower().strip() if query else ""
        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            if not query_lower or query_lower in data.get('name', '').lower():
                customers.append(data)
        return customers

    def save_customer_if_new(self, customer_data: dict) -> str:
        """Save new customer if name doesn't exist yet."""
        cust_name = customer_data.get('name', '').strip()
        if not cust_name:
            return ""

        existing = self.get_customers(cust_name)
        for e in existing:
            if e.get('name', '').strip().lower() == cust_name.lower():
                return e['id']

        doc_ref = self.db.collection('customers').document()
        payload = {
            "name": cust_name,
            "address": customer_data.get('address', '').strip(),
            "contactPerson": customer_data.get('contactPerson', '').strip(),
            "phone": customer_data.get('phone', '').strip(),
            "email": customer_data.get('email', '').strip(),
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        doc_ref.set(payload)
        return doc_ref.id

    def save_quotation(self, quotation_data: dict) -> str:
        """Save quotation document in Firestore."""
        doc_ref = self.db.collection('quotations').document()
        quotation_data['id'] = doc_ref.id
        quotation_data['createdAt'] = datetime.now().isoformat()
        quotation_data['updatedAt'] = datetime.now().isoformat()
        doc_ref.set(quotation_data)
        return doc_ref.id

    def get_quotation(self, quotation_id: str) -> dict:
        """Fetch quotation document by ID."""
        doc = self.db.collection('quotations').document(quotation_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return {}

    def get_all_quotations(self, search_query: str = "") -> list[dict]:
        """Fetch all quotations sorted by date descending."""
        docs = self.db.collection('quotations').get()
        quotations = []
        sq = search_query.lower().strip() if search_query else ""

        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            if sq:
                q_num = data.get('quotationNo', '').lower()
                c_name = data.get('customer', {}).get('name', '').lower()
                if sq not in q_num and sq not in c_name:
                    continue
            quotations.append(data)

        # Sort by date / createdAt descending
        quotations.sort(key=lambda x: x.get('createdAt', x.get('date', '')), reverse=True)
        return quotations

    def get_next_quotation_number(self, year: str) -> str:
        """
        Generates sequential quotation number for the given year.
        Format: QTN-YYYY-001
        Safe against duplicate number generation.
        """
        prefix = f"QTN-{year}-"
        all_q = self.get_all_quotations()
        matching_seqs = []

        for q in all_q:
            q_no = q.get('quotationNo', '')
            if q_no.startswith(prefix):
                try:
                    num_part = int(q_no.replace(prefix, ''))
                    matching_seqs.append(num_part)
                except ValueError:
                    pass

        next_seq = max(matching_seqs) + 1 if matching_seqs else 1
        return f"{prefix}{next_seq:03d}"

    # ------------------ INVOICE METHODS ------------------

    def save_invoice(self, invoice_data: dict) -> str:
        """Save invoice document in Firestore."""
        doc_ref = self.db.collection('invoices').document()
        invoice_data['id'] = doc_ref.id
        invoice_data['createdAt'] = datetime.now().isoformat()
        invoice_data['updatedAt'] = datetime.now().isoformat()
        doc_ref.set(invoice_data)
        return doc_ref.id

    def get_invoice(self, invoice_id: str) -> dict:
        """Fetch invoice document by ID."""
        doc = self.db.collection('invoices').document(invoice_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return {}

    def get_all_invoices(self, search_query: str = "") -> list[dict]:
        """Fetch all invoices sorted by date descending."""
        docs = self.db.collection('invoices').get()
        invoices = []
        sq = search_query.lower().strip() if search_query else ""

        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            if sq:
                inv_num = data.get('invoiceNo', '').lower()
                c_name = data.get('customer', {}).get('name', '').lower()
                if sq not in inv_num and sq not in c_name:
                    continue
            invoices.append(data)

        invoices.sort(key=lambda x: x.get('createdAt', x.get('date', '')), reverse=True)
        return invoices

    def get_next_invoice_number(self, year: str) -> str:
        """
        Generates sequential invoice number for the given year.
        Format: INV-YYYY-001
        """
        prefix = f"INV-{year}-"
        all_inv = self.get_all_invoices()
        matching_seqs = []

        for inv in all_inv:
            inv_no = inv.get('invoiceNo', '')
            if inv_no.startswith(prefix):
                try:
                    num_part = int(inv_no.replace(prefix, ''))
                    matching_seqs.append(num_part)
                except ValueError:
                    pass

        next_seq = max(matching_seqs) + 1 if matching_seqs else 1
        return f"{prefix}{next_seq:03d}"

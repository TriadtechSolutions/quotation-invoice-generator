"""
Integration test for WeasyPrint PDF rendering from Flask templates.
"""
import unittest
from app import app
from services.pdf_service import PDFService


class TestPDFGeneration(unittest.TestCase):
    def test_pdf_rendering_sample_data(self):
        """Test compiling sample quotation into PDF binary."""
        sample_quotation = {
            "quotationNo": "QTN-2026-001",
            "date": "2026-08-30",
            "serviceType": "vrf_amc",
            "companySnapshot": {
                "name": "Win Spares",
                "address": "No: 70, Dr. Alagappa Road, near Six Corner Road\nTatabad, Coimbatore - 641012",
                "phone": "93617 62191",
                "quotationTitle": "VRF Quotation",
                "greeting": "Greetings from WIN SPARES!",
                "closingText": "Thank you for allowing us to serve you. Please find our quotation for your requirements below.",
                "serviceFooter": "VRF Annual Maintenance Contract | Win Spares"
            },
            "customer": {
                "name": "Visesha Silk Sarees LLP",
                "address": "Shop No 1, 1216, Shri Hari Building, Nava India\nAvinashi Road, Coimbatore – 641004"
            },
            "items": [
                {
                    "item": "VRF Full Service",
                    "qty": 6,
                    "unit": "Units",
                    "rate": 2500,
                    "amount": 15000
                }
            ],
            "tax": {
                "sgstRate": 9,
                "cgstRate": 9,
                "sgstAmount": 1350,
                "cgstAmount": 1350
            },
            "subtotal": 15000,
            "grandTotal": 17700,
            "scope": [
                "6 VRF Units",
                "AC performance & operating condition checking",
                "Indoor & outdoor unit inspection",
                "Electrical connection & safety checking",
                "Drain line / drain system checking",
                "Refrigerant pressure & leakage inspection",
                "Temperature / performance checking",
                "Preventive maintenance report"
            ]
        }

        with app.test_request_context():
            pdf_bytes, filename = PDFService.generate_quotation_pdf(sample_quotation)
            
            self.assertIsNotNone(pdf_bytes)
            self.assertTrue(len(pdf_bytes) > 0)
            self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
            self.assertEqual(filename, "Quotation_Visesha-Silk-Sarees-LLP.pdf")


    def test_reportlab_fallback_direct(self):
        """Test direct ReportLab PDF generation for quotation and invoice."""
        sample_quotation = {
            "quotationNo": "QTN-2026-002",
            "date": "2026-09-05",
            "companySnapshot": {"name": "Win Spares", "address": "Coimbatore"},
            "customer": {"name": "Test Customer"},
            "items": [{"item": "Service Unit", "qty": 1, "rate": 1000, "amount": 1000}],
            "tax": {"sgstRate": 9, "cgstRate": 9, "sgstAmount": 90, "cgstAmount": 90},
            "grandTotal": 1180,
            "scope": ["Testing Scope"]
        }

        pdf_bytes = PDFService._generate_quotation_reportlab(sample_quotation)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

        sample_invoice = {
            "invoiceNo": "INV-2026-002",
            "date": "2026-09-05",
            "companySnapshot": {"name": "Win Spares", "address": "Coimbatore"},
            "customer": {"name": "Test Customer"},
            "items": [{"item": "Invoice Unit", "qty": 1, "rate": 2000, "amount": 2000}],
            "tax": {"sgstRate": 9, "cgstRate": 9, "sgstAmount": 180, "cgstAmount": 180},
            "grandTotal": 2360,
            "scope": ["Invoice Scope"],
            "notes": ["Important Note Test"]
        }

        inv_pdf_bytes = PDFService._generate_invoice_reportlab(sample_invoice)
        self.assertIsNotNone(inv_pdf_bytes)
        self.assertTrue(inv_pdf_bytes.startswith(b'%PDF-'))


if __name__ == '__main__':
    unittest.main()


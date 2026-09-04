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
            self.assertEqual(filename, "QTN-2026-001_Visesha-Silk-Sarees-LLP.pdf")


if __name__ == '__main__':
    unittest.main()

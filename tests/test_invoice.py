"""
Unit tests for Invoice Service and Invoice calculation logic.
"""
import unittest
from services.invoice_service import InvoiceService
from utils.formatting import format_indian_currency, format_date_display


class TestInvoiceModule(unittest.TestCase):

    def setUp(self):
        self.service = InvoiceService()

    def test_invoice_totals_calculation(self):
        """Test calculation of sample invoice items from reference sample."""
        payload = {
            'date': '2026-09-04',
            'customer': {
                'name': 'Vishesa Silk Sarees LLP',
                'address': 'Shop No 1, 1216, Shri Hari Building, Nava India, Avinashi Road, Coimbatore – 641004',
                'gstin': '33AAUFV8930G1ZN'
            },
            'items': [
                {'item': 'VRF Full Service', 'qty': 1, 'rate': 2000},
                {'item': 'VRF Unit 1 Terminal Change', 'qty': 1, 'rate': 650},
                {'item': 'Unit 1 Gas Topup (15% PSI)', 'qty': 1, 'rate': 950}
            ],
            'tax': {'sgstRate': 9.0, 'cgstRate': 9.0},
            'scope': [
                '3 VRF Units - Checked',
                'AC performance & operating condition checking - Checked'
            ],
            'notes': [
                'Unit 1 compressor terminal short circuiter and need to add relay coil component'
            ]
        }

        processed, errors = self.service.process_and_prepare(payload, generate_number=True)
        self.assertEqual(len(errors), 0)
        self.assertEqual(processed['subtotal'], 3600.0)
        self.assertEqual(processed['tax']['sgstAmount'], 324.0)
        self.assertEqual(processed['tax']['cgstAmount'], 324.0)
        self.assertEqual(processed['grandTotal'], 4248.0)
        self.assertEqual(len(processed['notes']), 1)
        self.assertEqual(processed['notes'][0], 'Unit 1 compressor terminal short circuiter and need to add relay coil component')

    def test_empty_notes_handling(self):
        """Test that empty notes list is properly maintained so template hides Section E."""
        payload = {
            'date': '2026-09-04',
            'customer': {'name': 'Test Customer', 'address': 'Coimbatore'},
            'items': [{'item': 'Service', 'qty': 1, 'rate': 1000}],
            'notes': []
        }
        processed, errors = self.service.process_and_prepare(payload, generate_number=False)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(processed['notes']), 0)

    def test_date_formatting(self):
        """Test DD/MM/YYYY date display format."""
        formatted = format_date_display('2026-09-04')
        self.assertEqual(formatted, '04/09/2026')


if __name__ == '__main__':
    unittest.main()

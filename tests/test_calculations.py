"""
Unit tests for calculations, formatting, and validation logic.
"""
import unittest
from utils.calculations import (
    calculate_item_amount,
    calculate_subtotal,
    calculate_tax_amounts,
    calculate_quotation_totals
)
from utils.formatting import format_indian_currency, sanitize_filename
from utils.validators import validate_quotation_data


class TestCalculations(unittest.TestCase):

    def test_sample_quotation_calculation(self):
        """Test exact numbers from the supplied sample quotation requirement."""
        items = [
            {'item': 'VRF Full Service', 'qty': 6, 'rate': 2500}
        ]
        totals = calculate_quotation_totals(items, sgst_rate=9.0, cgst_rate=9.0)

        self.assertEqual(totals['subtotal'], 15000.0)
        self.assertEqual(totals['tax']['sgstAmount'], 1350.0)
        self.assertEqual(totals['tax']['cgstAmount'], 1350.0)
        self.assertEqual(totals['grandTotal'], 17700.0)

    def test_multiple_items_calculation(self):
        """Test calculation with multiple items."""
        items = [
            {'item': 'Item A', 'qty': 2, 'rate': 1000}, # 2000
            {'item': 'Item B', 'qty': 3, 'rate': 500}   # 1500
        ]
        totals = calculate_quotation_totals(items, sgst_rate=9.0, cgst_rate=9.0)

        self.assertEqual(totals['subtotal'], 3500.0)
        self.assertEqual(totals['tax']['sgstAmount'], 315.0)
        self.assertEqual(totals['tax']['cgstAmount'], 315.0)
        self.assertEqual(totals['grandTotal'], 4130.0)

    def test_currency_formatting(self):
        """Test Indian currency string formatting."""
        self.assertEqual(format_indian_currency(2500, True, False), "₹2,500")
        self.assertEqual(format_indian_currency(15000, True, True), "₹15,000/-")
        self.assertEqual(format_indian_currency(1350, True, True), "₹1,350/-")
        self.assertEqual(format_indian_currency(17700, True, True), "₹17,700/-")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        self.assertEqual(sanitize_filename("Visesha Silk Sarees LLP"), "Visesha-Silk-Sarees-LLP")
        self.assertEqual(sanitize_filename("Win Spares & Co!"), "Win-Spares-Co")

    def test_validators(self):
        """Test server-side data validation."""
        valid_data = {
            'date': '2026-08-30',
            'customer': {'name': 'Test Cust', 'address': 'Test Addr'},
            'items': [{'item': 'VRF Service', 'qty': 1, 'rate': 1000}],
            'scope': ['Scope item 1']
        }
        is_valid, errors = validate_quotation_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid customer
        invalid_data = valid_data.copy()
        invalid_data['customer'] = {'name': '', 'address': ''}
        is_valid, errors = validate_quotation_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("Customer name is required.", errors)


if __name__ == '__main__':
    unittest.main()

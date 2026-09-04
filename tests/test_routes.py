"""
Integration tests for Flask application routes.
"""
import unittest
from app import app


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_dashboard_route(self):
        """Test GET / renders dashboard with 200 OK."""
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'WIN SPARES', res.data)
        self.assertIn(b'Document Management System', res.data)

    def test_new_quotation_route(self):
        """Test GET /quotation/new renders quotation form."""
        res = self.app.get('/quotation/new')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Create VRF Quotation', res.data)
        self.assertIn(b'Visesha Silk Sarees LLP', res.data)

    def test_quotation_preview_route(self):
        """Test POST /quotation/preview calculates preview."""
        payload = {
            'date': '2026-08-30',
            'serviceType': 'vrf_amc',
            'customer[name]': 'Visesha Silk Sarees LLP',
            'customer[address]': 'Shop No 1, 1216, Shri Hari Building, Nava India, Avinashi Road, Coimbatore – 641004',
            'items[0][item]': 'VRF Full Service',
            'items[0][qty]': '6',
            'items[0][rate]': '2500',
            'tax[sgstRate]': '9',
            'tax[cgstRate]': '9',
            'scope[]': ['6 VRF Units', 'AC performance checking']
        }
        res = self.app.post('/quotation/preview', data=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'VRF Quotation', res.data)
        self.assertIn(b'15,000', res.data)
        self.assertIn(b'17,700', res.data)

    def test_edit_quotation_repopulation(self):
        """Test POST /quotation/new with quotation_data_json re-populates form."""
        raw_json = '{"date": "2026-08-30", "customer": {"name": "Edited Customer", "address": "Coimbatore"}, "items": [{"item": "Custom Item", "qty": 2, "rate": 500}]}'
        res = self.app.post('/quotation/new', data={'quotation_data_json': raw_json})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Edited Customer', res.data)
        self.assertIn(b'Custom Item', res.data)

    def test_edit_invoice_repopulation(self):
        """Test POST /invoice/new with invoice_data_json re-populates form."""
        raw_json = '{"date": "2026-09-04", "customer": {"name": "Invoice Customer", "address": "Nava India"}, "items": [{"item": "Invoice Service", "qty": 1, "rate": 1200}], "notes": ["Note Item 1"]}'
        res = self.app.post('/invoice/new', data={'invoice_data_json': raw_json})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Invoice Customer', res.data)
        self.assertIn(b'Invoice Service', res.data)
        self.assertIn(b'Note Item 1', res.data)


if __name__ == '__main__':
    unittest.main()

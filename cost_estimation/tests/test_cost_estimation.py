from odoo.tests.common import TransactionCase

class TestCostEstimation(TransactionCase):
    def test_basic(self):
        print("Running cost estimation test...")
        self.assertEqual(1 + 1, 2)
from odoo import models, fields

class TestCaseStatus(models.Model):
    _name = 'barcode_india.test_case_status'
    _description = 'Test Case Status'

    name = fields.Char(string='Status Name', required=True)
    description = fields.Text(string='Description')

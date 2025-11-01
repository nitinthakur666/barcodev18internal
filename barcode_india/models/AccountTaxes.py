from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountTaxes(models.Model):
    _inherit = 'account.tax'

    bci_tax_class_id = fields.Integer(string="Tax Class Id")
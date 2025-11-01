from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api

class Companies(models.Model):
    _inherit = 'res.company'

    s3_invoice_date = fields.Date("Last Invoice Sync Date")
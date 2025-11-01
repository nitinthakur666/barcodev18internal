from odoo import models, fields, api

class ResolutionType(models.Model):
    _name = 'barcode_india.reason_code'
    _description = 'RCA Reason Code'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
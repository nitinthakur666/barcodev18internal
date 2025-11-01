from odoo import models, fields, api

class ResolutionType(models.Model):
    _name = 'barcode_india.resolution_type'
    _description = 'Resolution Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
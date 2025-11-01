from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    software = fields.Boolean('Software Product',related='categ_id.is_software')


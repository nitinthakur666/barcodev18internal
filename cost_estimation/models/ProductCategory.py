from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = "product.category"

    is_software = fields.Boolean('Is Software Product', default=False)
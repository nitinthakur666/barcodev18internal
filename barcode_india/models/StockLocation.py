from odoo import fields, models,api,_


class StockLOcation(models.Model):
    _inherit = "stock.location"

    bci_engineer_location = fields.Boolean(string="Engineer Location")
    bci_defective_location = fields.Boolean(string="Defective Location")
    bci_code = fields.Char("Code")
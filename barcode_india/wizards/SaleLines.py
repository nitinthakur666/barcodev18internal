from odoo import fields, models, _

class SaleLines(models.TransientModel):
    _name = 'bci.sale_line'
    _description = 'Sale Lines'

    bci_product = fields.Char("Product")
    bci_sale_price = fields.Float(string='Last SalePrice')
    bci_sale_date = fields.Date(string='Last Date')
    bci_sale_order = fields.Char(string='Last SaleOrder')
    

from odoo import fields, models, api, _


class CategorySummary(models.Model):
    _name = 'barcode_india.category_summary'
    _description = 'Model for category '
    
    name = fields.Many2one('barcode_india.pricing_category','Category')
    bci_user = fields.Many2one('res.users','Pending For')
    bci_stage = fields.Selection([('draft','Draft'),('pricing_updated','Pricing Updated')],string='Stage')
    bci_status = fields.Char('PT Status')
    bci_total_quote_amt = fields.Float('Total Quote Amount')
    bci_total_po_amt = fields.Float('Total PO Amount')
    bci_sale_id = fields.Many2one('sale.order','Sale Order',ondelete='cascade')
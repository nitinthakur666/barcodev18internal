from odoo import fields, models,api,_


class StockMove(models.Model):
    _inherit = "stock.move"

    bci_product = fields.Many2one("product.product",related="picking_id.bci_product",string="Product")
    bci_spare_transfer = fields.Boolean(related="picking_id.bci_spare_transfer",string="Spares Transfer")
    bci_rma_request_no = fields.Char(string="RMA Request No.")

    @api.onchange('bci_product')
    def _onchange_bci_product(self):
        if self.bci_product:
            spares = self.bci_product.mapped('bci_spare_ids.name')
            return {'domain': {'product_id': [('id','in',spares.ids)]}}
        else:
            return {'domain': {'product_id': []}}

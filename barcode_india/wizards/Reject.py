from odoo import models, fields, api

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Order Line Wizard'

    order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    reason = fields.Text(string='Reason for Rejection')

    @api.model
    def default_get(self, fields_list):
        res = super(RejectWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            order_line = self.env['sale.order.line'].browse(active_id)
            res['order_id'] = order_line.order_id.id
            res['product_id'] = order_line.product_id.id
        return res

    def confirm_reject(self):
        self.ensure_one()
        sale_order = self.order_id  
        product_name = self.product_id.name
        if sale_order:
            sale_order.message_post(
                body=f"Please remove the order line for {product_name}. Reason: {self.reason}",
            )
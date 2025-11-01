from odoo import fields, models,api, _

class SalesLine(models.TransientModel):
    _name = 'bci.sales_repricing'
    _description = 'Sales Repricing'
    
    existing_rate = fields.Float(string='Existing Rate')
    current_exchange_rate = fields.Float(string='Current Rate')
    repricing_currency = fields.Many2one('res.currency',compute='_compute_existing_rate',string='Currency')
    order_id = fields.Many2one('sale.order','Sale Order ID')
    
    @api.model
    def default_get(self, fields):
        defaults = super(SalesLine, self).default_get(fields)
        order = self.env['sale.order'].browse(self._context.get('active_id'))
        if order and order.currency_id:
            defaults['repricing_currency'] = order.order_line.currency_id
            defaults['existing_rate'] = order.bci_exchange_rate
            defaults['current_exchange_rate'] = order.currency_id.inverse_rate
        return defaults

    def _compute_existing_rate(self):
        for record in self:
            order = self.env['sale.order'].browse(self._context.get('active_id'))
            record.repricing_currency = order.order_line.currency_id
            record.current_exchange_rate = record.repricing_currency.inverse_rate

    def action_confirm(self):
        if self.order_id:
            self.sudo().order_id._reprice_orderline()

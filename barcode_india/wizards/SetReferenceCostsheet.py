from odoo import models, fields
from datetime import datetime, timedelta

class ReferenceCostsheetWizard(models.TransientModel):
    _name = 'reference.costsheet.wizard'
    _description = 'Reference Costsheet Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    validity_days = fields.Integer(string='Validity (Days)', required=True, default=15)
    company_ids = fields.Many2many('res.partner',string='Companys')

    def action_confirm(self):
        self.ensure_one()
        sale_order = self.sale_order_id
        if sale_order:
            validity_date = datetime.now() + timedelta(days=self.validity_days)
            
            sale_order.sudo().write({
                'use_reference_costsheet': True,
                'reference_costsheet_validity': validity_date.date(),
                'reference_company_ids': [(6, 0, self.company_ids.ids)]
            })
            sale_order.sudo().message_post(body="Reference Costsheet has been set.")
            return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class UnsetReferenceCostsheetWizard(models.TransientModel):
    _name = 'unset.reference.costsheet.wizard'
    _description = 'Unset Reference Costsheet Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    def action_confirm(self):
        if self.sale_order_id:
            self.sale_order_id.sudo().use_reference_costsheet = False
            self.sale_order_id.sudo().message_post(body="Reference Costsheet has been unset.")
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
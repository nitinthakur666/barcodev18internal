from odoo import fields, models, api, _


class PaymentTerms(models.Model):
    _name = 'barcode_india.payment_term'
    _description = 'Payment Terms'

    name = fields.Char('Milestone')
    sequence = fields.Integer("Sequence", default=1)
    order_id = fields.Many2one('sale.order','Order ID')
    percentange = fields.Float("Percentage")
    bci_is_approved = fields.Boolean('Is Approved?', default=True)
    bci_additional_payment_term = fields.Char('Additional Payment Term')
    bci_approve_note = fields.Char('Approve Note')
    
    def action_approve(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approve Payment Term'),
            'res_model': 'barcode_india.approve_pay_term',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_term_ids': self.ids,
            }
        }
   
    def write(self, vals):
        if 'percentange' in vals:
            vals['bci_is_approved'] = False
        return super(PaymentTerms, self).write(vals)
from odoo import api, fields, models


class AddNote(models.TransientModel):
    _name = 'barcode_india.approve_pay_term'
    _description = 'Add Note'

    payment_term_ids = fields.Many2many('barcode_india.payment_term', string='Payment Term IDs')
    approve_note = fields.Char('Approve Note')

    def action_approve_payment_term(self):
        if self.payment_term_ids:
            for record in self.payment_term_ids:
                if not record.bci_is_approved:
                    record.bci_approve_note = self.approve_note
                    record.bci_is_approved = True

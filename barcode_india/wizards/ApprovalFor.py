from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class ApprovedFor(models.TransientModel):
    _name = 'barcode_india.approval_for'
    _description = 'Approval'

    bci_approval_for = fields.Selection([('Remote Support','Remote Support'),('Field Service and Remote Support','Field Service and Remote Support'),('Complete Process','Complete Process')],'Approval For')
    bci_ticket_id = fields.Many2one('helpdesk.ticket',string="Ticket")


    def action_confirm(self):
        for record in self:
            approval_category = self.env["approval.category"].sudo().search([("approval_type","=",record.bci_approval_for)], limit=1)
            if not approval_category:
                raise UserError("Please create approval category!")
            vals = {
                "request_owner_id" : record.bci_ticket_id.user_id and record.bci_ticket_id.user_id.id,
                "bci_approval_for" : record.bci_approval_for,
                "category_id" : approval_category.id,
                "partner_id" : record.bci_ticket_id.partner_id and record.bci_ticket_id.partner_id.id,
                "bci_helpdesk_ticket": record.bci_ticket_id.id,
                "date" : date.today()
            }
            approval_request = self.env["approval.request"].sudo().create(vals)
            if approval_request:
                record.bci_ticket_id.bci_approval_for = record.bci_approval_for
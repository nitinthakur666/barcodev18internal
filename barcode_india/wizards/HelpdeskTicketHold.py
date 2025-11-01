from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class HelpdeskTicketHoldWizard(models.TransientModel):
    _name = 'helpdesk.wizard.hold'
    _description = 'Wizard to hold Helpdesk Ticket'

    reason = fields.Text('Reason', required=True)

    def action_hold_ticket(self):
        ticket_id = self.env.context.get('default_ticket_id')
        if not ticket_id:
            raise UserError("No active ticket found.")
        ticket = self.env['helpdesk.ticket'].browse(ticket_id)
        hold_stage = self.env['helpdesk.stage'].search([('bci_hold_stage', '=', True)], limit=1)
        if not hold_stage:
            raise UserError("No hold stage defined.")
        ticket.write({
            'stage_id': hold_stage.id,
            'bci_stages_ids': [(0, 0, {
                        'bci_ticket_id': self.id,
                        'bci_stage': hold_stage.id,
                        'hold_remarks': self.reason
                    })]
        })

class HelpdeskTicketCancelWizard(models.TransientModel):
    _name = 'helpdesk.wizard.cancel'
    _description = 'Wizard to cancel Helpdesk Ticket'

    cancel_reason = fields.Text('Reason', required=True)

    def action_cancel_ticket(self):
        ticket_id = self.env.context.get('default_ticket_id')
        if not ticket_id:
            raise UserError("No active ticket found.")
        ticket = self.env['helpdesk.ticket'].browse(ticket_id)
        cancelled_stage = self.env['helpdesk.stage'].search([('bci_cancelled_stage', '=', True)], limit=1)
        if not cancelled_stage:
            raise UserError("No cancelled stage defined.")
        ticket.write({
            'stage_id': cancelled_stage.id,
            'bci_stages_ids': [(0, 0, {
                'bci_ticket_id': ticket.id,
                'bci_stage': cancelled_stage.id,
                'hold_remarks': self.cancel_reason
            })]
        })
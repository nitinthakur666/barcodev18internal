from odoo import fields, models, _


class CreateQuotation(models.TransientModel):
    _name = 'bci.create_quotation'
    _description = 'Create Quotation'

    bci_location = fields.Many2one('stock.location',string="BCI Location")
    bci_ticket_id = fields.Many2one('helpdesk.ticket',string="Ticket")


    def action_confirm(self):
        for record in self:
            sale_order = self.env['sale.order'].create({'partner_id': record.bci_ticket_id.partner_id.id,'bci_helpdesk': record.bci_ticket_id.id,'bci_location':record.bci_location.id})
            if sale_order:
                hold_stage = self.env['helpdesk.stage'].search([('bci_hold_stage','=',True)]).filtered(lambda x: record.bci_ticket_id.team_id.id in x.team_ids.ids)
                if hold_stage:
                    sale_order.bci_helpdesk.stage_id = hold_stage.id
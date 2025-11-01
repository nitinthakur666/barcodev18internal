from odoo import models, fields, api,_
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError,ValidationError

class Escalation(models.Model):
    _name = 'barcode_india.escalation'
    _description = 'Escalation'

    name = fields.Char("Name", required="1")
    bci_tat = fields.Float("TAT (%)")
    bci_email_template = fields.Many2one("mail.template","Email Template", required="1")
    bci_user_ids = fields.Many2many("res.users", string="Sent to")
    bci_sla = fields.Many2many("helpdesk.sla",string="SLA")


class HelpdeskEscalation(models.Model):
    _name = 'barcode_india.helpdesk_escalation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Helpdesk Escalation'

    name = fields.Many2one("barcode_india.escalation","Escalation")
    # bci_mail_sent = fields.Boolean("Mail Sent?")
    bci_ticket_id = fields.Many2one("helpdesk.ticket","Ticket")
    bci_sla = fields.Many2one("helpdesk.sla",string="SLA")
    bci_user_ids = fields.Many2many("res.users", related="name.bci_user_ids")
    # bci_due_date = fields.Date("Due Date")
    bci_due_datetime = fields.Datetime("Due Date")
    bci_status = fields.Selection([('Sent','Sent'),('Cancel','Cancel')], 'Status')

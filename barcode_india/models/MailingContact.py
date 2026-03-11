from odoo import models, fields, api,_


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    bci_survey_id = fields.Many2one('survey.survey', string='Survey')

class Employee(models.Model):
    _inherit = 'hr.employee'

    bci_lob = fields.Many2one('barcode_india.lob', string='LOB')

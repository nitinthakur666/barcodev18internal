from odoo import models, fields, api,_


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    bci_survey_id = fields.Many2one('survey.survey', string='Survey')

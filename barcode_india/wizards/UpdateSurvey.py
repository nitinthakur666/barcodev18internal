from odoo import api, fields, models

class UpdateSurvey(models.TransientModel):
    _name = 'barcode_india.update_survey'
    _description = 'Update Survey'

    survey_id = fields.Many2one('survey.survey', string='Survey')
    mailing_contacts = fields.Many2many('mailing.contact', string='Mailing Contacts')
    partner_ids = fields.Many2many('res.partner', string='Partners')

    def action_update_survey(self):
        self.ensure_one()
        if self.mailing_contacts:
            for contact in self.mailing_contacts:
                contact.write({'bci_survey_id': self.survey_id.id})
        elif self.partner_ids:
            for contact in self.partner_ids:
                contact.write({'bci_survey_id': self.survey_id.id})
        return {'type': 'ir.actions.act_window_close'}

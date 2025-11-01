from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class Mailing(models.Model):
    _inherit = 'mailing.mailing'

    bci_survey_id = fields.Many2one('survey.survey', string='Survey')

    def action_update_survey(self):
        self.ensure_one()
        action = {
            'name': _('Update Survey on Recipients'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'barcode_india.update_survey',
            'target': 'new',
            'context': {'default_survey_id': self.bci_survey_id.id}
        }
        if self.mailing_model_real == 'mailing.contact':
            action['context']['default_mailing_contacts'] = [(6,0,self.env[self.mailing_model_real].search(self._parse_mailing_domain()).ids)]
            return action
        elif self.mailing_model_real == 'res.partner':
            action['context']['default_partner_ids'] = [(6,0,self.env[self.mailing_model_real].search(self._parse_mailing_domain()).ids)]
            return action
        else:
            raise ValidationError(_("Not valid on selected Recipients model!"))

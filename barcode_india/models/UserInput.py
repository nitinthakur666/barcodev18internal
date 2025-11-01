from odoo import api, fields, models

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    def get_start_url_2(self, survey_id):
        return '%s?answer_token=%s' % (survey_id.get_start_url(), self.access_token)

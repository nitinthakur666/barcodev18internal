from odoo import fields, models, _
from odoo.tools.mail import is_html_empty


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    lost_type = fields.Selection([('Lost Rejection','Lost Rejection'),('Technical Rejection','Technical Rejection')], default='Lost Rejection')

    def action_lost_reason_apply(self):
        self.ensure_one()
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({"bci_lost_type": self.lost_type, "bci_lost_reason_id": self.lost_reason_id.id, "bci_lost_reason": self.lost_feedback})
        if not is_html_empty(self.lost_feedback):
            leads._track_set_log_message(
                '<div style="margin-bottom: 4px;"><p>%s:</p>%s<br /></div>' % (
                    _('Lost Comment'),
                    self.lost_feedback
                )
            )
        res = leads.action_set_lost(lost_reason_id=self.lost_reason_id.id)
        return res
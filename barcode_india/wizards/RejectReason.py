from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class RejectReasonWizard(models.TransientModel):
    _name = 'barcode_india.reject_reason_wizard'
    _description = 'Reject Reason'

    bci_reject_reason = fields.Many2one("barcode_india.reject_reason", "Reject Reason", required="1")
    bci_rejection_remark = fields.Text("Rejection Remark")
    bci_crm_id = fields.Many2one('crm.lead',string="Lead")


    def action_confirm(self):
        for record in self:
            record.bci_crm_id.bci_lead_status_value = 'REJECT'
            record.bci_crm_id.bci_lead_status = self.env.ref('barcode_india.lead_status4').id
            record.bci_crm_id.bci_reject_reason = record.bci_reject_reason.id
            record.bci_crm_id.bci_rejection_remark = record.bci_rejection_remark
from odoo import models, fields, api, _


class CreateTask(models.TransientModel):
    _inherit = 'helpdesk.create.fsm.task'

    def _generate_task_values(self):
        self.ensure_one()
        values = super(CreateTask, self)._generate_task_values()
        values['bci_asset_id'] = self.helpdesk_ticket_id.bci_asset and self.helpdesk_ticket_id.bci_asset.id or False
        values['bci_product_id'] = self.helpdesk_ticket_id.bci_asset and self.helpdesk_ticket_id.bci_asset.bci_product.id or False
        values['bci_site_id'] = self.helpdesk_ticket_id.bci_site and self.helpdesk_ticket_id.bci_site.id or False
        values['bci_address'] = self.helpdesk_ticket_id.bci_address
        values['bci_site_phone'] = self.helpdesk_ticket_id.bci_site_phone
        values['bci_pm_status'] = self.project_id.bci_is_pm and self.helpdesk_ticket_id.bci_asset_ids and [(0,0,{'name':asset.id}) for asset in self.helpdesk_ticket_id.bci_asset_ids] or False
        return values

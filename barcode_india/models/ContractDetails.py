from odoo import models, fields, api, _

class ContractDetails(models.Model):
    _name = 'barcode_india.contracts.details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract Details'

    sequence = fields.Integer('Sequence', default=10)
    bci_contracts = fields.Many2one('barcode_india.contracts','Contracts', ondelete='cascade')
    bci_projects = fields.Many2one('project.project','Projects')
    bci_startdate = fields.Date(related='bci_contracts.bci_start',string='Start Date')
    bci_enddate = fields.Date(related='bci_contracts.bci_end',string='End Date')
    bci_partner = fields.Many2one('res.partner','Customer')
    bci_site_ids = fields.Many2many('res.partner', 'contract_details_site_rel', 'contract_id', 'partner_id', string="Sites")
    bci_plants_ids = fields.Many2many('res.partner', 'contract_details_plant_rel', 'contract_id', 'partner_id', string="Plants")
    renewal_opportunity = fields.Many2one('crm.lead','Renewal Opportunity')
    bci_opportunity = fields.Many2one('crm.lead','Opportunity')

    @api.onchange("bci_projects")
    def onchange_project_id(self):
        for record in self:
            if record.bci_projects and record.bci_contracts.id not in record.bci_projects.bci_contract_ids.ids:
                record.bci_projects.bci_contract_ids = [(4,record.bci_contracts.id)]
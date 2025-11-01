# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta,datetime
from odoo.exceptions import UserError

Preferred_Selection = [('Remote Server Support','Remote Server Support'),
                        ('On Call Support','On-Call Support'),
                        ('On Site Visit Support','On Site Visit Support')]

Stage_type = [('Draft','Draft'),
                ('Active','Active'),
                ('Cancelled','Cancelled'),
                ('Expired','Expired'),
                ('Invoiced','Invoiced'),
                ('Pending Renewal','Pending Renewal')]

class ContractType(models.Model):
    _name = 'barcode_india.contracts.type'
    _description = 'Contract Type'

    name = fields.Char(required=True, translate=True)
    type = fields.Selection([('Hardware','Hardware'),('Software','Software')], string='Type')

class ContractStage(models.Model):
    _name = 'barcode_india.contracts.stage'
    _description = 'Contract Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    stage_type = fields.Selection(Stage_type, string='Stage Type')
    # is_invoice_stage = fields.Boolean('Is Invoice Stage')
    # is_draft_stage = fields.Boolean('Is Draft Stage')


class Contract(models.Model):
    _name = 'barcode_india.contracts'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Customer Contracts'
    _order = 'id desc'

    name  = fields.Char('Name', tracking=1, copy=False)
    active = fields.Boolean('Active', default=True, tracking=2)
    bci_customer = fields.Many2one('res.partner','Customer')
    bci_address_verification = fields.Selection([('Yes','Yes'),('No','No')],'Address Verification Request')
    bci_renewal_status = fields.Selection([('In Progress','In Progress'),('To Renew','To Renew'),('Renewed','Renewed'),('To Be Activated','To Be Activated'),('Pending Commercial Closure','Pending Commercial Closure')], string="Renewal Status")
    bci_start = fields.Date('Start Date', compute='_compute_start_end_date', store=True,tracking=2)
    bci_end = fields.Date('End Date', compute='_compute_start_end_date', store=True, tracking=2)
    bci_origin = fields.Char('Source of Origin')
    bci_saleperson = fields.Many2one('res.users','Sales Person')
    bci_team_id = fields.Many2one('crm.team','Sales Team')
    bci_stage_id = fields.Many2one('barcode_india.contracts.stage','Stage', default=1)
    bci_type = fields.Many2one('barcode_india.contracts.type','Type')
    bci_site = fields.Many2one('res.partner','Site')
    bci_street = fields.Char('Street', related='bci_site.street')
    bci_street2 = fields.Char('Street 2',related='bci_site.street2')
    bci_street3 = fields.Char('Street 3',related='bci_site.street3')
    bci_street4 = fields.Char('Street 4',related='bci_site.street4')
    bci_city = fields.Char('City', related='bci_site.city')
    bci_state_id = fields.Many2one(string='State', related='bci_site.state_id')
    bci_zip = fields.Char('Zip', related='bci_site.zip')
    bci_country_id = fields.Many2one(string='Country', related='bci_site.country_id')

    bci_local_visit = fields.Integer('Local Visit')
    bci_outstation_visit = fields.Integer('Outstation Visit')

    bci_invoice_date = fields.Date('ERP Invoice Date')
    bci_invoice_number = fields.Char('ERP Invoice Number')
    bci_sopf_number = fields.Char('SOPF Reference')
    bci_invoice_internal_id  = fields.Integer('ERP Invoice Internal ID')
    bci_order_ref = fields.Char('ERP Order Reference')
    bci_site_count = fields.Integer('Sites', compute='_compute_site_count')
    bci_site_ids = fields.One2many('barcode_india.site', 'bci_contract_id', string='Sites')
    bci_assets_count = fields.Integer('Assets Count', compute='_compute_assets_count', compute_sudo=True)
    bci_assets_ids = fields.One2many('barcode_india.assets', 'bci_contract_id', string='Assets')
    bci_preferred_applicable = fields.Selection(Preferred_Selection,'Preferred and Applicable Options')
    bci_ticket_ids = fields.One2many('helpdesk.ticket', 'bci_contract_id', string='Tickets')
    bci_ticket_count = fields.Integer('Ticket Count', compute='_compute_ticket_count')
    bci_pm = fields.Boolean('Preventive Maintenance')
    bci_pm_frequency = fields.Integer('PM Frequency (days)')
    bci_amc_required = fields.Boolean('AMC Required', compute="_compute_amc_required", store=True)
    bci_opportunity_ids = fields.One2many('crm.lead', 'bci_contract_id', string='Opportunities')
    bci_opportunity_count = fields.Integer('Opportunity Count', compute='_compute_opportunity_count')
    bci_contract_details_count = fields.Integer('Contract Detauls Count', compute='_compute_contract_details_count')
    bci_renewal_opportunity = fields.Many2one('crm.lead','Renewal Opportunity')
    bci_contract_type_find = fields.Selection(related='bci_type.type',string="Type of Contract", store=True)
    bci_stage_type = fields.Selection(related='bci_stage_id.stage_type',string="Stage Type")
    bci_opportunity = fields.Many2one('crm.lead','Opportunity')
    bci_service_product = fields.Many2one('product.product','Service Product')
    bci_contract_id = fields.Many2one('barcode_india.contracts',"Renew Contract")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('barcode_india.contracts_seq')
        return super().create(vals_list)
    
    @api.depends('bci_assets_ids.bci_invoice_date','bci_assets_ids.bci_end_date','bci_assets_ids.bci_oem_start_date','bci_assets_ids.bci_oem_end_date')
    def _compute_start_end_date(self):
        for record in self:
            if record.bci_assets_ids:
                start_date = record.bci_assets_ids.filtered('bci_invoice_date').mapped('bci_invoice_date') + record.bci_assets_ids.filtered('bci_oem_start_date').mapped('bci_oem_start_date')
                end_date = record.bci_assets_ids.filtered('bci_end_date').mapped('bci_end_date') + record.bci_assets_ids.filtered('bci_oem_end_date').mapped('bci_oem_end_date')
                record.bci_start = start_date and min(start_date) or False
                record.bci_end = end_date and max(end_date) or False

    @api.depends('bci_end')
    def _compute_amc_required(self):
        date = fields.Date.today() + timedelta(days=60)
        for record in self:
            if not record.bci_amc_required and record.bci_end and record.bci_end >= date:
                record.bci_amc_required = True

    @api.depends('bci_site_ids')
    def _compute_site_count(self):
        contract_data = self.env['barcode_india.site'].read_group([('bci_contract_id', '=', self.id)], ['bci_contract_id'], ['bci_contract_id'])
        contract_mapped_data = dict((data['bci_contract_id'][0], data['bci_contract_id_count']) for data in contract_data)
        for contract in self:
            contract.bci_site_count = contract_mapped_data.get(contract.id, 0)
    
    def action_view_sites(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sites',
            'res_model': 'barcode_india.site',
            'view_mode': 'tree',
            'domain': [('bci_contract_id', '=', self.id)],
            'context': {'default_bci_contract_id': self.id,'default_bci_customer': self.bci_customer and self.bci_customer.id}
        }

    @api.depends('bci_assets_ids')
    def _compute_assets_count(self):
        assets_data = self.env['barcode_india.assets'].sudo().read_group([('bci_contract_id', '=', self.id)], ['bci_contract_id'],
                                                                    ['bci_contract_id'])
        count = sum([r['bci_contract_id_count'] for r in assets_data])
        for record in self:
            record.bci_assets_count = count

    def action_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assets',
            'res_model': 'barcode_india.assets',
            'view_mode': 'tree,form',
            'domain': [('bci_contract_id', '=', self.id)],
            'context': {'default_bci_customer': self.bci_customer.id,'default_bci_contract_id': self.id,'default_bci_site': self.bci_site.id}
        }

    def action_previous_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Assets',
            'res_model': 'barcode_india.assets',
            'view_mode': 'tree,form',
            'domain': [('bci_contract_ids', '=', self.id)]
        }

    def action_draft_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Assets',
            'res_model': 'barcode_india.assets',
            'view_mode': 'tree,form',
            'domain': [('bci_contract_id.bci_contract_id', '=', self.id)]
        }
    
    @api.depends('bci_ticket_ids')
    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group([('bci_contract_id', 'in', self.ids)], ['bci_contract_id'], ['bci_contract_id'])
        data_map = {data['bci_contract_id'][0]: data['bci_contract_id_count']for data in ticket_data}
        for contract in self:
            contract.bci_ticket_count = data_map.get(contract.id, 0)

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'name': _('Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'context': {'default_bci_contract_id': self.id},
            'domain': [('bci_contract_id', '=', self.id)],
        }
    
    @api.depends('bci_opportunity_ids')
    def _compute_opportunity_count(self):
        opportunity_data = self.env['crm.lead']._read_group([('bci_contract_id', 'in', self.ids)], ['bci_contract_id'], ['bci_contract_id'])
        data_map = {data['bci_contract_id'][0]: data['bci_contract_id_count']for data in opportunity_data}
        for contract in self:
            contract.bci_opportunity_count = data_map.get(contract.id, 0)

    def _compute_contract_details_count(self):
            for rec in self:
                rec.bci_contract_details_count = self.env['barcode_india.contracts.details'].sudo().search_count([('bci_contracts', '=', self.id)])

    def action_view_opportunities(self):
        self.ensure_one()
        return {
            'name': _('Opportunities'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'context': {'default_bci_contract_id': self.id},
            'domain': [('bci_contract_id', '=', self.id)],
        }
    
    # def generate_amc_opportunity(self):
    #     for contract in self:
    #         contract.bci_opportunity_ids = [(0, 0, {
    #             'name': 'AMC Renewal for %s' % contract.name,
    #             'type': 'opportunity',
    #             'partner_id': contract.bci_customer.id
    #         })]
    #         contract.write({'bci_amc_required': False})

    # def _cron_amc_opportunity_generation(self):
    #     date = fields.Date.today() + timedelta(days=60)
    #     contracts = self.sudo().search([('bci_amc_required','=',True),('bci_end','!=',False),('bci_end','<=',date)], limit=50)
    #     contracts.generate_amc_opportunity()

    def action_contract_details(self):
        self.ensure_one()
        return {
            'name': _('Contract Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.contracts.details',
            'view_mode': 'list,form',
            'context': {'default_bci_contracts': self.id,
                        'default_bci_partner': self.bci_customer.id if self.bci_customer else False,
                        'default_renewal_opportunity':self.bci_renewal_opportunity.id if self.bci_renewal_opportunity else False,
            },
            'domain': [('bci_contracts', '=', self.id)],
        }

    def _cron_renew_opportunity_generation(self, limit=False, days=60):
        date = fields.Date.today() + timedelta(days=days)
        contracts = self.sudo().search([('bci_end', '=', date),('bci_renewal_opportunity','=',False)], limit=limit)
        draft_stage = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Draft")])
        if contracts:
            for contract in contracts:
                Opportunity = self.env['crm.lead']
                opportunity_vals = {
                    'name': f'Renewal- {contract.name}',
                    'partner_id': contract.bci_customer.id,
                    'bci_contract_id': contract.id,
                    'type': 'opportunity'
                }
                opportunity = Opportunity.create(opportunity_vals)
                if opportunity:
                    new_contract = contract.copy()
                    new_contract.write({'bci_opportunity': opportunity.id,'bci_stage_id': draft_stage and draft_stage.id or False})
                    contract.bci_renewal_opportunity = opportunity
                    contract.bci_renewal_status = 'To Renew'
                    contract.bci_contract_id = new_contract.id
                    contract.bci_contract_id.bci_renewal_status = 'Pending Commercial Closure'
                    contract_detail = self.env['barcode_india.contracts.details'].sudo().search([('bci_contracts', '=', contract.id)])
                    assets = self.env['barcode_india.assets'].sudo().search([('bci_contract_id', '=', contract.id)])
                    if contract_detail:
                        for rec in contract_detail:
                            if contract.bci_service_product and contract.bci_service_product.bci_coverage:
                                new_start_date = contract.bci_end + timedelta(days=1)
                                end_date = new_start_date + timedelta(days=contract.bci_service_product.bci_coverage.no_of_days)
                                new_contract.write({'bci_start': new_start_date, 'bci_end': end_date})
                                new_contract_detail = rec.copy()
                                new_contract_detail.write({'bci_contracts':new_contract.id,'bci_opportunity': opportunity.id})
                                rec.write({"renewal_opportunity": opportunity.id})
                    if assets:
                        for rec in assets:
                            rec.write({"renewal_opportunity": opportunity.id, "bci_draft_contract": new_contract.id})
                else:
                    raise UserError("Cannot create Opportunity")

    def activate_contract(self,limit=False, days=1):
        active_stage = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Active")])
        expired_stage = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Expired")])
        date = fields.Date.today() - timedelta(days=days)
        contracts = self.sudo().search([('bci_end', '=', date),('bci_contract_id','!=',False)], limit=limit)
        for record in contracts:
            if record.bci_assets_ids:
                for rec in record.bci_assets_ids:
                    end_date = rec.bci_end_date + timedelta(days=rec.bci_service_product.bci_coverage.no_of_days)
                    if rec.bci_draft_contract:
                        rec.write({'bci_end_date': end_date,'bci_contract_id': record.bci_contract_id.id,'bci_contract_ids': [(4, record.id)], 'bci_draft_contract':False})
                        record.bci_contract_id.bci_stage_id = active_stage and active_stage.id
                        record.bci_contract_id.bci_renewal_status = 'In Progress'
                        record.bci_stage_id = expired_stage and expired_stage.id
                        record.bci_renewal_status = 'Renewed'
            else:
                record.bci_contract_id.bci_stage_id = active_stage and active_stage.id
                record.bci_contract_id.bci_renewal_status = 'In Progress'
                record.bci_stage_id = expired_stage and expired_stage.id
                record.bci_renewal_status = 'Renewed'

    def expired_contract(self,limit=False, days=1):
        active_stage = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Active")])
        expired_stage = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Expired")])
        date = fields.Date.today() - timedelta(days=days)
        contracts = self.sudo().search([('bci_end', '=', date),('bci_contract_id','=',False),('bci_stage_id','=',active_stage.id)], limit=limit)
        if contracts:
            for record in contracts:
                record.bci_stage_id = expired_stage and expired_stage.id
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


status_selection = [('draft','Draft'),
                    ('active','Active'),
                    ('cancelled','Cancelled'),
                    ('expired','Expired'),
                    ('invoiced','Invoiced'),
                    ('pending_renewal','Pending Renewal'),
                    ('replaced','Replaced')]
class AssetsStage(models.Model):
    _name = 'barcode_india.assets.stage'
    _description = 'Assets Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    type = fields.Selection(status_selection,"Type")

    @api.constrains('type')
    def _check_type(self):
        for rec in self:
            if rec.type:
                already_record = self.search([('type','=',rec.type),('id','!=',rec.id)])
                if already_record:
                    raise UserError(_("Pleaase define only one %s type stage!"%(rec.type)))


class Assets(models.Model):
    _name = 'barcode_india.assets'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Assets'
    _order = 'id desc'

    name  = fields.Char('Name', tracking=1)
    active = fields.Boolean('Active', default=True, tracking=2)
    bci_customer = fields.Many2one('res.partner','Customer')
    bci_product = fields.Many2one('product.product','Product')
    bci_service_product = fields.Many2one('product.product','Service Product')
    bci_contract_id = fields.Many2one('barcode_india.contracts','Contract', ondelete='cascade')
    bci_contract_ids = fields.Many2many('barcode_india.contracts',string='Previous Contract')
    bci_draft_contract = fields.Many2one('barcode_india.contracts','Draft Contract')
    bci_origin = fields.Char('Source of Origin')
    bci_stage_id = fields.Many2one('barcode_india.assets.stage','Stage',default=1)
    # bci_status = fields.Selection(status_selection,'Status', default='active')
    bci_site = fields.Many2one('res.partner','Site')
    bci_street = fields.Char('Street', related='bci_site.street')
    bci_street2 = fields.Char('Street 2',related='bci_site.street2')
    bci_street3 = fields.Char('Street 3',related='bci_site.street3')
    bci_street4 = fields.Char('Street 4',related='bci_site.street4')
    bci_city = fields.Char('City', related='bci_site.city')
    bci_state_id = fields.Many2one(string='State', related='bci_site.state_id')
    bci_zip = fields.Char('Zip', related='bci_site.zip')
    bci_country_id = fields.Many2one(string='Country', related='bci_site.country_id')
    bci_invoice_date = fields.Date('ERP Invoice Date')
    bci_invoice_number = fields.Char('ERP Invoice Number')
    bci_end_date = fields.Date('End Date')
    bci_line_no = fields.Char('Line No.')
    bci_lot = fields.Many2one('stock.lot','Lots/Serial Numbers')
    bci_replaced_by = fields.Many2one('barcode_india.assets','Replaced By')

    bci_oem_start_date = fields.Date('OEM Start Date')
    bci_oem_end_date = fields.Date('OEM End Date')
    bci_delivery_type  = fields.Char('Delivery Type')
    bci_oem_contract_no  = fields.Char('OEM Contract No')

    bci_pm = fields.Boolean('Preventive Maintenance', compute="_compute_pm_details", store=True, readonly=False)
    bci_pm_frequency = fields.Integer('PM Frequency (days)', compute="_compute_pm_details", store=True, readonly=False)
    bci_pm_next_date = fields.Date('Next PM Date', compute="_compute_pm_details", store=True, readonly=False)
    renewal_opportunity = fields.Many2one('crm.lead','Renewal Opportunity')
    bci_opportunity = fields.Many2one('crm.lead','Opportunity')
    bci_model_number_id = fields.Many2one(string='Model Number', related='bci_product.bci_model_number_id')

    @api.depends('bci_invoice_date','bci_contract_id','bci_contract_id.bci_pm','bci_contract_id.bci_pm_frequency','bci_product','bci_product.categ_id','bci_product.categ_id.bci_pm')
    def _compute_pm_details(self):
        for record in self:
            record.bci_pm = record.bci_contract_id and record.bci_contract_id.bci_pm and record.bci_product and record.bci_product.categ_id and record.bci_product.categ_id.bci_pm or False
            if record.bci_pm:
                record.bci_pm_frequency = record.bci_contract_id.bci_pm_frequency
                date = fields.Date.today()
                if record.bci_invoice_date and record.bci_invoice_date > date:
                    date = record.bci_invoice_date
                if date:
                    record.bci_pm_next_date = date + relativedelta(days=record.bci_pm_frequency)

    @api.onchange('bci_service_product','bci_invoice_date')
    def onchange_bci_service_product(self):
        for record in self:
            if record.bci_invoice_date and record.bci_service_product and record.bci_service_product.bci_coverage and record.bci_service_product.bci_coverage.no_of_days:
                next_date = record.bci_invoice_date + relativedelta(days=record.bci_service_product.bci_coverage.no_of_days)
                record.bci_end_date = next_date

    def action_get_serial_number(self):
        self.ensure_one()
        if not self.bci_lot:
            lot = self.env['stock.lot'].sudo()
            serial_number = lot.search([('name','=',self.name),('product_id','=',self.bci_product.id)])
            if not serial_number:
                serial_number = lot.create({'name': self.name,
                                            'product_id': self.bci_product.id,
                                            'company_id': self.env.company.id})
            self.bci_lot = serial_number.id
        return self.bci_lot

    def action_generate_pm_ticket(self):
        if self.filtered(lambda x: not x.bci_pm or x.bci_pm_frequency <= 0):
            raise UserError(_('PM not required !'))
        team_id = self.env['helpdesk.team'].search([('bci_type','=','Preventive Maintenance')], limit=1)
        if not team_id:
            raise UserError(_('PM Team not found !'))
        value_list = []
        partners = self.mapped('bci_customer')
        for partner in partners:
            assets = self.filtered(lambda x: x.bci_customer == partner)
            sites = assets.mapped('bci_site')
            for site in sites:
                site_assets = assets.filtered(lambda x: x.bci_site == site)
                values = {
                    'name' : 'PM - %s'%(site.display_name),
                    'partner_id': partner.id,
                    'bci_site': site.id,
                    'team_id' : team_id.id,
                    'bci_asset_ids': [(6,0,site_assets.ids)]
                }
                contracts = site_assets.mapped('bci_contract_id')
                if contracts and len(contracts) == 1:
                    values['bci_contract_id'] = contracts[0].id
                value_list.append(values)
            non_site_assets = assets.filtered(lambda x: not x.bci_site)
            values = {
                'name' : 'PM - %s'%(partner.display_name),
                'partner_id': partner.id,
                'team_id' : team_id.id,
                'bci_asset_ids': [(6,0,non_site_assets.ids)]
            }
            contracts = non_site_assets.mapped('bci_contract_id')
            if contracts and len(contracts) == 1:
                values['bci_contract_id'] = contracts[0].id
            value_list.append(values)
        ticket = self.env['helpdesk.ticket'].sudo().create(value_list)
        for asset in self:
            asset.write({'bci_pm_next_date': fields.Date.today() + relativedelta(days=asset.bci_pm_frequency)})

    def action_previous_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Assets',
            'res_model': 'barcode_india.contracts',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.bci_contract_ids.ids)]
        }
    
    def name_get(self):
        result = []
        for asset in self:
            name = asset.name or ''
            if asset.bci_invoice_date:
                invoice_date = asset.bci_invoice_date.strftime('%d/%m/%Y')
                name += f' - {invoice_date}'
            if asset.bci_end_date:
                end_date = asset.bci_end_date.strftime('%d/%m/%Y')
                name += f' - {end_date}'
            result.append((asset.id, name))
        return result

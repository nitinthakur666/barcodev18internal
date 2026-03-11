# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CostEstimation(models.Model):
    _name = 'cost_estimation.cost_estimation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cost Estimation'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    order_id = fields.Many2one('sale.order', string='Sales Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    activity_estimate_hours = fields.Float(string='Activity Estimate Hours', tracking=True)
    technical_risk_impact_estimate_hours = fields.Float(string='Technical Risk Impact Estimate Hours', tracking=True)
    business_risk_impact_estimate_hours = fields.Float(string='Business Risk Impact Estimate Hours', tracking=True)
    baseline_costing_cost = fields.Float(string='Baseline Cost', tracking=True)
    technical_risk_impact_cost = fields.Float(string='Technical Risk Impact Cost', tracking=True)
    technical_risk_impact_percent = fields.Float(string='Technical Risk Impact', tracking=True)
    business_risk_impact_cost = fields.Float(string='Business Risk Impact Cost', tracking=True)
    business_risk_impact_percent = fields.Float(string='Business Risk Impact', tracking=True)
    amc_cost = fields.Float(string='Application Support - Annual', tracking=True)
    software_support = fields.Float(string='One year software support (above 90 days)', tracking=True)
    scope_creep_factored = fields.Float(string='Scope Creep Factored', tracking=True)
    timeline_deviation = fields.Float(string='Timeline Deviation', tracking=True)
    project_overheads = fields.Float(string='Project Overheads', tracking=True)
    estimated_man_days = fields.Float(string='Estimated Man Days', tracking=True)
    manday_rate = fields.Float(string='Manday Rate', tracking=True)
    quotation_cost = fields.One2many('cost_estimation.quotation_cost', 'cost_estimation', string='Quotation Cost',copy=True)
    project_cost = fields.One2many('cost_estimation.project_cost', 'cost_estimation', string='Outcome',copy=True)
    effort_basis = fields.One2many('cost_estimation.effort_basis', 'cost_estimation', string='Effort Basis',copy=True)
    technical_factor = fields.One2many('cost_estimation.technical_factor', 'cost_estimation', string='Technical Factor',copy=True)
    business_factor = fields.One2many('cost_estimation.business_factor', 'cost_estimation', string='Business Factor',copy=True)
    costing = fields.One2many('cost_estimation.costing', 'cost_estimation', string='Calculation',copy=True)
    cost_computed = fields.Boolean(string='Cost Computed', compute='_compute_cost_computed', store=True)
    quote_updated = fields.Boolean(string='Quote Updated', compute='_compute_quote_updated', store=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s (#%s)" % (record.name, record.id)))
        return result

    def _compute_calculation(self):
        for record in self:
            record.activity_estimate_hours = record.costing and sum(record.costing.mapped('activity_estimate_hours')) or 0
            record.technical_risk_impact_estimate_hours = record.costing and sum(record.costing.mapped('technical_risk_impact_estimate_hours')) or 0
            record.business_risk_impact_estimate_hours = record.costing and sum(record.costing.mapped('business_risk_impact_estimate_hours')) or 0
            record.baseline_costing_cost = record.costing and sum(record.costing.mapped('base_price')) or 0
            record.technical_risk_impact_cost = record.costing and sum(record.costing.mapped('technical_risk')) or 0
            record.business_risk_impact_cost = record.costing and sum(record.costing.mapped('business_risk')) or 0
            record.amc_cost = record.costing and sum(record.costing.filtered(lambda x: x.code == 'B').mapped('total')) * 0.3 or 0
            record.software_support = record.amc_cost and (record.amc_cost / 12) * 9 or 0
            record.scope_creep_factored = record.costing and sum(record.costing.filtered(lambda x: x.calculation_factor == 'Scope Creep Factored').mapped('technical_risk')) + sum(record.costing.filtered(lambda x: x.calculation_factor == 'Scope Creep Factored').mapped('business_risk')) or 0
            record.timeline_deviation = record.costing and sum(record.costing.filtered(lambda x: x.calculation_factor == 'Timeline Deviation').mapped('technical_risk')) + sum(record.costing.filtered(lambda x: x.calculation_factor == 'Timeline Deviation').mapped('business_risk')) or 0
            record.project_overheads = record.costing and sum(record.costing.filtered(lambda x: x.calculation_factor == 'Project Overheads').mapped('technical_risk')) + sum(record.costing.filtered(lambda x: x.calculation_factor == 'Project Overheads').mapped('business_risk')) or 0
            record.estimated_man_days = sum([record.activity_estimate_hours, record.technical_risk_impact_estimate_hours, record.business_risk_impact_estimate_hours]) / 8 or 0
            record.manday_rate = record.estimated_man_days and (sum([record.baseline_costing_cost, record.technical_risk_impact_cost, record.business_risk_impact_cost]) / record.estimated_man_days) or 0
            record.technical_risk_impact_percent = record.baseline_costing_cost and (record.technical_risk_impact_cost / record.baseline_costing_cost) or 0
            record.business_risk_impact_percent = record.baseline_costing_cost and (record.business_risk_impact_cost / record.baseline_costing_cost) or 0

    @api.depends('effort_basis', 'technical_factor', 'business_factor')
    def _compute_cost_computed(self):
        for record in self:
            record.cost_computed = False

    @api.depends('effort_basis', 'technical_factor', 'business_factor', 'costing', 'project_cost', 'quotation_cost')
    def _compute_quote_updated(self):
        for record in self:
            record.quote_updated = False

    def action_create_inputs(self):
        self.ensure_one()
        if not self.effort_basis:
            self.effort_basis = [(0, 0, {'phase': phase.id}) for phase in self.env['cost_estimation.phase'].sudo().search([])]
        if not self.technical_factor:
            self.technical_factor = [(0, 0, {'factor': factor.id}) for factor in self.env['cost_estimation.factor'].sudo().search([('type', '=', 'Technical')])]
        if not self.business_factor:
            self.business_factor = [(0, 0, {'factor': factor.id}) for factor in self.env['cost_estimation.factor'].sudo().search([('type', '=', 'Business')])]

    def action_compute_cost(self):
        self.ensure_one()
        if not self.costing:
            self.costing = [(0, 0, {'phase': effort.phase.id}) for effort in self.effort_basis]
        if not self.project_cost:
            self.project_cost = [(0, 0, {'phase': effort.phase.id}) for effort in self.effort_basis]
        self.costing._compute_costing()
        self.project_cost._compute_project_cost()
        self._compute_calculation()
        self.quotation_cost._compute_price()
        self.cost_computed = True

    def action_update_quote(self):
        self.ensure_one()
        if any(list(map(lambda x: not x.quotation_cost, self.project_cost))):
            raise UserError(_('All Outcome are not consumed in the Quotation Cost !'))
        if not self.order_id.estimation:
            raise UserError(_('Estimation Flag is not set on the Quote !'))
        self.order_id.order_line = [(5, 0, 0)]
        self.order_id.order_line = [(0, 0, {'product_id': cost.product_id.id,
                                            'product_uom_qty': cost.product_uom_qty,
                                            'price_unit': cost.price_unit,
                                            'bci_suggested_price_unit' : cost.price_unit}) for cost in self.quotation_cost.filtered(lambda x: x.price_unit != 0)]
        self.quote_updated = True

    @api.model
    def create(self, vals):
        res = super(CostEstimation, self).create(vals)
        res.action_create_inputs()
        return res

    def action_view_costing(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calculation',
            'res_model': 'cost_estimation.costing',
            'view_mode': 'list,form',
            'domain': [('cost_estimation', '=', self.id)]
        }

    def action_view_project_cost(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Outcome',
            'res_model': 'cost_estimation.project_cost',
            'view_mode': 'list,form',
            'domain': [('cost_estimation', '=', self.id)]
        }
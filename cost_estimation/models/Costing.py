# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Calculation(models.Model):
    _name = 'cost_estimation.calculation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Calculation'
    _order = 'sequence, id'
    _rec_name = 'resource'

    resource = fields.Many2one('cost_estimation.resource', string='Resource', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    activity = fields.Float(string='Activity', tracking=True)
    baseline_costing = fields.Float(string='Baseline Costing', tracking=True)
    technical_risk_impact = fields.Float(string='Technical Risk Impact', tracking=True)
    business_risk_impact = fields.Float(string='Business Risk Impact', tracking=True)
    costing = fields.Many2one('cost_estimation.costing', string='Costing', ondelete='cascade')


class Costing(models.Model):
    _name = 'cost_estimation.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Calculation'
    _order = 'sequence, id'
    _rec_name = 'phase'

    phase = fields.Many2one('cost_estimation.phase', string='Phase', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    code = fields.Selection([('D', 'D'), ('B', 'B'), ('S', 'S')], string='Code', compute='_compute_phase_type', store=True, tracking=True)
    calculation_factor = fields.Selection([('Scope Creep Factored', 'Scope Creep Factored'), ('Timeline Deviation', 'Timeline Deviation'), ('Project Overheads', 'Project Overheads')], string='Calculation Factor', compute='_compute_phase_type', store=True, tracking=True)
    activity_estimate_hours = fields.Float(string='Activity Estimate Hours', tracking=True)
    technical_risk_impact_estimate_hours = fields.Float(string='Technical Risk Impact Estimate Hours', tracking=True)
    business_risk_impact_estimate_hours = fields.Float(string='Business Risk Impact Estimate Hours', tracking=True)
    man_hours = fields.Float(string='Man Hours', compute='_compute_total', store=True, tracking=True)
    base_price = fields.Float(string='Base Price', compute='_compute_total', store=True, tracking=True)
    technical_risk = fields.Float(string='Technical Risk', compute='_compute_total', store=True, tracking=True)
    business_risk = fields.Float(string='Business Risk', compute='_compute_total', store=True, tracking=True)
    total = fields.Float(string='Total', compute='_compute_total', store=True, tracking=True)
    calculation = fields.One2many('cost_estimation.calculation', 'costing', string='Calculation', tracking=True)
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('phase')
    def _compute_phase_type(self):
        for record in self:
            record.code = record.phase and record.phase.type or False
            record.calculation_factor = record.phase and record.phase.calculation_factor or False

    @api.depends('calculation')
    def _compute_total(self):
        for record in self:
            record.man_hours = record.calculation and sum(record.calculation.mapped('activity')) or 0
            record.base_price = record.calculation and sum(record.calculation.mapped('baseline_costing')) or 0
            record.technical_risk = record.calculation and sum(record.calculation.mapped('technical_risk_impact')) or 0
            record.business_risk = record.calculation and sum(record.calculation.mapped('business_risk_impact')) or 0
            record.total = sum([record.base_price, record.technical_risk, record.business_risk]) or 0

    def _compute_costing(self):
        for record in self:
            if record.cost_estimation:
                try:
                    effort_basis = record.cost_estimation.effort_basis.filtered(lambda x: x.phase == record.phase)
                    activity_estimate_hours = effort_basis.total_days * 8
                    record.activity_estimate_hours = activity_estimate_hours
                    technical_rating = 0
                    for factor in record.phase.risk_data.filtered(lambda x: x.applied and x.type == 'Technical').mapped('factor'):
                        level = record.cost_estimation.technical_factor.filtered(lambda x: x.factor == factor).level
                        technical_rating += level.risk_rating_lines.filtered(lambda x: x.factor == factor).rating
                    technical_risk_impact_estimate_hours = activity_estimate_hours * technical_rating
                    record.technical_risk_impact_estimate_hours = technical_risk_impact_estimate_hours
                    business_rating = 0
                    for factor in record.phase.risk_data.filtered(lambda x: x.applied and x.type == 'Business').mapped('factor'):
                        risk = record.cost_estimation.business_factor.filtered(lambda x: x.factor == factor).risk
                        business_rating += risk.risk_rating_lines.filtered(lambda x: x.factor == factor).rating
                    business_risk_impact_estimate_hours = activity_estimate_hours * business_rating
                    record.business_risk_impact_estimate_hours = business_risk_impact_estimate_hours
                    for phase_allocation in effort_basis.phase.phase_allocations:
                        calculation_values = {'resource': phase_allocation.resource.id,
                                              'activity': activity_estimate_hours * phase_allocation.allocation,
                                              'baseline_costing': activity_estimate_hours * phase_allocation.allocation * (phase_allocation.resource.quoted_n / 8),
                                              'technical_risk_impact': technical_risk_impact_estimate_hours * record.phase.phase_allocations.filtered(lambda x: x.resource == phase_allocation.resource).allocation * (phase_allocation.resource.quoted_n / 8),
                                              'business_risk_impact': business_risk_impact_estimate_hours * record.phase.phase_allocations.filtered(lambda x: x.resource == phase_allocation.resource).allocation * (phase_allocation.resource.quoted_n / 8)}
                        calculation = record.calculation.filtered(lambda x: x.resource == phase_allocation.resource)
                        if calculation:
                            record.calculation = [(1, calculation.id, calculation_values)]
                        else:
                            record.calculation = [(0, 0, calculation_values)]
                except Exception as e:
                    record.message_post(body=_("Error while computing cost<br/>"
                                               "<b>Error:</b> %s<br/>") % (str(e)))

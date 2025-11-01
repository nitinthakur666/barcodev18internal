# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectCost(models.Model):
    _name = 'cost_estimation.project_cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Outcome'
    _order = 'sequence, id'
    _rec_name = 'phase'

    phase = fields.Many2one('cost_estimation.phase', string='Project Deliverables', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    man_hours = fields.Float(string='Man Hours', tracking=True)
    baseline_cost = fields.Float(string='Baseline Cost', tracking=True)
    technical_risk = fields.Float(string='Technical Risk', tracking=True)
    business_risk = fields.Float(string='Business Risk', tracking=True)
    total_estimate = fields.Float(string='Total Estimate', compute='_compute_total_estimate', store=True, tracking=True)
    risk_buffered = fields.Float(string='Risk Buffered', group_operator='avg', compute='_compute_risk_buffered', store=True, tracking=True)
    quotation_cost = fields.Many2one('cost_estimation.quotation_cost', string='Quotation Cost')
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('baseline_cost', 'technical_risk', 'business_risk')
    def _compute_total_estimate(self):
        for record in self:
            record.total_estimate = sum([record.baseline_cost, record.technical_risk, record.business_risk]) or 0

    @api.depends('baseline_cost', 'total_estimate')
    def _compute_risk_buffered(self):
        for record in self:
            record.risk_buffered = record.total_estimate and record.baseline_cost and (record.total_estimate / record.baseline_cost) - 1 or 0

    def _compute_project_cost(self):
        for record in self:
            if record.cost_estimation:
                costing = record.cost_estimation.costing.filtered(lambda x: x.phase == record.phase)
                record.man_hours = costing.man_hours
                record.baseline_cost = costing.base_price
                record.technical_risk = costing.technical_risk
                record.business_risk = costing.business_risk

# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BusinessFactor(models.Model):
    _name = 'cost_estimation.business_factor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Business Factor'
    _order = 'sequence, id'
    _rec_name = 'factor'

    @api.model
    def _get_default_risk(self):
        return self.env['cost_estimation.risk_rating'].search([], limit=1)

    factor = fields.Many2one('cost_estimation.factor', string='Factor', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    description = fields.Char(string='Description', compute='_compute_factor_values', store=True, tracking=True)
    risk = fields.Many2one('cost_estimation.risk_rating', string='Risk', default=_get_default_risk, tracking=True)
    general_hints = fields.Char(string='General Hints', compute='_compute_factor_values', store=True, tracking=True)
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('factor')
    def _compute_factor_values(self):
        for record in self:
            record.description = record.factor and record.factor.description or False
            record.general_hints = record.factor and record.factor.general_hints or False

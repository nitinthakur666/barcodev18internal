# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TechnicalFactor(models.Model):
    _name = 'cost_estimation.technical_factor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Technical Factor'
    _order = 'sequence, id'
    _rec_name = 'factor'

    @api.model
    def _get_default_risk(self):
        return self.env['cost_estimation.risk_rating'].search([], limit=1)

    factor = fields.Many2one('cost_estimation.factor', string='Factor', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    description = fields.Char(string='Description', compute='_compute_factor_values', store=True, tracking=True)
    level = fields.Many2one('cost_estimation.risk_rating', string='Level', default=_get_default_risk, tracking=True)
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('factor')
    def _compute_factor_values(self):
        for record in self:
            record.description = record.factor and record.factor.description or False

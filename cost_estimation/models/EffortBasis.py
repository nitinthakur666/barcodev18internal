# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EffortBasis(models.Model):
    _name = 'cost_estimation.effort_basis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Effort Basis'
    _order = 'sequence, id'
    _rec_name = 'phase'

    phase = fields.Many2one('cost_estimation.phase', string='Phase', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    estimated_man_days = fields.Float(string='Estimated Man Days', tracking=True)
    correction_days = fields.Float(string='Corrections Days', tracking=True)
    total_days = fields.Float(string='Total Days', compute='_compute_total_days', store=True, tracking=True)
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('estimated_man_days', 'correction_days')
    def _compute_total_days(self):
        for record in self:
            record.total_days = sum([record.estimated_man_days, record.correction_days]) or 0

# -*- coding: utf-8 -*-

from odoo import models, fields, _


class RiskRatingLine(models.Model):
    _name = 'cost_estimation.risk_rating_line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Risk Rating Line'
    _order = 'sequence, id'
    _rec_name = 'factor'

    factor = fields.Many2one('cost_estimation.factor', string='Factor', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    rating = fields.Float(string='Rating', tracking=True)
    risk_rating = fields.Many2one('cost_estimation.risk_rating', string='Risk Rating', ondelete='cascade')

    _sql_constraints = [
        ('unique_risk_rating_line', 'unique(factor,risk_rating)', _('Another risk data already exists in the risk rating with this factor!')),
    ]


class RiskRating(models.Model):
    _name = 'cost_estimation.risk_rating'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Risk Rating'
    _order = 'sequence, id'

    name = fields.Integer(string='Rating', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    risk_rating_lines = fields.One2many('cost_estimation.risk_rating_line', 'risk_rating', string='Risk Rating Lines')

    _sql_constraints = [
        ('unique_risk_rating', 'unique(name)', _('Another risk rating already exists with this name!')),
    ]

# -*- coding: utf-8 -*-

from odoo import models, fields, _


class Factor(models.Model):
    _name = 'cost_estimation.factor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Factor'
    _order = 'sequence, id'

    name = fields.Char(string='Factor', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    type = fields.Selection([('Technical', 'Technical'), ('Business', 'Business')], string='Type', tracking=True)
    description = fields.Char(string='Description', tracking=True)
    general_hints = fields.Char(string='General Hints', tracking=True)

    _sql_constraints = [
        ('unique_factor', 'unique(name,type)', _('Another factor already exists with this name and type!')),
    ]

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Resource(models.Model):
    _name = 'cost_estimation.resource'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Resource'
    _order = 'sequence, id'

    name = fields.Char(string='Resource', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    salary = fields.Float(string='Salary', tracking=True)
    overhead = fields.Float(string='Overhead', tracking=True)
    ctc = fields.Float(string='CTC', compute='_compute_ctc', store=True, tracking=True)
    per_day = fields.Float(string='Per day', compute='_compute_perday', store=True, tracking=True)
    margin = fields.Float(string='Margin', tracking=True)
    quote = fields.Float(string='Quote', compute='_compute_quote', store=True, tracking=True)
    salary_n = fields.Float(string='Salary-N', tracking=True)
    overhead_n = fields.Float(string='Overhead-N', tracking=True)
    ctc_n = fields.Float(string='CTC-N', compute='_compute_ctc_n', store=True, tracking=True)
    manday_n = fields.Float(string='Manday-N', compute='_compute_manday_n', store=True, tracking=True)
    margin_n = fields.Float(string='Margin-N', tracking=True)
    quoted_n = fields.Float(string='Quote-N', compute='_compute_quoted_n', store=True, tracking=True)
    increase = fields.Float(string='Increase', compute='_compute_increase', store=True, tracking=True)

    _sql_constraints = [
        ('unique_resource', 'unique(name)', _('Another resource already exists with this name!')),
    ]

    @api.depends('salary', 'overhead')
    def _compute_ctc(self):
        for record in self:
            record.ctc = record.salary*(1+record.overhead) or 0

    @api.depends('ctc')
    def _compute_perday(self):
        for record in self:
            record.per_day = record.ctc/(12*22) or 0

    @api.depends('per_day', 'margin')
    def _compute_quote(self):
        for record in self:
            record.quote = record.per_day/(1-record.margin) or 0

    @api.depends('salary_n', 'overhead_n')
    def _compute_ctc_n(self):
        for record in self:
            record.ctc_n = record.salary_n*(1+record.overhead_n) or 0

    @api.depends('ctc_n')
    def _compute_manday_n(self):
        for record in self:
            record.manday_n = record.ctc_n/(12*20) or 0

    @api.depends('manday_n', 'margin_n')
    def _compute_quoted_n(self):
        for record in self:
            record.quoted_n = record.manday_n/(1-record.margin_n) or 0

    @api.depends('quote', 'quoted_n')
    def _compute_increase(self):
        for record in self:
            record.increase = record.quote and record.quoted_n and (record.quoted_n-record.quote) / record.quote or 0

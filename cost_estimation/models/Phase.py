# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RiskData(models.Model):
    _name = 'cost_estimation.risk_data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Risk Data'
    _order = 'sequence, id'
    _rec_name = 'factor'

    factor = fields.Many2one('cost_estimation.factor', string='Factor', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    applied = fields.Boolean(string='Applied', tracking=True)
    type = fields.Selection([('Technical', 'Technical'), ('Business', 'Business')], string='Type', compute='_compute_type', store=True, tracking=True)
    phase = fields.Many2one('cost_estimation.phase', string='Phase', ondelete='cascade')

    _sql_constraints = [
        ('unique_risk_data', 'unique(factor,phase)', _('Another risk data already exists in the phase with this factor!')),
    ]

    @api.depends('factor')
    def _compute_type(self):
        for record in self:
            record.type = record.factor and record.factor.type or False


class PhaseAllocation(models.Model):
    _name = 'cost_estimation.phase_allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phase Allocation'
    _order = 'sequence, id'
    _rec_name = 'resource'

    resource = fields.Many2one('cost_estimation.resource', string='Resource', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    allocation = fields.Float(string='Allocation', tracking=True)
    phase = fields.Many2one('cost_estimation.phase', string='Phase', ondelete='cascade')

    _sql_constraints = [
        ('unique_phase_allocation', 'unique(resource,phase)', _('Another phase allocation already exists in the phase with this resource!')),
    ]

    @api.constrains('allocation', 'phase')
    def _check_allocation(self):
        for record in self:
            if record.allocation and record.phase and record.phase.total > 100:
                raise UserError(_('Total Allocations exceeds the limit of 100% !'))


class Phase(models.Model):
    _name = 'cost_estimation.phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phase'
    _order = 'sequence, id'

    name = fields.Char(string='Phase', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    type = fields.Selection([('D', 'D'), ('B', 'B'), ('S', 'S')], string='Type', tracking=True)
    calculation_factor = fields.Selection([('Scope Creep Factored', 'Scope Creep Factored'), ('Timeline Deviation', 'Timeline Deviation'), ('Project Overheads', 'Project Overheads')], string='Calculation Factor', tracking=True)
    total = fields.Float(string='Total', compute='_compute_total', store=True, tracking=True)
    phase_allocations = fields.One2many('cost_estimation.phase_allocation', 'phase', string='Phase Allocations')
    risk_data = fields.One2many('cost_estimation.risk_data', 'phase', string='Risk Data')

    _sql_constraints = [
        ('unique_phase', 'unique(name)', _('Another phase already exists with this name!')),
    ]

    @api.depends('phase_allocations')
    def _compute_total(self):
        for record in self:
            record.total = record.phase_allocations and sum(record.phase_allocations.mapped('allocation')) or 0

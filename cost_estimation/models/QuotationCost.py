# -*- coding: utf-8 -*-

from odoo import models, fields, api


class QuotationCost(models.Model):
    _name = 'cost_estimation.quotation_cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quotation Cost'
    _order = 'sequence, id'
    _rec_name = 'product_id'

    name = fields.Text(string='Description', compute='_compute_description', store=True, readonly=False, required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, tracking=True)
    project_cost = fields.One2many('cost_estimation.project_cost', 'quotation_cost', string='Project', domain="[('id', 'in', project_costs)]", required=True, tracking=True)
    project_costs = fields.Many2many('cost_estimation.project_cost', string='Project Costs', compute='_compute_project_costs', tracking=True)
    product_uom_qty = fields.Float(string='Quantity', default=1, tracking=True)
    price_unit = fields.Float(string='Unit Price', compute='_compute_price', store=True, tracking=True,copy=True)
    cost_estimation = fields.Many2one('cost_estimation.cost_estimation', string='Cost Estimation', ondelete='cascade')

    @api.depends('product_id')
    def _compute_description(self):
        for record in self:
            record.name = record.product_id.get_product_multiline_description_sale()

    @api.depends('project_cost')
    def _compute_price(self):
        for record in self:
            record.price_unit = record.project_cost and sum(record.project_cost.mapped('total_estimate')) or 0
    
    @api.depends('cost_estimation', 'project_cost')
    def _compute_project_costs(self):
        for record in self:
            domain = [('id', 'in', record.cost_estimation.project_cost.ids), ('quotation_cost', '=', False)]
            record.project_costs = self.env['cost_estimation.project_cost'].search(domain)

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'project_costs' not in default and self.project_costs:
            default['project_costs'] = [(6, 0, self.project_costs.ids)]

        if 'project_cost' not in default and self.project_cost:
            default['project_cost'] = [(6, 0, self.project_cost.ids)]
        return super().copy_data(default)

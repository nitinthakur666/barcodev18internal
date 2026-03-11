# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    estimation = fields.Boolean(string='Estimation')
    cost_estimation_ids = fields.One2many('cost_estimation.cost_estimation', 'order_id', string='Cost Estimations')
    cost_estimation_count = fields.Integer(string='Cost Estimation Count', compute='_compute_cost_estimation_count')

    # @api.depends('cost_estimation_ids')
    # def _compute_cost_estimation_count(self):
    #     cost_estimation_data = self.env['cost_estimation.cost_estimation']._read_group([('order_id', 'in', self.ids)], ['order_id'], ['order_id'])
    #     data_map = {data['order_id'][0]: data['order_id_count']for data in cost_estimation_data}
    #     for order in self:
    #         order.cost_estimation_count = data_map.get(order.id, 0)

    @api.depends('cost_estimation_ids')
    def _compute_cost_estimation_count(self):
        # Read grouped data from cost_estimation model using Odoo 18 _read_group syntax
        cost_estimation_data = self.env['cost_estimation.cost_estimation']._read_group(
            domain=[('order_id', 'in', self.ids)],
            groupby=['order_id'],
            aggregates=['__count'],
        )

        # Map partner/order ID to count
        data_map = {order.id: count for order, count in cost_estimation_data}

        # Assign the computed count to each record
        for order in self:
            order.cost_estimation_count = data_map.get(order.id, 0)

    def action_generate_cost_estimation(self):
        for order in self:
            for estimation in order.cost_estimation_ids:
                estimation.write({'active':False})
            order.cost_estimation_ids = [(0, 0, {'name': order.name,
                                                 'partner_id': order.partner_id.id, })]

    def action_view_cost_estimation(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Cost Estimation'),
            'res_model': 'cost_estimation.cost_estimation',
        }
        cost_estimations = self.mapped('cost_estimation_ids')
        if len(cost_estimations) == 1:
            action['res_id'] = cost_estimations.id
            action['view_mode'] = 'form'
        else:
            action['domain'] = [('id', 'in', self.cost_estimation_ids.ids)]
            action['view_mode'] = 'list,form'
        return action

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if "cost_estimation_ids" not in default:
            default["cost_estimation_ids"] = [
                fields.Command.create(estimation.copy_data()[0]) for estimation in self.cost_estimation_ids.filtered('active')
            ]
        return super().copy_data(default)

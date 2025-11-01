# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Users(models.Model):
    _inherit = 'res.users'

    bci_salesperson = fields.Char(string="Sale Person Code",copy=False)

    is_on_holiday = fields.Boolean(string="Is on Holiday",copy=False)

    alternateuser = fields.Many2one('res.users',string='Alternate Partner ID', domain=lambda self: self._get_alternateuser_domain())

    @api.model
    def _get_alternateuser_domain(self):
        current_user_id = self._uid
        return [('id', '!=', current_user_id)]

    @api.onchange('is_on_holiday')
    def _onchange_(self):
        if self.is_on_holiday == False:
            self.alternateuser = None
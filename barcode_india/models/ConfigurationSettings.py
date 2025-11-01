# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bci_username = fields.Char(string="Username", config_parameter='bci.username')
    bci_password = fields.Char(string="Password", config_parameter='bci.password')
    bci_base_url = fields.Char(string="Base Url", config_parameter='bci.base_url')
    bci_hardware_project = fields.Many2one('project.project',string="Hardware Project:",config_parameter='bci.hardware_project')
    bci_hardware_user = fields.Many2one('res.users',string="Hardware User: " , domain=lambda self: [("groups_id", "=", self.env.ref( "barcode_india.group_barcode_india_pre_sales").id)],config_parameter='bci.hardware_head')
    bci_hardware_tags = fields.Many2many('project.tags','hardware_tags',string="Hardware Tags: ")
    bci_software_project = fields.Many2one('project.project',string="Software Project:",config_parameter='bci.software_project')
    bci_software_user = fields.Many2one('res.users',string="Software User: " , domain=lambda self: [("groups_id", "=", self.env.ref( "barcode_india.group_barcode_india_pre_sales").id)],config_parameter='bci.software_head' )
    bci_software_tags = fields.Many2many('project.tags','software_tags_rel',string="Software Tags: ")
    bci_freight_product = fields.Many2one('product.template',string="Freight Product: ",config_parameter='bci.freight_product')
    bci_installation_product = fields.Many2one('product.template',string="Installation Product: ",config_parameter='bci.installation_product')
    bci_exchange_threshold = fields.Float(string='Exchange Threshold',config_parameter='bci.exchange_threshold')
    bci_cost_threshold = fields.Float(string='Cost Threshold',config_parameter='bci.cost_threshold')
    bci_use_latest_price = fields.Boolean(string='Use latest vendor price',config_parameter='bci.bci_use_latest_price')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('bci.hardware_tags', repr(self.bci_hardware_tags.ids))
        self.env['ir.config_parameter'].sudo().set_param('bci.software_tags', repr(self.bci_software_tags.ids))
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        hardware_config = with_user.get_param('bci.hardware_tags')
        software_config = with_user.get_param('bci.software_tags')
        res.update(bci_hardware_tags=[(6, 0, literal_eval(hardware_config))] if hardware_config else [])
        res.update(bci_software_tags=[(6, 0, literal_eval(software_config))] if software_config else [])
        return res
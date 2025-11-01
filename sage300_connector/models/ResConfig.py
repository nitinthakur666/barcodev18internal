# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # module_sage = fields.Boolean("Sage CRM")
    s3_username = fields.Char("Username", config_parameter='s3.username')
    s3_password = fields.Char("Password", config_parameter='s3.password')
    s3_base_url = fields.Char("Base Url", config_parameter='s3.base_url')
    s3_pricelist = fields.Char("Pricelist", config_parameter='s3.pricelist')
    s3_billing_cycle = fields.Char("Billing Cycle", config_parameter='s3.billing_cycle')
    s3_invoice_date = fields.Date("Last Invoice Sync Date",related='company_id.s3_invoice_date', readonly=False)
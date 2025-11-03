from odoo import api, fields, models,_
from odoo.exceptions import UserError
from datetime import datetime


class ProductTemplates(models.Model):
    _inherit = 'product.template'

    bci_code = fields.Char("Code")
    bci_warranty = fields.Char("Standard Warranty(In Months)")
    bci_complete_unit_rma = fields.Boolean(string="Complete Unit RMA")
    bci_spare_count = fields.Integer(string="Spare Count",compute="_compute_spare_count")
    bci_spare_ids = fields.One2many('barcode_india.spare', 'product_tmpl_id', string='Spares')
    bci_is_resource_product = fields.Boolean(string='Resource Product')
    # bci_parent_product = fields.Many2one('product.template','Parent Product')
    bci_model_number = fields.Char("Model Number")
    bci_pricing_category = fields.Many2one("barcode_india.pricing_category",string="Pricing Category")
    bci_margin = fields.Float(string='Margin Default(%)',related='bci_erp_category.margin_default')
    bci_discount_category = fields.Many2one('barcode_india.discount_category', string='Discount Category')
    bci_discount = fields.Float(string='Principal Discount(%)')
    bci_pricing_factor = fields.Many2one('barcode_india.pricing_factor', string='Pricing Factor')
    bci_duty = fields.Float(string='Duty(%)',related='bci_pricing_factor.bci_duty')
    bci_freight = fields.Float(string='Freight(%)',related='bci_pricing_factor.bci_freight')
    bci_ins = fields.Float(string='Ins(%)',related='bci_pricing_factor.bci_ins')
    bci_clearing_nd_handling = fields.Float(string='Clearing and Handling Cost',related='bci_pricing_factor.bci_clearing_nd_handling')
    bci_forex = fields.Float(string='Forex',related='bci_pricing_factor.bci_forex')
    bci_exchange_rate = fields.Float(string='Exchange Rate',compute='_compute_cost',group_operator=False)
    bci_purchase_cost = fields.Float(string='Purchase Cost', compute='_compute_cost')
    bci_purchase_cost_change = fields.Boolean(string='Cost Change',default=False)
    bci_purchase_currency = fields.Many2one('res.currency',string='Purchase Currency',compute='_compute_cost',  group_operator=False)
    bci_landed_cost = fields.Float(string='Landed Cost', compute='_compute_cost')
    bci_erp_category = fields.Many2one('barcode_india.erp_acc_category','ERP Category') 
    bci_account_set_code = fields.Many2one("barcode_india.account_set_code","Account Set Code")

    bci_own_company = fields.Many2one("barcode_india.own_company","Own Company")
    bci_oem_product_group = fields.Many2one("barcode_india.oem_product_group","OEM & Product Group")
    bci_warranty_amc = fields.Many2one("barcode_india.warranty_amc","Warranty/AMC/Carepack Type")
    bci_coverage = fields.Many2one("barcode_india.coverage","Coverage")
    bci_service_category = fields.Many2one("barcode_india.service_category","Service Category")
    bci_coverage_type = fields.Many2one("barcode_india.coverage_type","Coverage Type")
    bci_onsite_coverage = fields.Many2one("barcode_india.onsite_coverage","Onsite Coverage")
    bci_standby_equipment = fields.Many2one("barcode_india.standby_equipment","Engineer & Standby Equipment")
    bci_sla = fields.Many2one("helpdesk.sla","SLA")
    bci_sla_product = fields.Many2one("product.template","Service Product", copy=False)
    # bci_carepack_ids = fields.Many2many("product.template",string="Carepack Products")
    bci_carepack_ids = fields.Many2many('product.template', 'care_pack_table', 'name', 'bci_sla_product', string="Carepack Products", copy=False)
    bci_factor_price = fields.Float(string='Factor Price')
    bci_kitting_item = fields.Boolean(string='Kitting Item',default=False)
    bci_model_number_id = fields.Many2one("barcode_india.model_number",string="Model Number")
    

    def _compute_spare_count(self):
        for rec in self:
            rec.bci_spare_count = self.env['barcode_india.spare'].sudo().search_count([('product_tmpl_id','=',rec.id)])

    def action_barcode_india_spare(self):
        self.ensure_one()
        default_product_id = self.product_variant_id.id if self.product_variant_count == 1 else False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Spares',
            'res_model': 'barcode_india.spare',
            'view_mode': 'list',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {
                'default_product_tmpl_id': self.id,
                'default_product_id': default_product_id,
            }
        }

    @api.onchange('seller_ids')
    def _onchange_bci_purchase_cost(self):
        for record in self:
            if record.seller_ids and record.seller_ids[0].price: 
                record.bci_purchase_cost_change = True

	# @api.model
    # def create(self, vals):
    #     rec = super(ProductTemplates, self).create(vals)
    #     already_exist = rec.mapped('optional_product_ids').filtered(lambda x: x.bci_parent_product)
    #     if already_exist:
    #         for record in already_exist:
    #             raise UserError('%s product already exists in %s product'%(record.name, record.bci_parent_product.name))
    #     map_parent = rec.mapped('optional_product_ids').filtered(lambda x: not x.bci_parent_product)
    #     if map_parent:
    #         for record in map_parent:
    #             record.bci_parent_product = rec.id
    #     return rec

    # def write(self, vals):
    #     optional_prod = self.optional_product_ids
    #     rec = super(ProductTemplates, self).write(vals)
    #     if 'optional_product_ids' in vals.keys():
    #         for record in self:
    #             already_exist = record.mapped('optional_product_ids').filtered(lambda x: x.bci_parent_product and x.bci_parent_product.id != record.id)
    #             if already_exist:
    #                 for line in already_exist:
    #                     raise UserError('%s product already exists in %s product'%(line.name, line.bci_parent_product.name))
    #             map_parent = record.mapped('optional_product_ids').filtered(lambda x: not x.bci_parent_product)
    #             if map_parent:
    #                 for line in map_parent:
    #                     line.bci_parent_product = record.id
    #             if optional_prod:
    #                 remove_prod = optional_prod - self.optional_product_ids
    #                 remove_prod.write({'bci_parent_product': False})
    #     return rec
    
    @api.depends('bci_pricing_factor','seller_ids')
    def _compute_cost(self):
        self._compute_product_cost()

    def _compute_product_cost(self):
        base_currency_id = self.env.company.currency_id or False
        use_latest_price = self.env['ir.config_parameter'].sudo().get_param('bci.bci_use_latest_price')
        for rec in self:
            if rec.bci_pricing_factor and base_currency_id:
                duty, freight, ins, clearing_nd_handling, forex = (rec.bci_pricing_factor.bci_duty, rec.bci_pricing_factor.bci_freight, rec.bci_pricing_factor.bci_ins, rec.bci_pricing_factor.bci_clearing_nd_handling, rec.bci_pricing_factor.bci_forex)
                if rec.seller_ids:
                    if use_latest_price:
                        latest_seller = rec.seller_ids.sorted(key=lambda r: r.create_date or datetime.min, reverse=True)[0]
                        vendor_price = latest_seller.price
                        vendor_currency = latest_seller.currency_id
                        vendor_discount_category = latest_seller.discount_category
                        vendor_discount_percentage = latest_seller.bci_discount_percentage
                    else:
                        vendor_price, vendor_currency = rec.seller_ids.mapped('price')[0], rec.seller_ids.mapped('currency_id')[0]
                        vendor_discount_category = rec.seller_ids.mapped('discount_category')[0] if rec.seller_ids.mapped('discount_category') else False 
                        vendor_discount_percentage = rec.seller_ids and rec.seller_ids.mapped('bci_discount_percentage')[0]

                    if vendor_price and vendor_currency:
                        # if vendor_currency.id == base_currency_id.id:
                        #     rec.bci_purchase_cost = vendor_price or False
                        #     rec.bci_purchase_currency = base_currency_id.id or False
                        #     rec.bci_exchange_rate = base_currency_id.rate or False
                        #     rec.bci_landed_cost = ((vendor_price) + ((vendor_price * freight)/100) + ((vendor_price * ins)/100))*1.01 + ((vendor_price * duty)/100) + ((vendor_price * clearing_nd_handling)/100) +((vendor_price * forex)/100)
                        #     if vendor_discount_percentage and vendor_discount_percentage != 0.0:
                        #         rec.bci_discount = vendor_discount_percentage
                        #     elif vendor_discount_category:
                        #         rec.bci_discount = vendor_discount_category.bci_discount if vendor_discount_category else False
                        #     else:
                        #         rec.bci_discount = False
                       
                        # else:
                        if vendor_discount_percentage and vendor_discount_percentage != 0.0:
                            discount = vendor_discount_percentage
                        elif vendor_discount_category:
                            discount = vendor_discount_category.bci_discount if vendor_discount_category else False
                        else:
                            discount = False

                        rec.bci_discount = discount
                        rec.bci_discount_category = vendor_discount_category or False
                        rec.bci_exchange_rate = vendor_currency.compute(1, base_currency_id) or False
                        forex_amount = (rec.bci_exchange_rate * (100 + forex)) / 100
                        ins_amount = (forex_amount * (100 + ins)) / 100
                        freight_amount = (ins_amount * (100 +freight)) / 100
                        duty_amount = (freight_amount * (100 + duty)) / 100
                        factor_price = (duty_amount * (100 + clearing_nd_handling)) / 100

                        rec.bci_factor_price = factor_price
                        vendor_price_after_disc = (vendor_price * (100 - discount)) / 100
                        rec.bci_purchase_cost = (vendor_price_after_disc * factor_price) or False
                        rec.bci_landed_cost = (rec.bci_purchase_cost * 100) / (100-rec.bci_erp_category.margin_default)
                        rec.bci_purchase_currency = vendor_currency.id or False
                    else:
                        rec.bci_purchase_cost = rec.standard_price or False
                        rec.bci_purchase_currency = base_currency_id.id or False
                        rec.bci_exchange_rate = base_currency_id.rate or False
                        raise UserError("Price or Currency is missing in Seller Line under Purchase Tab")
                else:
                    rec.bci_purchase_cost = rec.standard_price or False
                    rec.bci_purchase_currency = base_currency_id.id or False
                    rec.bci_exchange_rate = base_currency_id.rate or False
                    final_cost = ((rec.standard_price) + ((rec.standard_price * freight)/100) + ((rec.standard_price * ins)/100))*1.01 + ((rec.standard_price * duty)/100) + ((rec.standard_price * clearing_nd_handling)/100) +((rec.standard_price * forex)/100)
                    rec.bci_landed_cost = final_cost
            else:
                rec.bci_purchase_cost = rec.standard_price or False
                rec.bci_purchase_currency = base_currency_id.id or False
                rec.bci_exchange_rate = base_currency_id.rate or False
                rec.bci_landed_cost = 0

class ProductProduct(models.Model):
    _inherit = "product.product"

    bci_spare_count = fields.Integer(string="Spare Count",compute="_compute_variant_spare_count")

    def _compute_variant_spare_count(self):
        for rec in self:
            rec.bci_spare_count = self.env['barcode_india.spare'].sudo().search_count([('product_id','=',rec.id)])

    def action_barcode_india_spare(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Spares',
            'res_model': 'barcode_india.spare',
            'view_mode': 'list',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_tmpl_id': self.product_tmpl_id.id,
                'default_product_id': self.id,
            }
        }


class ProductCategory(models.Model):
    _inherit = "product.category"

    bci_code = fields.Char(string="Code")
    bci_pm = fields.Boolean('Preventive Maintenance')

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    discount_category = fields.Many2one('barcode_india.discount_category',string='Discount Category')
    bci_discount_percentage = fields.Float(string='Discount Percentage')
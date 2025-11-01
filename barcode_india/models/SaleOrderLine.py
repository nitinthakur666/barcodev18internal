from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bci_part_number = fields.Char('Part Number', related='product_id.default_code', store=True)
    bci_model_number = fields.Char('Model Number', related='product_id.bci_model_number', store=True)
    bci_pricing_category = fields.Many2one('barcode_india.pricing_category',related='product_id.bci_pricing_category', string='Pricing Category',store=True)
    bci_list_price = fields.Float(string='Quote Price', group_operator=False)
    bci_guide_price = fields.Float(string='Guide Price', group_operator=False)
    bci_applied_discount = fields.Float(string='Applied Discount', group_operator=False)
    # bci_exchange_rate = fields.Float(string='Exchange Rate',related='order_id.bci_exchange_rate', store=True, group_operator=False)
    bci_target_margin = fields.Float(string='Margin %', group_operator=False)
    bci_approved_margin = fields.Float(string='Margin Approved %', group_operator=False,compute='_compute_margin')
    bci_include_scm_cost = fields.Boolean(string='Include in SCM Cost?')
    bci_include_hem_cost = fields.Char(string='Include in HEM Cost')
    bci_warranty = fields.Integer(string='Warranty in Months', group_operator=False)
    bci_approved_quote_amount = fields.Integer(string='Approved Quote Amount', group_operator=False)
    bci_approval_stage = fields.Selection([('pending','Approval Pending'),('approved','Approved')],string='Stage',default='pending')
    bci_role = fields.Selection(related='order_id.bci_user_role',string='Role')
    bci_pricing_factor = fields.Many2one('barcode_india.pricing_factor', string='Pricing Factor')
    bci_discount_category = fields.Many2one('barcode_india.discount_category', string='Discount Category')
    bci_discount = fields.Float(string='Principal Discount(%)')
    bci_landed_cost = fields.Float(string='Landed Cost')
    bci_duty = fields.Float(string='Duty(%)')
    bci_freight = fields.Float(string='Freight(%)')
    bci_ins = fields.Char(string='Ins')
    bci_clearing_nd_handling = fields.Char(string='Clearing and Healing')
    bci_forex = fields.Char(string='Forex')
    bci_exchange_rate = fields.Float(string='Exchange Rate')
    bci_purchase_cost = fields.Float(string='Purchase Cost')
    bci_principal_cost = fields.Float(string='Principal Cost',store=True)
    bci_purchase_currency = fields.Many2one('res.currency', string='Purchase Currency')
    bci_suggested_price_unit = fields.Float(string="Suggested Price")
    # price_unit = fields.Float()
    bci_approver = fields.Many2one('res.users',string='Approver',related='bci_pricing_category.approver',store=True)
    bci_pricing_provider = fields.Many2many('res.users', related='bci_pricing_category.pricing_provider', string='Pricing Provider')
    bci_line_landed_cost = fields.Float(string=' Line Landed Cost')
    is_line_approver =  fields.Boolean('Is Line Approver?',compute='_compute_line_approver')
    is_line_pricing_provider = fields.Boolean('Is Line Approver?',compute='_compute_line_pricing_provider')
    bci_section = fields.Char(string='Section')
    bci_subsection = fields.Char(string='Sub Section')
    bci_is_optional = fields.Boolean(string='Is Optional?')
    
    product_last_sale_price = fields.Float(string='Last Sale Price',store=True)
    product_last_sale_date = fields.Date(string='Last Sale Date',store=True)
    product_last_sale_order = fields.Char(string='Last Sale Order',store=True)
    is_sales_person = fields.Boolean('Is Sales Person ?', compute='_compute_is_sales_person')
    # remaining_item = fields.Float('SOPF Remaining Item', compute='_compute_remaining_item', store=True)
    sopf_done_quantity = fields.Float('SOPF Done Quantity', default=0.0)
    sopf_done_amount = fields.Float('SOPF Done Amount', default=0.0)
    bci_price_with_discount = fields.Float(string='Price With Apply Discount', related='product_template_id.bci_landed_cost')
    bci_is_reference = fields.Boolean(related='order_id.is_reference',string='Is Reference?')
    select_product = fields.Boolean(string="Select", default=False)
    special_price = fields.Float(string='Special Buy Price')
    special_price_applicable = fields.Boolean(related='product_template_id.special_price_applicable', store=True)
    special_price_locked = fields.Boolean(string='Special Price Locked', default=False)

    related_creation_date = fields.Date(string='SOPF Creation Date', related='order_id.creation_date')
    related_sopf_sequence = fields.Char(string='SOPF Sequence', related='order_id.sopf_sequence')
    related_po_number = fields.Char(string='PO Number', related='order_id.po_number')
    related_order_untaxed_amount = fields.Monetary(string='Order Untaxed Amount', related='order_id.amount_untaxed')
    related_order_total = fields.Monetary(string='Order Total', related='order_id.amount_total')

    def _compute_is_sales_person(self):
        for rec in self:
            user = self.env['res.users'].sudo().browse(self._uid)
            rec.is_sales_person = user.has_group('barcode_india.group_barcode_india_sale_person') or False
    
    @api.onchange('product_template_id')
    def _get_product_domain(self):
        self.sudo().product_template_id._compute_product_cost()
        if self.order_id.bci_erp_category and not self.order_id.bypass_quote:
            return {'domain': {'product_template_id': [('bci_erp_category', 'in', self.order_id.bci_erp_category.ids),('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]}}
        else:
            return {'domain': {'product_template_id': [('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]}}           

    def open_product_last_sale_popup(self):
        self.ensure_one()
        last_sale_order = (
            self.env['sale.order'].search([('order_line.product_id', '=', self.product_id.id),('partner_id','=',self.order_id.partner_id.id),('name','<',self.order_id.name)], limit=1, order='date_order desc'))
        if last_sale_order:
            self.product_last_sale_price = last_sale_order.order_line.filtered(lambda l: l.product_id == self.product_id).price_unit
            self.product_last_sale_date = last_sale_order.date_order
            self.product_last_sale_order = last_sale_order.name
        return {
            'type': 'ir.actions.act_window',
            'name': 'Last Sale Order',
            'res_model': 'bci.sale_line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_product': self.product_id.name,
                'default_bci_sale_price': self.product_last_sale_price,
                'default_bci_sale_date': self.product_last_sale_date,
                'default_bci_sale_order': self.product_last_sale_order,
            },
        }

    def _compute_line_approver(self):
        for rec in self:
            logged_in_user = user = self.env['res.users'].sudo().browse(self._uid)
            if rec.bci_approver.id == logged_in_user.id:
                rec.is_line_approver = True
            else:
                rec.is_line_approver = False

    def _compute_line_pricing_provider(self):
        for rec in self:
            logged_in_user = user = self.env['res.users'].sudo().browse(self._uid)
            if logged_in_user.id in rec.bci_pricing_provider.ids:
                rec.is_line_pricing_provider = True
            else:
                rec.is_line_pricing_provider = False


    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Order Line',
            'res_model': 'reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def write(self, vals):
        if self.env.context.get('updating_approval_stage'):
            return super(SaleOrderLine, self).write(vals)
        is_duplicating = self.env.context.get('is_duplicating', False)
        allowed_fields = [
            'bci_section', 
            'bci_subsection', 
            'bci_is_optional',
            'sequence'
        ]
        unauthorized_fields = [field for field in vals.keys() if field not in allowed_fields]
        
        for record in self:
            if not is_duplicating and record._check_freight_and_installation_product(record.order_id.id, record.id) and record.display_type == False:
                if unauthorized_fields:
                    raise ValidationError(_("Cannot modify lines when Freight and Installation product is present"))
            old_values = {field: getattr(record, field) for field in vals.keys() if field in record}          
            if not record.order_id.bypass_quote and not is_duplicating and record.display_type == False:
                if ('special_price' in vals and vals['special_price'] > 0 or record.special_price_applicable != False) and not record.special_price_locked:
                    vals['bci_approval_stage'] = 'pending'
                if 'bci_suggested_price_unit' in vals.keys() and vals['bci_suggested_price_unit'] < record.bci_list_price:
                    vals['bci_approval_stage'] = 'pending'
            result = super(SaleOrderLine, self).write(vals)
            new_values = {field: getattr(record, field) for field in vals.keys() if field in record}
            changes = {key: {'old': old_values.get(key), 'new': new_values.get(key)} for key in vals.keys()}
            if changes and not is_duplicating:
                change_list = "\n".join([f"<li>{key}: From <b>{change['old']}</b> to <b>{change['new']}</b></li>" for key, change in changes.items()])
                body = f"<ul>{change_list}</ul>"
                record.order_id.message_post(
                    body=f"Changes in Order Line {record.id}:\n{body}",
                )
           
            # if 'bci_discount' in vals:
            #     if record.product_id.bci_discount_category.is_promocode == True:
            #         raise ValidationError("You cannot apply discount on Promo Price!")
            return result

    def _check_freight_and_installation_product(self, order_id, line_id=None):
        if self.env.context.get('bypass_freight_installation_check'):
            return False
        if not order_id:
            return False
        order = self.env['sale.order'].browse(order_id)
        if not order.estimation:
            freight_product_id = self.env['ir.config_parameter'].sudo().get_param('bci.freight_product')
            installation_product_id = self.env['ir.config_parameter'].sudo().get_param('bci.installation_product')
            forbidden_products = [freight_product_id, installation_product_id]
            has_special_product = False
            for order_line in order.order_line:
                if str(order_line.product_template_id.id) in forbidden_products:
                    has_special_product = True
                    break
            if has_special_product:
                if line_id:
                    line = self.browse(line_id)
                    if str(line.product_template_id.id) in forbidden_products:
                        return False
                return True
        return False

    def action_approve(self):
        for rec in self:
            if rec.special_price_applicable and rec.special_price <= 0:
                raise UserError(_("Special price is required for this product. Please enter a special price."))
            if rec.bci_suggested_price_unit <= 0.00:
                raise UserError(_("Please Enter Unit Price"))
            vals = {
                'bci_approval_stage': 'approved'
            }
            if rec.special_price > 0 or rec.special_price_applicable:
                vals['special_price_locked'] = True
            rec.with_context(updating_approval_stage=True).sudo().write(vals)
            if rec.order_id.user_id:
                template_id = self.env.ref('barcode_india.email_template_sale_line_approval').id
                template = self.env['mail.template'].browse(template_id)
                template.send_mail(rec.id, force_send=False)
        return True

        
    @api.model_create_multi
    def create(self, vals_list):
        processed_vals_list = []
        for vals in vals_list:
            if vals.get('order_id'):
                if self._check_freight_and_installation_product(vals['order_id']) and vals.get('display_type', False) == False:
                    raise ValidationError(_("Cannot create new lines when Freight and Installation product is present"))
            if vals.get('product_template_id'):
                product = self.env['product.template'].browse(vals['product_template_id'])
                if 'bci_approval_stage' not in vals:
                    special_price = vals.get('special_price', 0)
                    special_price_applicable = product.special_price_applicable if product else False
                    suggested_price = vals.get('bci_suggested_price_unit', 0)
                    display_type = vals.get('display_type', False)
                    special_price_locked = vals.get('special_price_locked')
                    if (special_price > 0 or special_price_applicable != False) and not special_price_locked:
                        vals['bci_approval_stage'] = 'pending'
                    elif suggested_price == 0.00 and display_type == False:
                        vals['bci_approval_stage'] = 'pending'
                    else:
                        vals['bci_approval_stage'] = 'approved'
                if product:
                    vals['bci_discount'] = product.bci_discount
            processed_vals_list.append(vals)
        records = super(SaleOrderLine, self).create(processed_vals_list)
        return records

    def unlink(self):
        for record in self:
            if record._check_freight_and_installation_product(record.order_id.id, record.id) and record.display_type == False:
                raise ValidationError(_("Cannot remove lines when Freight and Installation product is present"))
        
        category_summary = self.env['barcode_india.category_summary'].sudo()
        for record in self:
            if record.bci_pricing_category:
                exist_record = category_summary.search([('name', '=', record.bci_pricing_category.id), ('bci_sale_id', '=', record.order_id.id)])
                if exist_record and exist_record.bci_total_quote_amt > record.price_unit:
                    exist_record.bci_total_quote_amt -= record.price_unit
                else:
                    exist_record.unlink()
        return super(SaleOrderLine, self).unlink()
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        super(SaleOrderLine, self)._compute_price_unit()
        for line in self:
            line.bci_pricing_factor = line.product_id.bci_pricing_factor or False
            line.bci_discount_category = line.product_id.bci_discount_category
            line.bci_duty = line.product_id.bci_pricing_factor and line.product_id.bci_pricing_factor.bci_duty
            line.bci_freight = line.product_id.bci_pricing_factor and line.product_id.bci_pricing_factor.bci_freight
            line.bci_ins = line.product_id.bci_pricing_factor and line.product_id.bci_pricing_factor.bci_ins
            line.bci_clearing_nd_handling = line.product_id.bci_pricing_factor and line.product_id.bci_pricing_factor.bci_clearing_nd_handling
            line.bci_forex = line.product_id.bci_pricing_factor and line.product_id.bci_pricing_factor.bci_forex
            line.bci_exchange_rate = line.product_id.bci_exchange_rate
            line.bci_purchase_cost = line.product_id.bci_purchase_cost
            vendor_price= line.product_id.seller_ids.mapped('price')
            line.bci_principal_cost  = vendor_price[0] if vendor_price else 0.00
            line.bci_purchase_currency = line.product_id.bci_purchase_currency
            line.bci_landed_cost = line.product_id.bci_landed_cost
            line.bci_line_landed_cost = line.bci_landed_cost * line.product_uom_qty
            # line.bci_discount = line.product_id.bci_discount
            line.bci_target_margin = line.product_id.bci_erp_category and line.product_id.bci_erp_category.margin_default
            line.bci_approved_margin = line.product_id.bci_erp_category and line.product_id.bci_erp_category.margin_default
            # discounted_price = line.bci_landed_cost - ((line.bci_landed_cost * line.bci_discount)/100 or 0.00 )  
            line.bci_suggested_price_unit = line.bci_landed_cost #* (100 - line.bci_discount) / (100 - line.bci_target_margin)
            line.price_unit = round(line.bci_suggested_price_unit,2)

    @api.depends('price_unit','bci_suggested_price_unit')
    def _compute_margin(self):
        for line in self:
            landed_price = (line.bci_landed_cost*(100- line.bci_discount)/100) * line.product_uom_qty or 0.00
            total_price = line.price_unit * line.product_uom_qty
            line.bci_approved_margin = ((total_price-landed_price)/total_price)*100 if total_price != 0 else 0


    @api.onchange('bci_suggested_price_unit')
    def _onchange_suggested_price(self):
        for rec in self:
            rec.price_unit = round(rec.bci_suggested_price_unit,2)
            # rec.bci_landed_cost = rec.bci_suggested_price_unit * (100 - rec.bci_target_margin) / (100 - rec.bci_discount)
            rec.bci_landed_cost = rec.bci_suggested_price_unit * (100 - rec.bci_target_margin) / 100 
            rec.bci_purchase_cost = rec.bci_landed_cost
            rec.bci_line_landed_cost = rec.bci_landed_cost * rec.product_uom_qty

    @api.onchange('bci_discount')
    def _onchange_bci_discount(self):
        self.sudo().product_template_id._compute_product_cost()
        for line in self:
            if line.product_id.bci_discount_category.is_promocode == True:
                    raise ValidationError("You cannot change the discount on Promo Price!")
            if line.bci_suggested_price_unit and line.bci_discount >= 0:
                vendor_price_after_disc = (line.product_id.seller_ids.mapped('price')[0] * (100 - line.bci_discount)) / 100
                purchase_cost = (vendor_price_after_disc * line.product_id.bci_factor_price) or False
                landed_cost = (purchase_cost * 100) / (100-line.bci_target_margin)
                line.bci_suggested_price_unit = landed_cost
                line.price_unit = line.bci_suggested_price_unit
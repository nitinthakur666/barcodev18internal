from odoo import fields, models, api,_
from odoo.exceptions import ValidationError

class ReferenceCostsheet(models.TransientModel):
    _name = 'bci.reference_costsheet'
    _description = 'Reference Costsheet'

    current_sale_order_id = fields.Many2one('sale.order', string='Current Sale Order', required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user, readonly=True)
    reference_sale_order_ids = fields.Many2many('sale.order', string='Reference Quotations', compute="_compute_reference_sale_orders")
    selected_sale_order_id = fields.Many2one('sale.order', string='Selected Reference Costsheet')
    reference_order_line_ids = fields.One2many('bci.reference_costsheet.line', 'wizard_id', string='Reference Order Lines')

    @api.depends('current_sale_order_id.partner_id', 'current_sale_order_id.bci_quote_type')
    def _compute_reference_sale_orders(self):
        for record in self:
            if record.current_sale_order_id:
                domain = ['|', 
                    ('partner_id', '=', record.current_sale_order_id.partner_id.id),
                    ('reference_company_ids', 'in', record.current_sale_order_id.partner_id.id),
                    ('bci_quote_type', '=', record.current_sale_order_id.bci_quote_type.id),
                    ('id', '!=', record.current_sale_order_id.id),
                    ('bci_stage', '=', 'approved'),
                    ('use_reference_costsheet', '=', True),  
                ]
                record.reference_sale_order_ids = self.env['sale.order'].search(domain)
            else:
                record.reference_sale_order_ids = False

    def _get_excluded_product_templates(self):
        """Get excluded product template ids from system parameters"""
        freight_templates = self.env['ir.config_parameter'].sudo().get_param('bci.freight_product_templates', '').strip()
        installation_templates = self.env['ir.config_parameter'].sudo().get_param('bci.installation_product_templates', '').strip()
        
        freight_template_ids = [int(x.strip()) for x in freight_templates.split(',') if x.strip().isdigit()] if freight_templates else []
        installation_template_ids = [int(x.strip()) for x in installation_templates.split(',') if x.strip().isdigit()] if installation_templates else []
        
        freight_category = self.env['ir.config_parameter'].sudo().get_param('bci.freight_category_id', '').strip()
        installation_category = self.env['ir.config_parameter'].sudo().get_param('bci.installation_category_id', '').strip()
        
        freight_category_id = int(freight_category) if freight_category and freight_category.isdigit() else False
        installation_category_id = int(installation_category) if installation_category and installation_category.isdigit() else False
        
        if freight_category_id:
            freight_products = self.env['product.template'].search([('categ_id', '=', freight_category_id)])
            freight_template_ids.extend(freight_products.ids)
        
        if installation_category_id:
            installation_products = self.env['product.template'].search([('categ_id', '=', installation_category_id)])
            installation_template_ids.extend(installation_products.ids)
        
        if not freight_template_ids and not installation_template_ids:
            freight_patterns = ['delivery', 'freight', 'shipping', 'transport']
            for pattern in freight_patterns:
                freight_products = self.env['product.template'].search([('name', 'ilike', pattern)])
                freight_template_ids.extend(freight_products.ids)
            
            installation_patterns = ['installation', 'setup', 'mounting']
            for pattern in installation_patterns:
                installation_products = self.env['product.template'].search([('name', 'ilike', pattern)])
                installation_template_ids.extend(installation_products.ids)
        
        freight_template_ids = list(set(freight_template_ids))
        installation_template_ids = list(set(installation_template_ids))
        
        return freight_template_ids + installation_template_ids

    def _is_excluded_product(self, product):
        excluded_template_ids = self._get_excluded_product_templates()
        return product.product_tmpl_id.id in excluded_template_ids

    @api.onchange('selected_sale_order_id')
    def _onchange_selected_sale_order(self):
        self.ensure_one()
        self.reference_order_line_ids = [(5, 0, 0)]

        if self.selected_sale_order_id:
            if not self.env.user.has_group('barcode_india.group_reference_costsheet_admin') and self.selected_sale_order_id.reference_costsheet_validity and self.selected_sale_order_id.reference_costsheet_validity < fields.Date.today():
                raise ValidationError("This reference costsheet has expired.Please contact your reference costsheet admin")
        
        if self.selected_sale_order_id:
            excluded_product_tmpl_ids = self._get_excluded_product_templates()
            
            new_lines = []
            for line in self.selected_sale_order_id.order_line:
                if line.product_id.product_tmpl_id.id not in excluded_product_tmpl_ids:
                    new_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal,
                        'special_price' : line.special_price,
                        'select_product': False,
                        'special_price_locked': line.special_price_locked,
                    }))

            if new_lines:
                self.reference_order_line_ids = new_lines

    def reference_costsheet_wizard(self):
        self.ensure_one()
        if not self.selected_sale_order_id:
            raise ValidationError("Please select a reference quotation.")
        if not self.reference_order_line_ids.filtered(lambda l: l.select_product):
            raise ValidationError(_("Please select at least one product before confirming."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bci.reference_costsheet.confirmation',
            'view_mode': 'form',
            'view_id': self.env.ref('barcode_india.view_bci_reference_costsheet_confirmation_form').id,
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def action_confirm(self):
        self = self.sudo()
        self.ensure_one()
        excluded_product_tmpl_ids = self._get_excluded_product_templates()
        self.current_sale_order_id.order_line.unlink()
        
        order_lines = []
        for line in self.reference_order_line_ids.filtered(lambda l: l.select_product):
            if line.product_id.product_tmpl_id.id not in excluded_product_tmpl_ids:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_template_id': line.product_id.product_tmpl_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'discount': line.discount if hasattr(line, 'discount') else 0.0,  
                    'tax_id': [(6, 0, line.product_id.taxes_id.ids)],  
                    'bci_suggested_price_unit': line.price_unit,  
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'bci_purchase_cost': line.product_id.bci_purchase_cost,
                    'bci_landed_cost': line.product_id.bci_landed_cost,
                    'special_price_applicable': line.product_id.special_price_applicable,
                    'special_price': line.special_price,
                    'special_price_locked': line.special_price_locked,
                }))
        
        if order_lines:
            self.current_sale_order_id.write({'order_line': order_lines})
        
        return {'type': 'ir.actions.act_window_close'}


class ReferenceCostsheetLine(models.TransientModel):
    _name = 'bci.reference_costsheet.line'
    _description = 'Reference Costsheet Line'

    wizard_id = fields.Many2one('bci.reference_costsheet', string="Wizard")
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_qty = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")
    special_price = fields.Float(string="Special Price")
    price_subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    select_product = fields.Boolean(string="Select")
    special_price_locked = fields.Boolean(string='Special Price Locked')

    @api.depends("product_uom_qty", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit


class ReferenceCostsheetConfirmation(models.TransientModel):
    _name = 'bci.reference_costsheet.confirmation'
    _description = 'Reference Costsheet Confirmation'

    def confirm_action(self):
        self.ensure_one()
        wizard = self.env['bci.reference_costsheet'].browse(self._context.get('active_id'))
        return wizard.action_confirm()

    def cancel_action(self):
        return {'type': 'ir.actions.act_window_close'}
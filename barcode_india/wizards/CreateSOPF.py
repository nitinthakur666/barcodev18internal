from odoo import fields, models, api, _,exceptions
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class CreateSOPF(models.TransientModel):
    _name = 'bci.create_sopf'
    _description = 'Create SOPF'

    sopf_type = fields.Selection(
        string='Company Type',
        selection=[('Single SOPF', 'Single SOPF'), ('Multiple SOPF', 'Multiple SOPF')],
        default="Single SOPF"
    )
    order_id = fields.Many2one('sale.order', 'Sale Order ID')

    order_lines_id = fields.One2many(
        'bci.create_sopf.line',
        'sopf_wizard_id',
        string='Sale Order Lines',
    )

    # purchase_contact = fields.Many2one('res.partner',string="Purchase Contact")
    # finance_contact = fields.Many2one('res.partner',string="Finance Contact")
    # store_contact = fields.Many2one('res.partner',string="Store Contact")
    purchase_contact_name = fields.Char(string='Purchase Contact Name')
    purchase_contact_email = fields.Char(string='Purchase Email')
    purchase_contact_phone = fields.Char(string='Purchase Phone')
    finance_contact_name = fields.Char(string='Finance Contact Name')
    finance_contact_email = fields.Char(string='Finance Email')
    finance_contact_phone = fields.Char(string='Finance Phone')
    store_contact_name = fields.Char(string='Store Contact Name')
    store_contact_email = fields.Char(string='Store Email')
    store_contact_phone = fields.Char(string='Store Phone')

    instructions = fields.Text(string="Instructions", default="To create a SOPF order You can change the quantity of non-Freight or non-Installation Products and You can change the Unit Price of Freight or Installation Products.")

    po_attach_ids = fields.Many2many('ir.attachment',string='Purchase Order Attachments', help='Attach one or more files if needed.')
    special_instructions = fields.Text(string="Special Instructions")
    customer_id = fields.Many2one('res.partner', string="Customer")
    invoice_address_id = fields.Many2one('res.partner', string="Invoice Address")
    delivery_address_id = fields.Many2one('res.partner', string="Delivery Address")
    po_date = fields.Date(string='PO Date', default=fields.Date.context_today)
    po_number = fields.Char(string="PO Number")
    creation_date = fields.Date(string='SOPF Date', default=fields.Date.context_today)
    sopf_sequence = fields.Char(string='Name', required=True, copy=False,tracking=True,default=lambda self: _('New'))
    delivery_schedule = fields.Char(string="Delivery Schedule")

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('sopf_sequence', _('New')) == _('New'):
    #             seq = self.env['ir.sequence'].next_by_code('bci.create_sopf')
    #             vals['sopf_sequence'] = seq
    #     return super(CreateSOPF, self).create(vals_list)

    @api.onchange('order_id')
    def _onchange_order_id(self):
        if self.order_id:
            order_lines = self.order_id.order_line.filtered(lambda line: line.product_id and line.product_uom_qty)
            self.order_lines_id = [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': (line.product_uom_qty - line.sopf_done_quantity),
                'price_unit': (line.price_unit - line.sopf_done_amount),
                'special_price': line.special_price,
                'special_price_locked': line.special_price_locked,
                'sale_order_line_id': line.id,
            }) for line in order_lines if ((line.product_uom_qty - line.sopf_done_quantity) != 0.0 and (
                        line.price_unit - line.sopf_done_amount) != 0.0)]

            # partner_id = self.order_id.partner_id.id
            # domain = [('parent_id', '=', partner_id)]
            # return {'domain': {'purchase_contact': domain, 'finance_contact': domain, 'store_contact': domain}}

    @api.onchange('order_lines_id')
    def _onchange_order_lines_id(self):
        bci_freight_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'))
        bci_installation_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'))

        for line in self.order_lines_id:
            original_product_uom_qty = line.sale_order_line_id.product_uom_qty
            original_price_unit = line.sale_order_line_id.price_unit

            if (line.product_id.product_tmpl_id.id == bci_freight_product or line.product_id.product_tmpl_id.id == bci_installation_product):
                # Check if the quantity has changed
                if line.product_uom_qty != original_product_uom_qty:
                    line.product_uom_qty = original_product_uom_qty
                    # raise ValidationError(
                    #     "Quantity entered for Product '%s' cannot be modified for Freight or Installation Products."
                    #     % line.product_id.name
                    # )

            else:
                # Check if the Price has changed
                if line.price_unit != original_price_unit:
                    line.price_unit = original_price_unit
                    # raise ValidationError(
                    #     "Unit Price entered for Product '%s' cannot be modified for Non-Freight or Non-Installation Products."
                    #     % line.product_id.name
                    # )

    def action_confirm(self):
        new_order = None

        seq = self.env['ir.sequence'].next_by_code('bci.create_sopf')
        self.sopf_sequence = seq

        if not self.po_attach_ids:
            raise exceptions.UserError("Please attach at least one file before confirming!")

        bci_freight_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'))
        bci_installation_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'))

        if self.sopf_type == "Multiple SOPF":
            for line in self.order_lines_id:
                original_product_uom_qty = line.sale_order_line_id.product_uom_qty
                original_price_unit = line.sale_order_line_id.price_unit
                if (line.product_id.product_tmpl_id.id == bci_freight_product or line.product_id.product_tmpl_id.id == bci_installation_product):
                    # Check if the quantity has changed
                    if line.product_uom_qty != original_product_uom_qty:
                        raise ValidationError(
                            "Quantity entered for Product '%s' cannot be modified for Freight or Installation Products."
                            % line.product_id.name
                        )
                else:
                    # Check if the Price has changed
                    if line.price_unit != original_price_unit:
                        raise ValidationError(
                            "Unit Price entered for Product '%s' cannot be modified for Non-Freight or Non-Installation Products."
                            % line.product_id.name
                        )

                if line.product_uom_qty > (
                        original_product_uom_qty - line.sale_order_line_id.sopf_done_quantity) or line.product_uom_qty == 0.0:
                    # Check if Quantity exceeds the limit
                    raise ValidationError(
                        "Quantity entered for Product '%s' exceeds the remaining item '%s' in the sale order line." % (
                            line.product_id.name,
                            (original_product_uom_qty - line.sale_order_line_id.sopf_done_quantity)))

                if line.price_unit > (
                        original_price_unit - line.sale_order_line_id.sopf_done_amount) or line.price_unit == 0.0:
                    # Check if Price exceeds the limit
                    raise ValidationError(
                        "Unit Price entered for Product '%s' exceeds the remaining amount '%s' in the sale order line." % (
                            line.product_id.name, (original_price_unit - line.sale_order_line_id.sopf_done_amount)))
                if not new_order:
                    new_order = self.order_id.with_context(bypass_freight_installation_check=True).copy()
                    new_order.with_context(bypass_freight_installation_check=True).write({
                        'order_line': [(5, 0, 0)],
                        'state': 'SOPF',
                        'sopf_order': self.order_id.id,
                        'partner_id' : self.customer_id.id,
                        'partner_invoice_id':  self.invoice_address_id.id,
                        'partner_shipping_id': self.delivery_address_id.id,
                        # 'purchase_contact': self.purchase_contact.id,
                        # 'finance_contact': self.finance_contact.id,
                        # 'store_contact': self.store_contact.id,
                        'purchase_contact_name': self.purchase_contact_name,
                        'purchase_contact_email': self.purchase_contact_email,
                        'purchase_contact_phone': self.purchase_contact_phone,
                        'finance_contact_name': self.finance_contact_name,
                        'finance_contact_email': self.finance_contact_email,
                        'finance_contact_phone': self.finance_contact_phone,
                        'store_contact_name': self.store_contact_name,
                        'store_contact_email': self.store_contact_email,
                        'store_contact_phone': self.store_contact_phone,
                        'special_instructions': self.special_instructions,
                        'po_number' : self.po_number,
                        'po_date': self.po_date,
                        'po_attach_ids': [(6, 0, self.po_attach_ids.ids)],
                        'creation_date' : self.creation_date,
                        'sopf_sequence' : self.sopf_sequence,
                        'bci_delivery_schedule': self.delivery_schedule,
                        'bci_pt_approval': 'approved',
                        'bci_margin_approval' : 'approved',
                        'bci_special_approval' : 'approved',
                        'bci_stage' : 'approved',
                    })
                if (line.product_id.product_tmpl_id.id != bci_freight_product and line.product_id.product_tmpl_id.id != bci_installation_product):
                    self.env['sale.order.line'].with_context(bypass_freight_installation_check=True).create({
                        'order_id': new_order.id,
                        'product_id': line.product_id.id,
                        'product_template_id': line.product_id.product_tmpl_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'bci_suggested_price_unit': line.price_unit,
                        'bci_purchase_cost' : line.product_id.bci_purchase_cost,
                        'bci_landed_cost' : line.product_id.bci_landed_cost,
                        'special_price_applicable' : line.product_id.special_price_applicable,
                        'special_price' : line.special_price,
                        'bci_approval_stage': 'approved',
                        'special_price_locked' : line.special_price_locked,
                    })
                    line.sale_order_line_id.with_context(bypass_freight_installation_check=True).sopf_done_quantity += line.product_uom_qty

                elif (
                        line.product_id.product_tmpl_id.id == bci_freight_product or line.product_id.product_tmpl_id.id == bci_installation_product):
                    self.env['sale.order.line'].with_context(bypass_freight_installation_check=True).create({
                        'order_id': new_order.id,
                        'product_id': line.product_id.id,
                        'product_template_id': line.product_id.product_tmpl_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'bci_suggested_price_unit': line.price_unit,
                        'bci_purchase_cost' : line.product_id.bci_purchase_cost,
                        'bci_landed_cost' : line.product_id.bci_landed_cost,
                        'special_price_applicable' : line.product_id.special_price_applicable,
                        'special_price' : line.special_price,
                        'bci_approval_stage': 'approved',
                        'special_price_locked' : line.special_price_locked,
                    })
                    line.sale_order_line_id.with_context(bypass_freight_installation_check=True).sopf_done_amount += line.price_unit

            self.order_id.so_state = 'split'
            self.order_id.bci_stage = 'approved'

            self.order_id._compute_is_sopf_button_visible()
        
            if not self.order_id.is_sopf_button_visible:
                self.order_id.action_confirm()
        
        elif self.sopf_type == "Single SOPF":
            self.order_id.with_context(bypass_freight_installation_check=True).write({
                # 'purchase_contact': self.purchase_contact.id,
                # 'finance_contact': self.finance_contact.id,
                # 'store_contact': self.store_contact.id,
                'purchase_contact_name': self.purchase_contact_name,
                'purchase_contact_email': self.purchase_contact_email,
                'purchase_contact_phone': self.purchase_contact_phone,
                'finance_contact_name': self.finance_contact_name,
                'finance_contact_email': self.finance_contact_email,
                'finance_contact_phone': self.finance_contact_phone,
                'store_contact_name': self.store_contact_name,
                'store_contact_email': self.store_contact_email,
                'store_contact_phone': self.store_contact_phone,
                'special_instructions': self.special_instructions,
                'po_number' : self.po_number,
                'po_attach_ids': [(6, 0, self.po_attach_ids.ids)],
                'creation_date' : self.creation_date,
                'sopf_sequence' : self.sopf_sequence,
                'bci_delivery_schedule': self.delivery_schedule,
                'po_date': self.po_date,
            })

            for line in self.order_id.with_context(bypass_freight_installation_check=True).order_line:
                if (line.product_id.product_tmpl_id.id != bci_freight_product and line.product_id.product_tmpl_id.id != bci_installation_product):
                    line.sopf_done_quantity = line.product_uom_qty

                elif (line.product_id.product_tmpl_id.id == bci_freight_product or line.product_id.product_tmpl_id.id == bci_installation_product):
                    line.sopf_done_amount += line.price_unit

            self.order_id.action_confirm()
            
class CreateSOPFLine(models.TransientModel):
    _name = 'bci.create_sopf.line'
    _description = 'Create SOPF Line'

    sopf_wizard_id = fields.Many2one('bci.create_sopf', 'Wizard')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity', required=True)
    price_unit = fields.Float('Unit Price')
    special_price = fields.Float('Special Price')
    special_price_locked = fields.Boolean('Special Price Locked')
    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_qty = 1.0
            self.price_unit = self.product_id.list_price
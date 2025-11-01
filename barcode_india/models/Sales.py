from odoo import fields,models,api,_,exceptions
import json
from odoo.exceptions import UserError,ValidationError
from odoo.tools import html_escape
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _order = 'bci_version,id'

    bci_helpdesk = fields.Many2one('helpdesk.ticket','Helpdesk')
    bci_location = fields.Many2one('stock.location','BCI Location',default=lambda self: self.env['stock.location'].search([('bci_code', 'ilike', 'BCILGN')], limit=1).id)
    bci_stage = fields.Selection([('draft','Draft'),('pricing_request','Pricing Request'),('pricing_updated','Pricing Updated'),('pending_approval','Pending Approval'),('approved','Approved'),('rejected','Rejected')],string='Stage', default='draft',readonly=False,compute='_compute_bci_stage',store=True,tracking=True,copy=False)
    bci_version =  fields.Integer('Version',default=0)
    bci_cost_sheet_count = fields.Integer('Cost Sheet Count',compute='_compute_cost_sheet_count')
    bci_exchange_rate = fields.Float(string='Exchange Rate')
    bci_freight = fields.Float(string='Freight %')
    bci_duty = fields.Float(string='Duty %')
    bci_margin = fields.Float(string='Margin %')
    bci_is_low_value_order = fields.Boolean('Is this a low value order?')
    bci_is_cost_sheet_final = fields.Boolean('Is Cost Sheet Final?')
    bci_category_summary = fields.One2many('barcode_india.category_summary', 'bci_sale_id',string='Category Summary', copy=False)
    bci_payment_terms = fields.One2many('barcode_india.payment_term','order_id',string='Payment Terms',copy=True,tracking=True)
    bci_readonly_fields = fields.Char('Readonly Fields')
    bci_user_role = fields.Selection([('guest','Guest'),('pre_sales','Pre Sales'),('sale_person','Sale Person'),('category_head','Category Head'),('management','Management')],compute='_compute_user_role',string='Roles')
    bci_validity_expired = fields.Boolean('Is Validity Expired?')
    validity_expired_message = fields.Char(string='Validity Expired Message', compute='_compute_validity_expired_message')
    bci_exchange_expired = fields.Boolean('Is exchange Expired?')
    exchange_expired_message = fields.Char(string='Exchange Expired Message', compute='_compute_exchange_expired_message')
    bci_cost_expired = fields.Boolean('Is cost Expired?')
    cost_expired_message = fields.Char(string='Cost Expired Message', compute='_compute_cost_expired_message')
    bci_exchange_threshold = fields.Float('Exchange Threshold',default=2)
    bci_cost_diff_threshold = fields.Float('Purchase Cost Threshold',default=2)
    bci_quote_type = fields.Many2one('barcode_india.quotation_type','Quote Type',order='sequence')
    bci_erp_category = fields.Many2many(related='bci_quote_type.erp_category',string='ERP Category')
    bci_deal_margin = fields.Float('Deal Margin(%)' ,compute='_compute_deal_margin',store=True)
    bci_margin_approver = fields.Many2many('res.users',string='Approver')
    is_approver = fields.Boolean(compute='_compute_is_approver',string="Is Approver?")
    bci_pt_approval = fields.Selection([('pending','Pending'),('approved','Approved')],string="Payment Term Approval Status",default='approved',copy=False)
    bci_margin_approval = fields.Selection([('pending','Pending'),('approved','Approved')],string="Margin Approval Status?",default='pending',copy=False)
    bci_special_approval = fields.Selection([('pending','Pending'),('approved','Approved')],string="Special Approval Status?",default='pending',copy=False)
    bci_printout_type = fields.Selection([('section','Section'),('sub_section','Sub Section'),('details','Details')],string="Type",default='details')
    bci_show_optional = fields.Boolean(string='Show Optional?')
    bypass_quote = fields.Boolean(related='bci_quote_type.bci_bypass_quote', string="Bypass quote", readonly=True)
    bci_bg_pg = fields.Selection([('bg','ABG'),('pbg','PBG')],string='Any ABG/PBG for Payment. Will need additional Approvals?')
    bci_payment_period = fields.Selection([('within_45_days','As per Payment Terms'),('beyond_45_days','More than 30 Days')],default='within_45_days',string='Payment period. Anything beyond 30 days will need additional Approvals.')
    bci_ld_clause = fields.Boolean(string='Is there a LD Clause?',default=False)
    is_send_for_pricing = fields.Boolean(string='send for pricing',default=False)
    bci_presales_ids = fields.Many2many('res.users', related='opportunity_id.bci_presales_ids', string='Pre-Sales', readonly=True)
    bci_installation_type = fields.Many2one('barcode_india.installation_types',string="Installation Type")
    bci_freight_type = fields.Many2one('barcode_india.freight_types',string="Freight Type")
    bci_installation_amount = fields.Float(string='Installation Amount',readonly=True)
    bci_freight_amount = fields.Float(string='Freight Amount',readonly=True)
    po_attach_ids = fields.Many2many('ir.attachment',string='Purchase Order Attachments', help='Attach one or more files if needed.')
    special_instructions = fields.Text(string="Special Instructions")
    bci_is_estimation = fields.Boolean(related='bci_quote_type.estimation',string="Estimation")
    check_quote_type_message = fields.Char(string='Message :',default="Please set a value in 'Quote Type' before editing the order lines!")
    po_number = fields.Char(string="PO Number")
    po_date = fields.Date(string='PO Date')
    check_payment_message = fields.Char(string='Message',compute='_compute_payment_message')

    state = fields.Selection(
        selection_add=[
            ('SOPF','SOPF')
        ])
    sopf_order = fields.Many2one('sale.order',string="SOPF Order")
    purchase_contact = fields.Many2one('res.partner',string="Purchase Contact")
    finance_contact = fields.Many2one('res.partner',string="Finance Contact")
    store_contact = fields.Many2one('res.partner',string="Store Contact")

    purchase_contact_name = fields.Char(string='Purchase Contact Name')
    purchase_contact_email = fields.Char(string='Purchase Email')
    purchase_contact_phone = fields.Char(string='Purchase Phone')
    finance_contact_email = fields.Char(string='Finance Email')
    finance_contact_name = fields.Char(string='Finance Contact Name')
    finance_contact_phone = fields.Char(string='Finance Phone')
    store_contact_name = fields.Char(string='Store Contact Name')
    store_contact_email = fields.Char(string='Store Email')
    store_contact_phone = fields.Char(string='Store Phone')

    creation_date = fields.Date(string='SOPF Creation Date')
    sopf_sequence = fields.Char(string='Name')

    bci_sopf_count = fields.Integer('SOPF Count', compute='_compute_sopf_count')
    bci_auto_approval = fields.Float(related='bci_quote_type.auto_approval',string="Auto Approval Margin(%)")
    is_sopf_button_visible = fields.Boolean(string='Is SOPF Button Visible',compute='_compute_is_sopf_button_visible',store=True)
    is_new_version = fields.Boolean(string='Is New Version', default=False)
    bci_delivery_schedule = fields.Char(string="Delivery Schedule")
    approval_approvers_ids = fields.Many2many('res.users','sale_order_all_approvers_rel',string='All Approvers')
    partner_credit_limit = fields.Float(related='partner_id.bci_outstanding_balance_exceed',string="Customer Credit Limit",store=True)
    partner_outstanding_balance = fields.Float(related='partner_id.bci_outstanding_balance',string="Customer Outstanding Balance",store=True)
    advance_100 = fields.Boolean(string="100% Advance", help="If checked, PT Approval is bypassed.")
    use_reference_costsheet = fields.Boolean(string="Set As Reference Costsheet",tracking=True)
    is_reference = fields.Boolean(string="Is Reference", help="If checked, the reference cost sheet will be used to populate the current cost sheet.")
    reference_costsheet_validity = fields.Date(string='Reference Costsheet Validity',tracking=True)
    reference_company_ids = fields.Many2many('res.partner','bci_reference_company_rel', string='Reference Companys',tracking=True)

    @api.model
    def create(self, vals):
        if 'bci_payment_terms' in vals and vals.get('bci_stage') != 'approved' and not vals.get('advance_100'):
            vals['bci_pt_approval'] = 'pending'
        order = super(SaleOrder, self).create(vals)
        if order.bypass_quote == True:
            order.bci_stage = 'approved'
            order.bci_is_cost_sheet_final = True
        if order.order_line and (line.bci_approval_stage != 'approved' for line in order.order_line):
            order.is_send_for_pricing = True
        if order.state != 'SOPF' and order.order_line and all(line.bci_approval_stage == 'approved' for line in order.order_line):
            order.bci_stage = 'pricing_updated'
        if order.po_attach_ids:
            order.mapped('po_attach_ids').write({
            'res_model': order._name,
            'res_id': order.id
        })
        expected_terms = order._get_default_payment_terms()
    
        is_modified = False
        if not order.is_new_version:
            if len(order.bci_payment_terms) != len(expected_terms):
                is_modified = True
            else:
                for actual, expected in zip(order.bci_payment_terms, expected_terms):
                    expected_dict = expected[2]
                    if (actual.name != expected_dict['name'] or 
                        actual.percentange != expected_dict['percentange']):
                        is_modified = True
                        break
            if is_modified and not order.advance_100:
                order.write({
                    'bci_pt_approval': 'pending'
                })
            else:
                if order.bci_pt_approval != 'approved':
                    order.write({
                        'bci_pt_approval': 'approved'
                    })
        return order
            # if is_modified:
            #     order.write({
            #         'bci_pt_approval': 'pending'
            #     })
            # else:
            #     if order.bci_pt_approval != 'approved':
            #         order.write({
            #             'bci_pt_approval': 'approved'
            #         })
        # return order

    def write(self, vals):
        for record in self:
            old_terms_list = []
            if 'bci_payment_terms' in vals and record._origin.bci_payment_terms:
                old_terms_list = [f"{term.name}: {term.percentange}%" for term in record._origin.bci_payment_terms]
            if 'advance_100' in vals and vals['advance_100'] and record.bci_pt_approval == 'pending':
                vals['bci_pt_approval'] = 'approved'
            # if 'bci_payment_terms' in vals and record._origin.bci_payment_terms:
            #     old_terms_list = [f"{term.name}: {term.percentange}%" for term in record._origin.bci_payment_terms]
            if 'bci_payment_terms' in vals:
                if record.bci_stage != 'approved' and not record.advance_100:
                    vals['bci_pt_approval'] = 'pending'
            if 'order_line' in vals:
                if vals['order_line'] and (line.bci_approval_stage != 'approved' for line in record.order_line):
                    vals['is_send_for_pricing'] = True
                if vals['order_line'] and record.bci_margin_approval == 'approved':
                    record.bci_margin_approval = 'pending'
            if 'bci_bg_pg' in vals:
                if vals['bci_bg_pg'] and record.bci_special_approval == 'approved':
                    record.bci_special_approval = 'pending'
            if 'bypass_quote' or 'bci_quote_type' or 'order_line' in vals:
                if record.bypass_quote:
                    vals['bci_stage'] = 'approved'
            if record.po_attach_ids:
                record.mapped('po_attach_ids').write({
                    'res_model': record._name,
                    'res_id': record.id
                })
            res = super(SaleOrder, self).write(vals)

            if 'bci_payment_terms' in vals:
                new_terms = []
                for term in record.bci_payment_terms:
                    new_terms.append(f"{term.name}: {term.percentange}%")
                if old_terms_list != new_terms:
                    body = """
                        <p>Payment Terms changed:</p>
                        <ul>
                            <li>Old values: %s</li>
                            <li>New values: %s</li>
                        </ul>
                    """ % (
                        "\n".join(old_terms_list) if old_terms_list else 'None', 
                        "\n".join(new_terms) if new_terms else 'None'
                    )
                    
                    record.message_post(body=body)
            return res
        
    def copy(self, default=None):
        self = self.with_context(is_duplicating=True)
        return super(SaleOrder, self).copy(default)

    @api.depends('partner_id')
    def _compute_user_id(self):
        for order in self:
            if order.partner_id and not (order._origin.id and order.user_id):
                order.user_id = self.env.user

    @api.depends('bci_payment_period')
    def _compute_payment_message(self):
        for record in self:
            if record.bci_payment_period != 'within_45_days':
                record.check_payment_message = "You have chosen a custom Payment Period. Please make sure the milestones are updated as well!"
            else:
                record.check_payment_message = False

    def _compute_is_approver(self):
        user = self.env['res.users'].sudo().browse(self._uid)
        if user and user in self.bci_margin_approver:
            self.is_approver = True
        else:
            self.is_approver = False

    @api.depends('bci_validity_expired')
    def _compute_validity_expired_message(self):
        for order in self:
            if order.bci_validity_expired:
                order.validity_expired_message = "BCI Quote Validity has expired for this Quotation. Please take action."
            else:
                order.validity_expired_message = None
    
    @api.depends('bci_exchange_expired')
    def _compute_exchange_expired_message(self):
        for order in self:
            if order.bci_exchange_expired:
                order.exchange_expired_message = "BCI Exchange Rate has expired for this sale order. Please take action."
            else:
                order.exchange_expired_message = None

    @api.depends('bci_cost_expired')
    def _compute_cost_expired_message(self):
        for order in self:
            if order.bci_cost_expired:
                order.cost_expired_message = "BCI Cost has expired for this sale order. Please take action."
            else:
                order.cost_expired_message = None

    def send_for_approval(self):
        for rec in self:
            if not rec.bci_payment_terms:
                raise ValidationError(_("Payment Terms are required before sending for approval."))
            approval_requests_exist = False
            all_approvers = set()
            quote_type = rec.bci_quote_type
            if rec.bci_quote_type and rec.amount_total > rec.bci_quote_type.quote_limit and rec.bci_quote_type.quotetype_after_limit:
                quote_type = rec.bci_quote_type.quotetype_after_limit
            if not rec.estimation:
                freight_product_id = int(self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'))
                installation_product_id = int(self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'))
                orderline_product_ids = rec.order_line.mapped('product_template_id.id')
                for product_template_id in orderline_product_ids:
                    product_template = self.env['product.template'].browse(product_template_id)
                    if product_template.bci_erp_category.freight_applicable:
                        if freight_product_id not in orderline_product_ids:
                            raise ValidationError(_("Please Add Freight Products."))
                    if product_template.bci_erp_category.installation_applicable:
                        if installation_product_id not in orderline_product_ids:
                            raise ValidationError(_("Please Add Installation Products."))

            rec.bci_stage = 'pending_approval'
            # Payment Term Approval
            if rec.bci_pt_approval and rec.bci_pt_approval != 'approved' and not rec.bypass_quote:
                pt_category_id = self.env['approval.category'].sudo().search([('bci_is_pt_approval', '=', True)])
                request_model = self.env['approval.request'].sudo()

                def extract_user_ids(users):
                    user_ids = []
                    for user in users:
                        user_id = user.alternateuser.id if user.alternateuser else user.id
                        user_ids.append(user_id)
                    return user_ids

                approver_ids = []

                price_subtotal = rec.amount_total or 0.00
                margin_lines = self.env['barcode_india.pt_matrix'].sudo().search([('quotations_type_id', '=', rec.bci_quote_type.id),'|',('value','>=',price_subtotal),'|',('customer_type', '=', rec.partner_id.bci_customer_type),('customer_type', '=', 'all'),'|',('customer_category', '=', rec.partner_id.bci_customer_category),('customer_category', '=', 'all')],order='sequence asc')
                if margin_lines:
                    for margin_line in margin_lines:
                        sale_person = rec.user_id
                        sale_person_limit = self.env['barcode_india.sale_person_limit'].sudo().search([('quot_type', '=', quote_type.id),('user', '=', sale_person.id),('payment_deal_value', '>', rec.amount_total)], limit=1)
                        if sale_person_limit:
                            rec.bci_pt_approval = 'approved'
                            break
                        if margin_line.recommending_authority == 'sale_person' or margin_line.approving_authority == 'sale_person':
                            if not sale_person_limit:
                                continue
                        if margin_line.recommending_authority == 'user':
                            recommender_user_ids = extract_user_ids(margin_line.recommending_approvers)
                            if not recommender_user_ids:
                                raise UserError("Specific Users are not defined")
                            approver_ids.extend(recommender_user_ids)
                            all_approvers.update(recommender_user_ids)

                        elif margin_line.recommending_authority == 'vertical_head':
                            vertical_head_id = extract_user_ids(rec.partner_id and rec.partner_id.parent_id and rec.partner_id.parent_id.bci_vertical and rec.partner_id.parent_id.bci_vertical.vertical_head or (rec.partner_id.bci_vertical and rec.partner_id.bci_vertical.vertical_head))
                            if not vertical_head_id:
                                raise UserError("Vertical Head is not defined")
                            approver_ids.extend(vertical_head_id)
                            all_approvers.update(vertical_head_id)
                        elif margin_line.recommending_authority == 'region_head':
                            region_head_id = extract_user_ids(rec.user_id.partner_id and rec.user_id.partner_id.parent_id and rec.user_id.partner_id.parent_id.bci_region_user and rec.user_id.partner_id.parent_id.bci_region_user.region_head or (
                                        rec.user_id.partner_id.bci_region_user and rec.user_id.partner_id.bci_region_user.region_head))
                            if not region_head_id:
                                raise UserError("Region Head is not defined")
                            approver_ids.extend(region_head_id)
                            all_approvers.update(region_head_id)
                        
                        if margin_line.approving_authority == 'user':
                            approver_user_ids = extract_user_ids(margin_line.approvers)
                            if not approver_user_ids:
                                raise UserError("Specific Users are not defined")
                            approver_ids.extend(approver_user_ids)
                            all_approvers.update(approver_user_ids)
                        elif margin_line.approving_authority == 'vertical_head':
                            vertical_head_id = extract_user_ids(rec.partner_id and rec.partner_id.parent_id and rec.partner_id.parent_id.bci_vertical and rec.partner_id.parent_id.bci_vertical.vertical_head or (rec.partner_id.bci_vertical and rec.partner_id.bci_vertical.vertical_head))
                            if not vertical_head_id:
                                raise UserError("Vertical Head is not defined")
                            approver_ids.extend(vertical_head_id)
                            all_approvers.update(vertical_head_id)
                        elif margin_line.approving_authority == 'region_head':
                            region_head_id = extract_user_ids(rec.user_id.partner_id and rec.user_id.partner_id.parent_id and rec.user_id.partner_id.parent_id.bci_region_user and rec.user_id.partner_id.parent_id.bci_region_user.region_head or (
                                        rec.user_id.partner_id.bci_region_user and rec.user_id.partner_id.bci_region_user.region_head))
                            if not region_head_id:
                                raise UserError("Region Head is not defined")
                            approver_ids.extend(region_head_id)
                            all_approvers.update(region_head_id)
                        break
                else:
                    raise UserError("Please Add atleast 1 User to approve your request!!!!!")
                if approver_ids:
                    unique_user_ids = []
                    seen = set()
                    for user_id in approver_ids:
                        if user_id not in seen:
                            unique_user_ids.append(user_id)
                            seen.add(user_id)
                    if unique_user_ids:
                        approval_requests_exist = True               
                    approval_request = request_model.create({
                        'name': f'Payment Term Approval for {rec.name}',
                        'category_id': pt_category_id.id or False,
                        'bci_sale_order_id': rec.id or False,
                        'request_owner_id': self.env.user.id,
                        'request_status': 'pending',
                        'date_confirmed': fields.Datetime.now()
                    })
                    approval_request.approver_ids.unlink()
                    approval_request.approver_ids = [(0, 0, {'user_id': user_id,'required': True}) for user_id in unique_user_ids]
                    approval_request.action_confirm()
            # margin approval
            if not rec.bci_margin_approval or rec.bci_margin_approval == 'approved' or rec.bypass_quote:
                continue

            def extract_user_ids(users):
                return [user.alternateuser.id if user.alternateuser else user.id for user in users]

            margin_category = self.env['approval.category'].sudo().search([('bci_is_margin_approval', '=', True)], limit=1)
            request_model = self.env['approval.request'].sudo()

            def create_approval_request(approver_ids):
                if approver_ids:
                    approval_request = request_model.create({
                        'name': f'Margin Approval for {rec.name}',
                        'category_id': margin_category.id or False,
                        'bci_sale_order_id': rec.id or False,
                        'request_owner_id': self.env.user.id,
                        'request_status': 'new',
                        'date_confirmed': fields.Datetime.now()
                    })
                    approval_request.approver_ids.unlink()
                    approval_request.approver_ids = [(0, 0, {'user_id': user_id, 'required': True}) for user_id in approver_ids]
                    approval_request.action_confirm()

            def handle_approver_type(margin):
                approver_ids = []
                is_approved = False
                if margin.approver_type == 'sale_person':
                    sale_person = rec.user_id
                    if sale_person:
                        sale_person_limit = self.env['barcode_india.sale_person_limit'].search([('quot_type', '=', margin.quotation_type_id.id),('user','=',sale_person.id)], limit=1)
                        if sale_person_limit and rec.amount_total < sale_person_limit.deal_value:
                            rec.bci_margin_approval = 'approved'
                            is_approved = True
                if margin.approver_type == 'user':
                    if margin.approver:
                        approver_ids.extend([approver.id for approver in margin.approver])
                    else:
                        raise UserError("Specific users are not defined")
                elif margin.approver_type == 'vertical_head':
                    vertical_head_ids = extract_user_ids(
                        rec.partner_id.parent_id.bci_vertical.vertical_head or 
                        rec.partner_id.bci_vertical.vertical_head
                    )
                    if vertical_head_ids:
                        approver_ids.extend(vertical_head_ids)
                    else:
                        raise UserError("Vertical Head is not defined")
                elif margin.approver_type == 'region_head':
                    region_head_ids = extract_user_ids(
                        rec.user_id.partner_id.parent_id.bci_region_user.region_head or 
                        rec.user_id.partner_id.bci_region_user.region_head
                    )
                    if region_head_ids:
                        approver_ids.extend(region_head_ids)
                    else:
                        raise UserError("Region Head is not defined")
                return approver_ids, is_approved
            if not rec.estimation:
                if rec.bci_auto_approval <= round(rec.bci_deal_margin, 2):
                    rec.bci_margin_approval = 'approved'

                elif rec.bci_deal_margin < 0:
                    approver_ids = []
                    applicable_margin = min(quote_type.margin_ids, key=lambda m: m.deal_margin if m.deal_margin == 0 else float('inf'))

                    approver_ids, is_approved = handle_approver_type(applicable_margin)
                    if is_approved:
                        continue

                    create_approval_request(approver_ids)

                else:
                    approver_ids = []
                    previous_margin = quote_type.auto_approval

                    sorted_margins = sorted(quote_type.margin_ids, key=lambda m: m.deal_margin, reverse=True)

                    approver_ids = []
                    for margin in sorted_margins:
                        if previous_margin > rec.bci_deal_margin >= float(margin.deal_margin):
                            new_approver_ids, is_approved = handle_approver_type(margin)
                            approver_ids.extend(new_approver_ids)
                            # if is_approved:
                            #     break
                           
                            if margin.approver_type == 'sale_person' and is_approved == True:
                                break
                            elif margin.approver_type == 'sale_person' and is_approved == False:
                                continue
                            previous_margin = margin.deal_margin
                    create_approval_request(approver_ids)
            elif rec.estimation:
                rec.bci_margin_approval = 'approved'
                    
            # Special Approval
            if rec.bci_special_approval != 'approved' and not rec.bypass_quote:
                special_approvers = []
                if rec.bci_bg_pg and quote_type.bg_pbg_approval:
                    special_approvers.append(quote_type.bg_pbg_approval.id)
                    all_approvers.add(quote_type.bg_pbg_approval.id)
                elif rec.bci_bg_pg and not quote_type.bg_pbg_approval:
                    raise ValidationError("BG/PBG approval is not set in the quotation type.")
                if rec.bci_payment_period == 'beyond_45_days' and quote_type.special_approval:
                    special_approvers.append(quote_type.special_approval.id)
                    all_approvers.add(quote_type.special_approval.id)
                elif rec.bci_payment_period == 'beyond_45_days' and not quote_type.special_approval:
                    raise ValidationError("Special approval is not set for payment period in the quotation type.")
                if rec.bci_ld_clause and quote_type.ld_clause_approval:
                    special_approvers.append(quote_type.ld_clause_approval.id)
                    all_approvers.add(quote_type.ld_clause_approval.id)
                elif rec.bci_ld_clause and not quote_type.ld_clause_approval:
                    raise ValidationError("LD clause approval is not set in the quotation type.")
                if special_approvers:
                    approval_requests_exist=True
                    special_category_id = self.env['approval.category'].sudo().search([('bci_is_special_approval', '=', True)])
                    request_model = self.env['approval.request'].sudo()

                    unique_user_ids = list(set(special_approvers))
                    
                    approval_request = request_model.create({
                        'name': f'Special Approval for {rec.name}',
                        'category_id': special_category_id.id or False,
                        'bci_sale_order_id': rec.id or False,
                        'request_owner_id': self.env.user.id,
                        'request_status': 'new',
                        'date_confirmed': fields.Datetime.now(),
                    })

                    approval_request.approver_ids.unlink()
                    for approver_id in unique_user_ids:
                        approval_request.approver_ids = [(0, 0, {'user_id': approver_id, 'required': True})]
                    approval_request.action_confirm()
                else:
                    rec.bci_special_approval = 'approved'          
            rec.approval_approvers_ids = [(6, 0, list(all_approvers))]
            if approval_requests_exist:
                if rec.order_line:
                    all_product_heads = set()
                    for line in rec.order_line:
                        product_heads = line.product_template_id.bci_erp_category.product_head
                        for product_head in product_heads:
                            if product_head:
                                all_product_heads.add(product_head)
                    for product_head in all_product_heads:
                        mail_template = rec.env.ref('barcode_india.bci_approval_template')
                        if mail_template:
                            mail_template.write({'email_to': product_head.partner_id.email})
                            mail_template.send_mail(rec.id, force_send=True)
                            rec.message_post(
                                body="Sent approval request email to %s" % product_head.partner_id.name)
                
            if rec.bci_pt_approval == 'approved' and rec.bci_margin_approval == 'approved' and rec.bci_special_approval == 'approved' and rec.bci_stage == 'pending_approval':
                rec.bci_stage = 'approved'

    def action_freight_and_installation(self):
        for order in self:
            if not order.estimation:
                freight_product_id = {
                    'bci_freight_product': self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'),
                }
                forbidden_freight_product = [freight_product_id['bci_freight_product']]

                installation_product_id = {
                    'bci_installation_product': self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'),
                }
                forbidden_installation_product = [installation_product_id['bci_installation_product']]

                total_price_freight = 0.0
                total_price_installation = 0.0
                freight_amount = 0.0
                installation_amount = 0.0

                freight_applicable = False
                installation_applicable = False

                for line in order.order_line:
                    if str(line.product_template_id.id) in forbidden_freight_product:
                        raise ValidationError(_("Remove Freight product to recalculate"))
                    if str(line.product_template_id.id) in forbidden_installation_product:
                        raise ValidationError(_("Remove Installation product to recalculate"))
                    
                    if line.product_template_id.bci_erp_category.freight_applicable:
                        total_price_freight += line.price_subtotal
                        freight_applicable = True
                    if line.product_template_id.bci_erp_category.installation_applicable:
                        total_price_installation += line.price_subtotal
                        installation_applicable = True

                if order.bci_freight_type:
                    freight_amount = total_price_freight * (order.bci_freight_type.percentage_ofHardware / 100)
                else:
                    raise ValidationError(_("Please Add Freight Type"))

                if order.bci_installation_type:
                    installation_amount = total_price_installation * (order.bci_installation_type.percentage_of_Hardware / 100)
                else:
                    raise ValidationError(_("Please Add Installation Type"))

                order.write({
                    'bci_freight_amount': freight_amount,
                    'bci_installation_amount': installation_amount,
                })
                max_sequence = max(order.order_line.mapped('sequence'), default=0)
                new_lines = []

                if freight_applicable:
                    freight_product_template = self.env['product.template'].sudo().search([('id', '=', freight_product_id['bci_freight_product'])])
                    if freight_product_template:
                        freight_price = max(freight_amount, order.bci_freight_type.minimumcharge)
                        new_lines.append((0, 0, {
                            'product_template_id': freight_product_template.id,
                            'product_id': freight_product_template.product_variant_id.id,
                            'product_uom_qty': 1.0,
                            'price_unit': freight_price,
                            'bci_suggested_price_unit' : freight_price,
                            'bci_approval_stage': 'approved',
                            'sequence': max_sequence + 1,
                        }))
                    else:
                        raise ValidationError(_("Cannot find freight product"))

                if installation_applicable:
                    installation_product_template = self.env['product.template'].sudo().search([('id', '=', installation_product_id['bci_installation_product'])])
                    if installation_product_template:
                        installation_price = max(installation_amount, order.bci_installation_type.minimum_charge)
                        new_lines.append((0, 0, {
                            'product_template_id': installation_product_template.id,
                            'product_id': installation_product_template.product_variant_id.id,
                            'product_uom_qty': 1.0,
                            'price_unit': installation_price,
                            'bci_suggested_price_unit' : installation_price,
                            'bci_approval_stage': 'approved',
                            'sequence': max_sequence + 1,
                        }))
                    else:
                        raise ValidationError(_("Cannot find installation product"))

                if new_lines and order.bci_freight_type and order.bci_installation_type:
                    order.write({
                        'order_line': new_lines
                    })

    @api.onchange('bci_quote_type')
    def _onchange_quote_type(self):       
        for order in self:
            order.estimation = order.bci_quote_type and order.bci_quote_type.estimation or False
            if order.bci_quote_type:
                tnc = self.env['barcode_india.tnc'].search([
                    ('bci_quotation_type', '=', order.bci_quote_type.id)
                ])
                bullet_points = ['<li style="font-size: 20px;"><b>{}</b> : {}</li>'.format(html_escape(t.name), html_escape(t.bci_description)) for t in tnc]
                order.note = '<ol>{}</ol>'.format('<br>'.join(bullet_points))
            else:
                order.note = False

    @api.depends('order_line.bci_approval_stage','bci_pt_approval','bci_margin_approval','bci_quote_type','bci_special_approval')
    def _compute_bci_stage(self):
        for order in self:
            
            if order.state != 'SOPF' and order.order_line and all(line.bci_approval_stage == 'approved' for line in order.order_line) and order.bci_stage != 'pending_approval':
                order.bci_stage = 'pricing_updated'
            if not all(line.bci_approval_stage == 'approved' for line in order.order_line) and not order.estimation:
            #     order.is_send_for_pricing = True
                order.bci_stage = 'draft'
            if order.bci_pt_approval == 'approved' and order.bci_margin_approval == 'approved' and order.bci_special_approval == 'approved' and order.bci_stage == 'pending_approval':
                order.bci_stage = 'approved'
    
    @api.depends('order_line.price_unit','order_line.bci_landed_cost','order_line.product_uom_qty','order_line.bci_discount', 'order_line.special_price', 'order_line.special_price_applicable')
    def _compute_deal_margin(self):
        for order in self:
            freight_product_id = int(self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'))
            installation_product_id = int(self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'))
            landed_price_total = sum(order.order_line.filtered(lambda line: line.product_template_id.id not in [freight_product_id, installation_product_id]).mapped(lambda line: (line.special_price * line.product_uom_qty if line.special_price_applicable or line.special_price > 0 else line.bci_purchase_cost * line.product_uom_qty))) or 0.00
            price_total = sum(order.order_line.filtered(lambda line: line.product_template_id.id not in [freight_product_id, installation_product_id]).mapped(lambda line: (line.price_unit * line.product_uom_qty))) or 0.01
            order.bci_deal_margin = (1 - (landed_price_total / price_total))*100 or 0

    def _action_confirm(self): 
        for order in self:
            if order.bci_helpdesk:
                in_progress_stage = self.env['helpdesk.stage'].sudo().search([('bci_in_progress_stage','=',True)]).filtered(lambda x: order.bci_helpdesk.team_id.id in x.team_ids.ids)
                if in_progress_stage:
                    order.bci_helpdesk.stage_id = in_progress_stage.id
                    order.bci_helpdesk.bci_approval_for = 'Complete Process'
                    order.bci_helpdesk.bci_is_approved = True
            if order.partner_id.customer_rank == 0:
                order.partner_id.customer_rank = 1
            partner_id = order.partner_id and order.partner_id.parent_id or order.partner_id
            if not partner_id.bci_group_code and not partner_id.bci_tax_group and not partner_id.bci_terms_code:
                raise UserError("Please check  - Group Code / Tax Group / Terms Code mapped on the Customer (%s)"%(partner_id.name))
            if not partner_id.bci_vertical or not partner_id.bci_sub_vertical or not partner_id.bci_sub_vertical_category: 
                raise UserError(f"Vertical / Sub Vertical / Sub Vertical Category is mandatory for customer {partner_id.name}")
            if partner_id.bci_contact_type != 'Company':
                raise UserError(f"Contact Type must be 'Company' for customer {partner_id.name}")
            if not partner_id.country_id:
                raise UserError(f"Country is mandatory for customer {partner_id.name}")
            validation_errors = []
            for line in order.order_line:
                product = line.product_id
                if not product.categ_id and line.display_type == False:
                    validation_errors.append(f"Product Category is missing for {product.name}")
                if not product.bci_account_set_code and line.display_type == False:
                    validation_errors.append(f"Account Set Code is missing for {product.name}")
                if not product.bci_code and line.display_type == False:
                    validation_errors.append(f"BCI Code is missing for {product.name}")
            if validation_errors:
                error_message = "Order Validation Errors:\n" + "\n".join(f"- {error}" for error in validation_errors)
                raise UserError(error_message)
            
            if not partner_id.bci_code:
                partner_id.bci_code = self.env['ir.sequence'].next_by_code('barcode_india.company_code')
                partner_id.bci_contact_type = 'Company'
                partner_id.customer_rank += 1
        return super(SaleOrder, self)._action_confirm()
    
    def _compute_cost_sheet_count(self):
        self.ensure_one()
        self.bci_cost_sheet_count = self.env['sale.order.line'].sudo().search_count([('order_id','=',self.id)])
        
    def _compute_user_role(self):
        self.ensure_one()
        user = self.env.user or False
        if user:
            if user.has_group('barcode_india.group_barcode_india_management'):
                self.bci_user_role = 'management'
            elif user.has_group('barcode_india.group_barcode_india_cat_head'):
                self.bci_user_role = 'category_head'
            elif user.has_group('barcode_india.group_barcode_india_sale_person'):
                self.bci_user_role = 'sale_person'
            elif user.has_group('barcode_india.group_barcode_india_pre_sales'):
                self.bci_user_role = 'pre_sales'
            elif user.has_group('barcode_india.group_barcode_india_guest'):
                self.bci_user_role = 'guest'
            else:
                self.bci_user_role = False

    def action_use_reference_costsheet(self):
        return {
            'name': 'Select Reference Costsheet',
            'type': 'ir.actions.act_window',
            'res_model': 'bci.reference_costsheet',
            'view_mode': 'form',
            'view_id': self.env.ref('barcode_india.view_bci_reference_costsheet_wizard_form').id,
            'target': 'new', 
            'context': {
                'default_current_sale_order_id': self.id,
                'default_user_id': self.user_id.id,
            },
        }

    def action_confirm_reference_costsheet(self):
        return {
            'name': _('Set Reference Costsheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'reference.costsheet.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id,
                        'default_validity_days': 15,},
        }

    def action_unset_reference_costsheet(self):
        return {
            'name': _('Unset Reference Costsheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'unset.reference.costsheet.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }
                
        
    def action_view_cost_sheet(self):
        self.ensure_one()
        view_record = self.env['barcode_india.view_master'].sudo().search([('bci_role','=',self.bci_user_role),('bci_stage','=',self.bci_stage)],limit=1) or False
        if view_record and view_record.bci_view.id:
            tree_view_id = view_record.bci_view.id
        else:
            tree_view_id = self.env.ref('barcode_india.barcode_india_order_line_tree_view_second').id
        
        return {
            'name': _('Cost Sheet'),
            'res_model': 'sale.order.line',
            'view_mode': 'list',
            'view_id':tree_view_id,
            'context': {'default_order_id': self.id, 'search_default_bci_pricing_category':1},
            'domain': [('order_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window'
        }
        
    def action_view_sopf_order(self):
        return {
            'name': _('SOPF'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'context': {'default_sopf_order': self.id},
            'domain': [('sopf_order', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window'
        }

    @api.depends('order_line')
    def _compute_sopf_count(self):
        for record in self:
            record.bci_sopf_count = self.env['sale.order'].search_count([('sopf_order', '=', record.id)])

    def action_view_approval(self):
        return {
            'name': _('Approval'),
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'context': {'default_bci_sale_order_id': self.id},
            'domain': [('bci_sale_order_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window'
        }


    @api.onchange('partner_id', 'bci_quote_type')
    def _onchange_payment_terms(self):
        for order in self:
            order.bci_payment_terms = [(5, 0, 0)] + self._get_default_payment_terms()

    def _get_default_payment_terms(self):
        self.ensure_one()
        lines = []
        if not self.is_new_version:
            found_matching_terms = False
            if self.bci_quote_type and self.partner_id.bci_pricing_terms:
                partner_payment_terms = self.partner_id.bci_pricing_terms.filtered(lambda x: x.bci_quote_type.id == self.bci_quote_type.id)
                if partner_payment_terms:
                    found_matching_terms = True
                    for pt_line in partner_payment_terms.bci_pt_line_ids:
                        terms_vals = {
                            'name': pt_line.name,
                            'order_id': self.id,
                            'percentange': pt_line.bci_percentage,
                        }
                        lines.append((0, 0, terms_vals))
            if not found_matching_terms and self.bci_quote_type and self.bci_quote_type.payment_terms_ids:
                for pt_line in self.bci_quote_type.payment_terms_ids:
                    terms_vals = {
                        'name': pt_line.name,
                        'order_id': self.id,
                        'percentange': pt_line.bci_percentage,
                    }
                    lines.append((0, 0, terms_vals))
        return lines
    
    def action_create_new_quotation(self):
        new_orders = self.env['sale.order']
        new_approvals = self.env['approval.request']
        
        for order in self:
            version_part = order.name.split('-')[-1]
            numeric_version = int(version_part) if version_part.isdigit() else 0
            new_version = numeric_version + 1
            new_name = f"{order.name.rsplit('-', 1)[0]}-{new_version:02d}"
            bci_pt_approval = order.bci_pt_approval
            new_order = order.with_context(bypass_freight_installation_check=True).copy(default={
                'bci_version': new_version,
                'name': new_name,
                'is_new_version': True,
                'bci_stage' : 'draft',
                'bci_pt_approval': bci_pt_approval,
            })
            new_orders |= new_order

            approvals = self.env['approval.request'].search([('bci_sale_order_id', '=', order.id)])
            for approval in approvals:
                new_approval = approval.copy(default={'bci_sale_order_id': new_order.id})
                new_approval.write({
                    'request_status': 'cancel'
                })
                new_approvals |= new_approval
                approval.action_cancel()

        self._action_cancel()
        return {
            'name': _('New Quotation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'res_model': 'sale.order',
            'target': 'current',
            'res_id': new_orders.ids[0],
            'context': {'default_bci_stage': 'Draft'}
        }
    
    def view_bci_sales_repricing_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send For Repricing'),
            'res_model': 'bci.sales_repricing',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
            
    def view_bci_create_sopf_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create SOPF'),
            'res_model': 'bci.create_sopf',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_customer_id': self.partner_id.id,
                'default_invoice_address_id':self.partner_invoice_id.id,
                'default_delivery_address_id':self.partner_shipping_id.id,
                'default_purchase_contact': self.partner_invoice_id.id,
                'default_finance_contact': self.partner_invoice_id.id,
                'default_store_contact': self.partner_shipping_id.id,

            }
        }

    def _set_validity_expired(self,limit=False):
        orders = self.search([('bci_validity_expired','=',False),('state', 'in', ['draft','sent']),('validity_date', '<=', fields.Date.today())],limit=limit)
        if orders:
            for order in orders:
                order.bci_validity_expired = True
                message = _("Expiring validity for this order as Expiration date passed.")
                order.message_post(body=message)
                
    def _check_exchange_diff(self, limit=False):
        exchange_threshold = float(self.env['ir.config_parameter'].sudo().get_param('bci.exchange_threshold'))
        currencies = self.env['res.currency'].search([('active', '=', True)])
        for currency in currencies:
            base_currency_rate = currency.inverse_rate
            exchange_diff_minus_percentage = (base_currency_rate - base_currency_rate * exchange_threshold / 100) if base_currency_rate != 0 else 0
            exchange_diff_plus_percentage = (base_currency_rate + base_currency_rate * exchange_threshold/ 100) if base_currency_rate != 0 else 0
            orders = self.search([('bci_exchange_expired', '=', False), ('state', 'in', ['draft', 'sent']),('order_line.bci_purchase_currency','=',currency.id),'|', ('order_line.bci_exchange_rate', '<', exchange_diff_minus_percentage),('order_line.bci_exchange_rate', '>', exchange_diff_plus_percentage)], limit=limit)
            if orders:
                orders.write({'bci_exchange_expired': True})
                for order in orders:
                    message = _("Expiring validity for this order because the difference between the exchange rate at the time of order and the current exchange rate exceeds the set threshold .")
                    order.message_post(body=message)
                
    def _check_cost_diff(self, limit=False):
        cost_threshold = float(self.env['ir.config_parameter'].sudo().get_param('bci.cost_threshold'))
        orders = self.env['sale.order'].search([('bci_cost_expired', '=', False), ('state', 'in', ['draft', 'sent']), ('order_line.product_id.bci_purchase_cost_change', '=', True),('order_line.product_id.bci_purchase_currency','!=',self.env.company.currency_id.id)], limit=limit)
        if orders:
            order_lines = orders.mapped('order_line').filtered(lambda line: line.bci_purchase_cost != 0.0)
            if order_lines:
                saller_prices = order_lines.mapped(lambda line: line.product_id.seller_ids.mapped('price')[0])
                cost_diff_minus = saller_prices - order_lines.mapped('bci_principal_cost')
                cost_diff_plus = saller_prices + order_lines.mapped('bci_principal_cost')
                cost_diff_minus_percentage = (cost_diff_minus / cost_threshold) * 100 if cost_threshold != 0 else 0
                cost_diff_plus_percentage = (cost_diff_plus / cost_threshold) * 100 if cost_threshold != 0 else 0
                if all(abs(cost_diff_minus_percentage) < cost_threshold or abs(cost_diff_plus_percentage) > cost_threshold):
                    # raise Exception(orders)
                    orders.write({'bci_cost_expired': True})
                    for order in orders:
                        message = _("Expiring validity for these orders because the difference between the purchase cost at the time of order and the current purchase cost exceeds the set threshold .")
                        order.message_post(body=message)

    def action_send_for_pricing(self):
        for record in self:
            if record.order_line:
                sent_approvers = set()
                for line in record.order_line:
                    if line.bci_approval_stage == 'pending' and line.bci_approver:
                        approver_email = line.bci_approver.partner_id.email
                        if approver_email and approver_email not in sent_approvers:
                            mail_template = record.env.ref('barcode_india.bci_pricing_category_template')
                            if mail_template:
                                mail_template.write({'email_to': approver_email})
                                mail_template.send_mail(self.id, force_send=False)
                                record.message_post(body=f"Sent pricing request email to {approver_email}")
                                sent_approvers.add(approver_email)
                if sent_approvers:
                    record.bci_stage = 'pricing_request'
            else:
                raise UserError("Please Add Order Lines")

    # def get_term_and_condition(self):
    #     for rec in self:
    #         tnc_ids = self.env['barcode_india.tnc'].sudo().search([('bci_quotation_type','=',rec.bci_quote_type.id)]) or False
    #         return tnc_ids

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
        super(SaleOrder, self)._compute_amounts()
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.bci_is_optional)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + order.amount_tax

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'currency_id')
    def _compute_tax_totals(self):
        super(SaleOrder, self)._compute_tax_totals()
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.bci_is_optional)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )
            
    @api.constrains('bci_payment_terms')
    def _constrain_payment_terms(self):
        for record in self:
            if record.bci_payment_terms:
                if sum(record.bci_payment_terms.mapped('percentange')) != 100:
                    raise ValidationError(_("Sum of Milestone line's percentage must be equal to 100"))

    def _reprice_orderline(self):
        for line in  self.order_line:
            line.sudo().product_template_id._compute_product_cost()
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
            line.bci_discount = line.product_id.bci_discount
            line.bci_target_margin = line.product_id.bci_erp_category and line.product_id.bci_erp_category.margin_default
            line.bci_suggested_price_unit = line.bci_landed_cost #* (100 - line.bci_discount) / (100 - line.bci_target_margin)
    
    @api.depends('order_line.sopf_done_quantity', 'order_line.sopf_done_amount')
    def _compute_is_sopf_button_visible(self):
        
        bci_freight_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.freight_product'))
        bci_installation_product = int(self.env['ir.config_parameter'].sudo().get_param('bci.installation_product'))

        for order in self:
            order.is_sopf_button_visible = any(
                (line.price_unit != line.sopf_done_amount) if (
                    line.product_id.product_tmpl_id.id == bci_freight_product or
                    line.product_id.product_tmpl_id.id == bci_installation_product
                ) else (line.product_uom_qty != line.sopf_done_quantity)
                for line in order.order_line
            )
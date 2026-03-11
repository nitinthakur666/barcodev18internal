from odoo import models, fields, api,_
from odoo.exceptions import UserError,ValidationError

class CaseType(models.Model):
    _name = 'barcode_india.case_type'
    _description = 'Case Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
    type = fields.Selection([('hardware','Hardware'),
                            ('custom software','Custom Software'),
                            ('sales','Sales')],string="Type")

class CaseSubType(models.Model):
    _name = 'barcode_india.case_sub_type'
    _description = 'Case Sub Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
    bci_case_type = fields.Many2one('barcode_india.case_type', 'Case Type')

class ProblemType(models.Model):
    _name = 'barcode_india.problem_type'
    _description = 'Problem Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)

class ProblemSubType(models.Model):
    _name = 'barcode_india.problem_sub_type'
    _description = 'Problem Sub Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
    bci_problem_type = fields.Many2one('barcode_india.problem_type', 'Problem Type')

class Chargeable(models.Model):
    _name = 'barcode_india.chargeable'
    _description = 'Chargeable'

    active = fields.Boolean('Active', default=True)
    name = fields.Many2one('barcode_india.case_type', 'Case Type')
    bci_case_sub_type = fields.Many2one('barcode_india.case_sub_type', 'Case Sub Type')
    bci_problem_type = fields.Many2one('barcode_india.problem_type', 'Problem Type')
    bci_problem_sub_type_id = fields.Many2one('helpdesk.ticket.type', 'Problem Sub Type') #Need to check
    bci_warranty_status = fields.Selection([('In Warranty','In Warranty'),('In Grace','In Grace'),('Out of Warranty','Out of Warranty')],'Warranty Status')
    bci_chargeable = fields.Boolean('Chargeable')
    
class HelpdeskTicketTimespent(models.Model):
    _name = 'helpdesk.stage_timespent'
    _description = 'Helpdesk Ticket Stage Timespent'
    _order = 'id desc'
    
    active = fields.Boolean('Active', default=True)
    bci_ticket_id = fields.Many2one('helpdesk.ticket',string='Ticket',ondelete='cascade') 
    bci_stage = fields.Many2one('helpdesk.stage',string='Stage')
    bci_to_date = fields.Datetime('To')
    create_date = fields.Datetime('From')
    hold_remarks = fields.Text('Remarks')

class OperationTypes(models.Model):
    _name = 'barcode_india.operation_type'
    _description = 'Operation Type'
    _order ="sequence,id"

    sequence = fields.Integer(string="Sequence", default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Many2one('stock.picking.type',string="Operation Type")
    bci_rma = fields.Many2one('barcode_india.rma_masters',string="RMA")

class RMAMasters(models.Model):
    _name = 'barcode_india.rma_masters'
    _description = 'RMA Masters'
    _order = 'sequence, id'
    _rec_name = 'bci_rma'

    active = fields.Boolean('Active', default=True)
    bci_rma = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", default=1)
    bci_receive_at_bci = fields.Boolean(string="Receive at BCI Location")
    bci_receive_at_engineer = fields.Boolean(string="Receive at Engineer Location")
    bci_receive_at_defective = fields.Boolean(string="Receive at Defective Location")
    bci_oem_involved = fields.Boolean(string="OEM Involved")
    bci_spare_transfer = fields.Boolean(string="Spares Transfer")
    bci_operation_types = fields.One2many('barcode_india.operation_type','bci_rma',string="Operation Types")

class Sparedata(models.Model):
    _name = 'barcode_india.spare'
    _description = 'Spares'

    active = fields.Boolean('Active', default=True)
    name = fields.Many2one('product.product',string="Spare")
    spare_tmpl_id = fields.Many2one(related="name.product_tmpl_id",store=True,string="Spare Template")
    product_id = fields.Many2one('product.product',string="Product",domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    product_tmpl_id = fields.Many2one('product.template',string="Product Template")


class LeadType(models.Model):
    _name = 'lead.type'
    _description = 'Lead Type'

    name = fields.Char('Lead Type')
    active = fields.Boolean("Active", default=True)


class Region(models.Model):
    _name = 'barcode_india.region'
    _description = 'Region'

    name = fields.Char('Region')
    region_head = fields.Many2one('res.users', string='Region Head')
    active = fields.Boolean("Active", default=True)
    regional_technical_head = fields.Many2one('res.users', string='Regional Technical Head')


class Vertical(models.Model):
    _name = 'barcode_india.vertical'
    _description = 'Vertical'

    name = fields.Char('Vertical', required="1")
    code = fields.Char(string="Code", required="1")
    vertical_head = fields.Many2one('res.users',string="Vertical Head")
    active = fields.Boolean("Active", default=True)


class ApplicationType(models.Model):
    _name = 'application.type'
    _description = 'Application Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Application Type')


class Probability(models.Model):
    _name = 'barcode_india.probability'
    _description = 'Probability'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Probability')


class Activities(models.Model):
    _name = 'barcode_india.activities'
    _description = 'Activities'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Activity Name')


class Stages(models.Model):
    _name = 'barcode_india.stages'
    _description = 'Stages'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Stage Name')


class Sites(models.Model):
    _name = 'barcode_india.site'
    _description = 'Sites'

    active = fields.Boolean('Active', default=True)
    name = fields.Many2one('res.partner','Site')
    bci_customer = fields.Many2one('res.partner','Customer')
    bci_contract_id = fields.Many2one('barcode_india.contracts',string='Contract',ondelete="cascade")

class FinalResolution(models.Model):
    _name = 'barcode_india.final_resolution'
    _description = 'Final Resolution'
    _order = 'id desc'

    active = fields.Boolean('Active', default=True)
    name = fields.Html(string='Resolution',required=True)
    bci_task_id = fields.Many2one('project.task',string='Task',ondelete='cascade')
    bci_ticket_id = fields.Many2one('helpdesk.ticket',string='Ticket',related='bci_task_id.helpdesk_ticket_id',store=True,ondelete='cascade')

class TermsConditions(models.Model):
    _name = 'barcode_india.tnc'
    _description = 'Terms & Conditions'
    _order = 'sequence, id'

    sequence = fields.Integer("Sequence", default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    bci_quotation_type = fields.Many2many('barcode_india.quotation_type', string='Quotation Type')
    bci_description = fields.Text(string="Description")

class PTMaster(models.Model):
    _name = 'barcode_india.pt_master'
    _inherit = 'barcode_india.track_mixin'
    _description = 'Payment Terms'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Milestone')
    sequence = fields.Integer("Sequence", default=1)
    # bci_amount = fields.Float(string="Amount(INR)")
    bci_percentage = fields.Float(string="Percentage")
    bci_pricingcategory_id = fields.Many2one('barcode_india.pricing_category', string='Pricing Category')
    partner_id = fields.Many2one('res.partner',string='Partner ID')
    quote_type_id = fields.Many2one('barcode_india.quotation_type',string='Quote Type')
    # bci_amount_type = fields.Boolean(string="Is a Percentage?")

    @api.model
    def create(self, vals):
        res = super(PTMaster, self).create(vals)
        res.track_changes(res.quote_type_id, vals)
        return res
    
    def write(self, vals):
        for record in self:
            record.track_changes(record.quote_type_id, vals)
        res = super(PTMaster, self).write(vals)
        return res

class CostsheetViewMaster(models.Model):
    _name = 'barcode_india.view_master'
    _description = 'Readonly Master'

    active = fields.Boolean('Active', default=True)
    bci_stage = fields.Selection([('draft','Draft'),('pricing_request','Pricing Request'),('approved','Approved'),('rejected','Rejected')],string='Stage')
    bci_role = fields.Selection([('guest','Guest'),('pre_sales','Pre Sales'),('sale_person','Sale Person'),('category_head','Category Head'),('management','Management')], string='Role')
    bci_view = fields.Many2one('ir.ui.view',string='View')

class PricingFactor(models.Model):
    _name = 'barcode_india.pricing_factor'
    _description = 'Pricing Factor Master'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    bci_duty = fields.Float(string='Duty(%)')
    bci_freight = fields.Float(string='Freight(%)')
    bci_ins = fields.Float(string='Ins(%)')
    bci_clearing_nd_handling = fields.Float(string='Clearing and Handling Cost')
    bci_forex = fields.Float(string='Forex')


class DiscountCategory(models.Model):
    _name = 'barcode_india.discount_category'
    _description = 'Discount Category Master'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    bci_discount = fields.Float(string='Discount(%)')
    is_promocode = fields.Boolean(string='Is Promo Price?')

class CustomerPTLine(models.Model):
    _name = 'barcode_india.customer_pt_line'
    _description = 'Customer Payment Terms Lines'
    _order = 'sequence,id'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Milestone')
    sequence = fields.Integer("Sequence", default=1)
    bci_percentage = fields.Float(string="Percentage")
    bci_customer_pt_master_id = fields.Many2one('barcode_india.customer_pt_master', string='Customer PT Master ID')

class CustomerPTMaster(models.Model):
    _name = 'barcode_india.customer_pt_master'
    _description = 'Customer Payment Terms'
    _order = 'sequence,id'
    
    sequence = fields.Integer("Sequence", default=1)
    active = fields.Boolean('Active', default=True)
    bci_quote_type = fields.Many2one('barcode_india.quotation_type', string='Quote Type')
    partner_id = fields.Many2one('res.partner',string='Partner ID')
    bci_pt_line_ids = fields.One2many('barcode_india.customer_pt_line','bci_customer_pt_master_id',string='Payment Terms')
    
    @api.onchange('bci_quote_type')
    def _compute_bci_pt_line_ids(self):
        for rec in self:
            lines = [(5, 0, 0)]
            if rec.bci_quote_type.payment_terms_ids:
                for line in rec.bci_quote_type.payment_terms_ids:
                    terms_vals = {
                        'name': line.name,
                        'sequence': line.sequence,
                        'bci_percentage': line.bci_percentage,
                        'bci_customer_pt_master_id': rec.id,
                    }
                    lines.append((0, 0, terms_vals))
                rec.bci_pt_line_ids = lines

class QuotationType(models.Model):
    _name = 'barcode_india.quotation_type'
    _description = 'Quotation Type Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence,id'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', tracking=1)
    sequence = fields.Integer("Sequence", default=1, tracking=1)
    estimation = fields.Boolean(string='Estimation', tracking=1)
    auto_approval = fields.Float("Auto Approval Margin(%)", tracking=1)
    pt_margin_ids = fields.One2many('barcode_india.pt_matrix', 'quotations_type_id', string='PaymentTerms Matrix')
    margin_ids = fields.One2many('barcode_india.margin_matrix', 'quotation_type_id', string='Approval Matrix')
    payment_terms_ids = fields.One2many('barcode_india.pt_master', 'quote_type_id', string='Payment Terms IDs')
    erp_category = fields.Many2many('barcode_india.erp_acc_category',string='ERP Category',tracking=1)
    bci_bypass_quote = fields.Boolean(string='Pricing & Approvals not Required', tracking=1)
    special_approval = fields.Many2one('res.users',string='Non Standard PT Approver', tracking=1)
    bg_pbg_approval = fields.Many2one('res.users',string='BG/PBG Approver', tracking=1)
    ld_clause_approval = fields.Many2one('res.users',string='LD Clause Approver', tracking=1)
    apply_quotetype_limit = fields.Boolean(string='Apply QuoteType Limit', tracking=1)
    quote_limit = fields.Float(string='Quote Limit', tracking=1)
    quotetype_after_limit = fields.Many2one('barcode_india.quotation_type', string='QuoteType After Limit', domain="[('id', '!=', id), ('id', '!=', False)]")
    
    @api.constrains('payment_terms_ids')
    def _constrain_payment_terms(self):
        for record in self:
            if record.payment_terms_ids:
                if sum(record.payment_terms_ids.mapped('bci_percentage')) != 100:
                    raise ValidationError(_("Sum of Milestone line's percentage must be equal to 100"))

    @api.model_create_multi
    def create(self, vals_list):
        res = super(QuotationType, self).create(vals_list)

        for res, vals in zip(res, vals_list):
            res.track_changes(vals)

        return res
    
    def write(self, vals):
        self.track_changes(vals)                
        res = super(QuotationType, self).write(vals)
        return res

    def get_many2many_value(self, record, value, field):
        ids = []

        if isinstance(value, list):
            for command in value:
                if not isinstance(command, (list, tuple)):
                    continue

                if command[0] == 6:  # replace
                    ids = command[2]
                elif command[0] == 4:  # add
                    ids.append(command[1])
                elif command[0] == 3:  # remove
                    if command[1] in ids:
                        ids.remove(command[1])

                elif command[0] == 0:
                    rec = self.env[record._fields[field].comodel_name].create(command[2])
                    ids.append(rec.id)

        result = self.env[record._fields[field].comodel_name].browse(ids)
        return result.mapped('name') if result else []

    def track_changes(self, values):
        msg = "<ul>"
        for key in values:
            if key in ['erp_category']:
                string=self._fields[key].string
                old_value = self[key] or ''
                new_value = values[key] or ''
                if self._fields[key].type == 'many2many':
                    old_value = ", ".join(self[key].mapped('name')) if self[key] else ''
                    new_value = self.get_many2many_value(self, new_value, key)
                msg += "<li>" + _(
                    "%(string)s: %(old_value)s -> %(new_value)s",
                    string=string,
                    old_value=old_value,
                    new_value=new_value
                ) + "</li>"
        msg += "</ul>"
        self.message_post(body=msg)                

class MarginMatrix(models.Model):
    _name = 'barcode_india.margin_matrix'
    _inherit = 'barcode_india.track_mixin'
    _description = 'Margin Matrix'

    active = fields.Boolean('Active', default=True)
    deal_margin = fields.Integer('Deal Margin(%)')
    sequence = fields.Integer('Sequence', default=1)
    auto_approval = fields.Float("Auto Approval(%)")
    approver_type = fields.Selection([('vertical_head','Vertical Head'),('region_head','Region Head'),('sale_person','Sale Person'),('user','Specific Users')],string='Approver Type')
    # users = fields.Many2many('res.users','quot_users',string='Users')
    approver = fields.Many2many('res.users',string='Approvers')
    quotation_type_id =fields.Many2one('barcode_india.quotation_type',string="Quotation Type")

    @api.model
    def create(self, vals):
        res = super(MarginMatrix, self).create(vals)
        res.track_changes(res.quotation_type_id, vals)
        return res
    
    def write(self, vals):
        for record in self:
            record.track_changes(record.quotation_type_id, vals)
        res = super(MarginMatrix, self).write(vals)
        return res

class Approval(models.Model):
    _name = 'barcode_india.approval'
    _description = 'Approval'

    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Asset')
    approval_type = fields.Selection([('role','Role'),('user','User')],string='Approval Type')
    approval_role = fields.Many2one('res.groups',string='Role',domain=lambda self: [('privilege_id.category_id', '=', self.env.ref('barcode_india.category_barcode_india').id)])
    approval_user = fields.Many2one('res.users',string='User')
    pt_matrix = fields.Many2one('barcode_india.pt_matrix', string='PaymentTerms Matrix')

class PTApprovalMatrix(models.Model):
    _name = 'barcode_india.pt_matrix'
    _description = 'Payment Term Approval Matrix'
    _inherit = 'barcode_india.track_mixin'

    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean('Active', default=True)
    customer_type = fields.Selection([('existing','Existing Customers'),('new','New Customers'),('all','All')],string='Customer Type')
    customer_category = fields.Selection([('a','A'),('b','B'),('c','C'),('all','All')],string='Customer Category')
    value = fields.Float('Deal Value Upto')
    approving_authority = fields.Selection([('vertical_head','Vertical Head'),('region_head','Region Head'),('sale_person','Sale Person'),('user','Specific Users')],string='Approving Authority')
    # approving_authority_users = fields.Many2many('res.users',string='User')
    approvers = fields.Many2many('res.users','pt_matrix_approvers',string='Approvers')
    recommending_authority = fields.Selection([('vertical_head','Vertical Head'),('region_head','Region Head'),('sale_person','Sale Person'),('user','Specific Users')],string='Recommending Authority Type')
    # recommending_users = fields.Many2many('res.users','pt_matrix_user',string='User')
    recommending_approvers = fields.Many2many('res.users','pt_matrix_approver',string='Approvers',)
    quotations_type_id =fields.Many2one('barcode_india.quotation_type',string="Quotation Type")

    @api.model
    def create(self, vals):
        res = super(PTApprovalMatrix, self).create(vals)
        res.track_changes(res.quotations_type_id, vals)
        return res
    
    def write(self, vals):
        for record in self:
            record.track_changes(record.quotations_type_id, vals)
        res = super(PTApprovalMatrix, self).write(vals)
        return res

class PMStatus(models.Model):
    _name = 'barcode_india.pm_status'
    _description = 'PM Status'

    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Many2one('barcode_india.assets', string='Asset')
    product_id = fields.Many2one(related='name.bci_product', string='Product', store=True)
    status = fields.Selection([('Pending','Pending'),('PM Complete - No Issues','PM Complete - No Issues'),('PM Complete - Issue Found','PM Complete - Issue Found')], string='Status', default='Pending')
    comments = fields.Text(string='Comments')
    task_id = fields.Many2one('project.task', string='Task')
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket')

    def action_create_ticket(self):
        self.ensure_one()
        team_id = self.env['helpdesk.team'].search([('bci_type','=','Hardware')], limit=1)
        case_type_id = self.env['barcode_india.case_type'].search([('type','=','hardware')], limit=1)
        if not team_id or not case_type_id:
            raise UserError(_('Hardware Team or Case Type not found !'))
        ticket = self.env['helpdesk.ticket'].sudo().create({'name': self.name.name,
                                                            'team_id': team_id.id,
                                                            'bci_case_type': case_type_id.id,
                                                            'bci_asset': self.name.id,
                                                            'description': self.comments})
        self.ticket_id = ticket.id

class SalePersonLimit(models.Model):
    _name = 'barcode_india.sale_person_limit'
    _description = 'Sale Person Limit'
    
    active = fields.Boolean('Active', default=True)
    user = fields.Many2many('res.users',string="User")
    quot_type = fields.Many2one('barcode_india.quotation_type',string="Quot Type")
    deal_value = fields.Float(string="Margin Approval limit")
    payment_deal_value = fields.Float(string="Payment Terms Approval limit")

class SuperCategory(models.Model):
    _name = 'barcode_india.super_category'
    _description = 'Super Category'

    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name')
    line_of_business_ids = fields.One2many('barcode_india.line_of_business', 'super_category_id',string='Line Of Business')

class LineOfBusiness(models.Model):
    _name = 'barcode_india.line_of_business'
    _description = 'Line Of Business'

    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name')
    super_category_id = fields.Many2one('barcode_india.super_category',string="Super Category")
    erp_ids = fields.One2many('barcode_india.erp_acc_category', 'lineof_business_id',string='ERP Category')

class ErpAccountCategory(models.Model):
    _name = 'barcode_india.erp_acc_category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ERP Category'

    sequence = fields.Integer('Sequence', default=1, tracking=1)
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='ERP Category', tracking=1)
    lineof_business_id = fields.Many2one('barcode_india.line_of_business',string='line of business', tracking=1)
    freight_applicable = fields.Boolean('Freight Applicable', default=False, tracking=1)
    installation_applicable = fields.Boolean('Installation Applicable', default=False, tracking=1)
    margin_default = fields.Float('Default Margin', tracking=1)
    product_head = fields.Many2many('res.users',string='Product Head')

class AccountSetCode(models.Model):
    _name = 'barcode_india.account_set_code'
    _description = 'Account Set Code'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class LOB(models.Model):
    _name = 'barcode_india.lob'
    _description = 'LOB'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")

class LeadStatus(models.Model):
    _name = 'barcode_india.lead_status'
    _description = 'Status'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    is_mql = fields.Boolean("Is MQL?")
    is_sql = fields.Boolean("Is SQL?")
    is_reject = fields.Boolean("Rejected?")

    @api.constrains('is_mql',)
    def _check_is_mql(self):
        for rec in self:
            if rec.is_mql:
                already_record = self.search([('is_mql','=',True),('id','!=',rec.id)])
                if already_record:
                    raise ValidationError(_("You can define only one MQL Stage!"))

    @api.constrains('is_sql',)
    def _check_is_sql(self):
        for rec in self:
            if rec.is_sql:
                already_record = self.search([('is_sql','=',True),('id','!=',rec.id)])
                if already_record:
                    raise ValidationError(_("You can define only one SQL Stage!"))

    @api.constrains('is_reject',)
    def _check_is_reject(self):
        for rec in self:
            if rec.is_reject:
                already_record = self.search([('is_reject','=',True),('id','!=',rec.id)])
                if already_record:
                    raise ValidationError(_("You can define only one Reject Stage!"))

class GroupCode(models.Model):
    _name = 'barcode_india.group_code'
    _description = 'Group Code'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Description", required="1")
    code = fields.Char(string="Code", required="1")
    type = fields.Selection([('Customer','Customer'),('Vendor','Vendor')],string="Type", required="1")

class TaxGroups(models.Model):
    _name = 'barcode_india.tax_group'
    _description = 'Tax Group'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")
    type = fields.Selection([('Customer','Customer'),('Vendor','Vendor')],string="Type", required="1")

class TermsCode(models.Model):
    _name = 'barcode_india.terms_code'
    _description = 'Terms Code'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Description", required="1")
    code = fields.Char(string="Code", required="1")
    type = fields.Selection([('Customer','Customer'),('Vendor','Vendor')],string="Type", required="1")

class SubVertical(models.Model):
    _name = 'barcode_india.sub_vertical'
    _description = 'Sub Vertical'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")
    vertical_id = fields.Many2one("barcode_india.vertical","Vertical", required="1")

class SubVerticalCategory(models.Model):
    _name = 'barcode_india.sub_vertical_category'
    _description = 'Sub Vertical Category'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")
    sub_vertical_id = fields.Many2one("barcode_india.sub_vertical","Sub Vertical", required="1")

class LocationInventory(models.Model):
    _name = 'barcode_india.location_inventory'
    _description = 'Location Wise Inventory'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Item Description", required="1")
    item_no = fields.Char(string="Item No.", required="1")
    location = fields.Char(string="Location")
    category = fields.Char(string="Category")
    quantity_on_hand = fields.Float(string="Quantity On Hand")
    quantity_on_po_order = fields.Float(string="Quantity On Purchase Order")
    quantity_on_so = fields.Float(string="Quantity On Sale Order")

class RejectReason(models.Model):
    _name = 'barcode_india.reject_reason'
    _description = 'Reject Reason'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")


class Status(models.Model):
    _name = 'barcode_india.status'
    _description = 'Status'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Stage Name')
    probability = fields.Integer("Probability")

class OwnCompany(models.Model):
    _name = 'barcode_india.own_company'
    _description = 'Own Company'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class OEM(models.Model):
    _name = 'barcode_india.oem_product_group'
    _description = 'OEM & Product Group'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class Warranty(models.Model):
    _name = 'barcode_india.warranty_amc'
    _description = 'Warranty/AMC/Carepack Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class Coverage(models.Model):
    _name = 'barcode_india.coverage'
    _description = 'Coverage'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    no_of_days = fields.Integer("No. of Days")
    code = fields.Char(string="Code", required="1")

class ServiceCategory(models.Model):
    _name = 'barcode_india.service_category'
    _description = 'Service Category'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class CoverageType(models.Model):
    _name = 'barcode_india.coverage_type'
    _description = 'Coverage Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class OnsiteCoverage(models.Model):
    _name = 'barcode_india.onsite_coverage'
    _description = 'Onsite Coverage'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")

class StandbyEquipment(models.Model):
    _name = 'barcode_india.standby_equipment'
    _description = 'Engineer & Standby Equipment'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", required="1")
    code = fields.Char(string="Code", required="1")


class InstallationTypes(models.Model):
    _name = 'barcode_india.installation_types'
    _description = 'Installation Types'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Type')
    minimum_charge = fields.Float("Minimum Charge")
    percentage_of_Hardware = fields.Float("Percentage of Hardware(%)")


class FreightTypes(models.Model):
    _name = 'barcode_india.freight_types'
    _description = 'Freight Types'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Type')
    minimumcharge = fields.Float("Minimum Charge")
    percentage_ofHardware = fields.Float("Percentage of Hardware(%)")


class BanCRMt(models.Model):
    _name = 'barcode_india.bant_crm'
    _description = 'BANT CRM'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    weightage = fields.Float('Weightage(%)')
    requirement_score = fields.Integer(string='Requirement Score')
    weightage_value = fields.Integer(string='Weightage Value', compute='_compute_weightage_value',store=True)
    bci_lead_id = fields.Many2one('crm.lead', 'Lead')
    

    @api.depends('weightage', 'requirement_score')
    def _compute_weightage_value(self):
        for record in self:
            record.weightage_value = record.requirement_score * record.weightage


class Bant(models.Model):
    _name = 'barcode_india.bant'
    _description = 'BANT'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    weightage = fields.Float('Weightage(%)')


class AssignReports(models.Model):
    _name = 'barcode_india.assign_report'
    _description = 'Assign Reports'

    active = fields.Boolean('Active', default=True)
    updated_by = fields.Many2one('res.users', string='Updated By')
    updated_on = fields.Datetime(string='Updated On', default=lambda self: fields.Datetime.now(), readonly=True)
    previous_user = fields.Many2one('res.users', string='Previous User')
    updated_user = fields.Many2one('res.users', string='Engineer')
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket Ref.')
    bci_support_type = fields.Selection([('remote_support', 'Remote support'), ('onsite_support', 'On-site support'), ('foc', 'FOC'), ('carry_in_support', 'Carry-in support'),('House Support','In-House Support'),('RMA Process','RMA Process'),('Quotation','Quotation')], 'Support Type')
    resolved_on = fields.Datetime(string='Case Resolved On', related="ticket_id.close_date", store=True)
    engineer_update = fields.Char(string="Engineer Update")
    remark = fields.Char(string="Remark")
    team_id = fields.Many2one('helpdesk.team', string="Team", related="ticket_id.team_id", store=True)

    # @api.onchange("ticket_id.close_date")
    # def onchange_previous_user(self):
    #     for record in self:
    #         record.resolved_on = record.ticket_id.close_date

    ticket_create_date = fields.Datetime(related="ticket_id.create_date", string="Created on", store=True)
    ticket_customer = fields.Many2one(related="ticket_id.partner_id", string="Ticket Ref./Customer", store=True)
    ticket_serial_no = fields.Many2one(related="ticket_id.bci_asset", string="Ticket Ref./Serial No.", store=True)
    ticket_product = fields.Many2one(related="ticket_id.bci_product", string="Ticket Ref./Product", store=True)
    ticket_warranty_status = fields.Selection(related="ticket_id.bci_warranty_status", string="Ticket Ref./Warranty Status", store=True)
    ticket_case_type = fields.Many2one(related="ticket_id.bci_case_type", string="Ticket Ref./Case Type", store=True)
    ticket_problem_type = fields.Many2one(related="ticket_id.bci_problem_type", string="Ticket Ref./Problem Type", store=True)
    ticket_stage = fields.Many2one(related="ticket_id.stage_id", string="Ticket Ref./Stage", store=True)
    ticket_resolution = fields.Char(related="ticket_id.bci_resolution", string="Ticket Ref./Resolution", store=True)
    ticket_total_days_open = fields.Integer(related="ticket_id.bci_total_no_of_days_open", string="Ticket Ref./Total No of Days Open", store=True)
    ticket_total_days_resolve = fields.Integer(related="ticket_id.bci_time_to_resolve_ticket", string="Ticket Ref./Total No of Days to resolve the ticket", store=True)
    last_updated_on = fields.Datetime(related="ticket_id.write_date", string="Last Updated on", store=True)
    
    @api.model
    def create(self, vals):
        vals['updated_on'] = fields.Datetime.now()
        return super().create(vals)
    
    def write(self, vals):
        vals['updated_on'] = fields.Datetime.now()
        return super().write(vals)

class SOPFHeader(models.Model):
    _name = 'barcode_india.sopf_header'
    _description = 'SOPF Header'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='SOPF Number')
    company_name = fields.Char(string='Company Name')
    company_id = fields.Char(string='Company ID')
    sopf_legacycompanyid = fields.Char(string='Legacy Company ID')
    costsheet_id = fields.Char(string='Costsheet ID')
    po_number = fields.Char(string='PO Number')
    order_date = fields.Datetime(string='Order Date')
    sopf_status = fields.Char(string='SOPF Status')
    sopf_total_amount_with_tax = fields.Float(string='SOPF Total Amount with Tax')
    payment_terms = fields.Html(string='Payment Terms')
    payment_schedule = fields.Html(string='Delivery Schedule')
    sopf_salesperson = fields.Text(string='Sales Person', size=50)
    sopf_billingaddress = fields.Text(string='Billing Address', size=200)
    sopf_shippingaddress = fields.Text(string='Shipping Address', size=200)
    item_ids = fields.One2many('barcode_india.sopf_items', 'sopf_id', string='SOPF Items')
    file_name = fields.Char(string='File Name')
    folder_path = fields.Char(string='Folder Path')

class SOPFItems(models.Model):
    _name = 'barcode_india.sopf_items'
    _description = 'SOPF Items'
    _rec_name = 'sopf_number_text'
    
    active = fields.Boolean('Active', default=True)
    sopf_id = fields.Many2one('barcode_india.sopf_header', string='SOPF Number')
    sopf_number_text = fields.Char(string='SOPF Number Text')
    part_number = fields.Char(string='Part Number')
    item_description = fields.Text(string='Item Description')
    quantity = fields.Integer(string='Quantity')
    price = fields.Float(string='Order Price')
    tax_applicable = fields.Integer(string='Tax Applicable')
    amount_after_tax = fields.Float(string='Amount After Tax')
    pricing_category = fields.Char(string='Pricing Category')
    approved_quote_price = fields.Float(string='Approved Quote Price')
    discount_applied = fields.Float(string='Discount Applied')
    total_order_amount = fields.Float(string='Total Order Amount')
    order_price = fields.Float(string='Order Price')
    model_number = fields.Char(string='Model Number')
    warranty = fields.Integer(string='Warranty (Months)')
    hsn_code = fields.Integer(string='HSN Code')
    gst_tax_rate = fields.Float(string='GST Tax Rate')
    status = fields.Char(string='Status')

class ModelNumber(models.Model):
    _name = 'barcode_india.model_number'
    _description = 'Model Number'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Model Number", required="1")

class ModelNumber(models.Model):
    _name = 'barcode_india.oem'
    _description = 'OEM'

    name = fields.Char(string="Number", required="1")

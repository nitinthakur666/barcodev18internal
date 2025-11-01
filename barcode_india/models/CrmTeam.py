from odoo import api, fields, models, _
from datetime import date, datetime,timedelta
from ast import literal_eval

class Team(models.Model):
    _inherit = 'crm.team'

    bci_code = fields.Char('Code')

class CRMTag(models.Model):
    _inherit = 'crm.tag'

    active = fields.Boolean("Active", default=True)

class Crmleads(models.Model):
    _inherit = 'crm.lead'

    def _lead_status_id(self):
        status = self.env['barcode_india.lead_status'].sudo().search([] ,order='id asc')
        return status and status[0] or False

    bci_lead = fields.Many2one('lead.type' , string='Lead Type')
    bci_region = fields.Many2one('barcode_india.region' , string='Region')
    bci_vertical = fields.Many2one('barcode_india.vertical',string='Vertical')
    bci_sub_vertical = fields.Many2one("barcode_india.sub_vertical","Sub Vertical")
    bci_sub_vertical_category = fields.Many2one("barcode_india.sub_vertical_category","Sub Vertical Category")
    bci_application_type = fields.Many2many('application.type',string='Application Type')
    bci_no_of_site_visit = fields.Integer(string='No. of Site Visit')
    bci_no_of_meetings = fields.Integer(string="No of Meetings")
    bci_no_of_revision = fields.Integer(string="No of Revision")
    bci_team_presale = fields.Many2many('res.users',string='Team Presale')
    bci_probability = fields.Many2one('barcode_india.probability', string='Probability')
    bci_activities = fields.Many2one('barcode_india.activities', string='Activities')
    company_id = fields.Many2one('res.company', store=True, copy=False,string="Company",default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",related='company_id.currency_id')
    bci_software = fields.Monetary(string='Software')
    bci_stage = fields.Many2one('barcode_india.stages',string='Clickup Stage')
    bci_project_title = fields.Char(string='Project Title')
    bci_lead_state = fields.Selection([('lead','Lead'),('qualification','Qualification')],string='Lead State')
    bci_task_id = fields.Char(string='Task ID')
    bci_task_custom_id = fields.Char(string='Task Custom ID')
    bci_start_date = fields.Date(string='Start Date')
    bci_date_created = fields.Date(string='Date Created')
    bci_space = fields.Char(string='Space')
    bci_folder = fields.Char(string='Folder')
    bci_list = fields.Char(string='List')
    bci_lists = fields.Char(string='Lists')
    bci_contract_id = fields.Many2one('barcode_india.contracts', 'Previous Contract')

    bci_turnover = fields.Selection([("0-100 Cr","0-100 Cr"),("101-500 Cr","101-500 Cr"),("501 & Above","501 & Above")],"Turnover")
    bci_any_other_info = fields.Text("Any Other Info")
    bci_department = fields.Char("Department")
    bci_linkedin = fields.Char("Linkedin")
    bci_account_type = fields.Selection([("High Touch","NAL"),("UNAL","UNAL")],"Account Type")
    
    bci_lead_status = fields.Many2one("barcode_india.lead_status","Lead Status", default=_lead_status_id)
    bci_lead_status_value = fields.Selection([('NEW','NEW'),('MQL','MQL'),('SQL','SQL'),('REJECT','REJECT')],'Status Value', default="NEW")

    bci_geography = fields.Char(string='Geography')
    bci_lob_first_level = fields.Char(string='LOB (First Level)')
    bci_prospect_expectation = fields.Selection([('exploring', 'Exploring'),
                                                 ('visit', 'Visit'),
                                                 ('offer', 'Offer')],
                                                string='Prospect expectation from BCI (call/visit) on the next steps')
    bci_application_area = fields.Char(string='Application Area')
    bci_use_case = fields.Text(string='Use Case')
    bci_key_issue = fields.Char(string='Key Issues/Pain Points/Challenges')
    bci_discovery_details = fields.Text(string='Vertical/sales discovery call + requirement understanding in detail')
    bci_solution_fit = fields.Text(string='Solution fit')
    bci_lob = fields.Many2one('barcode_india.lob', string='LOB')
    bci_location_type = fields.Selection([('Single Location', 'Single Location'),
                                          ('Multiple Locations', 'Multiple Locations')],
                                         string='Location Type')
    bci_location = fields.Char("Location")
    bci_seniority = fields.Selection([('CXO/VP/AVP', 'CXO/VP/AVP'),
                                      ('GM/Manager', 'GM/Manager'),
                                      ('Consultant', 'Consultant'),
                                      ('Junior Member', 'Junior Member')],
                                     string='Seniority')
    bci_budget = fields.Monetary(string='Budget')
    bci_current_erp = fields.Text(string='Current ERP')   
    bci_contract_details_count = fields.Integer('Contract Details Count', compute='_compute_contract_detail_count')
    bci_reject_reason = fields.Many2one("barcode_india.reject_reason", "Reject Reason")
    bci_rejection_remark = fields.Text("Rejection Remark")
    bci_status = fields.Many2one("barcode_india.status","Pipeline Status",tracking=True)
    bci_presales_ids = fields.Many2many('res.users',relation='bci_presales_rel',string='Pre-Sales',tracking=True)
    decision_maker_ids = fields.Many2many('res.partner',relation='bci_decision_maker_rel',string='Decision Makers')
    influencer_ids = fields.Many2many('res.partner',relation='bci_influencer_rel',string='Internal Influencers')
    influencer_ext_ids = fields.Many2many('res.partner',relation='bci_influencer_ext_rel',string='External Influencers')
    user_ids = fields.Many2many('res.partner',relation='bci_user_rel',string='Users')
    expected_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency',compute='_compute_expected_revenue', tracking=True)
    bci_hardware_pre_sales = fields.Many2one('res.users',string='Hardware Pre-Sales',readonly=True,tracking=True)
    bci_software_pre_sales = fields.Many2one('res.users',string='Software Pre-Sales',readonly=True,tracking=True)
    bci_bant_ids = fields.One2many('barcode_india.bant_crm', 'bci_lead_id', string='Bant')
    total_weightage_value = fields.Integer(string='Total Weightage Value', compute='_compute_total_weightage_value', store=True)
    bci_priority = fields.Selection([
        ('low', 'Low'),
        ('average', 'Average'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='BANT Score', compute='_compute_priority', store=True)
    bant_remarks = fields.Char(string='Bant Remark',compute='_compute_bant_remarks', help='0 value in Requirement Score in the Bant',store=True)
    bci_technical_qualified = fields.Boolean("Technically Qualified")
    bci_technical_description = fields.Char("Technical Description")
    bci_lost_type = fields.Selection([('Lost Rejection','Lost Rejection'),('Technical Rejection','Technical Rejection')],string="Lost/Technical Type")
    bci_lost_reason_id = fields.Many2one('crm.lost.reason', 'Lost/Technical Reason')
    bci_lost_reason = fields.Html("Lost/Technical Description")
    bci_task_count = fields.Integer(compute='_compute_task_count', string="Number of task")

    bci_industry_id = fields.Many2one('res.partner.industry',string='Industry')
    bci_requirement = fields.Selection([('Hardware','Hardware'),('Software','Software'),('Consumables','Consumables')],string="Requirement")
    bci_status_lead = fields.Selection([('Initial Discussion','Initial Discussion'),('On Hold','On Hold'),('Lost','Lost'),('Dropped','Dropped/Not Qualified'),('Won','Won')],string="Status")
    date_deadline = fields.Date('Expected Closing', help="Estimate of the date on which the opportunity will be won.",tracking=True)

    def _compute_task_count(self):
        for rec in self:
            rec.bci_task_count = self.env['project.task'].sudo().search_count([('lead_id', '=', self.id)])

    @api.depends('bci_bant_ids.requirement_score')
    def _compute_bant_remarks(self):
        for lead in self:
            requirement_scores = lead.bci_bant_ids.mapped('requirement_score')
            if any(score == 0 for score in requirement_scores):
                lead.bant_remarks = '?'
            else:
                lead.bant_remarks = ''


    def action_set_won(self):
        rec = super(Crmleads, self).action_set_won()
        for lead in self:
            contract_id = self.env['barcode_india.contracts'].sudo().search([('bci_opportunity', '=', lead.id)])
            if contract_id:
                contract_id.write({'bci_renewal_status' : 'To Be Activated'})
        return rec
    
    @api.model
    def create(self, vals):
        lead = super(Crmleads, self).create(vals)
        bant_records = self.env['barcode_india.bant'].search([])
        vals = []
        for rec in bant_records:
            vals.append((0,0,{'name': rec.name,'weightage': rec.weightage,'bci_lead_id': lead.id}))
        lead.bci_bant_ids = vals
        return lead

    @api.depends('total_weightage_value')
    def _compute_priority(self):
        for lead in self:
            if lead.total_weightage_value < 40:
                lead.bci_priority = 'low'
            elif 40 <= lead.total_weightage_value <= 60:
                lead.bci_priority = 'average'
            elif 61 <= lead.total_weightage_value <= 80:
                lead.bci_priority = 'medium'
            else:
                lead.bci_priority = 'high'

    @api.depends('bci_bant_ids.weightage_value')
    def _compute_total_weightage_value(self):
        for record in self:
            total_value = sum(record.bci_bant_ids.mapped('weightage_value'))
            record.total_weightage_value = total_value

    @api.depends('order_ids.amount_total')
    def _compute_expected_revenue(self):
        for lead in self:
            total_revenue = sum(quote.amount_total for quote in lead.order_ids)
            lead.expected_revenue = total_revenue


    def action_view_contract(self):
        self.ensure_one()
        return {
            'name': _('Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.contracts',
            'view_mode': 'list,form',
            'domain': [('bci_opportunity', '=', self.id)],
        }

    def action_view_task(self):
        self.ensure_one()
        return {
            'name': _('Task'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)]
        }

    def convert_to_mql(self):
        for record in self:
            record.bci_lead_status_value = 'MQL'
            record.bci_lead_status = self.env.ref('barcode_india.lead_status2').id

    def convert_to_sql(self):
        for record in self:
            record.bci_lead_status_value = 'SQL'
            record.bci_lead_status = self.env.ref('barcode_india.lead_status3').id

    def action_rejected(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Reason'),
            'res_model': 'barcode_india.reject_reason_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_crm_id': self.id,
            }
        }

    def action_show_contract_details(self):
        self.ensure_one()
        return {
            'name': _('Contract Detail'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.contracts.details',
            'view_mode': 'list,form',
            'domain': [('bci_opportunity', '=', self.id)],
        }

    def _compute_contract_detail_count(self):
        for rec in self:
            rec.bci_contract_details_count = self.env['barcode_india.contracts.details'].sudo().search_count([('bci_opportunity', '=', rec.id)])

    def add_pre_sales_task(self):
        self.ensure_one()
        return {
            'name': 'project task',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'views': [[False, 'form']],
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }
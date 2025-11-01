from odoo import models, fields, api, _

class Projects(models.Model):
    _inherit = 'project.project'

    bci_contract_ids = fields.Many2many('barcode_india.contracts',string='Contract')
    bci_partner_ids = fields.Many2many('res.partner',string='Customers')
    bci_user_ids = fields.Many2many('res.users',string='Users')
    bci_primary_user = fields.Many2one('res.users',string='Primary User')
    bci_senior_designated = fields.Many2one('res.users',string='Senior Designated User')
    bci_is_pm = fields.Boolean(string='Preventive Maintenance')
    bci_contract_details_count = fields.Integer('Contract Details Count', compute='_compute_contract_details_count')
    bci_cr = fields.Boolean("CR")
    bci_parent_project = fields.Many2one("project.project","Parent Project")
    bci_parent_project_count = fields.Integer("Parent Project Count", compute='_compute_parent_project_count')
    is_presales_project = fields.Boolean("Is Pre-sales Project")
    bci_summary = fields.Html(string='Summary')
    bci_is_bug = fields.Boolean(string="Is Bug?")
    bci_bug_task = fields.One2many('project.task', 'bci_reported_project', string='Bugs')
    bci_bug_task_count = fields.Integer("Bugs Task Count", compute='_compute_bugs_count')
    bci_test_case = fields.One2many('barcode_india.test_cases', 'project_id', string='Test Cases')
    bci_test_case_count = fields.Integer("Test Cases Count", compute='_compute_test_case_count')
    is_product = fields.Boolean(string="Is Product")
    bug_type = fields.Selection([
        ('blocker', 'Blocker'),
        ('functional_positive', 'Funtional Positive'),
        ('functional_negative', 'Funtional Negative'),
        ('uiux_cosmetic', 'UI/UX Cosmetic'),
        ('uiux_design', 'UI/UX Design Issue'),
        ('requirement_mismatch', 'Requirement Mismatch'),
        ('hardware_not_available', 'Hardware Not Available'),
        ('data_not_available', 'Data Not Available'),
        ('under_development', 'Under Development'),
        ('observation', 'Observation'),
        ('sap_dependent', 'SAP Dependent'),
        ('missing_feature', 'Missing Feature'),
        ('api_issue', 'API Issue'),
        ('performance_issue', 'Performance Issue')
    ], string="Bug Type", required=True)
    bug_priority = fields.Selection([
        ('blocker', 'Blocker'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('observation', 'Observation')
    ], string="Bug Priority", required=True)
    bug_severity = fields.Selection([
        ('p1_critical', 'P1 - Critical'),
        ('p2_high', 'P1 - High'),
        ('p3_medium', 'P3 - Medium'),
        ('p4_low', 'P4 - Low'),
        ('p5_observation', 'P5 - Observation')
    ], string="Bug Severity", required=True)
    bug_impact_module = fields.Selection([
        ('login', 'Login'),
        ('dashboard', 'Dashboard'),
        ('um', 'UM'),
        ('masters', 'Masters'),
        ('global_masters', 'Global Masters'),
        ('transactions', 'Transactions'),
        ('global_transactions', 'Global Transactions'),
        ('reports', 'Reports'),
        ('audit_trail', 'Audit Trail'),
        ('21_cfr', '21 CFR'),
        ('vapt', 'VAPT'),
        ('performance', 'Performance')
    ], string="Bug Impact Module", required=True)
    bug_cluster_type = fields.Selection([
        ('functionality_related', 'Functionality Related'),
        ('messages_validation', 'Messages & Validation'),
        ('uiux_related', 'UI/UX Related'),
        ('search_filter', 'Search, Filter & Pagination'),
        ('missing_feature', 'Module or Feature Missing from Application'),
        ('missing_srs', 'Module or Feature Missing from SRS'),
        ('field_dropdown', 'Field & Dropdown Related'),
        ('database_related', 'Database Related'),
        ('printing_hardware', 'Printing/Hardware Related'),
        ('auto_selection', 'Auto Selection Related'),
        ('dashboard', 'Dashboard')
    ], string="Bug Cluster Type", required=True)
    product_process_bifurcation = fields.Selection([
        ('um', 'UM'),
        ('dashboards', 'Dashboards'),
        ('rm_masters', 'RM-Masters'),
        ('rm_transactions', 'RM-Transactions'),
        ('rm_reports', 'RM-Reports'),
        ('mes_masters', 'MES-Masters'),
        ('mes_transactions', 'MES-Transactions'),
        ('mes_reports', 'MES-Reports'),
        ('fg_masters', 'FG-Masters'),
        ('fg_transactions', 'FG-Transactions'),
        ('fg_reports', 'FG-Reports')
    ], string="Product Process Bifurication", required=True)
    bug_platform = fields.Selection([
        ('web_laptop', 'Web - Laptop'),
        ('web_android', 'Web - Android'),
        ('web_ios', 'Web - iOS'),
        ('tablet_android', 'Tablet - Android'),
        ('tablet_ios', 'Tablet - iOS'),
        ('desktop_app', 'Desktop App'),
        ('device_apk', 'Device - APK')
    ], string="Bug Platform", required=True)
    bug_environment = fields.Selection([
        ('internal_qa', 'Internal QA'),
        ('uat', 'UAT'),
        ('support', 'Support')
    ], string="Bug Environment", required=True)
    is_product_package_selected = fields.Boolean(
        string="Product Package Selected?",
        default=False
    )
    product_package_selection =fields.Selection([
        ('silver_lite', 'Silver Lite'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('diamond', 'Diamond')
    ], string="Product Package Selection List", required=True)
    software_project = fields.Boolean(string="Software Project?")

    @api.depends('bci_bug_task')
    def _compute_bugs_count(self):
        for rec in self:
            rec.bci_bug_task_count = self.env['project.task'].sudo().search_count([('bci_reported_project', '=', rec.id)])

    @api.depends('bci_test_case')
    def _compute_test_case_count(self):
        for rec in self:
            rec.bci_test_case_count = self.env['barcode_india.test_cases'].sudo().search_count([('project_id', '=', rec.id)])

    @api.onchange('partner_id','bci_partner_ids')
    def bci_contract_ids_onchange(self):
        customers = self.partner_id | self.bci_partner_ids
        if customers:
            return {'domain': {'bci_contract_ids': [('bci_customer', 'in', customers.ids)]}}
        else:
            return {'domain': {'bci_contract_ids': [('id', '=', False)]}}

    def _compute_contract_details_count(self):
        for rec in self:
            rec.bci_contract_details_count = self.env['barcode_india.contracts.details'].sudo().search_count([('bci_projects', '=', rec.id)])

    def action_show_bugs(self):
        self.ensure_one()
        return {
            'name': _('Bugs'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'context': {'default_bci_reported_project': self.id},
            'domain': [('bci_reported_project', '=', self.id)],
        }

    def action_show_test_case(self):
        self.ensure_one()
        return {
            'name': _('Test Cases'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.test_cases',
            'view_mode': 'list',
            'domain': [('project_id', '=', self.id)],
        }
    
    def action_show_contract_details(self):
        self.ensure_one()
        return {
            'name': _('Contract Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.contracts.details',
            'view_mode': 'list,form',
            'context': {
                'default_bci_projects': self.id,
            },
            'domain': [('bci_projects', '=', self.id)],
        }

    def _compute_parent_project_count(self):
        for record in self:
            record.bci_parent_project_count = self.sudo().search_count([("bci_parent_project","=",record.id)])

    def action_parent_project_details(self):
        self.ensure_one()
        return {
            'name': _('CR'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'list,form',
            'context': {
                'default_bci_parent_project': self.id,
            },
            'domain': [('bci_parent_project', '=', self.id)],
        }

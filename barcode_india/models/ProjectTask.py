from odoo import fields, models, api ,_
from odoo.exceptions import ValidationError
from datetime import timedelta


class ProjectTask(models.Model):
    _inherit = 'project.task'

    bci_issue_resolved = fields.Boolean(string='Issue Resolved')
    bci_bulk_import = fields.Boolean(string='Is Bulk Import?')
    bci_ticket_count = fields.Integer(string='Ticket Count',compute='_compute_ticket_count')
    bci_ticket_ids = fields.One2many('helpdesk.ticket', 'bci_bulk_task_id', string='Bulk Tickets')
    bci_site_id = fields.Many2one('res.partner', string='Site')
    bci_site_phone = fields.Char(string=' Site Phone')
    bci_asset_id = fields.Many2one('barcode_india.assets', string='Serial Number')
    bci_product_id = fields.Many2one('product.product', string='Product')
    bci_final_resolution = fields.One2many('barcode_india.final_resolution','bci_task_id', string='Final Resolution')
    bci_pm_status = fields.One2many('barcode_india.pm_status','task_id', string='PM Status')
    bci_is_pm = fields.Boolean(related='project_id.bci_is_pm', string='Preventive Maintenance')
    lead_id = fields.Many2one('crm.lead', 'Related Lead')
    bci_address = fields.Text(string="Site Address")
    hide_fields = fields.Boolean("Hide Fields")
    bci_quotation_count = fields.Integer(compute='_compute_bci_quotation_count', string="Number of Quotations")
    bci_actual_start_date = fields.Datetime(string='Actual Start Date',tracking=True)
    bci_actual_end_date = fields.Datetime(string='Actual End Date',tracking=True)
    bci_reported_project = fields.Many2one('project.project', string='Reported Project')
    bci_reported_task = fields.Many2one('project.task', string='Reported Task')
    bci_is_bug = fields.Boolean(string="Is Bug?", related='project_id.bci_is_bug')
    bci_bug_task = fields.One2many('project.task', 'bci_reported_task', string='Bugs')
    bci_bug_task_count = fields.Integer("Bugs Task Count", compute='_compute_bugs_count')
    bci_test_case = fields.One2many('barcode_india.test_cases', 'task_id', string='Test Cases')
    bci_test_case_count = fields.Integer("Test Cases Count", compute='_compute_test_case_count')

    @api.depends('bci_bug_task')
    def _compute_bugs_count(self):
        for rec in self:
            rec.bci_bug_task_count = self.env['project.task'].sudo().search_count([('bci_reported_task', '=', rec.id)])

    @api.depends('bci_test_case')
    def _compute_test_case_count(self):
        for rec in self:
            rec.bci_test_case_count = self.env['barcode_india.test_cases'].sudo().search_count([('task_id', '=', rec.id)])

    
    @api.depends('lead_id')
    def _compute_bci_quotation_count(self):
        for task in self:
            task.bci_quotation_count = len(task.lead_id.order_ids.filtered_domain(task.lead_id._get_lead_quotation_domain()))

    def action_show_related_quotations(self):
        self.ensure_one()
        return {
            'name': 'Quotations',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('opportunity_id', '=', self.lead_id.id)],
            'target': 'current',
            'context' : self.lead_id._prepare_opportunity_quotation_context()
        }

    def action_show_bugs(self):
        self.ensure_one()
        return {
            'name': _('Bugs'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'context': {'default_bci_reported_task': self.id, 'default_bci_reported_project': self.project_id.id},
            'domain': [('bci_reported_task', '=', self.id)],
        }

    def action_show_test_case(self):
        self.ensure_one()
        return {
            'name': _('Test Cases'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.test_cases',
            'view_mode': 'list',
            'context': {'default_task_id': self.id},
            'domain': [('task_id', '=', self.id)],
        }
    
    @api.depends('bci_ticket_ids')
    def _compute_ticket_count(self):
        task_data = self.env['helpdesk.ticket'].read_group([('bci_bulk_task_id', '=', self.id)], ['bci_bulk_task_id'], ['bci_bulk_task_id'])
        task_mapped_data = dict((data['bci_bulk_task_id'][0], data['bci_bulk_task_id_count']) for data in task_data)
        for task in self:
            task.bci_ticket_count = task_mapped_data.get(task.id, 0)

    def action_view_ticket(self):
        return {
            'name': _('Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': self.helpdesk_ticket_id.id,
        }

    def action_view_tickets(self):
        self.ensure_one()
        case_type = self.env['barcode_india.case_type'].sudo().search(
            [('type', '=', 'hardware')], limit=1)
        if not case_type:
            raise ValidationError(_("There is no Case Type for hardware!"))
        return {
            'name': _('Bulk Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'context': {'default_bci_case_type': case_type.id, 
                        'default_bci_bulk_task_id': self.id,
                        'create':True,'edit':True},
            'domain': [('bci_bulk_task_id', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def action_pm_status(self):
        return {
            'name': 'PM Status',
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.pm_status',
            'view_mode': 'tree',
            'domain': [('task_id', '=', self.id)],
            'target': 'current',
        }

    def action_fsm_validate(self, stop_running_timers=False):
        res = super(ProjectTask, self).action_fsm_validate(stop_running_timers)
        for task in self:
            if task.helpdesk_ticket_id:
                if not task.bci_issue_resolved and task.helpdesk_ticket_id.team_id.bci_owner_id:
                    task.helpdesk_ticket_id.user_id = task.helpdesk_ticket_id.team_id.bci_owner_id.id
                if task.bci_issue_resolved and task.helpdesk_ticket_id.team_id.to_stage_id:
                    task.helpdesk_ticket_id.stage_id = task.helpdesk_ticket_id.team_id.to_stage_id.id
        return res
    
    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        if vals.get('lead_id'):
            lead_id = vals.get('lead_id')
            if lead_id:
                lead = self.env['crm.lead'].browse(lead_id)
                users_assigned_to_task = res.user_ids.ids
                lead.write({'bci_presales_ids': [(4, user_id) for user_id in users_assigned_to_task]})
                self.send_email_notification(lead, users_assigned_to_task)
        return res

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'user_ids' in vals:
            for task in self:
                lead_id = task.lead_id.id
                if lead_id:
                    lead = self.env['crm.lead'].browse(lead_id)
                    existing_presales = lead.bci_presales_ids.ids
                    users_assigned_to_task = vals.get('user_ids')[0][2] if isinstance(vals.get('user_ids'), list) else []
                    for user_id in users_assigned_to_task:
                        if user_id not in existing_presales:
                            existing_presales.append(user_id)
                    lead.write({'bci_presales_ids': [(6, 0, existing_presales)]})
                    self.send_email_notification(lead, existing_presales)
        return res

   
    def send_email_notification(self, lead, existing_presales):
        if lead and existing_presales:
            mail_template = self.env.ref('barcode_india.bci_pre_sale_template')
            if mail_template:
                user_emails = self.env['res.users'].sudo().browse(existing_presales).mapped('email')
                user_emails = [email for email in user_emails if isinstance(email, str)]
                if user_emails:
                    mail_template.write({
                        'email_to': ', '.join(user_emails),
                        'email_from': lead.company_id.email,
                    })
                    mail_template.send_mail(lead.id, force_send=True)
                    lead.message_post(body="The pre-sales team for this opportunity has been updated and sent the Email to pre-sales users")
    
    def send_due_date_reminder(self, days_before=2):
        upcoming_tasks = self.env['project.task'].search([('date_deadline', '=', fields.Date.today() + timedelta(days=days_before)),('stage_id.fold', '=', False)])

        template = self.env.ref('barcode_india.bci_email_template_task_due_reminder', raise_if_not_found=False)

        if not template:
            raise ValidationError("Email template 'Task Due Date Reminder' not found. Please ensure the template is set up correctly.")

        for task in upcoming_tasks:
            for user in task.user_ids:
                if user.email:
                    template.with_context(lang=user.lang).send_mail(
                        task.id, 
                        force_send=True,
                        email_values={'email_to': user.email}
                    )

    @api.onchange('lead_id')
    def _get_project_domain(self):
        if self.lead_id:
            return {'domain': {'project_id': [('is_presales_project', '=', True)]}}
        else:
            return {'domain': {'project_id': []}}
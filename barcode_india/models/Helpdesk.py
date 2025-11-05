from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict


Preferred_Selection = [('Remote Server Support', 'Remote Server Support'),
                       ('On Call Support', 'On-Call Support'),
                       ('On Site Visit Support', 'On Site Visit Support')]


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    bci_owner_id = fields.Many2one('res.users', 'Owner')
    bci_type = fields.Selection([('Software', 'Software'), ('Hardware', 'Hardware'), ('Preventive Maintenance', 'Preventive Maintenance')], string='Type')

    def _cron_auto_close_tickets(self):
        super(HelpdeskTeam, self)._cron_auto_close_tickets()
        teams = self.env['helpdesk.team'].search_read(
            domain=[
                ('auto_close_ticket', '=', True),
                ('auto_close_day', '>', 0),
                ('to_stage_id', '!=', False)],
            fields=[
                'id',
                'auto_close_day',
                'from_stage_ids',
                'to_stage_id']
        )
        teams_dict = defaultdict(dict)  # key: team_id, values: the remaining result of the search_group
        today = fields.datetime.today()
        for team in teams:
            # Compute the threshold_date
            team['threshold_date'] = today - relativedelta(days=team['auto_close_day'])
            teams_dict[team['id']] = team
        tickets_domain = [('team_id', 'in', list(teams_dict.keys()))]
        tickets = self.env['helpdesk.ticket'].search(tickets_domain)

        def is_inactive_ticket(ticket):
            team = teams_dict[ticket.team_id.id]
            is_write_date_ok = ticket.write_date <= team['threshold_date']
            if team['from_stage_ids']:
                is_stage_ok = ticket.stage_id.id in team['from_stage_ids']
            else:
                is_stage_ok = not ticket.stage_id.fold
            return is_write_date_ok and is_stage_ok

        inactive_tickets = tickets.filtered(is_inactive_ticket)
        for ticket in inactive_tickets:
            # to_stage_id is mandatory in the view but not in the model so it is better to test it.
            if teams_dict[ticket.team_id.id]['to_stage_id']:
                ticket.write({'stage_id': teams_dict[ticket.team_id.id]['to_stage_id'][0]})


class HelpdeskTicketType(models.Model):
    _name = 'helpdesk.ticket.type'
    _description = 'Helpdesk Ticket Type'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    bci_problem_type = fields.Many2one('barcode_india.problem_type', 'Problem Type')
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "A type with the same name already exists."),
    ]


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    bci_hold_stage = fields.Boolean('Is Hold Stage')
    bci_in_progress_stage = fields.Boolean('Is In Progress Stage')
    bci_cancelled_stage = fields.Boolean('Is Cancelled Stage')

class HelpdeskSla(models.Model):
    _inherit = 'helpdesk.sla'

    def action_escalation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escalation',
            'res_model': 'barcode_india.escalation',
            'view_mode': 'list,form',
            'domain': [('bci_sla', '=', self.id)],
        }
    


class Helpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_type_id = fields.Many2one('helpdesk.ticket.type', 'Problem Sub Type')
    bci_project = fields.Many2one('project.project', 'Project')
    bci_contract_id = fields.Many2one('barcode_india.contracts', 'Contract')
    bci_preferred_applicable = fields.Selection(Preferred_Selection, 'Preferred and Applicable Options')
    bci_start = fields.Date('Contract Start Date')
    bci_end = fields.Date('Contract End Date')
    bci_resolution_type = fields.Many2one('barcode_india.resolution_type', 'Resolution Type')
    bci_reason_code = fields.Many2one('barcode_india.reason_code', 'RCA Reason Code')
    bci_resolution = fields.Char('Resolution')
    bci_related_ticket = fields.Many2one('helpdesk.ticket', 'Related Ticket')
    bci_warranty_status = fields.Selection([('In Warranty', 'In Warranty'), ('In Grace', 'In Grace'), ('Out of Warranty', 'Out of Warranty')], 'Warranty Status')
    bci_case_type = fields.Many2one('barcode_india.case_type', 'Case Type')
    bci_case_sub_type = fields.Many2one('barcode_india.case_sub_type', 'Case Sub Type')
    bci_problem_type = fields.Many2one('barcode_india.problem_type', 'Problem Type')
    bci_chargeable = fields.Boolean('Chargeable', compute='compute_chargeable', store=True)
    bci_sale_order_count = fields.Integer('Sale Order Count', compute='_compute_sale_order_count')
    bci_sale_order_ids = fields.One2many('sale.order', 'bci_helpdesk', string='Sale Orders')
    bci_site = fields.Many2one('res.partner', 'Site')
    bci_address = fields.Text(string="Site Address")
    bci_site_phone = fields.Char(string='Phone', compute="_compute_site_phone", store=True)
    bci_stages_ids = fields.One2many('helpdesk.stage_timespent', 'bci_ticket_id', 'stage')
    bci_total_no_of_days_open = fields.Integer(string='Total No of Days Open', compute='_compute_total_no_of_days_open')
    bci_total_no_of_days_in_current_stage = fields.Integer(string='Total No of Days in Current Stage', compute='_compute_total_no_of_days_in_current_stage')
    bci_time_to_resolve_ticket = fields.Integer(string='Total No of Days to resolve the ticket', compute='_compute_time_to_resolve_ticket', store=True)
    bci_barcode_case_type_find = fields.Selection(related='bci_case_type.type', store=True)
    bci_asset = fields.Many2one('barcode_india.assets', 'Serial No.')
    bci_product = fields.Many2one('product.product', string='Product', related='bci_asset.bci_product', store=True)
    bci_oem_start_date = fields.Date('OEM Start Date')
    bci_oem_end_date = fields.Date('OEM End Date')
    bci_delivery_type = fields.Char('Delivery Type')
    bci_oem_contract_no = fields.Char('OEM Contract No')
    bci_rma = fields.Boolean(string="RMA", compute="_compute_rma_applicable", store=True, readonly=False)
    bci_complete_unit_rma = fields.Boolean(string="Complete Unit RMA")
    bci_pickup_type_id = fields.Many2one('barcode_india.rma_masters', 'Picking Type')
    bci_oem_rma_request_no = fields.Char(string="OEM RMA Request No.")
    bci_pickings_count = fields.Integer('Transfers Count', compute="_compute_orders_pickings_count")
    bci_spare_pickings_count = fields.Integer('Spares Transfers Count', compute="_compute_spare_pickings_count")
    bci_orders_picking_ids = fields.One2many('stock.picking', 'bci_source_ticket', string="RMA Transfers")
    bci_bulk_task_id = fields.Many2one('project.task', string="Bulk Task ID")
    bci_final_resolution = fields.One2many('barcode_india.final_resolution', 'bci_ticket_id', string='Final Resolution')
    bci_partner_tags = fields.Many2many('res.partner.category', string='Customer Tags', compute='_compute_partner_tags', store=True)
    bci_support_type = fields.Selection([('remote_support', 'Remote support'), ('onsite_support', 'On-site support'), ('foc', 'FOC'), ('carry_in_support', 'Carry-in support'),('House Support','In-House Support'),('RMA Process','RMA Process'), ('Quotation','Quotation')], 'Support Type')
    bci_asset_ids = fields.Many2many('barcode_india.assets', string='Assets')
    bci_approval_for = fields.Selection([('Remote Support','Remote Support'),('Field Service and Remote Support','Field Service and Remote Support'),('Complete Process','Complete Process')],'Approval For',copy=False)
    bci_is_approved = fields.Boolean("Is Approved", copy=False)
    bci_approval_request_count = fields.Integer('Sale Order Count', compute='_compute_approval_request_count')
    bci_plant = fields.Many2one('res.partner', 'Plant')
    bci_show_rma = fields.Boolean("Show RMA", compute="compute_show_rma")
    bci_show_spare_rma = fields.Boolean("Show Spare RMA", compute="compute_show_spare_rma")
    bci_show_task = fields.Boolean("Show Task", compute="compute_show_task")

    bci_own_company = fields.Many2one("barcode_india.own_company","Own Company")
    bci_oem_product_group = fields.Many2one("barcode_india.oem_product_group","OEM & Product Group")
    bci_warranty_amc = fields.Many2one("barcode_india.warranty_amc","Warranty/AMC/Carepack Type")
    bci_coverage = fields.Many2one("barcode_india.coverage","Coverage")
    bci_service_category = fields.Many2one("barcode_india.service_category","Service Category")
    bci_coverage_type = fields.Many2one("barcode_india.coverage_type","Coverage Type")
    bci_onsite_coverage = fields.Many2one("barcode_india.onsite_coverage","Onsite Coverage")
    bci_standby_equipment = fields.Many2one("barcode_india.standby_equipment","Engineer & Standby Equipment")
    bci_sla = fields.Many2one("helpdesk.sla","SLA")
    bci_service_product = fields.Many2one('product.product','Service Product')

    bci_escalation = fields.One2many("barcode_india.helpdesk_escalation","bci_ticket_id","Escalation")
    bci_user_ids = fields.Many2many("res.users", string="Sent to")
    bci_severity = fields.Selection([('Low','Low'),('Medium','Medium'),('High','High')],string="Severity")
    bci_assign_report_ids = fields.One2many('barcode_india.assign_report', 'ticket_id', string='Assign Report Matrix')
    previous_user_id = fields.Many2one('res.users', string='Previous User')
    bci_resolved_by = fields.Many2one('res.users', string='Assigned to',readonly=False, tracking=True,domain=lambda self: [('groups_id', 'in', self.env.ref('helpdesk.group_helpdesk_user').id)])
    bci_remarks = fields.Text('Remarks')
    bci_hold_stage = fields.Boolean(related='stage_id.bci_hold_stage', string="hold Stage")
    bci_cancelled_stage = fields.Boolean(related='stage_id.bci_cancelled_stage', string='Cancel Stage')

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for record in self:
            if record.stage_id.bci_hold_stage:
                if not record.bci_remarks:
                    raise UserError('Please add remarks before putting the ticket on hold it.')
            if record.stage_id.bci_cancelled_stage:
                if not record.bci_remarks:
                    raise UserError('Please add remarks before putting the ticket on cancelling it.')

    def action_open_hold_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Put Ticket On Hold',
            'res_model': 'helpdesk.wizard.hold',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            },
        }

    def action_open_cancel_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Ticket',
            'res_model': 'helpdesk.wizard.cancel',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            },
        }

    @api.depends('partner_id')
    def _compute_partner_tags(self):
        for ticket in self:
            ticket.bci_partner_tags = ticket.partner_id and ticket.partner_id.category_id or False

    @api.depends('bci_barcode_case_type_find','bci_warranty_status','bci_chargeable','bci_approval_for','bci_is_approved','bci_rma')
    def compute_show_rma(self):
        for record in self:
            if record.bci_barcode_case_type_find == 'hardware':
                if record.bci_warranty_status in ["In Warranty","In Grace"] and record.bci_rma and record.bci_pickings_count == 0:
                    record.bci_show_rma = True
                elif record.bci_warranty_status == "Out of Warranty" and record.bci_rma and record.bci_pickings_count == 0:
                    if not record.bci_chargeable:
                        record.bci_show_rma = True
                    elif record.bci_chargeable and record.bci_approval_for == 'Complete Process' and record.bci_is_approved:
                        record.bci_show_rma = True
                    else:
                        record.bci_show_rma = False
                else:
                    record.bci_show_rma = False
            else:
                record.bci_show_rma = False

    @api.depends('bci_barcode_case_type_find','bci_warranty_status','bci_chargeable','bci_approval_for','bci_is_approved','bci_complete_unit_rma')
    def compute_show_spare_rma(self):
        for record in self:
            if record.bci_barcode_case_type_find == 'hardware':
                if record.bci_warranty_status in ["In Warranty","In Grace"] and not record.bci_complete_unit_rma:
                    record.bci_show_spare_rma = True
                elif record.bci_warranty_status == "Out of Warranty" and not record.bci_complete_unit_rma:
                    if not record.bci_chargeable:
                        record.bci_show_spare_rma = True
                    elif record.bci_chargeable and record.bci_approval_for == 'Complete Process' and record.bci_is_approved:
                        record.bci_show_spare_rma = True
                    else:
                        record.bci_show_spare_rma = False
                else:
                    record.bci_show_spare_rma = False
            else:
                record.bci_show_spare_rma = False

    @api.depends('bci_barcode_case_type_find','bci_warranty_status','bci_chargeable','bci_approval_for','bci_is_approved')
    def compute_show_task(self):
        for record in self:
            if record.bci_barcode_case_type_find == 'hardware':
                if record.bci_warranty_status and record.bci_warranty_status in ["In Warranty","In Grace"]:
                    record.bci_show_task = True
                elif record.bci_warranty_status and record.bci_warranty_status == "Out of Warranty":
                    if not record.bci_chargeable:
                        record.bci_show_task = True
                    elif record.bci_chargeable and record.bci_approval_for in ['Field Service and Remote Support','Complete Process'] and record.bci_is_approved:
                        record.bci_show_task = True
                    else:
                        record.bci_show_task = False
                else:
                    record.bci_show_task = True
            else:
                record.bci_show_task = True

    @api.depends('bci_warranty_status')
    def _compute_rma_applicable(self):
        for rec in self:
            rec.bci_rma = rec.bci_warranty_status in ['In Warranty', 'In Grace'] and True or False

    @api.depends('bci_orders_picking_ids')
    def _compute_orders_pickings_count(self):
        ticket_groups = self.env['stock.picking'].read_group([('bci_source_ticket', '!=', False), ('bci_spare_transfer', '=', False)], ['id:count_distinct'], ['bci_source_ticket'])
        ticket_count_mapping = dict(map(lambda group: (group['bci_source_ticket'][0], group['bci_source_ticket_count']), ticket_groups))
        for ticket in self:
            ticket.bci_pickings_count = ticket_count_mapping.get(ticket.id, 0)

    @api.depends('bci_orders_picking_ids')
    def _compute_spare_pickings_count(self):
        ticket_groups = self.env['stock.picking'].read_group([('bci_source_ticket', '!=', False), ('bci_spare_transfer', '!=', False)], ['id:count_distinct'], ['bci_source_ticket'])
        ticket_count_mapping = dict(map(lambda group: (group['bci_source_ticket'][0], group['bci_source_ticket_count']), ticket_groups))
        for ticket in self:
            ticket.bci_spare_pickings_count = ticket_count_mapping.get(ticket.id, 0)

    @api.depends('close_hours')
    def _compute_total_no_of_days_open(self):
        for rec in self:
            rec.bci_total_no_of_days_open = rec.open_hours and rec.open_hours/24 or 0

    def _compute_total_no_of_days_in_current_stage(self):
        for rec in self:
            if rec.date_last_stage_update:
                total_no_of_days = datetime.now() - rec.date_last_stage_update
                rec.bci_total_no_of_days_in_current_stage = total_no_of_days.days
            else:
                rec.bci_total_no_of_days_in_current_stage = 0

    @api.depends('create_date', 'close_date')
    def _compute_time_to_resolve_ticket(self):
        for rec in self:
            create_date = fields.Datetime.from_string(rec.create_date)
            if create_date and rec.close_date and rec.team_id:
                duration_data = rec.team_id.resource_calendar_id.get_work_duration_data(create_date, fields.Datetime.from_string(rec.close_date), compute_leaves=True)
                rec.bci_time_to_resolve_ticket = duration_data['days']
            else:
                rec.bci_time_to_resolve_ticket = False

    @api.depends('bci_case_type', 'bci_case_sub_type', 'bci_problem_type', 'ticket_type_id', 'bci_warranty_status')
    def compute_chargeable(self):
        for record in self:
            if record.bci_case_type or record.bci_case_sub_type or record.bci_problem_type or record.ticket_type_id or record.bci_warranty_status:
                domain = [('name', '=', record.bci_case_type.id), ('bci_case_sub_type', '=', record.bci_case_sub_type.id), ('bci_problem_type', '=', record.bci_problem_type.id), ('bci_problem_sub_type', '=', record.ticket_type_id.id), ('bci_warranty_status', '=', record.bci_warranty_status)]
                chargeable = self.env['barcode_india.chargeable'].search(domain, limit=1)
                record.bci_chargeable = chargeable.bci_chargeable if chargeable else False

    @api.depends('bci_site.phone')
    def _compute_site_phone(self):
        for record in self:
            if record.bci_site:
                record.bci_site_phone = record.bci_site.phone

    # def _inverse_site_phone(self):
    #     for record in self:
    #         if record._get_site_phone_update():
    #             record.bci_site.phone = record.bci_site_phone

    # def _get_site_phone_update(self):
    #     self.ensure_one()
    #     if self.bci_site and self.bci_site_phone != self.bci_site.phone:
    #         ticket_phone_formatted = self.bci_site_phone or False
    #         site_phone_formatted = self.bci_site.phone or False
    #         return ticket_phone_formatted != site_phone_formatted
    #     return False

    @api.onchange('bci_rma')
    def onchange_bci_rma(self):
        for record in self:
            if not record.bci_rma:
                record.bci_complete_unit_rma = True
            else:
                record.bci_complete_unit_rma = False

    @api.onchange('partner_id')
    def _get_project_domain(self):
        if self.partner_id:
            return {'domain': {'bci_project': ['|', ('partner_id', '=', self.partner_id.id), ('bci_partner_ids', '=', self.partner_id.id)]}}
        else:
            return {'domain': {'bci_project': []}}

    # @api.onchange('bci_project', 'bci_project.bci_contract_ids', 'bci_site', 'bci_asset')
    # def _get_contract_domain(self):
    #     if self.bci_project and self.bci_project.bci_contract_ids:
    #         if self.bci_site:
    #             return {'domain': {'bci_contract_id': [('id', 'in', self.bci_project.bci_contract_ids.ids), '|', ('bci_site', '=', self.bci_site.id), ('bci_site_ids.name', '=', self.bci_site.id)]}}
    #         else:
    #             return {'domain': {'bci_contract_id': [('id', 'in', self.bci_project.bci_contract_ids.ids)]}}
    #     elif self.bci_asset:
    #         return {'domain': {'bci_contract_id': [('id', '=', self.bci_asset.bci_contract_id.id)]}}
    #     else:
    #         return {'domain': {'bci_contract_id': []}}

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.bci_assign_report_ids = [(0, 0, {
                'updated_by' : self.env.user,
                'previous_user': self.previous_user_id.id,
                'updated_user': self.user_id.id,
                'ticket_id': self.id,
            })]
            self.previous_user_id = self.user_id.id
        else:
            self.previous_user_id = False

    @api.onchange('bci_asset','bci_project')
    def _get_contract_domain(self):
        for record in self:
            if record.bci_asset and record.bci_barcode_case_type_find != 'custom software':
                return {'domain': {'bci_contract_id': [('id', '=', record.bci_asset.bci_contract_id.id)]}}
            elif record.bci_project and record.bci_site:
                contracts = self.env["barcode_india.contracts.details"].sudo().search([("bci_projects","=",record.bci_project.id)]).filtered(lambda x: record.bci_site.id in x.bci_site_ids.ids and record.bci_plant.id in x.bci_plants_ids.ids).mapped('bci_contracts')
                if contracts:
                    return {'domain': {'bci_contract_id': [('id', 'in', contracts.ids)]}}

    @api.onchange('bci_end','bci_oem_end_date')
    def _onchange_end_date(self):
        for record in self:
            if record.bci_end:
                today_date = date.today()
                if record.bci_barcode_case_type_find == 'hardware':
                    end_date = record.bci_oem_end_date if record.bci_oem_end_date and record.bci_oem_end_date > record.bci_end else record.bci_end
                else:
                    end_date = record.bci_end
                next_date = end_date + relativedelta(months=1)
                if end_date >= today_date:
                    record.bci_warranty_status = 'In Warranty'
                if end_date < today_date and today_date <= next_date:
                    record.bci_warranty_status = 'In Grace'
                if today_date > next_date:
                    record.bci_warranty_status = 'Out of Warranty'

    @api.onchange('bci_asset')
    def _onchange_contract_asset(self):
        for record in self:
            if record.bci_asset:
                record.partner_id = record.bci_asset.bci_customer and record.bci_asset.bci_customer.id or False
                record.bci_site = record.bci_asset.bci_site and record.bci_asset.bci_site.id or False
                record.bci_contract_id = record.bci_asset.bci_contract_id and record.bci_asset.bci_contract_id.id or False
                record.bci_start = record.bci_asset.bci_invoice_date or False
                record.bci_end = record.bci_asset.bci_end_date or False
                record.bci_oem_start_date = record.bci_asset.bci_oem_start_date or False
                record.bci_oem_end_date = record.bci_asset.bci_oem_end_date or False
                record.bci_delivery_type = record.bci_asset.bci_delivery_type or False
                record.bci_oem_contract_no = record.bci_asset.bci_oem_contract_no or False
                record.bci_complete_unit_rma = record.bci_asset.bci_product and record.bci_asset.bci_product.bci_complete_unit_rma or False
                if record.bci_asset.bci_service_product:
                    record.bci_service_product = record.bci_asset.bci_service_product.id

    
    @api.onchange('bci_contract_id')
    def _onchange_bci_contract_id(self):
        for record in self:
            record.bci_preferred_applicable = record.bci_contract_id and record.bci_contract_id.bci_preferred_applicable or False
            if record.bci_barcode_case_type_find == 'custom software':
                record.bci_start = record.bci_contract_id and record.bci_contract_id.bci_start or False
                record.bci_end = record.bci_contract_id and record.bci_contract_id.bci_end or False
                record.bci_service_product = record.bci_contract_id and record.bci_contract_id.bci_service_product.id or False


    # @api.onchange('bci_service_product')
    def _onchange_service_product(self):
        for record in self:
            record.bci_own_company = record.bci_service_product and record.bci_service_product.bci_own_company and record.bci_service_product.bci_own_company.id or False
            record.bci_oem_product_group = record.bci_service_product and record.bci_service_product.bci_oem_product_group and record.bci_service_product.bci_oem_product_group.id or False
            record.bci_warranty_amc = record.bci_service_product and record.bci_service_product.bci_warranty_amc and record.bci_service_product.bci_warranty_amc.id or False
            record.bci_coverage = record.bci_service_product and record.bci_service_product.bci_coverage and record.bci_service_product.bci_coverage.id or False
            record.bci_service_category = record.bci_service_product and record.bci_service_product.bci_service_category and record.bci_service_product.bci_service_category.id or False
            record.bci_coverage_type = record.bci_service_product and record.bci_service_product.bci_coverage_type and record.bci_service_product.bci_coverage_type.id or False
            record.bci_onsite_coverage = record.bci_service_product and record.bci_service_product.bci_onsite_coverage and record.bci_service_product.bci_onsite_coverage.id or False
            record.bci_standby_equipment = record.bci_service_product and record.bci_service_product.bci_standby_equipment and record.bci_service_product.bci_standby_equipment.id or False
            record.bci_sla = record.bci_service_product and record.bci_service_product.bci_sla and record.bci_service_product.bci_sla.id or False
            record.sla_ids = [(6,0,record.bci_sla.ids)] if record.bci_service_product and record.bci_service_product.bci_sla else False
            if record.bci_sla:
                record.sudo()._sla_apply()
    
    
    @api.depends('bci_sale_order_ids')
    def _compute_sale_order_count(self):
        for record in self:
            record.bci_sale_order_count = self.env['sale.order'].search_count([('bci_helpdesk', '=', record.id)])

    @api.onchange('bci_plant')
    def _onchange_plant(self):
        for record in self:
            record.bci_site = record.bci_plant.bci_site or False
            record.partner_id = record.bci_site.bci_company.id or False

    @api.onchange('bci_site')
    def _onchange_address(self):
        for rec in self:
            res = [rec.bci_site.street, rec.bci_site.street2,rec.bci_site.street3,rec.bci_site.street4,
                   rec.bci_site.city, rec.bci_site.state_id and rec.bci_site.state_id.name, rec.bci_site.country_id and rec.bci_site.country_id.name,
                   rec.bci_site.zip]
            self.bci_address = ', '.join(filter(bool, res))
    
    def action_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('bci_helpdesk', '=', self.id)],
        }

    def action_create_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Quotation'),
            'res_model': 'bci.create_quotation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_ticket_id': self.id,
            }
        }


    def _compute_approval_request_count(self):
        for record in self:
            record.bci_approval_request_count = self.env['approval.request'].search_count([('bci_helpdesk_ticket', '=', record.id)])


    def action_approval_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Request',
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'domain': [('bci_helpdesk_ticket', '=', self.id)],
        }

    def action_submit_for_approval(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Submit For Approval'),
            'res_model': 'barcode_india.approval_for',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_ticket_id': self.id,
            }
        }

    def escalation_creation(self):
        for ticket in self:
            if ticket.sla_ids and not ticket.bci_escalation:
                for rec in ticket.sla_ids:
                    escalation = self.env["barcode_india.escalation"].sudo().search([]).filtered(lambda x: rec.id in x.bci_sla.ids)
                    for record in escalation:
                        self.env["barcode_india.helpdesk_escalation"].create({
                            "name": record.id,
                            "bci_ticket_id": ticket.id,
                            "bci_sla": rec.id,
                        })

    @api.model_create_multi
    def create(self, list_value):
        tickets = super(Helpdesk, self).create(list_value)
        for ticket in tickets:
            ticket._onchange_contract_asset()
            ticket._onchange_end_date()
            ticket._get_project_domain()
            ticket._get_contract_domain()
            ticket.bci_stages_ids = [(0, 0, {
                'bci_ticket_id': ticket.id,
                'bci_stage': ticket.stage_id.id
            })]
            if ticket.bci_asset.bci_replaced_by:
                message = '%s Serial No. has been replaced by %s'%(ticket.bci_asset.name,ticket.bci_asset.bci_replaced_by.name)
                raise UserError(message)
        tickets.escalation_creation()
        return tickets

    def write(self, vals):
        if 'stage_id' in vals:
            new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            old_value = self.bci_stages_ids.filtered(lambda x: x.bci_stage.id == self.stage_id.id and not x.bci_to_date)
            old_value = old_value and old_value[0] or False
            if not old_value or (old_value and old_value.bci_stage.id != vals['stage_id']):
                if old_value:
                    old_value.write({'bci_to_date': fields.Datetime.now()})
                if not (new_stage.bci_hold_stage or new_stage.bci_cancelled_stage):
                    vals.setdefault('bci_stages_ids', []).append((0, 0, {
                        'bci_ticket_id': self.id,
                        'bci_stage': vals['stage_id'],
                    }))

        if 'bci_asset' in vals.keys() and vals['bci_asset']:
            assets = self.env['barcode_india.assets'].browse(vals['bci_asset'])
            if assets and assets.bci_replaced_by:
                message ='%s Serial No. has been replaced by %s'%(assets.name,assets.bci_replaced_by.name)
                raise UserError(message)
        rec =  super(Helpdesk, self).write(vals)
        if 'stage_id' in vals.keys() and (new_stage.bci_hold_stage or new_stage.bci_cancelled_stage):
            self.bci_remarks = False
        self.escalation_creation()
        return rec

    def set_escalation_due_date(self):
        for record in self:
            if record.sla_deadline and record.bci_escalation:
                for rec in record.bci_escalation:
                    duration = record.sla_deadline - record.create_date
                    rec.bci_due_datetime = record.create_date + duration * rec.name.bci_tat
    
    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
    def _compute_sla_deadline(self):
        super(Helpdesk, self)._compute_sla_deadline()
        self.set_escalation_due_date()

    def action_bci_rma_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create BCI Transfer'),
            'res_model': 'bci.rma.transfer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_ticket_id': self.id,
                'default_bci_asset': self.bci_asset.id,
                'default_bci_partner_id': self.partner_id.id
            }
        }

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': ('RMA Transfers'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('bci_source_ticket', '=', self.id), ('bci_spare_transfer', '=', False)],
            'context': dict(self._context, create=False, default_company_id=self.company_id.id)
        }

    def action_bci_spare_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Spares Transfers'),
            'res_model': 'bci.rma.transfer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_ticket_id': self.id,
                'default_bci_asset': self.bci_asset.id,
                'default_bci_partner_id': self.partner_id.id,
                'default_bci_spare_transfer': True
            }
        }

    def action_view_spare_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': ('Spares Transfers'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('bci_source_ticket', '=', self.id), ('bci_spare_transfer', '!=', False)],
            'context': dict(self._context, create=False, default_company_id=self.company_id.id)
        }

    def mail_sent_job(self, limit=20):
        today_date = datetime.now()
        escalation = self.env["barcode_india.helpdesk_escalation"].sudo().search([('bci_due_datetime','<=',today_date),('bci_status','=',False)],limit=limit)
        for record in escalation:
            if record.bci_ticket_id and record.bci_ticket_id.stage_id and record.bci_ticket_id.stage_id.name not in ['Solved','Closed','Canceled']:
                record.bci_ticket_id.bci_user_ids = [(6,0,record.name.bci_user_ids.ids)]
                record.bci_ticket_id.with_context(force_send=True).message_post_with_template(record.name.bci_email_template.id, composition_mode='mass_mail')
                record.bci_status = 'Sent'
            else:
                record.bci_status = 'Cancel'

    def _get_escalation_ids(self):
        for record in self:
            return ','.join([x.email for x in record.bci_user_ids])
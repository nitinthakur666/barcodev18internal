from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import AccessError

class Partners(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=[('site','Site')])
    street3 = fields.Char('Street 3')
    street4 = fields.Char('Street 4')
    bci_code = fields.Char("Code")
    bci_survey_id = fields.Many2one('survey.survey', string='Survey')
    bci_parent_company = fields.Many2one('res.partner', 'Parent Company')
    bci_child_company_count = fields.Integer('Child Company Count',compute="_compute_child_company_count")
    bci_child_company_ids = fields.One2many("res.partner","bci_parent_company",string="Child Companies")
    bci_pricing_terms = fields.One2many('barcode_india.customer_pt_master','partner_id',string='Pricing Term')
    bci_legacy_customer_id = fields.Char("Legacy Customer ID")
    bci_turnover = fields.Selection([("0-100 Cr","0-100 Cr"),("101-500 Cr","101-500 Cr"),("501 & Above","501 & Above")],"Turnover")
    bci_any_other_info = fields.Text("Any Other Info")
    bci_department = fields.Char("Department")
    bci_linkedin = fields.Char("Linkedin")
    # bci_account_type = fields.Selection([("High Touch","High Touch/NAL"),("UNAL","UNAL")],"Account Type")
    bci_account_type = fields.Selection([("High Touch","NAL"),("UNAL","UNAL")],"Account Type")

    bci_region_user = fields.Many2one("barcode_india.region", "Region")
    bci_vertical = fields.Many2one("barcode_india.vertical","Vertical")
    bci_sub_vertical = fields.Many2one("barcode_india.sub_vertical","Sub Vertical")
    bci_sub_vertical_category = fields.Many2one("barcode_india.sub_vertical_category","Sub Vertical Category")

    bci_group_code = fields.Many2one("barcode_india.group_code","Group Code")
    bci_tax_group = fields.Many2one("barcode_india.tax_group","Tax Group")
    bci_terms_code = fields.Many2one("barcode_india.terms_code","Terms Code")

    bci_contact_type = fields.Selection([('Parent Company','Parent Company'),('Company','Company'),('Site','Site'),('Plant','Plant')],'Contact Type')
    bci_national_account_no = fields.Char('National Account No.')
    bci_site = fields.Many2one('res.partner','Site')
    bci_site_code = fields.Char("Site Code")
    bci_company = fields.Many2one('res.partner','Site(Company)')

    bci_contract_count = fields.Integer('Contract Count', compute='_compute_contract_count')
    bci_assets_count = fields.Integer('Assets Count', compute='_compute_assets_count')
    bci_site_count = fields.Integer('Site Count', compute='_compute_site_count')
    bci_plant_count = fields.Integer('Plant Count', compute='_compute_plant_count')

    bci_legal_name = fields.Char("Company Legal Name")
    bci_outstanding_balance_exceed = fields.Float("Credit Limit")
    bci_outstanding_balance = fields.Float("Outstanding Balance (Previous Day - EOD)")

    bci_customer_type = fields.Selection([('existing', 'Existing Customers'),('new', 'New Customers')] ,string='Customer Type',default='new')
    bci_customer_category = fields.Selection([('a', 'A'),('b', 'B'),('c', 'C')], string='Customer Category',default='c')
    # bci_sopf_count = fields.Integer(string='SOPF Count', compute='_compute_sopf_count')
    bci_legacy_sopf_count = fields.Integer(string='Legacy SOPF Count', compute='_compute_legacy_sopf_count')
    bci_legacy_sopf_items_count = fields.Integer(string='Legacy SOPF Items Count', compute='_compute_legacy_sopf_items_count')

    def _compute_contract_count(self):
        for rec in self:
            rec.bci_contract_count = self.env['barcode_india.contracts'].sudo().search_count([('bci_customer', '=', rec.id)])

    def _compute_assets_count(self):
        for rec in self:
            rec.bci_assets_count = self.env['barcode_india.assets'].sudo().search_count([('bci_customer', '=', rec.id)])

    def _compute_site_count(self):
        for rec in self:
            rec.bci_site_count = self.sudo().search_count([('bci_company', '=', self.id),('bci_contact_type','=','Site'),('is_company', '!=', False)])

    def _compute_plant_count(self):
        for rec in self:
            rec.bci_plant_count = self.sudo().search_count([('bci_site', '=', self.id),('bci_contact_type','=','Plant'),('is_company', '!=', False)])
    
    def _compute_legacy_sopf_count(self):
        for rec in self:
            rec.bci_legacy_sopf_count = self.env['barcode_india.sopf_header'].sudo().search_count(['|',('sopf_legacycompanyid', '=', rec.bci_legacy_customer_id),('company_id', '=', rec.bci_code)])

    # def _compute_sopf_count(self):
    #     for rec in self:
    #         rec.bci_sopf_count = self.env['barcode_india.sopf_header'].sudo().search_count([('company_id', '=', rec.bci_code)])
    
    def _compute_legacy_sopf_items_count(self):
        for record in self:
            record.bci_legacy_sopf_items_count = self.env['barcode_india.sopf_items'].search_count(['|',('sopf_id.sopf_legacycompanyid', '=', record.bci_legacy_customer_id),('sopf_id.company_id', '=', record.bci_code)])

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': _('Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.contracts',
            'view_mode': 'list,form',
            'context': {
                'default_bci_customer': self.id,
            },
            'domain': [('bci_customer', '=', self.id)]
            }

    def action_view_assets(self):
        self.ensure_one()
        return {
            'name': _('Assets'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.assets',
            'view_mode': 'list,form',
            'context': {
                'default_bci_customer': self.id,
            },
            'domain': [('bci_customer', '=', self.id)]
            }
            
    # def action_view_sopf(self):
    #     self.ensure_one()
    #     sopf_records = self.env['barcode_india.sopf_header'].search([
    #         ('company_id', '=', self.bci_code)
    #     ])
    #     action = {
    #         'name': 'SOPF Records',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'barcode_india.sopf_header',
    #         'view_mode': 'list,form',
    #         'domain': [('id', 'in', sopf_records.ids)],
    #         'context': {'default_company_id': self.bci_code},
    #     }
    #     return action

    def action_view_legacy_sopf(self):
        self.ensure_one()
        sopf_records = self.env['barcode_india.sopf_header'].search(['|',('sopf_legacycompanyid', '=', self.bci_legacy_customer_id),('company_id', '=', self.bci_code)])
        action = {
            'name': 'Legacy SOPF Records',
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.sopf_header',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sopf_records.ids)],
            'context': {
            'default_sopf_legacycompanyid': self.bci_legacy_customer_id,
            'default_company_id': self.bci_code
            },
        }
        return action

    def action_view_legacy_sopf_items(self):
        self.ensure_one()
        sopf_items = self.env['barcode_india.sopf_items'].search(['|',('sopf_id.sopf_legacycompanyid', '=', self.bci_legacy_customer_id),('sopf_id.company_id', '=', self.bci_code)])
        action = {
            'name': 'Legacy SOPF Items',
            'type': 'ir.actions.act_window',
            'res_model': 'barcode_india.sopf_items',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sopf_items.ids)],
            'context': {
                'default_sopf_legacycompanyid': self.bci_legacy_customer_id,
                'default_company_id': self.bci_code,
            },
        }
        return action
    
    @api.onchange("bci_site")
    def onchange_bci_site(self):
        for record in self:
            record.bci_company = record.bci_site and record.bci_site.bci_company.id or False

    @api.onchange("bci_company")
    def onchange_bci_company(self): 
        for record in self:
            record.bci_parent_company = record.bci_company and record.bci_company.bci_parent_company.id or False
    
    @api.onchange("bci_parent_company")
    def onchange_parent_company(self):
        for record in self:
            record.bci_national_account_no = record.bci_parent_company and record.bci_parent_company.bci_national_account_no or False
            if record.bci_code and record.bci_parent_company:
                vals = {
                    'res_model_id': self.env.ref('base.model_res_partner').id,
                    'res_id': record.id.origin,
                    'user_id': self.env.user.id,
                    'activity_type_id': self.env.ref('barcode_india.mail_activity_data_na').id,
                    'summary': _('Please Update NA with the %s ERP Code in ERP', record.bci_code),
                    'note': _('Please Update NA with the %s ERP Code in ERP', record.bci_code)
                }
                self.env['mail.activity'].sudo().create(vals)

    # def _compute_child_company_count(self):
    #     for rec in self:
    #         rec.bci_child_company_count = self.env['res.partner'].search_count(['|',('id','child_of',self.child_ids.ids),('id', 'child_of', self.bci_child_company_ids.ids)])

    def _compute_child_company_count(self):
        for rec in self:
            rec.bci_child_company_count = self.env['res.partner'].search_count([('bci_parent_company', '=', self.id),('bci_contact_type','=','Company'),('is_company', '!=', False)])

    # def action_view_child_company(self):
    #     action = self.env['ir.actions.act_window']._for_xml_id('contacts.action_contacts')
    #     all_child = self.with_context(active_test=False).search(['|',('id','child_of',self.child_ids.ids),('id', 'child_of', self.bci_child_company_ids.ids)])
    #     action["domain"] = [("id", "in", all_child.ids)]
    #     return action

    def action_view_child_company(self):
        self.ensure_one()
        return {
            'name': _('Child Companies'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'context': {
                'default_bci_parent_company': self.id,
            },
            'domain': [('bci_parent_company', '=', self.id),('bci_contact_type','=','Company'),('is_company', '!=', False)]
            }

    def action_view_site(self):
        self.ensure_one()
        return {
            'name': _('Site'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'context': {
                'default_bci_company': self.id,
            },
            'domain': [('bci_company', '=', self.id),('bci_contact_type','=','Site'),('is_company', '!=', False)]
            }

    def action_view_plant(self):
        self.ensure_one()
        return {
            'name': _('Plant'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'context': {
                'default_bci_site': self.id,
            },
            'domain': [('bci_site', '=', self.id),('bci_contact_type','=','Plant'),('is_company', '!=', False)]
            }

    # Sales
    # def _compute_sale_order_count(self):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #     all_partners.read(['parent_id'])
    #     sale_order_groups = self.env['sale.order']._read_group(
    #         domain=expression.AND([self._get_sale_order_domain_count(), [('partner_id', 'in', all_partners.ids)]]),
    #         fields=['partner_id'], groupby=['partner_id']
    #     )
    #     partners = self.browse()
    #     for group in sale_order_groups:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             if partner in self:
    #                 partner.sale_order_count += group['partner_id_count'] + self.get_parent_partner_sales_count(partner.bci_child_company_ids)
    #                 partners |= partner
    #             partner = partner.parent_id
    #     (self - partners).sale_order_count = 0
    #
    # def get_parent_partner_sales_count(self, bci_parent_company):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', bci_parent_company.ids)])
    #     all_partners.read(['parent_id'])
    #     sale_order_groups = self.env['sale.order']._read_group(
    #         domain=expression.AND([self._get_sale_order_domain_count(), [('partner_id', 'in', all_partners.ids)]]),
    #         fields=['partner_id'], groupby=['partner_id']
    #     )
    #     sale_order_count = 0
    #     for group in sale_order_groups:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             sale_order_count += group['partner_id_count']
    #             partner = partner.parent_id
    #     return sale_order_count

    @api.depends('child_ids', 'bci_child_company_ids')
    def _compute_sale_order_count(self):
        """Compute total number of sales orders including child and bci linked companies."""
        self.sale_order_count = 0

        # Fetch all partners including descendants
        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', self.ids)], ['parent_id']
        )

        # Aggregate sale order counts by partner
        sale_order_groups = self.env['sale.order'].with_context(active_test=False)._read_group(
            domain=expression.AND([
                self._get_sale_order_domain_count(),
                [('partner_id', 'in', all_partners.ids)],
            ]),
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        self_ids = set(self._ids)
        processed_partners = self.browse()

        for partner, count in sale_order_groups:
            while partner:
                if partner.id in self_ids:
                    # Count from child companies
                    partner.sale_order_count += count
                    # Add count from linked bci child companies
                    partner.sale_order_count += self.get_parent_partner_sales_count(partner.bci_child_company_ids)
                    processed_partners |= partner
                partner = partner.parent_id

        # Set remaining partners (not matched in results) to 0
        (self - processed_partners).sale_order_count = 0

    def get_parent_partner_sales_count(self, bci_parent_companies):
        """Get sale order count for all related bci child companies."""
        if not bci_parent_companies:
            return 0

        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', bci_parent_companies.ids)], ['parent_id']
        )

        sale_order_groups = self.env['sale.order'].with_context(active_test=False)._read_group(
            domain=expression.AND([
                self._get_sale_order_domain_count(),
                [('partner_id', 'in', all_partners.ids)],
            ]),
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        total_count = 0
        for partner, count in sale_order_groups:
            while partner:
                total_count += count
                partner = partner.parent_id
        return total_count

    def action_view_sale_order(self):
        action = super(Partners, self).action_view_sale_order()
        all_child = self.with_context(active_test=False).search(['|',('id', 'child_of', self.ids),('id', 'child_of', self.bci_child_company_ids.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    # Tickets
    # def _compute_ticket_count(self):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #     all_partners.read(['parent_id'])
    #     groups = self.env['helpdesk.ticket'].read_group(
    #         [('partner_id', 'in', all_partners.ids)],
    #         fields=['partner_id'], groupby=['partner_id'],
    #     )
    #     self.ticket_count = 0
    #     for group in groups:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             if partner in self:
    #                 partner.ticket_count += group['partner_id_count'] + self.get_parent_partner_ticket_count(partner.bci_child_company_ids)
    #             partner = partner.parent_id
    #
    # def get_parent_partner_ticket_count(self, bci_parent_company):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', bci_parent_company.ids)])
    #     all_partners.read(['parent_id'])
    #     groups = self.env['helpdesk.ticket']._read_group(
    #         [('partner_id', 'in', all_partners.ids)],
    #         fields=['partner_id'], groupby=['partner_id'],
    #     )
    #     ticket_count = 0
    #     for group in groups:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             ticket_count += group['partner_id_count']
    #             partner = partner.parent_id
    #     return ticket_count

    def _compute_ticket_count(self):
        # Fetch all partners including their children
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        # Use new Odoo 18 _read_group syntax
        groups = self.env['helpdesk.ticket']._read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        # Initialize ticket_count
        self.ticket_count = 0

        # Build mapping of partner_id → ticket_count
        data_map = {partner.id: count for partner, count in groups}

        # Iterate and compute ticket count hierarchy
        for record in self:
            total = 0
            partner_ids = self.with_context(active_test=False).search([('id', 'child_of', record.id)])
            for partner in partner_ids:
                total += data_map.get(partner.id, 0)
            total += self.get_parent_partner_ticket_count(record.bci_child_company_ids)
            record.ticket_count = total

    def get_parent_partner_ticket_count(self, bci_parent_company):
        # Compute ticket count for parent companies
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', bci_parent_company.ids)])
        all_partners.read(['parent_id'])

        groups = self.env['helpdesk.ticket']._read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        # Sum all related ticket counts
        ticket_count = sum(count for partner, count in groups)
        return ticket_count

    def action_open_helpdesk_ticket(self):
        action = super(Partners, self).action_open_helpdesk_ticket()
        all_child = self.with_context(active_test=False).search(['|',('id', 'child_of', self.ids),('id', 'child_of', self.bci_child_company_ids.ids)])
        action['domain'] = [('partner_id', 'in', all_child.ids)]
        return action

    # Invoices
    def action_view_partner_invoices(self):
        action = super(Partners, self).action_view_partner_invoices()
        all_child = self.with_context(active_test=False).search(['|',('id', 'child_of', self.ids),('id', 'child_of', self.bci_child_company_ids.ids)])
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'in', all_child.ids)
        ]
        return action

    # Opportunities
    # def _compute_opportunity_count(self):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #     all_partners.read(['parent_id'])
    #     opportunity_data = self.env['crm.lead'].with_context(active_test=False)._read_group(
    #         domain=[('partner_id', 'in', all_partners.ids)],
    #         fields=['partner_id'], groupby=['partner_id']
    #     )
    #     self.opportunity_count = 0
    #     for group in opportunity_data:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             if partner in self:
    #                 partner.opportunity_count += group['partner_id_count'] + self.get_parent_partner_opportunity_count(partner.bci_child_company_ids)
    #             partner = partner.parent_id

    @api.depends('child_ids', 'bci_child_company_ids')
    def _compute_opportunity_count(self):
        """Compute total opportunities including child companies and bci_child_company links."""
        self.opportunity_count = 0
        if not self.env.user._has_group('sales_team.group_sale_salesman'):
            return

        # Retrieve all children partners and prefetch parent_id
        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', self.ids)], ['parent_id']
        )

        # Aggregate CRM opportunities grouped by partner
        opportunity_data = self.env['crm.lead'].with_context(active_test=False)._read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        self_ids = set(self._ids)

        for partner, count in opportunity_data:
            while partner:
                if partner.id in self_ids:
                    # Add count from normal children
                    partner.opportunity_count += count
                    # Add count from bci_child_company_ids
                    partner.opportunity_count += self.get_parent_partner_opportunity_count(
                        partner.bci_child_company_ids)
                partner = partner.parent_id

    def get_parent_partner_opportunity_count(self, bci_parent_companies):
        """Count opportunities for bci_child_company_ids recursively."""
        if not bci_parent_companies:
            return 0

        # Include all descendants of these companies
        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', bci_parent_companies.ids)], ['parent_id']
        )

        # Aggregate CRM leads for these related partners
        groups = self.env['crm.lead'].with_context(active_test=False)._read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )

        total_count = 0
        for partner, count in groups:
            while partner:
                total_count += count
                partner = partner.parent_id
        return total_count

    # def get_parent_partner_opportunity_count(self, bci_parent_company):
    #     all_partners = self.with_context(active_test=False).search([('id', 'child_of', bci_parent_company.ids)])
    #     all_partners.read(['parent_id'])
    #     groups = self.env['crm.lead'].with_context(active_test=False)._read_group(
    #         [('partner_id', 'in', all_partners.ids)],
    #         fields=['partner_id'], groupby=['partner_id'],
    #     )
    #     opportunity_count = 0
    #     for group in groups:
    #         partner = self.browse(group['partner_id'][0])
    #         while partner:
    #             opportunity_count += group['partner_id_count']
    #             partner = partner.parent_id
    #     return opportunity_count

    def action_view_opportunity(self):
        action = super(Partners, self).action_view_opportunity()
        all_child = self.with_context(active_test=False).search(['|',('id', 'child_of', self.ids),('id', 'child_of', self.bci_child_company_ids.ids)])
        action['domain'] = [("partner_id", "in", all_child.ids)]
        return action

    @api.model
    def default_get(self, fields):
        rec = super(Partners, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        if active_model == 'crm.lead':
            lead = self.env[active_model].browse(self.env.context.get('active_id')).exists()
            if lead:
                rec["bci_linkedin"] = lead.bci_linkedin
                rec["bci_turnover"] = lead.bci_turnover
                rec["bci_any_other_info"] = lead.bci_any_other_info
                rec["bci_department"] = lead.bci_department
                rec["bci_account_type"] = lead.bci_account_type
        return rec

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            contact_type = vals.get('bci_contact_type')
            if self.env.user.has_group('barcode_india.group_operational_contact_manager'):
                if contact_type not in ['Site', 'Plant']:
                    raise AccessError(_("Operational Contact Managers can only create Site or Plant contacts"))
            if contact_type == 'Parent Company':
                vals['bci_national_account_no'] = self.env['ir.sequence'].next_by_code('barcode_india.national_account_code')
        return super().create(vals_list)


    def write(self, vals_list):
        if self.env.context.get('skip_corporate_check'):
            return super(Partners, self).write(vals_list)
        user = self.env.user
        original_vals = dict(vals_list)
        if user.has_group('barcode_india.group_corporate_contact_manager'):
            if set(original_vals.keys()) != {'child_ids'}:
                raise AccessError(_("Corporate Contact Managers are only allowed to manage child contacts."))
        if 'bci_contact_type' in vals_list:
            if user.has_group('barcode_india.group_operational_contact_manager'):
                if vals_list['bci_contact_type'] not in ['Site', 'Plant']:
                    raise AccessError(_("Operational Contact Managers can only modify contacts to Site or Plant types"))
        new_context = dict(self.env.context, skip_corporate_check=True)
        record = super(Partners, self.with_context(new_context)).write(vals_list)
        for rec in self:
            if rec.bci_contact_type == 'Parent Company' and not rec.bci_national_account_no:
                rec.bci_national_account_no = self.env['ir.sequence'].next_by_code('barcode_india.national_account_code')
        return record

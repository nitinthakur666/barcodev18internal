from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    def action_view_sale_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent','cancel'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        # if len(quotations) == 1:
        #     action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        #     action['res_id'] = quotations.id
        return action
    
    # def action_view_sale_quotation(self):
        
    #     quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent','cancel'))
    #     rec = super(CrmLead, self).action_view_sale_quotation()
    #     rec['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent','cancel'])]
    #     # raise Exception(rec)
    #     return rec
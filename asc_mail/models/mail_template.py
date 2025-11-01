import base64
import logging

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)

class MailTemplate(models.Model):
    
    _inherit = 'mail.template'
    
    def generate_recipients(self, results, res_ids):
        """Generates the recipients of the template. Default values can ben generated
        instead of the template values if requested by template or context.
        Emails (email_to, email_cc) can be transformed into partners if requested
        in the context. """
        self.ensure_one()
        mail_partner_ids = []
        mail_cc_partner_ids = []
        records_company = None
        if self._context.get('tpl_partners_only') and self.model and results and 'company_id' in self.env[self.model]._fields:
            records = self.env[self.model].browse(results.keys()).read(['company_id'])
            records_company = {rec['id']: (rec['company_id'][0] if rec['company_id'] else None) for rec in records}

        for res_id, values in results.items():
            partner_ids = values.get('partner_ids', list())
            Partner = self.env['res.partner']
            if self._context.get('tpl_partners_only'):
                mails = tools.email_split(values.pop('email_to', ''))
                if records_company:
                    Partner = Partner.with_context(default_company_id=records_company[res_id])
                for mail in mails:
                    partner = Partner.find_or_create(mail)
                    partner_ids.append(partner.id)
            partner_to = values.pop('partner_to', '')
            if partner_to:
                # placeholders could generate '', 3, 2 due to some empty field values
                tpl_partner_ids = [int(pid) for pid in partner_to.split(',') if pid]
                partner_ids += self.env['res.partner'].sudo().browse(tpl_partner_ids).exists().ids
            mail_partner_ids.extend(partner_ids)
            
            cc_partner_ids = []
            if self._context.get('tpl_partners_only'):
                cc_mails = tools.email_split(values.pop('email_cc', ''))
                if records_company:
                    Partner = Partner.with_context(default_company_id=records_company[res_id])
                for mail in cc_mails:
                    partner = Partner.find_or_create(mail)
                    cc_partner_ids.append(partner.id)
            mail_cc_partner_ids.extend(cc_partner_ids)
        result = super().generate_recipients(results, res_ids)
        for res_id, values in results.items():
            result[res_id]['partner_ids'] = mail_partner_ids
            result[res_id]['cc_partner_ids'] = cc_partner_ids
        return result
    
    
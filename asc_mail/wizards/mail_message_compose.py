import ast
import base64
import re

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression
# from odoo.tools import email_re


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    cc_partner_ids = fields.Many2many('res.partner', relation='mail_compose_message_res_cc_partner_rel', string='CC')
    bcc_partner_ids = fields.Many2many('res.partner', relation='mail_compose_message_res_bcc_partner_rel', string='BCC')   

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message, transform email_cc and email_to into partner_ids """
        multi_mode = True
        if isinstance(res_ids, int):
            multi_mode = False
            res_ids = [res_ids]

        returned_fields = fields + ['partner_ids', 'attachments']
        values = dict.fromkeys(res_ids, False)

        template_values = self.env['mail.template'].with_context(tpl_partners_only=True).browse(template_id).generate_email(res_ids, fields)
        returned_fields += ['cc_partner_ids']
        for res_id in res_ids:
            res_id_values = dict((field, template_values[res_id][field]) for field in returned_fields if template_values[res_id].get(field))
            res_id_values['body'] = res_id_values.pop('body_html', '')
            values[res_id] = res_id_values
            
        return multi_mode and values or values[res_ids[0]]
    
    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails. """
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        rendered_values = {}
        mass_mail_mode = self.composition_mode == 'mass_mail'

        # render all template-based value at once
        if mass_mail_mode and self.model:
            rendered_values = self.render_message(res_ids)
        # compute alias-based reply-to in batch
        reply_to_value = dict.fromkeys(res_ids, None)
        if mass_mail_mode and not self.reply_to_force_new:
            records = self.env[self.model].browse(res_ids)
            reply_to_value = records._notify_get_reply_to(default=False)
            # when having no specific reply-to, fetch rendered email_from value
            for res_id, reply_to in reply_to_value.items():
                if not reply_to:
                    reply_to_value[res_id] = rendered_values.get(res_id, {}).get('email_from', False)

        for res_id in res_ids:
            # static wizard (mail.message) values
            mail_values = {
                'subject': self.subject,
                'body': self.body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [partner.id for partner in self.partner_ids],
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'author_id': self.author_id.id,
                'email_from': self.email_from,
                'record_name': self.record_name,
                'reply_to_force_new': self.reply_to_force_new,
                'mail_server_id': self.mail_server_id.id,
                'mail_activity_type_id': self.mail_activity_type_id.id,
                'message_type': 'email' if mass_mail_mode else self.message_type,
            }
            if not mass_mail_mode:
                mail_values.update({
                    'cc_partner_ids': [partner.id for partner in self.cc_partner_ids],
                    'bcc_partner_ids' : [partner.id for partner in self.bcc_partner_ids]
                 })
            else:
                mail_values.update({
                    'email_bcc': ', '.join(self.bcc_partner_ids.mapped('email_formatted')),
                    'email_cc': ', '.join(self.cc_partner_ids.mapped('email_formatted'))
                })

            # mass mailing: rendering override wizard static values
            if mass_mail_mode and self.model:
                record = self.env[self.model].browse(res_id)
                mail_values['headers'] = repr(record._notify_by_email_get_headers())
                # keep a copy unless specifically requested, reset record name (avoid browsing records)
                mail_values.update(is_notification=not self.auto_delete_message, model=self.model, res_id=res_id, record_name=False)
                # auto deletion of mail_mail
                if self.auto_delete or self.template_id.auto_delete:
                    mail_values['auto_delete'] = True
                # rendered values using template
                email_dict = rendered_values[res_id]
                mail_values['partner_ids'] += email_dict.pop('partner_ids', [])
                mail_values.update(email_dict)
                if not self.reply_to_force_new:
                    mail_values.pop('reply_to')
                    if reply_to_value.get(res_id):
                        mail_values['reply_to'] = reply_to_value[res_id]
                if self.reply_to_force_new and not mail_values.get('reply_to'):
                    mail_values['reply_to'] = mail_values['email_from']
                # mail_mail values: body -> body_html, partner_ids -> recipient_ids
                mail_values['body_html'] = mail_values.get('body', '')
                mail_values['recipient_ids'] = [Command.link(id) for id in mail_values.pop('partner_ids', [])]

                # process attachments: should not be encoded before being processed by message_post / mail_mail create
                mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in email_dict.pop('attachments', list())]
                attachment_ids = []
                for attach_id in mail_values.pop('attachment_ids'):
                    new_attach_id = self.env['ir.attachment'].browse(attach_id).copy({'res_model': self._name, 'res_id': self.id})
                    attachment_ids.append(new_attach_id.id)
                attachment_ids.reverse()
                mail_values['attachment_ids'] = self.env['mail.thread'].with_context(attached_to=record)._message_post_process_attachments(
                    mail_values.pop('attachments', []),
                    attachment_ids,
                    {'model': 'mail.message', 'res_id': 0}
                )['attachment_ids']

            results[res_id] = mail_values

        results = self._process_state(results)
        return results
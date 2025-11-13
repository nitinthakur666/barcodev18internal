from odoo import models, fields


class MailMessage(models.Model):
    _inherit = 'mail.message'
 
    cc_partner_ids = fields.Many2many('res.partner', relation='mail_message_res_cc_partner_rel', string='CC')
    bcc_partner_ids = fields.Many2many('res.partner', relation='mail_message_res_bcc_partner_rel', string='BCC')   
 
    
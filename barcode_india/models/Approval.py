from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    
    bci_sale_order_id = fields.Many2one('sale.order','Quotation')
    bci_sale_partner_id = fields.Many2one(related='bci_sale_order_id.partner_id',string='Customer')
    bci_helpdesk_ticket = fields.Many2one('helpdesk.ticket','Helpdesk Ticket')
    bci_approval_for = fields.Selection([('Remote Support','Remote Support'),('Field Service and Remote Support','Field Service and Remote Support'),('Complete Process','Complete Process')],'Approval For')
    bci_payment_terms = fields.One2many(related='bci_sale_order_id.bci_payment_terms', string='Payment Terms', readonly=True)
    bci_deal_margin = fields.Float(related='bci_sale_order_id.bci_deal_margin', string='Deal Margin(%)', readonly=True)
    # recommender_request_id = fields.Many2one('approval.request', string='Recommender Request')

    # def can_approve(self):
    #     return self.recommender_request_id and self.recommender_request_id.request_status == 'approved'

    # def action_approve(self):
    #     if self.recommender_request_id and self._name == 'approval.request' and not self.can_approve():
    #         if self._name == 'approval.request':
    #             raise UserError("Cannot approve the request until the Recommender request is approved.")

    #     return super(ApprovalRequest, self).action_approve()


    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        rec = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.request_status == 'approved':         
                if request.category_id.approval_type == 'Payment Term Approval' and request.bci_sale_order_id:
                    request.bci_sale_order_id.bci_pt_approval = 'approved'
                if request.category_id.approval_type == 'Margin Approval' and request.bci_sale_order_id:
                    request.bci_sale_order_id.bci_margin_approval = 'approved'
                if request.category_id.approval_type == 'Special Approval' and request.bci_sale_order_id:
                    request.bci_sale_order_id.bci_special_approval = 'approved'
                if request.category_id.approval_type in ['Remote Support','Field Service and Remote Support','Complete Process'] and request.bci_helpdesk_ticket:
                    request.bci_helpdesk_ticket.bci_is_approved = True
        return rec

    def action_view_cost_sheet(self):
        self.ensure_one()
        bci_user_role = fields.Selection([('guest','Guest'),('pre_sales','Pre Sales'),('sale_person','Sale Person'),('category_head','Category Head'),('management','Management')],compute='_compute_user_role',string='Roles')
        view_record = self.env['barcode_india.view_master'].sudo().search([('bci_role','=',bci_user_role),('bci_stage','=',bci_user_role)],limit=1) or False
        if view_record and view_record.bci_view.id:
            tree_view_id = view_record.bci_view.id
        else:
            tree_view_id = self.env.ref('barcode_india.barcode_india_order_line_tree_view_second').id
        return {
            'name': _('Cost Sheet'),
            'res_model': 'sale.order.line',
            'view_mode': 'list',
            'view_id':tree_view_id,
            'context': {'default_order_id': self.bci_sale_order_id.id, 'search_default_bci_pricing_category':1},
            'domain': [('order_id', '=', self.bci_sale_order_id.id)],
            'target': 'current',
            'type': 'ir.actions.act_window'
        }

    def action_approve(self, approver=None):
        self._ensure_can_approve()
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        if approver:
            approver.write({'status': 'approved'})
            self.sudo()._update_next_approvers('pending', approver, only_next_approver=True)
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
            approval_template = self.env.ref('barcode_india.bci_approved_template_', raise_if_not_found=False)
            requester_email = self.request_owner_id.partner_id.email
            if approval_template and requester_email:
                approval_template.send_mail(self.id, email_values={'email_to': requester_email}, force_send=False)
                self.message_post(body=f"Sent approval confirmation email to {self.request_owner_id.partner_id.name}")
        return True

    def action_refuse(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        if approver:
            approver.write({'status': 'refused'})
            self.sudo()._update_next_approvers('refused', approver, only_next_approver=False, cancel_activities=True)
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
            refusal_template = self.env.ref('barcode_india.bci_approval_refuse_template', raise_if_not_found=False)
            requester_email = self.request_owner_id.partner_id.email
            if refusal_template and requester_email:
                refusal_template.send_mail(self.id, email_values={'email_to': requester_email}, force_send=False)
                self.message_post(
                    body=f"Approval request refused by {self.env.user.name}. Notification sent to {self.request_owner_id.partner_id.name}"
                )
        return True


    def action_cancel(self):
        self.mapped('approver_ids').write({'status': 'cancel'})
        self.sudo()._update_next_approvers('cancel', self.approver_ids, only_next_approver=False, cancel_activities=True)
        activities = self.sudo()._get_user_approval_activities(user=self.env.user)
        if activities:
            activities.action_feedback()
        cancel_template = self.env.ref('barcode_india.bci_approval_cancel_template', raise_if_not_found=False)
        requester_email = self.request_owner_id.partner_id.email
        if cancel_template and requester_email:
            cancel_template.send_mail(self.id, email_values={'email_to': requester_email}, force_send=False)
        self.message_post(body=f"Approval request cancelled by {self.env.user.name}")
        purchases = getattr(self, 'product_line_ids', False) and self.product_line_ids.purchase_order_line_id.order_id
        if purchases:
            for purchase in purchases:
                product_lines = self.product_line_ids.filtered(lambda line: line.purchase_order_line_id.order_id.id == purchase.id)
                purchase._activity_schedule_with_view(
                    'mail.mail_activity_data_warning',
                    views_or_xmlid='barcode_india.exception_approval_request_canceled',
                    user_id=self.env.user.id,
                    render_context={'approval_requests': self, 'product_lines': product_lines}
                )
        return True
        
    def action_withdraw(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        if approver:
            approver.write({'status': 'pending'})
            self.sudo()._update_next_approvers('waiting', approver, only_next_approver=False, cancel_activities=True)
            withdrawal_template = self.env.ref('barcode_india.bci_approval_withdraw_template', raise_if_not_found=False)
            requester_email = self.request_owner_id.partner_id.email
            if withdrawal_template and requester_email:
                withdrawal_template.send_mail(self.id, email_values={'email_to': requester_email}, force_send=False)
            self.message_post(body=f"Approval request withdrawn by {self.env.user.name}. Request has been reset to pending state.")
            domain = [('res_model', '=', self._name), ('res_id', '=', self.id), ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id)]
            self.env['mail.activity'].search(domain).unlink()
            next_approvers = self.approver_ids.filtered(lambda a: a.status == 'pending')
            for approver in next_approvers:
                if approver.user_id:
                    self.activity_schedule('mail.mail_activity_data_todo', user_id=approver.user_id.id, note=_('Approval request requires your attention.'))
        return True

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'
    
    bci_is_pt_approval = fields.Boolean('PT Approval Category')
    bci_is_margin_approval = fields.Boolean('Margin Approval Category')
    bci_is_special_approval = fields.Boolean('Special Approval')
    approval_type = fields.Selection(selection_add=[('Remote Support','Remote Support'),('Field Service and Remote Support','Field Service and Remote Support'),('Complete Process','Complete Process'),('Payment Term Approval','Payment Term Approval'),('Margin Approval','Margin Approval'),('Special Approval','Special Approval')])

    @api.constrains('approval_type',)
    def _check_approval_type(self):
        for rec in self:
            if rec.approval_type in ['Remote Support','Field Service and Remote Support','Complete Process','Payment Term Approval','Margin Approval']:
                already_exist = self.sudo().search([("approval_type","=", rec.approval_type),('id','!=',rec.id)])
                if already_exist:
                    raise ValidationError(_("The %s Category already Exists!"%(rec.approval_type)))



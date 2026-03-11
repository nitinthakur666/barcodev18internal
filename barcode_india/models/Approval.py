from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    
    bci_sale_order_id = fields.Many2one('sale.order','Quotation')
    bci_sale_partner_id = fields.Many2one(related='bci_sale_order_id.partner_id',string='Customer')
    bci_helpdesk_ticket = fields.Many2one('helpdesk.ticket','Helpdesk Ticket')
    bci_approval_for = fields.Selection([('Remote Support','Remote Support'),('Field Service and Remote Support','Field Service and Remote Support'),('Complete Process','Complete Process')],'Approval For')

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



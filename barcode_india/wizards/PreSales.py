from odoo import fields, models, _

class PreSales(models.TransientModel):
    _name = 'bci.pre_sales'
    _description = 'Pre Sales'
    
    bci_user = fields.Many2one('res.users',string="User" , domain=lambda self: [("groups_id", "=", self.env.ref( "barcode_india.group_barcode_india_pre_sales").id)] )
    lead_id = fields.Many2one('crm.lead','Lead')
   
    def action_confirm(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.lead_id.bci_pre_sales = record.bci_user
            
            project = self.env['ir.config_parameter'].sudo().get_param('bci.project')
            if record.bci_user:
                task_data = {
                    'name': "New Task",
                    'project_id': int(project),
                    'planned_hours': 1.0, 
                    'description': "Task description goes here",
                    'partner_id': record.lead_id.partner_id.id,
                    'lead_id': record.lead_id.id,
                }
                new_task = self.env['project.task'].sudo().create(task_data)
                record.lead_id.message_post(body= "New Task Created is id = " + str(new_task.id))

            mail_template = self.env.ref('barcode_india.bci_pre_sale_template')
            if mail_template:
                mail_template.write({
                    'email_to': record.bci_user.email,
                    'email_from': record.lead_id.company_id.email,
                })
                mail_template.send_mail(record.id, force_send=True)
                record.lead_id.message_post(body= record.bci_user.name + " assigned to the opportunity as pre-sales. ")
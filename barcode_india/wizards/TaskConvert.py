from odoo import api, fields, models, _

class HelpdeskTicketConvertWizard(models.TransientModel):
    _inherit = 'helpdesk.ticket.convert.wizard'

    def action_convert(self):
        tickets_to_convert = self._get_tickets_to_convert()

        created_tasks = self.env['project.task'].with_context(mail_create_nolog=True).create(
            [self._get_task_values(ticket) for ticket in tickets_to_convert]
        )

        for ticket, task in zip(tickets_to_convert, created_tasks):
            # ticket.active = False

            ticket_sudo, task_sudo = ticket.sudo(), task.sudo()
            ticket_sudo.message_post(body=_("Ticket converted into task %s", task_sudo._get_html_link()))
            task_sudo.message_post_with_view(
                'mail.message_origin_link',
                values={'self': task_sudo, 'origin': ticket_sudo},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
            )

        if len(created_tasks) == 1:
            return {
                'view_mode': 'form',
                'res_model': 'project.task',
                'res_id': created_tasks[0].id,
                'views': [(self.env.ref('project.view_task_form2').id, 'form')],
                'type': 'ir.actions.act_window',
            }
        return {
            'name': _('Converted Tasks'),
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'views': [(self.env.ref('project.view_task_tree2').id, 'list'), (self.env.ref('project.view_task_form2').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', created_tasks.ids)],
        }
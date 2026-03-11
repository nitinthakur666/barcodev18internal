from odoo import api, models
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"


    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):

        if self.env.context.get("restrict_to_hierarchy"):
            hierarchy_domain = self._domain_my_customers()
            domain = expression.AND([domain, hierarchy_domain])

        return super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('restrict_to_hierarchy'):
            res['user_id'] = self.env.user.id
            res['customer_rank'] = 1
        return res

    @api.model
    def _domain_my_customers(self):
        user = self.env.user

        allowed_user_ids = {user.id}

        emp = self.env["hr.employee"].sudo().search([("user_id", "=", user.id)], limit=1)
        if emp:
            sub_emps = self.env["hr.employee"].sudo().search([
                ("id", "child_of", emp.id),
                ("id", "!=", emp.id),
            ])
            sub_users = sub_emps.mapped("user_id").filtered(lambda u: u)

            allowed_user_ids.update(sub_users.ids)

        return [("user_id", "in", list(allowed_user_ids))]
    

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
        active_test=True,
    ):
        if self.env.context.get("restrict_to_hierarchy"):
            dom = self._domain_my_customers()
            args = expression.AND([args, dom])

        return super()._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
            active_test=active_test,
        )

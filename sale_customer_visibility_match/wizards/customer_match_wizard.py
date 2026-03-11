from odoo import _, fields, models, api
from odoo.exceptions import UserError
from odoo.osv import expression
from markupsafe import Markup, escape


class CustomerMatchWizard(models.TransientModel):
    _name = "customer.match.wizard"
    _description = "Match Customer Wizard"

    name = fields.Char(string="Name")
    phone = fields.Char(string="Phone")
    vat = fields.Char(string="GST No")
    line_ids = fields.One2many(
        "customer.match.wizard.line",
        "wizard_id",
        string="Results",
        readonly=True,
    )

    results_html = fields.Html(string="Results", compute="_compute_results_html", sanitize=True)

    @api.depends("line_ids.partner_name", "line_ids.vat", "line_ids.salesperson", "line_ids.state")
    def _compute_results_html(self):
        for wiz in self:
            rows = []
            for line in wiz.line_ids:
                rows.append(
                    f"<tr>"
                    f"<td>{escape(line.partner_name or '')}</td>"
                    f"<td>{escape(line.vat or '')}</td>"
                    f"<td>{escape(line.salesperson or '')}</td>"
                    f"<td>{escape(line.state or '')}</td>"
                    f"</tr>"
                )

            table = (
                "<div style='max-height:320px; overflow:auto; border:1px solid #ddd; border-radius:6px;'>"
                "<table class='table table-sm table-hover mb-0' style='width:100%; border-collapse:separate; border-spacing:0;'>"
                "<thead>"
                "<tr>"
                "<th style='position:sticky; top:0; background:#fff; z-index:2; border-bottom:1px solid #ddd;'>Name</th>"
                "<th style='position:sticky; top:0; background:#fff; z-index:2; border-bottom:1px solid #ddd;'>GST No</th>"
                "<th style='position:sticky; top:0; background:#fff; z-index:2; border-bottom:1px solid #ddd;'>Salesperson</th>"
                "<th style='position:sticky; top:0; background:#fff; z-index:2; border-bottom:1px solid #ddd;'>State</th>"
                "</tr>"
                "</thead>"
                "<tbody>"
                + ("".join(rows) if rows else "")
                + "</tbody></table></div>"
            )
            wiz.results_html = Markup(table)

    def action_search(self):
        self.ensure_one()

        if not (self.name or self.phone or self.vat):
            raise UserError(_("Please enter at least one search parameter."))

        parts = []
        name = (self.name or "").strip()
        phone = (self.phone or "").strip()
        vat = (self.vat or "").strip()

        if name:
            parts.append([("name", "ilike", name)])

        if phone:
            parts.append(expression.OR([[("phone", "ilike", phone)], [("mobile", "ilike", phone)]]))

        if vat:
            parts.append([("vat", "ilike", vat)])

        final_domain = expression.AND(parts)

        partners = self.env["res.partner"].sudo().search(final_domain, limit=100)

        self.line_ids.unlink()

        vals = []
        for partner in partners:
            vals.append((0, 0, {
                "partner_name": partner.name or "",
                "vat": partner.vat or "",
                "salesperson": partner.user_id.display_name or "",
                "state": partner.state_id.display_name if partner.state_id else "",
            }))

        self.write({"line_ids": vals})

        return None


class CustomerMatchWizardLine(models.TransientModel):
    _name = "customer.match.wizard.line"
    _description = "Match Customer Wizard Result Line"
    _order = "partner_name asc, id asc"

    wizard_id = fields.Many2one("customer.match.wizard", required=True, ondelete="cascade")

    partner_name = fields.Char(string="Name", readonly=True)
    vat = fields.Char(string="GST No", readonly=True)
    salesperson = fields.Char(string="Salesperson", readonly=True)
    state = fields.Char(string="State", readonly=True)

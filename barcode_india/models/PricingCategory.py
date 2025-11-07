from odoo import fields, models, api, _


class PricingCategory(models.Model):
    _name = 'barcode_india.pricing_category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Model for defining pricing Category'
    
    name = fields.Char('Category', tracking=1) 
    approver = fields.Many2one('res.users','Category Approver', tracking=1)
    pricing_provider = fields.Many2many('res.users','barcode_india_pricing_provider_rel',string='Pricing Provider',tracking=1)
    bci_pt_master_ids = fields.One2many("barcode_india.pt_master","bci_pricingcategory_id","Default Payment Terms", tracking=1)

    @api.model
    def create(self, vals):
        res = super(PricingCategory, self).create(vals)
        res.track_changes(vals)
        return res
    
    def write(self, vals):
        self.track_changes(vals)                
        res = super(PricingCategory, self).write(vals)
        return res

    def get_many2many_value(self, record, value, field):
        result = self.env[record._fields[field].comodel_name].browse(value[0][2])
        return result and result.mapped('name') or ''

    def track_changes(self, values):
        msg = "<ul>"
        for key in values.keys():
            if key in ['pricing_provider']:
                string=self._fields[key].string
                old_value = self[key] or ''
                new_value = values[key] or ''
                if self._fields[key].type == 'many2many':
                    old_value = old_value and old_value.mapped('name') or ''
                    new_value = self.get_many2many_value(self, new_value, key)
                msg += "<li>" + _(
                    "%(string)s: %(old_value)s -> %(new_value)s",
                    string=string,
                    old_value=old_value,
                    new_value=new_value
                ) + "</li>"
        msg += "</ul>"
        self.message_post(body=msg)
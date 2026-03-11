from odoo import models, _


class TrackMixin(models.AbstractModel):
    _name = 'barcode_india.track_mixin'
    _description = 'Track Mixin'

    def get_selection_value(self, record, value, field):
        selections = record.fields_get([field])[field]['selection']
        result = [selection[1] for selection in selections if value in selection]
        return result and result[0] or None

    def get_many2one_value(self, record, value, field):
        result = self.env[record._fields[field].comodel_name].browse(value)
        return result and result.name or None

    def get_many2many_value(self, record, value, field):
        result = self.env[record._fields[field].comodel_name].browse(value[0][2])
        return result and result.mapped('name') or None

    def track_changes(self, parent, values):
        if isinstance(values, list):
            if values:
                values = values[0]
            else:
                return

        if not isinstance(values, dict):
            return

        header = _("<span class='text-muted fw-bold'> %s </span><span class='fst-italic text-muted'> (%s) </span>", self._description, self.display_name)
        message = header + "<ul>"
        for key in values.keys():
            if key not in self._fields:
                continue

            if self._fields[key].comodel_name != parent._name:
                string = self._fields[key].string
                old_value = self[key] or None
                new_value = values[key] or None
                if self._fields[key].type == 'selection':
                    old_value = self.get_selection_value(self, old_value, key)
                    new_value = self.get_selection_value(self, new_value, key)
                elif self._fields[key].type == 'many2one':
                    old_value = old_value and old_value.name or None
                    new_value = self.get_many2one_value(self, new_value, key)
                elif self._fields[key].type == 'many2many':
                    old_value = old_value and old_value.mapped('name') or None
                    new_value = self.get_many2many_value(self, new_value, key)
                if old_value == new_value:
                    old_value = None
                if old_value or new_value:
                    message_line = _("<span class='text-muted fw-bold'> %s </span><i class='fa fa-long-arrow-right'/><span class='fw-bold text-info'> %s </span><span class='fst-italic text-muted'> (%s) </span>", old_value, new_value, string)
                    message += "<li>" + message_line + "</li>"
        message += "</ul>"
        parent.message_post(body=message)

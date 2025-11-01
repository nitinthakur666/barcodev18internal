from odoo import fields, models,api,_
from odoo.exceptions import UserError


class ReturnPicking(models.Model):
    _inherit = "stock.picking"

    bci_source_ticket = fields.Many2one("helpdesk.ticket",string="Source Ticket", ondelete="cascade")
    bci_product = fields.Many2one("product.product",string="Product")
    bci_spare_transfer = fields.Boolean(string="Spares Transfer")
    bci_moves_to_copy = fields.Boolean(string="Moves Copied",compute="_compute_moves_to_copy")
    bci_for_repair_at_bci = fields.Boolean(string="For Repair at BCI")
    bci_oem = fields.Many2one('barcode_india.oem',string="OEM")

    def _get_similar_transfers(self, record):
        return self.sudo().search([('id','!=',record.id),('bci_source_ticket','=',record.bci_source_ticket.id),('bci_spare_transfer','=',record.bci_spare_transfer),('state','=','draft'),('move_ids','=',False)])

    def _compute_moves_to_copy(self):
        for record in self:
            transfers = self._get_similar_transfers(record)
            if transfers and self.bci_spare_transfer and self._get_move_ids_without_package():
                record.bci_moves_to_copy = True
            else:
                record.bci_moves_to_copy = False

    def action_copy_moves(self):
        self.ensure_one()
        moves = self._get_move_ids_without_package()
        transfers = self._get_similar_transfers(self)
        if moves and transfers:
            for transfer in transfers:
                for move in moves:
                    move.copy({'picking_id': transfer.id})

    def action_change_asset(self):
        self.ensure_one()
        lot_id = self.move_line_ids.mapped('lot_id')
        if len(lot_id) != 1:
            raise UserError("Multiple / No Serial Numbers found on the Transfer!")
        return {
            'type': 'ir.actions.act_window',
            'name': _('Change Asset'),
            'res_model': 'bci.change_asset',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bci_current_lot_id': lot_id.id,
                'default_bci_stock_picking_id':self.id
            }
        }

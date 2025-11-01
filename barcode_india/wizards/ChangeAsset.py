from odoo import fields, models, _
from odoo.exceptions import UserError

class ChangeAsset(models.TransientModel):
    _name = 'bci.change_asset'
    _description = 'Change Asset'

    bci_current_lot_id = fields.Many2one("stock.lot","Current Serial Number")
    bci_new_asset = fields.Char("New Asset")
    bci_stock_picking_id = fields.Many2one("stock.picking","Stock Picking Id")


    def action_confirm(self):
        for record in self:
            asset_model = self.env["barcode_india.assets"].sudo()
            current_asset = asset_model.search([('bci_lot','=',record.bci_current_lot_id.id)])
            new_asset = asset_model.search([('name','=',record.bci_new_asset)])
            assets_stage = self.env["barcode_india.assets.stage"].sudo().search([('type','=','replaced')],limit=1)
            if new_asset:
                raise UserError("New Asset already exist. Change the Asset manually on the Operations.")
            if not assets_stage:
                raise UserError("Please create Replaced Stage in the Assets.")
            new_asset = current_asset.copy({
                'name': record.bci_new_asset,
                'bci_lot': False
            })
            new_lot_id = new_asset.action_get_serial_number()
            current_asset.write({'bci_stage_id':assets_stage.id,
                                 'bci_replaced_by':new_asset.id})
            picking_lines = record.bci_stock_picking_id.bci_source_ticket.mapped('bci_orders_picking_ids').filtered(lambda x:not x.bci_spare_transfer and x.state != 'done').mapped('move_line_ids').filtered(lambda x:x.lot_id.id == record.bci_current_lot_id.id)
            for line in picking_lines:
                line.write({'lot_id': new_lot_id.id})

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class RMATransfer(models.TransientModel):
    _name = 'bci.rma.transfer'
    _description = 'RMA Transfer'

    bci_asset = fields.Many2one('barcode_india.assets',string="Assets")
    bci_partner_id = fields.Many2one('res.partner',string="Customer")
    bci_ticket_id = fields.Many2one('helpdesk.ticket')
    bci_pickup_type_id = fields.Many2one('barcode_india.rma_masters','Picking Type')
    bci_receive_at_bci = fields.Boolean(related='bci_pickup_type_id.bci_receive_at_bci',string="Receive at BCI Location")
    bci_receive_at_engineer = fields.Boolean(related='bci_pickup_type_id.bci_receive_at_engineer',string="Receive at Engineer Location")
    bci_receive_at_defective = fields.Boolean(related='bci_pickup_type_id.bci_receive_at_defective',string="Receive at Defective Location")
    bci_oem_involved = fields.Boolean(related='bci_pickup_type_id.bci_oem_involved',string="OEM Involved")
    bci_location_id = fields.Many2one('stock.location',string='BCI Location')
    bci_oem_location_id = fields.Many2one('stock.location',string='OEM Location')
    bci_spare_transfer = fields.Boolean(string='Spares Transfer')
    bci_engineer_location = fields.Many2one('stock.location',string="Engineer location")
    bci_defective_location = fields.Many2one('stock.location',string="Defective location")
    bci_oem = fields.Many2one('barcode_india.oem',string="OEM")
    



    def action_confirm(self):
        self.ensure_one()
        lot = self.bci_asset.action_get_serial_number()
        if not lot:
            raise ValidationError(_('Lot/Serial Number not generated on the Asset!'))
        for opr in sorted(self.bci_pickup_type_id.mapped('bci_operation_types'), key=lambda x:x.sequence):
            location_id = opr.name.default_location_src_id
            location_dest_id = opr.name.default_location_dest_id
            if opr.name.default_location_src_id.usage == 'internal':
                if opr.name.default_location_src_id.bci_defective_location:
                    location_id = self.bci_defective_location
                elif opr.name.default_location_src_id.bci_engineer_location:
                    location_id = self.bci_engineer_location
                else:
                    location_id = self.bci_location_id
            elif opr.name.default_location_src_id.usage == 'supplier':
                location_id = self.bci_oem_location_id
            if opr.name.default_location_dest_id.usage == 'internal':
                if opr.name.default_location_dest_id.bci_defective_location:
                    location_dest_id = self.bci_defective_location
                elif opr.name.default_location_dest_id.bci_engineer_location:
                    location_dest_id = self.bci_engineer_location
                else:
                    location_dest_id = self.bci_location_id
            elif opr.name.default_location_dest_id.usage == 'supplier':
                location_dest_id = self.bci_oem_location_id
            picking_values = {
                'bci_source_ticket': self.bci_ticket_id.id,
                'picking_type_id': opr.name.id,
                'partner_id': self.bci_partner_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'bci_oem': self.bci_oem.id
            }
            if self.bci_spare_transfer:
                picking_values['bci_spare_transfer'] = self.bci_spare_transfer
                picking_values['bci_product'] = self.bci_spare_transfer and self.bci_asset.bci_product.id
            else:
                picking_values['move_line_ids'] = [(0, 0, {
                    'product_id': self.bci_asset.bci_product.id,
                    'qty_done': 1,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'company_id': self.env.company.id,
                    'lot_id': lot.id,
                })]
            self.bci_ticket_id.bci_orders_picking_ids = [(0, 0, picking_values)]
            if not self.bci_spare_transfer:
                self.bci_ticket_id.write({'bci_pickup_type_id':self.bci_pickup_type_id.id})

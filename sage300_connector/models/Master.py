from odoo import models, fields, api

class InvoiceSync(models.Model):
    _name = 'sage300_connector.invoice_sync'
    _description = 'Invoice Sync'

    s3_invoice_no = fields.Char('Invoice No.')
    s3_sopf_ref = fields.Char('SOPF Ref.')
    s3_invoice_date = fields.Date('Invoice Date')
    s3_amount = fields.Float('Amount')
    s3_document = fields.Binary('Document')
    s3_document_filename = fields.Char("Document Filename")
    s3_sale_order = fields.Many2one('sale.order','Sale Order')
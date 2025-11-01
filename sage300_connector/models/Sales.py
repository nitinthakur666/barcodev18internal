# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
from requests.auth import HTTPBasicAuth
import requests
from datetime import datetime, date

class SaleSyncLogs(models.Model):
    _name = 'sage300_connector.sale_logs'
    _description = "Sales Sync Logs"
    _order = 'id desc'
    
    name = fields.Char("Message")
    message = fields.Char("Description")
    ref = fields.Char("References")
    active = fields.Boolean("Active", default=True)
    request = fields.Text("Request")

    def _log_error(self, short_message, message, ref, request=''):
        self.sudo().create({
            'name': short_message,
            'message': message,
            'ref': ref,
            'request': request
        })
    
    
    def _so_get_process_logs(self):
        return self.env.ref("sage300_connector.action_sale_sync_logs").read()[0]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_state = fields.Selection([('pending','Pending'),('fail','Failed'),('done','Done'),('split','Split')],string="Push To erp",default='pending',copy=False)
    invoice_state = fields.Selection([('pending','Pending'),('sale','sale'),('done','Done')],string="Invoice status",default='pending')
    so_invoice_sync = fields.One2many("sage300_connector.invoice_sync", "s3_sale_order", "Invoice Sync")
    so_invoice_count = fields.Integer("invoice Count", compute="_compute_invoice_count")
    so_invoice_total = fields.Monetary("Total Invoiced Amount", compute="compute_invoice_total")
    so_outstandig_amount = fields.Monetary("Outstanding Invoice Amount", compute="compute_invoice_total")

    @api.depends("so_invoice_sync","amount_untaxed")
    def compute_invoice_total(self):
        for record in self:
            if record.so_invoice_sync:
                record.so_invoice_total = sum(record.so_invoice_sync.mapped('s3_amount'))
            if record.so_invoice_total and record.amount_untaxed:
                record.so_outstandig_amount = record.amount_untaxed - record.so_invoice_total
            else:
                record.so_outstandig_amount = 0
    
    @api.model
    def _so_run_process(self, limit=False):
        log_note = self.env['sage300_connector.sale_logs'].sudo()
        sale_order_id = self.env['sale.order'].sudo().search([('state','in' ,['sale','done','SOPF']),('so_state','in',['pending','fail'])],limit=limit)
        if sale_order_id:
            url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
            base_url = url + "/OE/OEOrders"
            username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
            password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
            pricelist = self.env['ir.config_parameter'].sudo().get_param('s3.pricelist')
            token = HTTPBasicAuth(username, password)
            headers = {'Content-Type': 'application/json'}
            for rec in sale_order_id:
                try:
                    products = rec.order_line.filtered(lambda line: line.product_id.product_tmpl_id.pt_state in ('pending','fail')).mapped('product_id.product_tmpl_id')
                    body = {}
                    if products:
                        products._cron_productsync_to_erp()
                    if all(line.product_id.pt_state == 'done' for line in rec.order_line if not line.display_type):
                        partner_id = rec.partner_id and rec.partner_id.parent_id or rec.partner_id
                        if pricelist and partner_id.bci_code and rec.bci_location and rec.bci_location.bci_code:
                            order_line = [{

                                        "LineType": "Item",
                                        "Item": x.product_id and x.product_id.bci_code and x.product_id.bci_code.strip(),
                                        "QuantityOrdered": x.product_uom_qty,
                                        "OriginalQuantityOrdered": x.product_uom_qty,
                                        "PriceList": pricelist,
                                        "OrderDiscountAmount": 0,
                                        "PricingUnitPrice": x.price_unit,
                                        "KitBOMNumber": "1" if x.product_id.bci_kitting_item else "",

                                        "OrderDetailOptionalFields": [{
                                            "OrderUniquifier": 0,
                                            "LineNumber": 0,
                                            "OptionalField": "GHSNCODE",
                                            "Value": x.product_id.l10n_in_hsn_code or "99999999",
                                            "OrderDetailOptionalFieldType": "Text",
                                            "Length": 60,
                                            "Decimals": 0,
                                            "AllowBlank": "true",
                                            "Validate": "true",
                                            "ValueSet": "Yes",
                                            "TypedValueFieldIndex": 0,
                                            "TextValue": x.product_id.l10n_in_hsn_code or "99999999"
                                        }]



                                    } for x in rec.order_line if not x.display_type]
            
                            body = {

                                        "OrderNumber": rec.sopf_sequence,
                                        "PurchaseOrderNumber": rec.po_number or "",
                                        "CustomerNumber": partner_id.bci_code.strip() or "",
                                        "BillToName" : rec.partner_invoice_id.name,
                                        "BillToAddressLine1": rec.partner_invoice_id.street or "", 
                                        "BillToAddressLine2": rec.partner_invoice_id.street2 or "",
                                        "BillToAddressLine3": rec.partner_invoice_id.street3 or "",
                                        "BillToAddressLine4": rec.partner_invoice_id.street4 or "",
                                        "BillToCity": rec.partner_invoice_id.city or "",
                                        "BillToStateProvince": rec.partner_invoice_id.state_id and rec.partner_invoice_id.state_id.name or "",
                                        "BillToZipPostalCode": rec.partner_invoice_id.zip or "",
                                        "BillToPhoneNumber": rec.partner_invoice_id.phone or "",
                                        "BillToFaxNumber": "",
                                        "ShipToName" : rec.partner_shipping_id.name,
                                        "ShipToAddressLine1": rec.partner_shipping_id.street or "",
                                        "ShipToAddressLine2": rec.partner_shipping_id.street2 or "",
                                        "ShipToAddressLine3": rec.partner_shipping_id.street3 or "",
                                        "ShipToAddressLine4": rec.partner_shipping_id.street4 or "",
                                        "ShipToCity": rec.partner_shipping_id.city or "",
                                        "ShipToStateProvince": rec.partner_shipping_id.state_id and rec.partner_shipping_id.state_id.name or "",
                                        "ShipToZipPostalCode": rec.partner_shipping_id.zip or "",
                                        # "ShipToPhoneNumber": 
                                        "ShipToFaxNumber": "",                                        
                                        "BillToContact": rec.finance_contact_name or "", 
                                        "BillToContactPhone": rec.finance_contact_phone or "",#rec.purchase_contact_phone or "",
                                        "BillToContactEmail": rec.finance_contact_email or "", 
                                        "ShipToContact":  rec.store_contact_name or "",
                                        "ShipToContactPhone": rec.store_contact_phone or "",
                                        "ShipToContactEmail": rec.purchase_contact_email or "",
                                        "ShipToPhoneNumber": rec.partner_shipping_id.phone or "",
                                        "ShipToEmail": rec.store_contact_email or "",
                                        "DefaultLocationCode": rec.bci_location and rec.bci_location.bci_code.strip() or "",
                                        "Salesperson1": rec.user_id and rec.user_id.bci_salesperson or "",
                                        "SalesPercentage1": 100,
                                        "OnHold": "false",
                                        "OrderOptionalFields": [{
                                                
                                                "OptionalField": "GINVTYPE",
                                                "Value": "R",
                                                "OrderOptionalFieldType": "Text",
                                                "Length": 60,
                                                "Decimals": 0,
                                                "AllowBlank": "true",
                                                "Validate": "false",
                                                "ValueSet": "Yes",
                                                "TypedValueFieldIndex": 0,
                                                "TextValue": "R"
                                            },

                                            {
                                                
                                                "OptionalField": "GPOS",
                                                "Value": "00",
                                                "OrderOptionalFieldType": "Text",
                                                "Length": 60,
                                                "Decimals": 0,
                                                "AllowBlank": "true",
                                                "Validate": "false",
                                                "ValueSet": "Yes",
                                                "TypedValueFieldIndex": 0,
                                                "TextValue": "00"
                                            }

                                        ],

                                        "OrderDetails": order_line

                            }
                            
                            response = requests.post(base_url, data=json.dumps(body), auth=token, headers=headers)
                            if response and response.ok:
                                data = response.json()
                                print(data)
                                # rec.message_post(body="Sale Order Push to sage300 API")
                                rec.so_state = "done"
                                log_note._log_error("Complete", "Sale Order Sync", rec.sopf_sequence , 'Sync successful')
                            else:
                                log_note._log_error("Error", "Sale Order Sync Un-successful", body, response.text)
                                rec.so_state = "fail"
                        else:
                            log_note._log_error("Error", "Sale Order Sync Un-successful", rec.name, "PriceList / Location Code is blank")
                            rec.so_state = "fail"
                    else:
                        log_note._log_error("Error", "Sale Order Sync Un-successful", "Product Error", "Product Not Synced. - %s"%(rec.name))
                        rec.so_state = "fail"
                except Exception as e:
                    log_note._log_error("Error", "Sale Order Sync", "Error" , '%s - %s'%(str(e),rec.name))
        else:
            log_note._log_error("Message", "Sale Order Sync", "Message" , 'No Record Found')

    
    def _cron_sale_order_sync(self):
        self._so_run_process()
    
    def _so_pending_records(self):
        return self.search_count([('so_state','in',['pending']),('state','in' ,['sale','done','SOPF'])])

    def _so_failed_records(self):
        return self.search_count([('so_state','in',['fail']),('state','in' ,['sale','done','SOPF'])])
    
    def _so_done_records(self):
        return self.search_count([('so_state','in',['done']),('state','in' ,['sale','done','SOPF'])])
    
    def _so_total_records(self):
        return self.search_count([])

    def _so_get_final_records(self):
        return self.env.ref('sage300_connector.action_sale_order_sync_final').read()[0]

    def _so_get_pending_records(self):
        return self.env.ref('sage300_connector.action_sale_order_sync_pending').read()[0]
    
    def _so_get_all_records(self):
        return self.env.ref('sage300_connector.action_sale_order_sync').read()[0]

    def _so_get_processed_records(self):
        return self.env.ref('sage300_connector.action_sale_order_sync_done').read()[0]

    def _so_get_failed_records(self):
        return self.env.ref('sage300_connector.action_sale_order_sync_failed').read()[0]

    def action_so_invoice_sync(self):
        self.ensure_one()
        return ({
                'name': 'IncoiceSync',
                'type': 'ir.actions.act_window',
                'res_model': 'sage300_connector.invoice_sync',
                'view_mode': 'tree,form',
                'domain': [('s3_sale_order', '=', self.id)],
                      
            })

    def _compute_invoice_count(self):
        for record in self:
            record.so_invoice_count = self.env['sage300_connector.invoice_sync'].sudo().search_count([('s3_sale_order','=',record.id)])
    
    def _invoice_sync(self):
        log_note = self.env['sage300_connector.sale_logs'].sudo()
        url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
        last_invoice_date = self.env.company.s3_invoice_date
        # date_covert = datetime.strptime(last_invoice_date, '%Y-%m-%d %H:%M:%S')
        base_url = url + "/OE/OEInvoices?%24filter=InvoiceDate%20ge%20" +"%s"%(str(last_invoice_date))
        username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
        password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
        # raise Exception(base_url)
        token = HTTPBasicAuth(username, password)
        response = requests.get(base_url, auth=token)
        if response and response.ok:
            data = response.json()
            if data["value"]:
                # try:
                for vals in data["value"]:
                    already_invoice = self.env["sage300_connector.invoice_sync"].search([("s3_invoice_no","=",vals['InvoiceNumber'])], limit=1)
                    if not already_invoice:
                        print('--vals---------',vals)
                        so_ref = self.env['sale.order'].search([('sopf_sequence','=',vals['OrderNumber'])])
                        print('--------so_ref------',so_ref)
                        if so_ref:
                            inv_date = datetime.strptime(vals['InvoiceDate'], '%Y-%m-%dT%H:%M:%SZ')
                            sage_invoice = self.env['sage300_connector.invoice_sync'].create({
                                        's3_invoice_no': vals['InvoiceNumber'],
                                        's3_sopf_ref': vals['OrderNumber'],
                                        's3_invoice_date': inv_date.date(),
                                        's3_amount':vals['InvoiceSubtotalAmount'],
                                        's3_sale_order': so_ref.id
                                        })
                            log_note._log_error("Complete", "Invoice Sync Created", so_ref.name , vals)
                        else:
                            log_note._log_error("Error", "Invoice Creation Logic", vals['InvoiceNumber'] , 'SOPF Ref Not exists' + str(vals))
                    else:
                        log_note._log_error("Error", "Invoice Creation Logic", vals['InvoiceNumber'] , 'Invoice Number Already Exist')
                self.env.company.write({'s3_invoice_date': date.today()})
            else:
                log_note._log_error("Message", "Invoice Creation Logic", "Message" , 'No record found')
                self.env.company.write({'s3_invoice_date': date.today()})
        else:
            log_note._log_error("Error", "Invoice Creation Logic", "Error" , response.text)

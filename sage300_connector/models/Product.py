from odoo import models, fields, api
import json
from datetime import datetime
from requests.auth import HTTPBasicAuth
import requests

class ProductSyncLogs(models.Model):
    _name = 'sage300_connector.product_logs'
    _description = "Product Sync Logs"
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
    
    
    def _po_get_process_logs(self):
        return self.env.ref("sage300_connector.action_product_sync_logs").read()[0]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    quantity_on_hand = fields.Float(string="Quantity On Hand")
    quantity_on_purchase_order = fields.Float(string="Quantity On Purchase Order")
    quantity_on_sales_order = fields.Float(string="Quantity On Sales Order")
    last_sync_date = fields.Date(string="Last Sync Date")
    pt_state = fields.Selection([('pending','Pending'),('fail','Failed'),('done','Done')],string="Push To erp",default='pending')
    
    @api.model
    def _pt_run_process(self,max_iterations=False):
        log_note = self.env['sage300_connector.product_logs'].sudo()
        url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
        base_url = url +"/IC/ICItems"
        username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
        password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
        token = HTTPBasicAuth(username, password)
        page_size = 100
        for page in range(1,max_iterations):
            params = {"$top": page_size, "$skip": (page - 1) * page_size}
            response = requests.get(base_url, auth=token, params=params)
            if response and response.ok:
                data = response.json()
                if data["value"]:
                    for vals in data["value"]:
                        try:
                            product_id = self.env['product.template'].search([('bci_code','=',vals['ItemNumber'])])
                            product_category = self.env['product.category'].search([('bci_code','=',vals['Category'])], limit=1)
                            if not product_category:
                                log_note._log_error("Error", "Category not exists", vals['Description'], vals)
                            product_uom = self.env['uom.uom'].search([('name','=',vals['ItemUnitsOfMeasure'][0]['UnitOfMeasure'])], limit=1)
                            if not product_uom:
                                log_note._log_error("Error", "UOM not exists", vals['Description'], vals)
                            if product_id and product_category and product_uom:
                                for product in product_id:
                                    bci_product = product.write({
                                                    'default_code': vals['ItemNumber'],
                                                    'name': vals['Description'],
                                                    'categ_id':product_category.id,
                                                    'uom_id':product_uom.id,
                                                    'uom_po_id':product_uom.id,
                                                    'quantity_on_hand':vals['QuantityOnHand'],
                                                    'quantity_on_purchase_order':vals['QuantityOnPurchaseOrder'],
                                                    'quantity_on_sales_order':vals['QuantityOnSalesOrder'],
                                                    'last_sync_date':datetime.now(),
                                                    'pt_state':'done',
                                                    })
                                    log_note._log_error("Complete", "Product Updated", product.name , vals)
                            elif product_category and product_uom:
                                sage_product = self.env['product.template'].create({
                                                'bci_code': vals['ItemNumber'],
                                                'default_code': vals['ItemNumber'],
                                                'name': vals['Description'],
                                                'categ_id':product_category.id,
                                                'uom_id':product_uom.id,
                                                'uom_po_id':product_uom.id,
                                                'quantity_on_hand':vals['QuantityOnHand'],
                                                'quantity_on_purchase_order':vals['QuantityOnPurchaseOrder'],
                                                'quantity_on_sales_order':vals['QuantityOnSalesOrder'],
                                                'last_sync_date':datetime.now(),
                                                'pt_state':'done'
                                                })
                                if sage_product:
                                    log_note._log_error("Complete", "Product Sage to Crm Created", sage_product.name , vals)
                        except Exception as e:
                            log_note._log_error("Error", "Product Sage to Crm Sync", "Error" , str(e) + str(vals))
                else:
                    # product.pt_state = "fail"
                    log_note._log_error("Message", "Product Sage to Crm Sync","No record Found" , False)
            else:
                log_note._log_error("Error", "Product Sage to Crm Sync", "Error" , response.text)

    def _cron_product_sync(self):
        self._pt_run_process()


    def _cron_productsync_to_erp(self):
        log_note = self.env['sage300_connector.product_logs'].sudo()
        # item_number = self.env['product.template'].sudo().search([('pt_state','in',['pending','fail'])],limit=limit)
        if self:
            url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
            base_url = url + "/IC/ICItems"
            username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
            password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
            token = HTTPBasicAuth(username, password)
            headers = {'Content-Type': 'application/json'}
            for product in self:
                try:
                    # body = {}
                    if product.bci_code and product.categ_id and product.categ_id.bci_code and product.bci_account_set_code and product.bci_account_set_code.code and product.uom_id and product.uom_id.name:
                        tax_id = product.taxes_id and product.taxes_id[0] or False
                        body = {
                            "UnformattedItemNumber": product.bci_code.strip(),
                            "AlternateItemSetNumber": 0,
                            "Description": product.name,
                            "Status": False,
                            "StructureCode": "BCIL",
                            "ItemNumber": product.bci_code.strip(),
                            "Category": product.categ_id and product.categ_id.bci_code.strip(),
                            "AccountSetCode": product.bci_account_set_code and product.bci_account_set_code.code.strip(),
                            "StockItem": False if product.bci_kitting_item else True,
                            "StockingUnitOfMeasure": product.uom_id.name or "",
                            "KittingItem": product.bci_kitting_item,
                            "ItemUnitsOfMeasure": [
                                {
                                    "ItemNumber": product.bci_code.strip(),
                                    "UnitOfMeasure": product.uom_id.name or ""
                                }
                            ],
                            "ItemOptionalFields": [
                                {
                                    "ItemNumber": product.bci_code.strip(),
                                    "OptionalField": "GHSNCODE",
                                    "Value": product.l10n_in_hsn_code or "99999999"
                                },
                                {
                                    "ItemNumber": product.bci_code.strip(),
                                    "OptionalField": "GITEMTYPE",
                                    "Value": "G"
                                }
                            ],
                            "ItemTaxAuthorities": [
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "06CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "06SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "06IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "07CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "07SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "07IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },	
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "19CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "19SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "19IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },	
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "27CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "27SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "27IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "29CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "29SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "29IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "33CGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "33SGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                },
                                {
                                "ItemNumber": product.bci_code.strip(),
                                "TaxAuthority": "33IGN",
                                "PurchaseTaxClass": tax_id and tax_id.bci_tax_class_id or 1,
                                "SalesTaxClass": tax_id and tax_id.bci_tax_class_id or 1
                                }
                            ]
                        }
                        # raise Exception(body)
                        response = requests.post(base_url, data=json.dumps(body), auth=token, headers=headers)
                        if response and response.ok:
                            data = response.json()
                            print(data)
                            product.pt_state = "done"
                            log_note._log_error("Complete", "Product Crm to Sage Sync", product.name , 'Sync successful')
                        else:
                            a = json.loads(response.text)
                            if a["error"]["code"] == 'RecordDuplicate':
                                product.pt_state = "done"
                            else:
                                log_note._log_error("Error", "Product Crm to Sage Sync Un-successful", body,response.text)
                                product.pt_state = "fail"
                            # product.is_pt_sync = True
                    else:
                        log_note._log_error("Error", "Product Crm to Sage Sync Un-successful", "%s - %s" %(product.name, product.bci_code), "BCI Code / Category / Account Set Code / Unit Of Measure is blank")
                        product.pt_state = "fail"
                except Exception as e:
                    log_note._log_error("Error", "Product Crm to Sage Sync", "Error" , '%s - %s'%(str(e),product.name))
        else:
            log_note._log_error("Message", "Product Crm to Sage Sync", "Message" , 'No Record Found')



    def _po_pending_records(self):
        return self.search_count([('pt_state','in',['pending'])])

    def _po_failed_records(self):
        return self.search_count([('pt_state','in',['fail'])])
    
    def _po_done_records(self):
        return self.search_count([('pt_state','in',['done'])])
    
    def _po_total_records(self):
        return self.search_count([])

    def _po_get_final_records(self):
        return self.env.ref('sage300_connector.action_product_sync_final').read()[0]

    def _po_get_pending_records(self):
        return self.env.ref('sage300_connector.action_product_sync_pending').read()[0]
    
    def _po_get_all_records(self):
        return self.env.ref('sage300_connector.action_product_sync').read()[0]

    def _po_get_processed_records(self):
        return self.env.ref('sage300_connector.action_product_sync_done').read()[0]

    def _po_get_failed_records(self):
        return self.env.ref('sage300_connector.action_product_sync_failed').read()[0]
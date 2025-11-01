from odoo import models, fields, api
import json
from requests.auth import HTTPBasicAuth
import requests
from datetime import datetime, date

class CustomerSyncLogs(models.Model):
    _name = 'sage300_connector.customer_logs'
    _description = "Customers Sync Logs"
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
    
    
    def _rp_get_process_logs(self):
        return self.env.ref("sage300_connector.action_customer_sync_logs").read()[0]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_state = fields.Selection([('pending','Pending'),('fail','Failed'),('done','Done')],string="Push To erp",default='pending',copy=False)
    
    
    @api.model
    def customer_push_to_erp(self, limit=False):
        log_note = self.env['sage300_connector.customer_logs'].sudo()
        partner_id = self.env['res.partner'].sudo().search([('is_company', '!=', False),('customer_state','in',['pending','fail']),('customer_rank','>',0),('bci_contact_type','=','Company'),('bci_code','!=',False)],limit=limit)
        if partner_id:
            url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
            base_url = url +'/AR/ARCustomers'
            username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
            password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
            billing_cycle = self.env['ir.config_parameter'].sudo().get_param('s3.billing_cycle')
            token = HTTPBasicAuth(username, password)
            headers = {'Content-Type': 'application/json'}
            for rec in partner_id:
                try:
                    body = {}
                    if rec.bci_code and rec.bci_group_code and rec.bci_group_code.code and billing_cycle and rec.bci_terms_code and rec.bci_terms_code.code and rec.bci_tax_group and rec.bci_tax_group.code and rec.country_id:
                        CustomerOptionalValues = [{
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "GINVTYPE",
                            "Value": "R",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": "R"
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "GPOS",
                            "Value": "00",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": "00"
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "GREGTYPE",
                            "Value": "Normal",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": "Normal"
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "GSTCODE",
                            "Value": "00",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": "00"
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "GSTIN",
                            "Value": rec.vat or "",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": rec.vat or ""
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "SUBVERTICAL",
                            "Value": rec.bci_sub_vertical and rec.bci_sub_vertical.code.strip() or "",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": rec.bci_sub_vertical and rec.bci_sub_vertical.code.strip() or ""
                            },
                            {
                            "CustomerNumber": rec.bci_code.strip(),
                            "OptionalField": "SUBVCATEGORY",
                            "Value": rec.bci_sub_vertical_category and rec.bci_sub_vertical_category.code.strip() or "",
                            "CustomerOptionalFieldValueType": "Text",
                            "Length": 60,
                            "Decimals": 0,
                            "AllowBlank": "true",
                            "Validate": "false",
                            "ValueSet": "Yes",
                            "TypedValueFieldIndex": 0,
                            "TextValue": rec.bci_sub_vertical_category and rec.bci_sub_vertical_category.code.strip() or ""
                            }]
                    
                        body = {
                                    "CustomerNumber": rec.bci_code.strip(),
                                    "ShortName": rec.name or "",
                                    "GroupCode": rec.bci_group_code.code.strip(),
                                    "NationalAccount": rec.bci_national_account_no and rec.bci_national_account_no.strip() or "",
                                    "OnHold": "No",
                                    "CustomerName": rec.name or "",
                                    "AddressLine1": rec.street or "",
                                    "AddressLine2": rec.street2 or "",
                                    "AddressLine3": rec.street3 or "",
                                    "AddressLine4": rec.street4 or "",
                                    "City": rec.city or "",
                                    "StateProvince": rec.state_id and rec.state_id.name or "",
                                    "ZipPostalCode": rec.zip or "",
                                    "Country": rec.country_id.code.strip() or "",
                                    "ContactName": rec.name or "",
                                    "BillingCycle": billing_cycle or "",
                                    "AccountType": "OpenItem",
                                    "Terms": rec.bci_terms_code.code.strip(),                               
                                    "TaxGroup": rec.bci_tax_group.code.strip(),
                                    "CustomerOptionalFieldValues": CustomerOptionalValues
                                    }
                        response = requests.post(base_url, data=json.dumps(body), auth=token, headers=headers)
                        if response and response.ok:
                            data = response.json()
                            rec.customer_state = "done"
                            log_note._log_error("Complete", "Customer Sync", rec.name , 'Sync successful')
                        else:
                            log_note._log_error("Error", "Customer Sync Un-successful", body, response.text)
                            rec.customer_state = "fail"
                    else:
                        log_note._log_error("Error", "Customer Sync Un-successful", "%s - %s" %(rec.name, rec.bci_code), "BCI Code/ Country / Group Code / National Account No / Billing Cycle / Terms Code / Tax Group is blank")
                        rec.customer_state = "fail"
                except Exception as e:
                    log_note._log_error("Error", "Customer Sync", "Error" , '%s - %s'%(str(e),rec.name))
        else:
            log_note._log_error("Error", "Customer Sync", "Message" , 'No Record Found')


    def _rp_pending_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['pending']),('customer_rank','>',0),('bci_contact_type','=','Company')])

    def _rp_failed_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['fail']),('customer_rank','>',0),('bci_contact_type','=','Company')])
    
    def _rp_done_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['done']),('bci_contact_type','=','Company')])
    
    def _rp_total_records(self):
        return self.search_count([])

    def _rp_get_final_records(self):
        return self.env.ref('sage300_connector.action_customer_sync_final').read()[0]

    def _rp_get_pending_records(self):
        return self.env.ref('sage300_connector.action_customer_sync_pending').read()[0]
    
    def _rp_get_all_records(self):
        return self.env.ref('sage300_connector.action_customer_sync').read()[0]

    def _rp_get_processed_records(self):
        return self.env.ref('sage300_connector.action_customer_sync_done').read()[0]

    def _rp_get_failed_records(self):
        return self.env.ref('sage300_connector.action_customer_sync_failed').read()[0]

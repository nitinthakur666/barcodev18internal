from odoo import models, fields, api
import json
from requests.auth import HTTPBasicAuth
import requests
from datetime import datetime, date

class NationalAccountSync(models.Model):
    _name = 'sage300_connector.customer_account_logs'
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
    
    
    def _na_get_process_logs(self):
        return self.env.ref("sage300_connector.action_national_account_sync_logs").read()[0]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_state = fields.Selection([('pending','Pending'),('fail','Failed'),('done','Done')],string="Push To erp",default='pending',copy=False)
    
    
    @api.model
    def national_account_push_to_erp(self, limit=False):
        log_note = self.env['sage300_connector.customer_logs'].sudo()
        partner_id = self.env['res.partner'].sudo().search([('is_company', '!=', False),('customer_state','in',['pending','fail']),('bci_contact_type','=','Parent Company')],limit=limit)
        if partner_id:
            url = self.env['ir.config_parameter'].sudo().get_param('s3.base_url')
            base_url = url +'/AR/ARNationalAccounts'
            username = self.env['ir.config_parameter'].sudo().get_param('s3.username')
            password = self.env['ir.config_parameter'].sudo().get_param('s3.password')
            billing_cycle = self.env['ir.config_parameter'].sudo().get_param('s3.billing_cycle')
            token = HTTPBasicAuth(username, password)
            headers = {'Content-Type': 'application/json'}
            for rec in partner_id:
                try:
                    body = {}
                    if rec.bci_national_account_no and rec.bci_group_code and rec.bci_group_code.code:
                        body= {
                                    "NationalAccountNumber": rec.bci_national_account_no.strip(),
                                    "GroupCode": rec.bci_group_code.code.strip(),
                                    "Status":"Active",
                                    "NationalAccountName":rec.name,
                                    "NationalAccountOptionalField":[
                                        {
                                            "NationalAccount":rec.bci_national_account_no.strip(),
                                            "OptionalField":"GINVTYPE",
                                            "Value":"R",
                                            "NationalAccountOptionalFieldType":"Text",
                                            "Length":5,
                                            "Decimals":0,
                                            "AllowBlank":"true",
                                            "Validate":"true",
                                            "ValueSet":"Yes",
                                            "TypedValueFieldIndex":0,
                                            "TextValue":"R"
                                        },
                                        {
                                            "NationalAccount":rec.bci_national_account_no.strip(),
                                            "OptionalField":"GPOS",
                                            "Value":"00",
                                            "NationalAccountOptionalFieldType":"Text",
                                            "Length":0,
                                            "Decimals":0,
                                            "AllowBlank":"true",
                                            "Validate":"true",
                                            "ValueSet":"Yes",
                                            "TypedValueFieldIndex":0,
                                            "TextValue":"00"
                                        },
                                        {
                                            "NationalAccount":rec.bci_national_account_no.strip(),
                                            "OptionalField":"GREGTYPE",
                                            "Value":"Normal",
                                            "NationalAccountOptionalFieldType":"Text",
                                            "Length":0,
                                            "Decimals":0,
                                            "AllowBlank":"true",
                                            "Validate":"true",
                                            "ValueSet":"Yes",
                                            "TypedValueFieldIndex":0,
                                            "TextValue":"Normal"
                                        },
                                        {
                                            "NationalAccount":rec.bci_national_account_no.strip(),
                                            "OptionalField":"GSTCODE",
                                            "Value":"00",
                                            "NationalAccountOptionalFieldType":"Text",
                                            "Length":0,
                                            "Decimals":0,
                                            "AllowBlank":"true",
                                            "Validate":"true",
                                            "ValueSet":"Yes",
                                            "TypedValueFieldIndex":0,
                                            "TextValue":"00"
                                        },
                                        {
                                            "NationalAccount":rec.bci_national_account_no.strip(),
                                            "OptionalField":"GSTIN",
                                            "Value":rec.vat or "",
                                            "NationalAccountOptionalFieldType":"Text",
                                            "Length":0,
                                            "Decimals":0,
                                            "AllowBlank":"true",
                                            "Validate":"true",
                                            "ValueSet":"Yes",
                                            "TypedValueFieldIndex":0,
                                            "TextValue":rec.vat or ""
                                        }
                                    ]
                                }
                        response = requests.post(base_url, data=json.dumps(body), auth=token, headers=headers)
                        if response and response.ok:
                            data = response.json()
                            rec.customer_state = "done"
                            log_note._log_error("Complete", "National Account Sync", rec.name , 'Sync successful')
                        else:
                            log_note._log_error("Error", "National Account Sync Un-successful", body, response.text)
                            rec.customer_state = "fail"
                    else:
                        log_note._log_error("Error", "National Account Sync Un-successful", "%s - %s" %(rec.name, rec.bci_national_account_no), "National Account Code / Group Code is blank")
                        rec.customer_state = "fail"
                except Exception as e:
                    log_note._log_error("Error", "National Account Sync", "Error" , '%s - %s'%(str(e),rec.name))
        else:
            log_note._log_error("Error", "National Account Sync", "Message" , 'No Record Found')


    def _na_pending_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['pending']),('bci_contact_type','=','Parent Company')])

    def _na_failed_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['fail']),('bci_contact_type','=','Parent Company')])
    
    def _na_done_records(self):
        return self.search_count([('is_company', '!=', False),('customer_state','in',['done']),('bci_contact_type','=','Parent Company')])
    
    def _na_total_records(self):
        return self.search_count([])

    def _na_get_final_records(self):
        return self.env.ref('sage300_connector.action_national_account_sync_final').read()[0]

    def _na_get_pending_records(self):
        return self.env.ref('sage300_connector.action_national_account_sync_pending').read()[0]
    
    def _na_get_all_records(self):
        return self.env.ref('sage300_connector.action_national_account_sync').read()[0]

    def _na_get_processed_records(self):
        return self.env.ref('sage300_connector.action_national_account_sync_done').read()[0]

    def _na_get_failed_records(self):
        return self.env.ref('sage300_connector.action_national_account_sync_failed').read()[0]

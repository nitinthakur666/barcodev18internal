from requests import auth
from odoo import api, fields, models

import requests
from requests.auth import HTTPBasicAuth
import json
import traceback
from itertools import groupby


class ContractSyncLogs(models.Model):
    _name = 'barcode_india.contract_sync_logs'
    _description = "Contract Sync Logs"
    _order = 'id desc'
    
    cs_records = fields.Integer("Records")
    cs_sync_name = fields.Char("Sync Name")
    cs_status = fields.Char("Status")
    cs_error = fields.Char("Message")

    def _cs_get_process_logs(self):
        return self.env.ref("barcode_india.action_contract_sync_logs").read()[0]

    def _log_error(self, records, status, error,sync_name):
        self.sudo().create({
            'cs_records': records,
            'cs_status': status,
            'cs_error': error,
            'cs_sync_name':sync_name
        })


class AssetsSync(models.Model):    
    _name = 'barcode_india.assets_sync'
    _description = 'Assets Sync'

    cs_contract_sync = fields.Many2one("barcode_india.contract_sync","Contract Sync", ondelete='cascade')
    name = fields.Char("Name")
    cs_product_code = fields.Char("Product Code")
    cs_invoice_date = fields.Date("Invoice Date")
    cs_invoice_number = fields.Char("Invoice Number")
    cs_line_number = fields.Char("Line Number")
    cs_quantity = fields.Integer("Quantity")
    cs_line_type = fields.Selection([('Hardware','Hardware'),('Carepack','Carepack')],"Line type")
    cs_sopf_ref = fields.Char("SOPF Ref")
    cs_product = fields.Many2one("product.template","Main Harware/Carepack Product")
    cs_service_product = fields.Many2one("product.template","Service Product")
    cs_care_pack_line = fields.Many2one("barcode_india.contract_sync","Carepack Contract Line")
    cs_careack_product = fields.Many2many("product.template",string="Carepack")
    
class ContractSync(models.Model):    
    _name = 'barcode_india.contract_sync'
    _order = "id desc"
    _description = 'Contract Sync'

    cs_state = fields.Selection([('pending','Pending'),('done','Processed'),('fail','Failed')],"Status")
    active = fields.Boolean("Active", default=True)

    name = fields.Char("Name")
    cs_invoice_number = fields.Char("Invoice Number")
    cs_invoice_date = fields.Date("Invoice Date")
    cs_origin = fields.Char("Origin")
    cs_customer_code = fields.Char("Customer Code")
    cs_customer_name = fields.Char("Customer Name")
    cs_site_code = fields.Char("Site Code")
    cs_street = fields.Char("Street")
    cs_street2 = fields.Char("Street2")
    cs_street3 = fields.Char("Street3")
    cs_street4 = fields.Char("Street4")
    cs_state_id = fields.Char("State")
    cs_city = fields.Char("City")
    cs_zip = fields.Char("Zip")
    cs_country = fields.Char("Country")
    cs_address_verification = fields.Char("Address Verification")
    cs_type = fields.Char("Type")
    cs_erp_oder_ref = fields.Char("ERP Order Ref")
    cs_sopf_ref = fields.Char("SOPF Ref")
    cs_invoice_internal_id = fields.Char("Invoice Internal Id")
    cs_sales_person = fields.Char("Salesperson")
    cs_preferred_applicable = fields.Char("Preferred Applicable")
    cs_ready_for_sync = fields.Boolean("Ready For Sync?")
    cs_assets_ids = fields.One2many('barcode_india.assets_sync', 'cs_contract_sync', string='Assets')
    cs_message = fields.Char("Error Message")

    def create_partner_record(self, name, street, street2, street3, street4, zip, city, state, country, code, customer_id=False, site=False):
        country_id = self.env["res.country"].sudo().search([("name", "=", country)], limit=1)
        state_id = self.env["res.country.state"].sudo().search([("name", "=", state)], limit=1)
        partner_name = "%s-%s"%(name,city) if site else name
        vals = {
            "name": partner_name,
            "street": street,
            "street2": street2,
            "street3": street3,
            "street4": street4,
            "zip": zip,
            "city": city,
            "state_id": state_id.id if state_id else False,
            "country_id": country_id.id if country_id else False,
        }
        if site and customer_id:
            vals["bci_contact_type"] = "Site"
            vals["company_type"]  = "company"
            vals["bci_company"] = customer_id.id
            vals["bci_site_code"] = code
        else:
            
            vals["company_type"]  = "company"
            vals["bci_contact_type"] = "Company"
            vals["bci_code"] = code
        contact = self.env["res.partner"].sudo().create(vals)
        return contact

    def contract_assets_creation(self, data_line=False, cs_care_pack_line=False):
        partner = self.env["res.partner"].sudo()
        contract_model = self.env["barcode_india.contracts"].sudo()
        contract_sync = data_line[0].cs_contract_sync
        log_note = self.env["barcode_india.contract_sync_logs"].sudo()
        stage_id = self.env['barcode_india.contracts.stage'].sudo().search([("stage_type","=","Invoiced")])
        # stage_id = self.env['barcode_india.contracts.stage'].sudo().search([("is_invoice_stage","=",True)])
        assets_stage = self.env["barcode_india.assets.stage"].sudo().search([('type','=','active')],limit=1)
        type = self.env['barcode_india.contracts.type'].sudo().search([("type","=",contract_sync.cs_type)])
        sales_person = self.env["res.users"].sudo().search([("bci_salesperson","=",contract_sync.cs_sales_person)], limit=1) if contract_sync.cs_sales_person else False
        team_id = False                        
        if sales_person:
            team_id = self.env["crm.team"].sudo().search([]).filtered(lambda x: sales_person.id in x.member_ids.ids)
        if contract_sync.cs_customer_code:
            customer_id = partner.search([("bci_code","=",contract_sync.cs_customer_code)], limit=1)
            if not customer_id:
                customer = self.create_partner_record(contract_sync.cs_customer_name,contract_sync.cs_street,contract_sync.cs_street2,contract_sync.cs_street3,contract_sync.cs_street4,contract_sync.cs_zip,contract_sync.cs_city,contract_sync.cs_state_id,contract_sync.cs_country,contract_sync.cs_customer_code)
                if customer:
                    customer_id = customer
                else:
                    Status = False
                    message = "Sync Un-Successful"
        if contract_sync.cs_site_code:
            site_id = partner.search([("bci_site_code","=",contract_sync.cs_site_code)], limit=1)
            if not site_id:
                customer = self.create_partner_record('Site',contract_sync.cs_street,contract_sync.cs_street2,contract_sync.cs_street3,contract_sync.cs_street4,contract_sync.cs_zip,contract_sync.cs_city,contract_sync.cs_state_id,contract_sync.cs_country,contract_sync.cs_site_code,customer_id,True)
                if customer:
                    site_id = customer
                else:
                    Status = False
                    message = "Sync Un-Successful"
        else:
            site_id = False
        vals = []
        if customer_id:
            for rec in data_line:
                vals.append((0,0,{
                    "name" : rec.name,
                    "bci_customer": customer_id.id,
                    "bci_site": site_id.id if site_id else False,
                    "bci_origin": contract_sync.cs_origin,
                    "bci_invoice_date": rec.cs_invoice_date,
                    "bci_invoice_number": rec.cs_invoice_number,
                    "bci_product": rec.cs_product.product_variant_id.id,
                    "bci_line_no": rec.cs_line_number,
                    "bci_service_product": cs_care_pack_line.cs_assets_ids.mapped('cs_service_product').product_variant_id.id if cs_care_pack_line else rec.cs_service_product.product_variant_id.id,
                    "bci_stage_id": assets_stage and assets_stage.id or 1
                    }))
            if vals:
                contract = contract_model.create(
                {
                    "bci_customer": customer_id.id,
                    "bci_origin": contract_sync.cs_origin,
                    "bci_invoice_date": contract_sync.cs_invoice_date,
                    "bci_invoice_number": contract_sync.cs_invoice_number,
                    "bci_address_verification": contract_sync.cs_address_verification,
                    "bci_preferred_applicable": contract_sync.cs_preferred_applicable,
                    "bci_order_ref": contract_sync.cs_erp_oder_ref,
                    "bci_sopf_number": contract_sync.cs_sopf_ref,
                    "bci_invoice_internal_id": contract_sync.cs_invoice_internal_id,
                    "bci_type": type.id if type else False,
                    "bci_site": site_id.id if site_id else False,
                    "bci_saleperson" : sales_person.id if sales_person else False,
                    "bci_team_id" : team_id.id if team_id else False,
                    "bci_stage_id" : stage_id and stage_id.id or 1,
                    "bci_assets_ids" : vals
                })
                if contract:
                    log_note._log_error(1,"Successful","%s Contract Created Successful -  %s"%(contract.name,vals), "Contract Creation")
                    contract.bci_assets_ids.onchange_bci_service_product()
                    if cs_care_pack_line:
                        cs_care_pack_line.cs_state = 'done'
                    for x in data_line:
                        x.cs_contract_sync.cs_state = 'done'
                else:
                    log_note._log_error(1,"Un-Successful","Contract Not Created -  %s"%(vals), "Contract Creation")
                    if cs_care_pack_line:
                        cs_care_pack_line.cs_state = 'fail'
                    for x in data_line:
                        x.cs_contract_sync.cs_state = 'fail'
        else:
            log_note._log_error(1,"Un-Successful","Customer Not Found -  %s"%(vals), "Contract Creation")
            if cs_care_pack_line:
                cs_care_pack_line.cs_state = 'fail'
            for x in data_line:
                x.cs_contract_sync.cs_state = 'fail'


    def _cs_run_process(self):
        log_note = self.env["barcode_india.contract_sync_logs"].sudo()
        assets_sync_record = list(self.env['barcode_india.assets_sync'].sudo().search([('cs_contract_sync.cs_state','in',['pending','fail']),('cs_contract_sync.cs_ready_for_sync','=',True),('cs_contract_sync.active','=',True)]))
        assets_sync_record.sort(key=lambda x: (x.cs_sopf_ref))
        for key, group in groupby(assets_sync_record, lambda x: (x.cs_sopf_ref)):
            data = list(group)
            records = self.env['barcode_india.assets_sync'].sudo().browse([x.id for x in data]).mapped('cs_contract_sync')
            try:
                hardware_line_with_carepack = [x for x in data if x.cs_line_type == 'Hardware' and x.cs_care_pack_line]
                hardware_line_without_carepack = [x for x in data if x.cs_line_type == 'Hardware' and not x.cs_care_pack_line]
                carepack_line = [x for x in data if x.cs_line_type == 'Carepack']
                if hardware_line_with_carepack:
                    hardware_line_with_carepack.sort(key=lambda x: (x.cs_care_pack_line.id))
                    for key, hw_group in groupby(hardware_line_with_carepack, lambda x: (x.cs_care_pack_line)):
                        hw_with_lines = list(hw_group)
                        if hw_with_lines:
                            self.contract_assets_creation(hw_with_lines, key)
                if hardware_line_without_carepack:
                    hardware_line_without_carepack.sort(key=lambda x: (x.cs_service_product.id))
                    for key, hw_group in groupby(hardware_line_without_carepack, lambda x: (x.cs_service_product)):
                        hw_without_lines = list(hw_group)
                        if hw_without_lines:
                            self.contract_assets_creation(hw_without_lines)
                if carepack_line:
                    for rec in carepack_line:
                        hw_lines = self.env['barcode_india.assets_sync'].sudo().search([('cs_sopf_ref','=',rec.cs_sopf_ref),('cs_line_type','=','Hardware')]).filtered(lambda x: rec.cs_product.id in x.cs_product.bci_carepack_ids.ids)
                        # hw_lines = self.env['barcode_india.assets_sync'].sudo().search([('cs_care_pack_line','=',rec.cs_contract_sync.id)])
                        if not hw_lines:
                            if not rec.cs_contract_sync.cs_message:
                                rec.cs_contract_sync.write({'cs_state': 'fail','cs_message':'Hardware product mapping not found for this carepack'})
                                log_note._log_error(1,"Un-Successful","Hardware product mapping not found for this carepack-  %s"%(rec.cs_contract_sync.name), "Contract Creation")
                        else:
                            assets_line = self.env["barcode_india.assets"].sudo().search([('bci_contract_id.bci_sopf_number','=',rec.cs_sopf_ref),('bci_product','=',hw_lines[0].cs_product.product_variant_id.id)])
                            if len(assets_line) == rec.cs_quantity:
                                hw_lines.write({'cs_care_pack_line': rec.cs_contract_sync.id})
                                assets_line.write({"bci_service_product": rec.cs_service_product and rec.cs_service_product.product_variant_id.id})
                                assets_line.onchange_bci_service_product()
                                rec.cs_contract_sync.cs_state = 'done'
            except Exception as e:
                records.write({'cs_state': 'fail'})
                message = "Contract Details - %s"%(",".join([x.name for x in records])) + str(e)
                log_note._log_error(len(records),"Un-Successful",message, "Contract Creation")

    def _cron_contract_sync(self):
        self._cs_run_process()

    def _cs_pending_records(self):
        return self.search_count([('cs_state','=','pending')])

    def _cs_failed_records(self):
        return self.search_count([('cs_state','=','fail')])
    
    def _cs_done_records(self):
        return self.search_count([('cs_state','=','done')])
    
    def _cs_total_records(self):
        return self.env['barcode_india.contract_sync'].sudo().search_count([])
    
    def _cs_get_final_records(self):
        return self.env.ref('barcode_india.action_contract_sync_final').read()[0]

    def _cs_get_pending_records(self):
        return self.env.ref('barcode_india.action_contract_sync_pending').read()[0]
    
    def _cs_get_all_records(self):
        return self.env.ref('barcode_india.action_contract_sync').read()[0]

    def _cs_get_processed_records(self):
        return self.env.ref('barcode_india.action_contract_sync_done').read()[0]

    def _cs_get_failed_records(self):
        return self.env.ref('barcode_india.action_contract_sync_failed').read()[0]
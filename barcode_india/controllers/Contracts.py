# -*- coding: utf-8 -*-
from odoo import http
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.http import request
import json, logging
import re
from itertools import groupby
from operator import itemgetter


class BciContractSync(http.Controller):
    
    @http.route("/api/readyforsync", type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def ContractSyncStatus(self, data={}, **kwargs):
        datas = json.loads(request.httprequest.data)
        username = request.httprequest.authorization.get("username", False)
        password = request.httprequest.authorization.get("password", False)
        if username and password:
            bci_username = request.env["ir.config_parameter"].sudo().get_param("bci.username")
            bci_password = request.env["ir.config_parameter"].sudo().get_param("bci.password")
            log_note = request.env["barcode_india.contract_sync_logs"].sudo()
            if (bci_username and bci_password and username and password and bci_username == username and bci_password == password):
                if datas:
                    record = datas
                    if record["sync_status"] == 'True':
                        contract_sync_ids = request.env["barcode_india.contract_sync"].sudo().search([("cs_state","=",["pending"]),("cs_ready_for_sync","=",False)])
                        contract_sync_ids_with_sopf_ref = list(contract_sync_ids.filtered(lambda x: x.cs_sopf_ref))
                        contract_sync_ids_without_sopf_ref = contract_sync_ids.filtered(lambda x: not x.cs_sopf_ref)
                        Message = ""
                        Status = False
                        if contract_sync_ids_with_sopf_ref:
                            contract_sync_ids_with_sopf_ref.sort(key=lambda x: (x.cs_sopf_ref))
                            for key, group in groupby(contract_sync_ids_with_sopf_ref, lambda x: (x.cs_sopf_ref)):
                                data = list(group)
                                if len(data) == 1 and "SPACK" in data[0].name:
                                    contract_with_hw_done = request.env["barcode_india.contract_sync"].sudo().search([("cs_state","=",["done"]),("cs_sopf_ref","=",data[0].cs_sopf_ref)])
                                    if not contract_with_hw_done:
                                        log_note._log_error(1,"Un-Successful","Only Carepack Line For - %s"%(data[0].name),"Ready For Sync")
                                        data[0].cs_message = "Only One Carepack Line"
                                        Message = Message + "Only Carepack Line For - %s \n "%(data[0].name)
                                    else:
                                        log_note._log_error(1,"Un-Successful","Only Carepack Line For - %s"%(data[0].name),"Ready For Sync")
                                        data[0].cs_message = "HW Contract already created"
                                        data[0].write({'cs_ready_for_sync':True})
                                        Message = Message + "HW Contract already created - %s \n "%(data[0].name)
                                else:
                                    for rec in data:
                                        rec.write({'cs_ready_for_sync':True})
                                    Status = True
                                    Message = Message + "Ready For Sync Flag Updated %s \n "%(",".join([x.name for x in data]))
                                    log_note._log_error(len(data),"Successful",Message,"Ready For Sync")
                        if contract_sync_ids_without_sopf_ref:
                            log_note._log_error(len(contract_sync_ids_without_sopf_ref.ids),"Un-Successful","No SOPF Ref For - %s"%(",".join([x.name for x in contract_sync_ids_without_sopf_ref])),"Ready For Sync")
                            for rec in contract_sync_ids_without_sopf_ref:
                                rec.cs_message = "No SOPF Ref"
                            Message = Message + "No SOPF Ref For - %s"%(",".join([x.name for x in contract_sync_ids_without_sopf_ref]))
                        else:    
                            Status = False
                            Message = Message + "No record For Flag Update"
                            log_note._log_error(0,"Un-Successful",Message,"Ready For Sync")
                        return {"Status": Status, "Message": Message}
                    else:
                        Status = False
                        Message = "Incorrect Value in sync status"
                        log_note._log_error(0,"Error",Message,"Ready For Sync")
                        return {"Status": Status, "Message": Message}
            else:
                return {"Status": False, "Message": "Invalid Credentials"}
        else:
            return {"Status": False, "Message": "Invalid Authorization"}
    
    @http.route("/api/contracts", type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def ContractSync(self, data={}, **kwargs):
        datas = json.loads(request.httprequest.data)
        username = request.httprequest.authorization.get("username", False)
        password = request.httprequest.authorization.get("password", False)
        log_note = request.env["barcode_india.contract_sync_logs"].sudo()
        if username and password:
            bci_username = request.env["ir.config_parameter"].sudo().get_param("bci.username")
            bci_password = request.env["ir.config_parameter"].sudo().get_param("bci.password")
            if (bci_username and bci_password and username and password and bci_username == username and bci_password == password):
                if datas:
                    record = datas
                    contract_model = request.env["barcode_india.contract_sync"].sudo()
                    assets_model = request.env["barcode_india.assets_sync"].sudo()
                    assets = record.get("assets", [])
                    if assets:
                        try:
                            vals = []
                            for rec in assets:
                                assets_exist = assets_model.search([('name','=',rec["name"]),('cs_invoice_number','=',rec["invoice_number"]),('cs_product_code','=',rec["product_code"])])
                                product = request.env["product.template"].sudo().search([("bci_code","=",rec["product_code"])], limit=1)
                                if not assets_exist:
                                    vals.append((0,0,{
                                        "name" : rec["name"],
                                        "cs_invoice_date": rec["invoice_date"],
                                        "cs_invoice_number": rec["invoice_number"],
                                        "cs_product_code": rec["product_code"],
                                        "cs_line_number": rec["line_number"],
                                        "cs_quantity": rec["quantity"],
                                        "cs_line_type": "Carepack" if "SPACK" in record["name"] else "Hardware",
                                        "cs_sopf_ref" : record["sopf_reference"],
                                        "cs_product" : product and product.id or False,
                                        "cs_service_product": product and product.bci_sla_product and product.bci_sla_product.id or False,
                                        "cs_careack_product": product and product.bci_carepack_ids and [(6,0,product.bci_carepack_ids.ids)] or False
                                        }))
                                else:
                                    Status = False
                                    Message = "Assets/Carepack Already exist %s"%(rec)
                                    log_note._log_error(1,"Un - Successful",Message, "Staging Table Sync")
                            if vals:
                                contract = contract_model.create(
                                {
                                    "name": record["name"],
                                    "cs_customer_name": record["customer_name"],
                                    "cs_customer_code": record["customer_code"],
                                    "cs_origin": record["origin"],
                                    "cs_invoice_date": record["invoice_date"],
                                    "cs_invoice_number": record["invoice_number"],
                                    "cs_site_code": record["site_code"],
                                    "cs_street": record["street"],
                                    "cs_street2": record["street2"],
                                    "cs_street3": record["street3"],
                                    "cs_street4": record["street4"],
                                    "cs_state_id": record["state"],
                                    "cs_city": record["city"],
                                    "cs_zip": record["zip"],
                                    "cs_country": record["country"],
                                    "cs_address_verification": record["address_verification"],
                                    "cs_preferred_applicable": record["preferred_applicable"],
                                    "cs_erp_oder_ref": record["erp_order_ref"],
                                    "cs_sopf_ref": record["sopf_reference"],
                                    "cs_invoice_internal_id": record["invoice_internal_id"],
                                    "cs_type": record["type"],
                                    "cs_sales_person": record["sales_person"],
                                    "cs_state": "pending",
                                    "cs_assets_ids" : vals
                                })
                                if contract:
                                    if "SPACK" in record["name"]:
                                        product = contract.cs_assets_ids.mapped('cs_product')
                                        quantity = sum(contract.cs_assets_ids.mapped('cs_quantity'))
                                        hw_lines = assets_model.search([('cs_sopf_ref','=',record["sopf_reference"]),('cs_line_type','=','Hardware'),('cs_care_pack_line','=',False)]).filtered(lambda x: product.id in x.cs_careack_product.ids)
                                        if len(hw_lines) == quantity:
                                            hw_lines.write({'cs_care_pack_line': contract.id})
                                    Status = True
                                    Message = "Contract Staging data created"
                                    log_note._log_error(1,"Successful","Contract Staging data created - %s, %s , %s"%(contract.name,contract.cs_sopf_ref,vals), "Staging Table Sync")
                            
                            return {"Status": Status, "Message": Message}
                        except Exception as e:
                            return {"Status": False, "Message": str(e)}
                    else:
                        log_note._log_error(0,"Un-Successful","No Assets/Carepack Detail pass", "Staging Table Sync")
            else:
                return {"Status": False, "Message": "Invalid Credentials"}
        else:
            return {"Status": False, "Message": "Invalid Authorization"}
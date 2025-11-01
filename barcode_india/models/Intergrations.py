# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class Integrations(models.Model):
    _name = 'barcode_india.integrations'
    _description = 'Integrations'
    _order = 'sequence, id'
    
    name = fields.Char("Process", required=True)
    process_code = fields.Char("Process Code", required=True)
    sequence = fields.Integer("Sequence", default=0)
    process = fields.Many2one("ir.model", required=True, ondelete = 'cascade')
    module = fields.Char("Module Name", required=True)
    cron_job = fields.Many2one("ir.cron", ondelete = 'cascade')
    active_job = fields.Boolean("Job Active", default=True)
    type = fields.Selection([('Base','Base')], "Type")
    limit = fields.Integer("Limit", default=0)
    debug_mode = fields.Boolean("Debug Mode", default=False)
    pending_records = fields.Integer("Pending Records", compute="_compute_pending_records")
    total_logs = fields.Integer("Logs", compute="_compute_total_logs")
    logs = fields.Many2one("ir.model", required=True, ondelete = 'cascade')
    records = fields.Integer("No Of Records", compute="_compute_total_records")
    failed_records = fields.Integer("Failed Records", compute="_compute_failed_records")
    processed_records = fields.Integer("Done Records", compute="_compute_done_records")
    has_process = fields.Boolean("Has Process", compute="_compute_record_process")
    final_records = fields.Integer("Final Records", compute="_compute_final_records")
    has_archive = fields.Boolean("Has Archive", compute="_compute_has_archive")
    
    def toggle_debug(self):
        self.debug_mode = not self.debug_mode
    
    def write(self, vals):
        super(Integrations, self).write(vals)
        if self.cron_job:
            self.cron_job.active = self.active_job

    def _compute_has_archive(self):
        for record in self:
            record.has_archive = bool(hasattr(self.env['%s'%(record.process.model)], '_%s_run_archive'%(record.process_code)))
           
    def _compute_final_records(self):
        for record in self:
            record.final_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_final_records'%(record.process_code)):
                record.final_records = getattr(record.env['%s'%(record.process.model)], '_%s_final_records'%(record.process_code))()

    def _compute_record_process(self):
        for record in self:
            record.has_process = bool(hasattr(self.env['%s'%(record.process.model)], '_%s_run_process'%(record.process_code)))

    def _compute_failed_records(self):
        for record in self:
            record.failed_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_failed_records'%(record.process_code)):
                record.failed_records = getattr(record.env['%s'%(record.process.model)], '_%s_failed_records'%(record.process_code))()
            
    def _compute_done_records(self):
        for record in self:
            record.processed_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_done_records'%(record.process_code)):
                record.processed_records = getattr(record.env['%s'%(record.process.model)], '_%s_done_records'%(record.process_code))()
    
    def _compute_total_records(self):
        for record in self:
            record.records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_total_records'%(record.process_code)):
                record.records = getattr(record.env['%s'%(record.process.model)], '_%s_total_records'%(record.process_code))()
    
    
    def _compute_pending_records(self):
        for record in self:
            record.pending_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_pending_records'%(record.process_code)):
                record.pending_records = getattr(record.env['%s'%(record.process.model)], '_%s_pending_records'%(record.process_code))()
            
    def _compute_total_logs(self):
        for record in self:
            record.total_logs = self.env['%s'%(record.logs.model)].sudo().search_count([])

    def run_process(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_run_process'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_run_process'%(self.process_code))(self.debug_mode,self.limit)
            
        raise UserError("%s does not implement _%s_run_process"%(self.module,self.process_code))

    def run_archive(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_run_archive'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_run_archive'%(self.process_code))()
            
        raise UserError("%s does not implement _%s_run_archive"%(self.module,self.process_code))	
        
    def get_final_records(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_get_final_records'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_get_final_records'%(self.process_code))()
            
        raise UserError("%s does not implement _%s_get_final_records"%(self.module,self.process_code))	
    
    def get_process_logs(self):
        if hasattr(self.env['%s'%(self.logs.model)], '_%s_get_process_logs'%(self.process_code)):
            return getattr(self.env['%s'%(self.logs.model)], '_%s_get_process_logs'%(self.process_code))()
            
        raise UserError("%s does not implement _%s_get_process_logs"%(self.module,self.process_code))

    def get_pending_records(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_get_pending_records'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_get_pending_records'%(self.process_code))()

        raise UserError("%s does not implement _%s_get_pending_records"%(self.module,self.process_code))

    def get_all_records(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_get_all_records'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_get_all_records'%(self.process_code))()
        
        raise UserError("%s does not implement _%s_get_all_records"%(self.module,self.process_code))

    def get_processed_records(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_get_processed_records'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_get_processed_records'%(self.process_code))()
        
        raise UserError("%s does not implement _%s_get_processed_records"%(self.module,self.process_code))

    def get_failed_records(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_get_failed_records'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_get_failed_records'%(self.process_code))()
        
        raise UserError("%s does not implement _%s_get_failed_records"%(self.module,self.process_code))




from odoo import api, fields, models
from odoo.exceptions import UserError

class Integrations(models.Model):
    _name = 'sage300_connector.integrations'
    _description = 'Integrations'
    
    name = fields.Char("Name", required=True)
    process_code = fields.Char("Process Code", required=True)
    sequence = fields.Integer("Sequence", default=0)
    process = fields.Many2one("ir.model", required=True, ondelete = 'cascade')
    logs = fields.Many2one("ir.model", required=True, ondelete = 'cascade')
    # do_not_push_records = fields.Integer("Do Not Push Records",compute="_compute_do_not_push_records")

    limit = fields.Integer("Limit", default=0)
    failed_records = fields.Integer("Failed Records", compute="_compute_failed_records")
    module = fields.Char("Module Name", required=True)
    pushed_records = fields.Integer("Pushed Records",compute="_compute_pushed_records")
    pending_records = fields.Integer("Pending Records",compute="_compute_pending_records")
    cron_job = fields.Many2one("ir.cron", ondelete = 'cascade')
    active_job = fields.Boolean("Job Active", default=True)
    has_process = fields.Boolean("Has Process", compute="_compute_record_process")

    def write(self, vals):
        super(Integrations, self).write(vals)
        if self.cron_job:
            self.cron_job.active = self.active_job

    def _compute_pending_records(self):
        for record in self:
            record.pending_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_pending_records'%(record.process_code)):
                record.pending_records = getattr(record.env['%s'%(record.process.model)], '_%s_pending_records'%(record.process_code))()

    def _compute_pushed_records(self):
        for record in self:
            record.pushed_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_pushed_records'%(record.process_code)):
                record.pushed_records = getattr(record.env['%s'%(record.process.model)], '_%s_pushed_records'%(record.process_code))()

    def _compute_failed_records(self):
        for record in self:
            record.failed_records = 0
            if hasattr(self.env['%s'%(record.process.model)], '_%s_failed_records'%(record.process_code)):
                record.failed_records = getattr(record.env['%s'%(record.process.model)], '_%s_failed_records'%(record.process_code))()
    
    def _compute_record_process(self):
        for record in self:
            record.has_process = bool(hasattr(self.env['%s'%(record.process.model)], '_%s_run_process'%(record.process_code)))

    def run_process(self):
        if hasattr(self.env['%s'%(self.process.model)], '_%s_run_process'%(self.process_code)):
            return getattr(self.env['%s'%(self.process.model)], '_%s_run_process'%(self.process_code))(False,self.limit)
            
        raise UserError("%s does not implement _%s_run_process"%(self.module,self.process_code))

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
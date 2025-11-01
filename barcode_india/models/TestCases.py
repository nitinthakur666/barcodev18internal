from odoo import models, fields

class TestCases(models.Model):
    _name = 'barcode_india.test_cases'
    _description = 'Test Cases'

    name = fields.Char(string='Text Case', required=True)
    test_status = fields.Many2one('barcode_india.test_case_status', string='Status')
    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project', string='Project', related='task_id.project_id', store=True)
    tag_ids = fields.Many2many('project.tags', string='Tags', related='task_id.tag_ids')
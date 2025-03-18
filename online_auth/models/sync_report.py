from odoo import models, fields

class AttendanceSyncReport(models.Model):
    _name = 'attendance.sync.report'
    _description = 'Attendance Synchronization Report'

    sync_date = fields.Datetime(string="Synchronization Date", default=fields.Datetime.now)
    employee_name = fields.Char(string="Employee Name")
    biometric_device_id = fields.Char(string="Biometric Device ID")
    work_email = fields.Char(string="Work Email")
    synced_fields = fields.Text(string="Synchronized Fields")
    empty_fields = fields.Text(string="Empty Fields")
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string="Sync Status", default='success')

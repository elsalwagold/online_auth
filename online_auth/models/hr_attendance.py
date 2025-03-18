from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    employee_work_email = fields.Char(string="Work Email", compute="_compute_employee_details", store=True)
    biometric_device_id = fields.Char(string="Biometric Device ID", compute="_compute_employee_details", store=True)

    @api.depends('employee_id')
    def _compute_employee_details(self):
        for record in self:
            record.employee_work_email = record.employee_id.work_email if record.employee_id else ''
            record.biometric_device_id = record.employee_id.device_id_num if record.employee_id and record.employee_id.device_id_num else 'NULL'

            # ✅ Debugging Log
            _logger.info("Computed Fields -> Employee: %s, Work Email: %s, Biometric ID: %s",
                         record.employee_id.name, record.employee_work_email, record.biometric_device_id)
    mapping_id = fields.Char(
        string='Mapping ID',
        help='Unique identifier for mapping attendance records between Odoo instances',
        readonly=True, copy=False, default='New'
    )

    @api.model
    def create(self, vals):
        if vals.get('mapping_id', 'New') == 'New':
            vals['mapping_id'] = self.env['ir.sequence'].next_by_code('hr.attendance.mapping.id') or '/'
        return super(HrAttendance, self).create(vals)

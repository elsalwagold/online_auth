from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

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

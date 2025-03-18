from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    biometric_device_id = fields.Char(string="Online Auth Device ID")  # Changed label to avoid conflict

    mapping_id = fields.Char(
        string='Mapping ID',
        help='Unique identifier for mapping employees between Odoo instances',
        readonly=True, copy=False, default='New'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('mapping_id', 'New') == 'New':
                vals['mapping_id'] = self.env['ir.sequence'].next_by_code('hr.employee.mapping.id') or '/'
        return super(HREmployee, self).create(vals_list)

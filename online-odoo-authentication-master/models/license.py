import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class OnlineAuthLicense(models.Model):
    _name = 'online.auth.license'
    _description = 'Online Auth License'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'license_key'

    license_key = fields.Char(string='License Key', required=True, tracking=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    activation_date = fields.Datetime(string='Activation Date', readonly=True)
    expiration_date = fields.Datetime(string='Expiration Date', readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid'),
    ], string='Status', default='draft', tracking=True)
    is_trial = fields.Boolean(string='Is Trial', default=False)
    max_users = fields.Integer(string='Maximum Users', default=0)
    features = fields.Text(string='Enabled Features')
    
    _sql_constraints = [
        ('license_key_uniq', 'unique(license_key)', 'License key must be unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('license_key'):
                vals['license_key'] = self._generate_license_key()
        return super(OnlineAuthLicense, self).create(vals_list)
    
    def _generate_license_key(self):
        """Generate a unique license key."""
        unique_id = str(uuid.uuid4())
        company = self.env.company
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        key_base = f"{company.name}-{timestamp}-{unique_id}"
        license_key = hashlib.sha256(key_base.encode()).hexdigest()[:32].upper()
        return license_key
    
    def action_activate_license(self):
        """Activate the license."""
        self.ensure_one()
        if self.status == 'active':
            raise UserError(_("License is already active."))
        
        # Here you would typically validate the license with an external service
        # For this example, we'll just set it as active
        self.write({
            'status': 'active',
            'activation_date': fields.Datetime.now(),
            'expiration_date': fields.Datetime.now() + timedelta(days=365),  # 1 year license
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("License activated successfully."),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_check_license(self):
        """Check if the license is valid."""
        self.ensure_one()
        
        if not self.expiration_date:
            self.status = 'invalid'
            return False
            
        if self.expiration_date < fields.Datetime.now():
            self.status = 'expired'
            return False
            
        # Check if the number of users exceeds the license limit
        if self.max_users > 0:
            active_users = self.env['res.users'].search_count([('active', '=', True)])
            if active_users > self.max_users:
                self.status = 'invalid'
                return False
                
        self.status = 'active'
        return True
    
    @api.model
    def get_license_status(self):
        """Get the current license status."""
        license = self.search([], limit=1)
        if not license:
            return {
                'status': 'not_found',
                'message': _("No license found. Please activate a license."),
            }
            
        license.action_check_license()
        
        if license.status == 'active':
            return {
                'status': 'active',
                'message': _("License is active."),
                'expiration_date': license.expiration_date,
                'days_left': (license.expiration_date - fields.Datetime.now()).days if license.expiration_date else 0,
            }
        elif license.status == 'expired':
            return {
                'status': 'expired',
                'message': _("License has expired. Please renew your license."),
            }
        else:
            return {
                'status': 'invalid',
                'message': _("License is invalid. Please contact support."),
            }
    
    @api.model
    def validate_license(self):
        """Validate the license and restrict access if invalid."""
        license_status = self.get_license_status()
        
        if license_status['status'] != 'active':
            # For trial, allow limited functionality
            if self.env['online.auth.license'].search([('is_trial', '=', True)], limit=1):
                _logger.warning("Using trial license with limited functionality")
                return True
                
            # For production, you might want to restrict access more severely
            raise UserError(_(
                "Your license is not valid. Status: %(status)s\n%(message)s"
            ) % {
                'status': license_status['status'],
                'message': license_status['message'],
            })
            
        return True 
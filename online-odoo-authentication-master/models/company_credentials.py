from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CompanyCredentials(models.Model):
    _name = 'online.auth.company.credentials'
    _description = 'Company Credentials for Online Authentication'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'company_name'
    _order = 'company_name'

    company_name = fields.Char(string='Company Name', required=True, index=True, tracking=True)
    url = fields.Char(string='URL', required=True, help='The URL of the remote Odoo instance', tracking=True)
    database = fields.Char(string='Database', required=True, help='The database name of the remote Odoo instance', tracking=True)
    login = fields.Char(string='Login', required=True, help='The username for authentication', tracking=True)
    password = fields.Char(string='Password', required=True, help='The password for authentication')
    token = fields.Char(string='API Token', help='The API token for authentication (if required)')
    is_active = fields.Boolean(string='Active', default=True, help='Whether these credentials are active', tracking=True)
    notes = fields.Text(string='Notes', help='Additional notes about these credentials')
    last_sync = fields.Datetime(string='Last Sync', readonly=True, help='The last time these credentials were used for synchronization', tracking=True)
    
    company_id = fields.Many2one('res.company', string='Local Company', default=lambda self: self.env.company, tracking=True)
    
    # Add a sequence field to allow ordering
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Add a color field for the kanban view
    color = fields.Integer(string='Color Index')
    
    _sql_constraints = [
        ('company_name_uniq', 'unique(company_name)', 'Company name must be unique!')
    ]
    
    @api.constrains('url')
    def _check_url(self):
        for record in self:
            if record.url and not (record.url.startswith('http://') or record.url.startswith('https://')):
                raise ValidationError(_("URL must start with 'http://' or 'https://'"))
    
    def test_connection(self):
        """Test the connection to the remote Odoo instance"""
        self.ensure_one()
        try:
            from ..src.api_client import OdooApiClient
            
            client = OdooApiClient(
                url=self.url,
                db=self.database,
                username=self.login,
                password=self.password,
                token=self.token
            )
            
            uid = client.authenticate()
            
            if uid:
                self.message_post(body=_("Connection test successful! Authenticated as user ID: %s") % uid)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection test successful!'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                self.message_post(body=_("Connection test failed! Could not authenticate."))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Connection test failed! Could not authenticate.'),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            self.message_post(body=_("Connection test failed! Error: %s") % str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Connection test failed! Error: %s') % str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }
    
    def update_last_sync(self):
        """Update the last sync datetime"""
        self.ensure_one()
        self.write({'last_sync': fields.Datetime.now()}) 
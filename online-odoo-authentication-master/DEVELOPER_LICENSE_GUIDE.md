# Online Odoo Authentication - Developer License Guide

This technical guide is intended for developers who want to implement, extend, or customize the licensing system in the Online Odoo Authentication module.

## Technical Overview

The licensing system is built on the following components:

1. **License Model** (`online.auth.license`): Stores license information and provides validation methods
2. **License Key Generation**: Cryptographic methods to create and validate license keys
3. **License Validation**: Methods to check license validity and enforce restrictions
4. **License UI**: Views and controllers for license management

## License Model Implementation

### Model Definition

```python
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
```

### Key Generation

The license key generation uses a combination of:
- UUID for uniqueness
- Company name for identification
- Timestamp for time-based validation
- SHA-256 hashing for security

```python
def _generate_license_key(self):
    """Generate a unique license key."""
    unique_id = str(uuid.uuid4())
    company = self.env.company
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    key_base = f"{company.name}-{timestamp}-{unique_id}"
    license_key = hashlib.sha256(key_base.encode()).hexdigest()[:32].upper()
    return license_key
```

### License Activation

The activation process:
1. Validates the license key format
2. Sets the activation date to the current time
3. Calculates the expiration date based on the license type
4. Updates the license status to 'active'

```python
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
```

### License Validation

The validation process checks:
1. If a license exists
2. If the license has expired
3. If the user count exceeds the license limit
4. If the license is in a valid state

```python
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
```

## Extending the License System

### Adding Custom License Types

You can extend the license system to support different types of licenses:

```python
# Add to the status field selection
status = fields.Selection([
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('expired', 'Expired'),
    ('invalid', 'Invalid'),
    ('suspended', 'Suspended'),  # New status
], string='Status', default='draft', tracking=True)

# Add a license type field
license_type = fields.Selection([
    ('basic', 'Basic'),
    ('standard', 'Standard'),
    ('premium', 'Premium'),
    ('enterprise', 'Enterprise'),
], string='License Type', default='basic', required=True)
```

### Adding Feature-Based Licensing

To implement feature-based licensing:

1. Define a model for license features:

```python
class OnlineAuthLicenseFeature(models.Model):
    _name = 'online.auth.license.feature'
    _description = 'License Feature'
    
    name = fields.Char(string='Feature Name', required=True)
    code = fields.Char(string='Feature Code', required=True)
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Feature code must be unique!')
    ]
```

2. Create a many-to-many relationship with the license model:

```python
# In the OnlineAuthLicense model
feature_ids = fields.Many2many(
    'online.auth.license.feature', 
    string='Enabled Features'
)
```

3. Add a method to check for specific features:

```python
def has_feature(self, feature_code):
    """Check if the license has a specific feature enabled."""
    self.ensure_one()
    return self.feature_ids.filtered(lambda f: f.code == feature_code)
```

### Implementing Remote License Validation

For more secure license validation, you can implement a remote validation service:

```python
def validate_with_remote_server(self):
    """Validate the license with a remote server."""
    validation_url = "https://your-license-server.com/validate"
    
    payload = {
        'license_key': self.license_key,
        'company_name': self.company_id.name,
        'database': self._cr.dbname,
        'user_count': self.env['res.users'].search_count([('active', '=', True)]),
    }
    
    try:
        response = requests.post(validation_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('valid'):
            self.write({
                'status': 'active',
                'expiration_date': fields.Datetime.from_string(result.get('expiration_date')),
                'max_users': result.get('max_users', 0),
                'features': result.get('features', ''),
            })
            return True
        else:
            self.write({
                'status': 'invalid',
            })
            return False
    except Exception as e:
        _logger.error("License validation error: %s", str(e))
        # Fallback to offline validation if remote validation fails
        return self.action_check_license()
```

## License Enforcement

### Module-Level Enforcement

To enforce licensing at the module level, add a post-init hook:

```python
def post_init_hook(cr, registry):
    """Verify license after module installation."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    license_obj = env['online.auth.license']
    
    # Check if a valid license exists
    license = license_obj.search([], limit=1)
    if not license:
        # Create a trial license if no license exists
        license_obj.create({
            'license_key': license_obj._generate_license_key(),
            'is_trial': True,
            'expiration_date': fields.Datetime.now() + timedelta(days=30),
            'status': 'active',
            'activation_date': fields.Datetime.now(),
            'max_users': 3,
            'features': 'basic_features',
        })
        
        # Log the creation of a trial license
        _logger.info("Created trial license for Online Auth module")
```

### Method-Level Enforcement

To protect specific methods with license validation:

```python
def protected_method(self):
    """A method that requires a valid license."""
    # Check license before proceeding
    license = self.env['online.auth.license'].search([], limit=1)
    if not license or not license.action_check_license():
        raise UserError(_("This feature requires a valid license."))
    
    # Method implementation
    return True
```

### Using a License Decorator

For cleaner code, create a license validation decorator:

```python
def requires_license(feature=None):
    """Decorator to check license before executing a method."""
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            license = self.env['online.auth.license'].search([], limit=1)
            
            # Check if license exists and is valid
            if not license or license.status != 'active':
                raise UserError(_("This feature requires a valid license."))
                
            # Check for specific feature if required
            if feature and not license.has_feature(feature):
                raise UserError(_("This feature is not included in your license."))
                
            return method(self, *args, **kwargs)
        return wrapper
    return decorator

# Usage example
@requires_license(feature='attendance_sync')
def action_sync_attendance(self):
    # Method implementation
    return True
```

## License Key Security

### Secure Key Storage

For enhanced security, consider encrypting the license key in the database:

```python
from cryptography.fernet import Fernet

def encrypt_license_key(self, key):
    """Encrypt a license key for secure storage."""
    cipher_key = self._get_encryption_key()
    cipher = Fernet(cipher_key)
    encrypted = cipher.encrypt(key.encode())
    return encrypted.decode()
    
def decrypt_license_key(self, encrypted_key):
    """Decrypt a stored license key."""
    cipher_key = self._get_encryption_key()
    cipher = Fernet(cipher_key)
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()
    
def _get_encryption_key(self):
    """Get or create an encryption key."""
    param = self.env['ir.config_parameter'].sudo()
    key = param.get_param('online_auth.license_encryption_key')
    
    if not key:
        # Generate a new key if none exists
        key = Fernet.generate_key().decode()
        param.set_param('online_auth.license_encryption_key', key)
        
    return key.encode()
```

### Hardware Binding

To bind licenses to specific hardware:

```python
def get_hardware_fingerprint(self):
    """Generate a hardware fingerprint for license binding."""
    import platform
    import uuid
    
    # Get system information
    system_info = {
        'platform': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                for elements in range(0, 48, 8)][::-1]),
        'database': self._cr.dbname,
    }
    
    # Create a fingerprint
    fingerprint_str = '-'.join([str(v) for v in system_info.values()])
    fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    return fingerprint
```

## License Reporting

### Usage Tracking

To track license usage:

```python
class OnlineAuthLicenseUsage(models.Model):
    _name = 'online.auth.license.usage'
    _description = 'License Usage Log'
    
    license_id = fields.Many2one('online.auth.license', string='License', required=True)
    feature_used = fields.Char(string='Feature Used')
    user_id = fields.Many2one('res.users', string='User', required=True)
    usage_time = fields.Datetime(string='Usage Time', default=fields.Datetime.now)
    
    @api.model
    def log_usage(self, feature_code):
        """Log the usage of a licensed feature."""
        license = self.env['online.auth.license'].search([], limit=1)
        if license:
            self.create({
                'license_id': license.id,
                'feature_used': feature_code,
                'user_id': self.env.user.id,
            })
```

### License Analytics

To provide license usage analytics:

```python
def get_usage_statistics(self):
    """Get usage statistics for the license."""
    self.ensure_one()
    
    # Get usage logs for this license
    usage_logs = self.env['online.auth.license.usage'].search([
        ('license_id', '=', self.id)
    ])
    
    # Group by feature
    feature_usage = {}
    for log in usage_logs:
        feature = log.feature_used or 'unknown'
        if feature not in feature_usage:
            feature_usage[feature] = 0
        feature_usage[feature] += 1
    
    # Group by user
    user_usage = {}
    for log in usage_logs:
        user = log.user_id.name or 'unknown'
        if user not in user_usage:
            user_usage[user] = 0
        user_usage[user] += 1
    
    return {
        'total_usage': len(usage_logs),
        'feature_usage': feature_usage,
        'user_usage': user_usage,
    }
```

## License API

### REST API for License Management

To provide a REST API for license management:

```python
# In a controller file
@http.route('/api/v1/license/validate', type='json', auth='user')
def validate_license(self, license_key=None):
    """API endpoint to validate a license key."""
    if not license_key:
        return {'success': False, 'error': 'No license key provided'}
    
    license = request.env['online.auth.license'].sudo().search([
        ('license_key', '=', license_key)
    ], limit=1)
    
    if not license:
        return {'success': False, 'error': 'License not found'}
    
    is_valid = license.action_check_license()
    
    return {
        'success': True,
        'valid': is_valid,
        'status': license.status,
        'expiration_date': fields.Datetime.to_string(license.expiration_date) if license.expiration_date else None,
        'features': license.features,
    }
```

---

## Best Practices

1. **Always encrypt sensitive license data** in the database
2. **Implement both online and offline validation** for better user experience
3. **Use a secure key generation algorithm** that includes hardware binding
4. **Regularly check license validity** in critical operations
5. **Provide clear error messages** when license validation fails
6. **Log license usage** for analytics and troubleshooting
7. **Implement graceful degradation** for expired licenses
8. **Use a decorator pattern** for clean license enforcement
9. **Consider using a remote validation service** for enhanced security
10. **Provide an easy license renewal process** for users

---

© 2025 Sabry Youssef - Online Odoo Authentication Module 
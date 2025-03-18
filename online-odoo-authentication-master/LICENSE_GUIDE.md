# Online Odoo Authentication - License Guide

This guide explains how to use the licensing system for the Online Odoo Authentication module, both as a developer and as an end user.

## Table of Contents

1. [Introduction](#introduction)
2. [For Developers](#for-developers)
   - [License Model Overview](#license-model-overview)
   - [Generating License Keys](#generating-license-keys)
   - [Implementing License Checks](#implementing-license-checks)
   - [Customizing License Features](#customizing-license-features)
3. [For Users](#for-users)
   - [Activating a License](#activating-a-license)
   - [Checking License Status](#checking-license-status)
   - [Managing Licenses](#managing-licenses)
4. [Troubleshooting](#troubleshooting)

## Introduction

The Online Odoo Authentication module uses a licensing system to manage access to commercial features. The license system supports different license types, including trial licenses and full commercial licenses with various features and user limits.

## For Developers

### License Model Overview

The license system is built around the `online.auth.license` model, which has the following key fields:

- `license_key`: Unique identifier for the license
- `status`: Current status (draft, active, expired, invalid)
- `activation_date`: When the license was activated
- `expiration_date`: When the license will expire
- `is_trial`: Whether this is a trial license
- `max_users`: Maximum number of users allowed
- `features`: Text field describing enabled features

### Generating License Keys

#### Method 1: Using the Built-in Generator

The module includes a built-in license key generator that creates secure, unique license keys. To generate a license key programmatically:

```python
def generate_license_key(self, company_name=None):
    """Generate a license key for a specific company."""
    license_obj = self.env['online.auth.license']
    vals = {
        # Optional values - will use defaults if not provided
        'company_id': self.env.company.id,
        'is_trial': False,
        'max_users': 10,
        'features': 'attendance_sync,employee_mapping,api_access'
    }
    new_license = license_obj.create(vals)
    return new_license.license_key
```

The system will automatically generate a unique license key based on:
- A UUID
- The company name
- Current timestamp
- SHA-256 hashing

#### Method 2: Creating a License Generation Script

For more control over license generation, you can create a standalone script:

```python
import hashlib
import uuid
from datetime import datetime, timedelta

def generate_license_key(company_name, expiration_days=365, is_trial=False, max_users=0):
    """Generate a license key with specific parameters."""
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    key_base = f"{company_name}-{timestamp}-{unique_id}"
    license_key = hashlib.sha256(key_base.encode()).hexdigest()[:32].upper()
    
    # You would typically store this information in a database
    # along with the generated key for verification later
    license_data = {
        'license_key': license_key,
        'company_name': company_name,
        'creation_date': datetime.now(),
        'expiration_date': datetime.now() + timedelta(days=expiration_days),
        'is_trial': is_trial,
        'max_users': max_users
    }
    
    return license_key, license_data
```

### Implementing License Checks

To enforce license restrictions in your module's functionality, use the license validation method:

```python
def my_protected_method(self):
    # Check if license is valid before proceeding
    self.env['online.auth.license'].validate_license()
    
    # If we get here, license is valid
    # Continue with the protected functionality
    return True
```

The `validate_license()` method will:
1. Check if any valid license exists
2. Verify if the license is active
3. Check if the license has expired
4. Validate user count against license limits
5. Raise an error if the license is invalid

### Customizing License Features

The `features` field in the license model is a text field that can store a comma-separated list of enabled features. You can extend this to check for specific features:

```python
def check_feature_enabled(self, feature_name):
    """Check if a specific feature is enabled in the license."""
    license = self.env['online.auth.license'].search([], limit=1)
    if not license or license.status != 'active':
        return False
        
    if not license.features:
        return False
        
    enabled_features = license.features.split(',')
    return feature_name in enabled_features
```

## For Users

### Activating a License

1. Navigate to **Online Authentication > Configuration > License Management**
2. Click **Create** to add a new license
3. Enter your license key in the **License Key** field
4. Click **Save** to store the license
5. Click the **Activate License** button to activate your license

If you received a license key from the vendor, you should enter it exactly as provided. The system will validate the key and activate the license if it's valid.

### Checking License Status

To check the status of your license:

1. Navigate to **Online Authentication > Configuration > License Management**
2. Select your license from the list
3. Click the **Check License** button to verify the current status

The system will update the license status based on:
- Expiration date
- User count compared to license limits
- Any other validation rules

### Managing Licenses

The license management interface allows you to:

- View all licenses in your system
- Check the status of each license
- See when licenses will expire
- Activate new licenses
- Track which features are enabled

For multi-company environments, you can assign specific licenses to different companies.

## Troubleshooting

### Common License Issues

1. **"License not found" error**
   - Ensure you have created and activated a license
   - Navigate to License Management and create a new license

2. **"License has expired" error**
   - Your license has reached its expiration date
   - Contact your vendor for a license renewal

3. **"User limit exceeded" error**
   - Your active user count exceeds the maximum allowed by your license
   - Upgrade your license or reduce the number of active users

4. **"Invalid license key" error**
   - The license key format is incorrect or has been tampered with
   - Ensure you entered the key exactly as provided by the vendor

### Getting Support

If you encounter issues with your license, contact support at:
- Email: sabry_youssef@me.com
- Website: https://github.com/sabry-youssef

---

© 2025 Sabry Youssef - Online Odoo Authentication Module 
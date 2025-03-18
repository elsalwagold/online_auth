# Source Code Directory

This directory contains additional source code files that are not directly part of the Odoo module structure but are used by the module.

## Contents

- **API Clients**: Code for interacting with external APIs
- **Utilities**: Helper functions and utilities
- **Documentation**: Additional documentation for developers

## Usage with Company Credentials

To use the API client with company credentials:

```python
from odoo.addons.online_auth.src.api_client import OdooApiClient

# Get company credentials
credentials = self.env['online.auth.company.credentials'].search([('is_active', '=', True)], limit=1)

if credentials:
    client = OdooApiClient(
        url=credentials.url,
        db=credentials.database,
        username=credentials.login,
        password=credentials.password,
        token=credentials.token
    )
    
    # Authenticate
    uid = client.authenticate()
    
    if uid:
        # Use the client to interact with the remote Odoo instance
        employees = client.search_read('hr.employee', [('active', '=', True)], ['name', 'work_email'])
        print(f"Found {len(employees)} employees")
```

## Usage

To use the code in this directory, import it from your Odoo module files as needed.

Example:

```python
from odoo.addons.online_auth.src.utils import format_date
```

## Development

When adding new code to this directory, please follow these guidelines:

1. Create a subdirectory for each major component
2. Add appropriate documentation for each file
3. Write unit tests for your code
4. Follow PEP 8 style guidelines 
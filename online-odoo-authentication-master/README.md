# Online Odoo Authentication

A comprehensive Odoo module for authenticating to online Odoo instances and synchronizing attendance records.

![Banner](static/description/banner.png)

## Features

- **Authentication Form**: A website form that lets you authenticate to your online Odoo instance with preset credentials
- **Attendance Synchronization**: Sync attendance records from your local instance to a remote Odoo instance
- **Employee Mapping**: Map local employees to remote employees using employee numbers
- **Sync Reports**: Track synchronization history and results
- **API Endpoints**: Access attendance data through REST API endpoints
- **Company Credentials Management**: Store and manage multiple company credentials
- **License Management**: Commercial licensing system with trial and full versions

## Installation

1. Download the module and place it in your Odoo addons directory
2. Update the module list in Odoo
3. Install the "Online Odoo Authentication" module

## Configuration

### Company Credentials

1. Navigate to **Online Authentication > Configuration > Company Credentials**
2. Create a new credential with your remote Odoo instance details:
   - URL (e.g., https://example.odoo.com)
   - Database name
   - Login credentials
   - API token (if required)

### License Management

1. Navigate to **Online Authentication > Configuration > License Management**
2. Enter your license key or activate the trial version
3. Click "Activate License" to validate and activate

## Usage

### Attendance Synchronization

1. Navigate to **Online Authentication > Attendance Sync**
2. Select the company credentials to use
3. Click "Preview Attendance Data" to see what will be synchronized
4. Click "Sync Attendance" to perform the synchronization

### Sync Reports

1. Navigate to **Online Authentication > Sync Reports**
2. View the history and results of your synchronization operations
3. Filter by status (success, failed, skipped) to troubleshoot issues

## Developer Documentation

For detailed developer documentation, please refer to:

- [License Guide](LICENSE_GUIDE.md) - How to use the licensing system
- [Developer License Guide](DEVELOPER_LICENSE_GUIDE.md) - Technical details for extending the licensing system

## Support

For support, please contact:
- Email: sabry_youssef@me.com
- Website: https://github.com/sabry-youssef

## License

This module is licensed under OPL-1 (Odoo Proprietary License v1.0).

## Author

Developed by Sabry Youssef.
01000059085
---

© 2025 Sabry Youssef - Online Odoo Authentication Module

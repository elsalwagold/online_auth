{
    'name': "Online Odoo Authentication",
    'version': '1.0',
    'summary': "Authenticate to the online Odoo instance using preset credentials",
    'description': """
        This module provides a website form that lets you authenticate to your online Odoo instance.
        The default values are pre-populated with the following credentials:
          • URL: https://smartfitnesssa-fitness-gym.odoo.com/
          • Database: smartfitnesssa-fitness-gym-main-17599672
          • Login: accountant@smartfitness.com.sa
          • Password: Sf@1475963
          • Token: bdc18716c1a86504b7955a7aec06d445f2a2a84c
          
        Key Features:
        - Authentication Form: A website form that lets you authenticate to your online Odoo instance with preset credentials
        - Attendance Synchronization: Sync attendance records from your local instance to a remote Odoo instance
        - Employee Mapping: Map local employees to remote employees using employee numbers
        - Sync Reports: Track synchronization history and results
        - API Endpoints: Access attendance data through REST API endpoints
        - Company Credentials Management: Store and manage multiple company credentials
    """,
    'category': 'Website',
    'author': "Sabry Youssef",
    'website': "https://github.com/sabry-youssef",
    'email': "sabry_youssef@me.com",
    'depends': ['website', 'base', 'hr', 'hr_attendance', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/menu_views.xml',
        'views/attendance_sync_views.xml',
        'views/company_credentials_views.xml',
        'views/auth_templates.xml',
        'views/hr_attendance_views.xml',
        'views/sync_report_views.xml',
        'views/license_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'online_auth/static/src/scss/style.scss',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'price': 99.99,
    'currency': 'USD',
    'live_test_url': 'https://edu-sabry.odoo.com/demo',
    'support': 'sabry_youssef@me.com',
}

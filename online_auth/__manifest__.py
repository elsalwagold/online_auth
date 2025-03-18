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
    """,
    'category': 'Website',
    'author': "Your Name",
    'website': "https://yourwebsite.com",
    'depends': ['website','base', 'hr', 'hr_attendance'],
    'data': [
        'data/ir_sequence.xml',
        'views/auth_templates.xml',
        'views/attendance_sync_views.xml',
        'views/hr_attendance_views.xml',
        'views/sync_report_views.xml',

    ],
    'installable': True,
    'application': True,
}

{
    'name': 'Faculty Management',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Manage faculty members in the history department',
    'description': 'Custom module for managing faculty members, including an invitation-based onboarding process.',
    'author': 'Evan Ricketts',
    'depends': ['base_setup', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/faculty_member_security.xml',
        'security/faculty_leave_security.xml',
        'views/faculty_member_views.xml',
        'views/faculty_onboarding_views.xml',
        'views/faculty_leave_views.xml',
        'views/faculty_member_menus.xml',
        'views/faculty_signup_templates.xml' # New website templates for signup
    ],
    'installable': True,
    'application': True
}

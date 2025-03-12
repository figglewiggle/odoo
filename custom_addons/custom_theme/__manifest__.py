{
    'name': 'Custom Theme',
    'version': '1.0',
    'category': 'Theme',
    'summary': 'Custom styling for Odoo to match the Queens History Department',
    'author': 'Evan Ricketts',
    'depends': ['web'],  # This ensures the module loads after the web module
    'assets': {
        'web.assets_backend': [
            'custom_theme/static/src/scss/custom_style.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'Pivot Export Control',
    'version': '19.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Control pivot view download based on export permissions',
    'description': """
        This module restricts the download option in pivot view based on user export permissions.
        The download XLSX button will only be visible if the user has export access rights.
    """,
    'author': 'Custom',
    'depends': ['web'],
    'data': [
        'security/groups.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pivot_export_control/static/src/js/pivot_controller.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
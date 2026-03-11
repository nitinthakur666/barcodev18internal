# -*- coding: utf-8 -*-
{
    'name': "sage300_connector",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/Card_Integrations.xml',  

        'views/ResConfig.xml',
        'views/Integrations.xml',
        
        'data/ScheduleTasks.xml',
        'data/Integrations.xml',
        'views/Sales.xml',
        'views/Product.xml',
        'views/InvoiceSync.xml',
        'views/Contacts.xml',
        'views/NationalAccount.xml',
        
        'views/Menuitem.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

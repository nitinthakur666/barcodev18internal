{
    "name": "Sales Customer Visibility & Matching",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Restrict customer visibility and add match utility",
    "depends": ["contacts", "sale_management", "crm", "hr", "mail"],

    "data": [
        "security/ir.model.access.csv",
        "views/customer_match_wizard_views.xml",
        "views/my_customers_views.xml",
        "views/menu_actions.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "sale_customer_visibility_match/static/src/js/my_customers_buttons.js",
        ],
    },

    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
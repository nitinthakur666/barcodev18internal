# -*- coding: utf-8 -*-
{
    'name': "Cost Estimation",
    'summary': """
        Cost Estimation
    """,
    'description': """
        Cost Estimation
    """,
    'author': "Squad Software Pvt Ltd",
    'website': "https://www.ascensivetechnologies.com",
    'category': 'Sales/Sales',
    'version': '18.0',
    'license': 'LGPL-3',
    'application': True,
    'depends': [
        'base',
        'sale',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/Resources.xml',
        'views/Factors.xml',
        'views/Phases.xml',
        'views/RiskRatings.xml',
        'views/EffortBasis.xml',
        'views/TechnicalFactors.xml',
        'views/BusinessFactors.xml',
        'views/Costings.xml',
        'views/ProjectCosts.xml',
        'views/QuotationCosts.xml',
        'views/CostEstimations.xml',
        'views/Sales.xml',
        'views/ProductCategories.xml',
        'views/MenuItems.xml',
    ],
    
}

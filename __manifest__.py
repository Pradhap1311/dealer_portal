# -*- coding: utf-8 -*-
{
    'name': 'Dealer Portal',
    'summary': 'Custom module for Dealer Portal functionalities',
    'description': """
        This module provides custom functionalities for a dealer portal,
        including extended views for sales, manufacturing, and accounting.
    """,
    'author': 'Your Company Name', # Replace with your company name
    'website': 'https://www.yourcompany.com', # Replace with your company website
    'category': 'Sales/CRM',
    'version': '1.0',
    'depends': [
        'sale_management',
        'mrp',
        'portal',
        'account',
        'stock',
    ],
    'data': [
        'security/dealer_portal_security.xml',
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/dealer_dashboard_templates.xml',
        'views/sale_order_portal_templates.xml',
        'views/mrp_production_portal_templates.xml',
        'views/stock_picking_portal_templates.xml',
        'views/account_payment_portal_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
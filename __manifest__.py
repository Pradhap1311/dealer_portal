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
        'base',
        'website',
        'sale_mrp',
        'purchase',
    ],
    'data': [
        'security/dealer_portal_security.xml',
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/dealer_dashboard_templates.xml',
        'views/sale_order_portal_templates.xml',
        'views/sale_order_status_cards.xml',
        'views/mrp_status_cards.xml',
        'views/mrp_production_portal_templates.xml',
        'views/delivery_status_cards.xml',
        'views/stock_picking_portal_templates.xml',
        'views/payment_status_cards.xml',
        'views/account_payment_portal_templates.xml',
        'views/portal_payments_templates.xml',
        'views/sale_order_portal_page_templates.xml',
        'views/mrp_workorder_views.xml',
        'views/purchase_portal_templates.xml',
        'views/vendor_bill_portal_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Shipping Service Integration',
    'version': '2.0.1',
    'category': 'Generic Modules/Warehouse Management',
    'description': """
OpenERP Integration with USPS, UPS and Fedex
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    #'depends': ['bista_sale_pur_loc','bista_batch_shipping'],
    'depends': ['sale','stock','delivery'],
    'init_xml': [],
    'data': [
        "security/shipping_security.xml",
        "security/ir.model.access.csv",
        #'wizard/shipping_process_view.xml',
        "shipping_data.xml",
        "stock_view.xml",
        "shipping_view.xml",
        "canada_shipping.xml",        
        "partner_view.xml",
        "sale_view.xml",
        "delivery_view.xml",
        "product_view.xml",
        #"batch_number_view.xml",
        "shipping_product_package_view.xml",
        "shipping_menu.xml",
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
        "name" : "Authorize.Net",
        "version" : "0.1",
        "author" : "Bista Solutions Pvt. Ltd",
        "website" : "http://www.bistasolutions.com",
        "category" : "Payment Gateway",
        "description": """Charge Customers via Authorize.Net""",
        "depends" : ['base','sale'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
            
            'authorize_net.xml',
            'sale_view.xml',
            'invoice_view.xml',
            'partner_view.xml',
            'transaction_wizard.xml',
            'wizard/new_profile.xml',
            'wizard/customer_profile.xml',
            'wizard/charge_customer.xml',
            'security/authorize_security.xml',
            'security/ir.model.access.csv',
        ],
        "installable": True
}
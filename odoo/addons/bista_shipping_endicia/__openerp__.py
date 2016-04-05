# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Endicia Integration',
    'version': '2.0.1',
    'category': 'Generic Modules/Warehouse Management',
    'description': """
OpenERP Integration with Endicia.
bista_shipping module uses this module for USPS calls.
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'depends': ['bista_shipping'],
    'init_xml': [],

    'update_xml': [
        "security/ir.model.access.csv",
        "shipping_view.xml",
        "wizard/buying_postage_view.xml",
        "wizard/change_passphrase_view.xml",
        "wizard/account_status_view.xml",
        "wizard/refund_request_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

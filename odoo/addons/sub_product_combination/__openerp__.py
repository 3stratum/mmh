# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'Order Line Components',
    'version': '1.0',
    'category': 'Sales',
    'description': """
    This module will generate delivery order for the components of Main Products like Bundle Products

    """,
    'author': 'Bista Solutions',
    'website': 'http://www.openerp.com',
    'depends': ["stock","base","sale","purchase","product"],
    'init_xml': [],
    'update_xml': [
                'product_view.xml',
                'sale_view.xml',
#                'stock_view.xml'
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    #'certificate': ,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

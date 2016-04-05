# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'Profile MMH',
    'version': '1.0',
    'author': 'Hucke Media',
    'category': 'Custom',
    'website': 'http://www.hucke-media.de',
    'summary': '',
    'description': """
Basic module for Dr. Clark
""",
    'depends': [
        'sale_margin',
    ],
    'data': [
        'view/sale.xml',
    ],
    'installable': True,
    'application': True,
}

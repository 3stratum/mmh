# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'Partner List Management',
    'version': '1.0',
    'author': 'Hucke Media',
    'category': 'Specific Industry Applications',
    'website': 'http://www.hucke-media.de',
    'summary': '',
    'description': """

""",
    'depends': [
        'marketing',
    ],
    'data': [
        'security/ir.model.access.csv',
        'view/list.xml',
    ],
    'installable': True,
    'application': True,
}

# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'Partner List Management MMH tasks',
    'version': '1.0',
    'author': 'Hucke Media',
    'category': 'Specific Industry Applications',
    'website': 'http://www.hucke-media.de',
    'summary': '',
    'description': """

""",
    'depends': [
        'marketing_list_management_cron',
        'sale_stock',
        'email_template_dateutil',
        'MMH_Tracking',
        'bista_mmh',
    ],
    'data': [
        'view/list.xml',
        'data/cron.xml',
        'data/email_template.xml',
    ],
    'installable': True,
    'application': True,
}

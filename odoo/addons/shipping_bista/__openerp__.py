# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Shipping Service Integration',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse Management',
    'description': """
OpenERP Integration with USPS, UPS and Fedex
    """,
    'author': 'Bista Solutions',
    'depends': ['sale','stock','delivery','product'],
    'init_xml': [],

    'update_xml': [
        "security/ir.model.access.csv",
        "wizard/generate_shipping_quotes.xml",
        "shipping_view.xml",
        "shipping_menu.xml",
        'sale_view.xml',
        'stock_view.xml',
        'delivery_view.xml',
        'product_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

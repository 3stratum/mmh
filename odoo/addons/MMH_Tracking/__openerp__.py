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
    'name': 'MMH Tracking Module',
    'version': '1.0',
    'category': 'Tools',
    'description': """MMH Tracking Module for ROI and Marketing""",
    'author': 'Tracy Sweder',
    'depends': ['base', 'account', 'sale', 'purchase', 'crm', 'stock'],
    'data': ['account/account_view.xml',
             'base/res_partner_view.xml',
             'crm/crm_view.xml',
             'purchase/purchase_view.xml',
             'sale/sale_view.xml',
             'stock/stock_view.xml',
             'security/mmh_tracking_security.xml',
             'security/ir.model.access.csv',
             'mmh_tracking_view.xml', ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

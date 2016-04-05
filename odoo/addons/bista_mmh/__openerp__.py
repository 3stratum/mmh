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
    'name': 'Bista MMH',
    'version': '1.1',
    'author': 'Bista Solutions',
    'website': 'http://www.openerp.com',
    'category': 'Manufacturing',
    'sequence': 18,
    'summary': 'Manufacturing Orders,',
    #'images': ['images/bill_of_materials.jpeg', 'images/manufacturing_order.jpeg', 'images/planning_manufacturing_order.jpeg', 'images/manufacturing_analysis.jpeg', 'images/production_dashboard.jpeg','images/routings.jpeg','images/work_centers.jpeg'],
    'depends': ['mrp', 'stock','sale','account_statement_base_import','base'],
    'description': """
Bista custom module for MMH.

    """,
    'update_xml': [
        'security/shipping_security.xml',
        'security/ir.model.access.csv',
        'wizard/statement_wizard_view.xml',
        'wizard/customer_wizard_view.xml',
        'wizard/customer_export_wizard.xml',
	'wizard/import_inventory_csv_view.xml',
	'wizard/journal_posting_view.xml',
        'account_report.xml',
        'sale_view.xml',
        'mrp_production_view.xml',
        'res_partner_view.xml',
        'purchase_view.xml',
        'account_invoice_view.xml',
        'stock_view.xml',
        'product_view.xml',
        'account_view.xml',
        'account_voucher_view.xml',
       
    ],
    
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

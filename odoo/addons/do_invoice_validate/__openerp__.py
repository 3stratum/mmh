# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Enterprise Resource Planning and Management Solution
#
#    Copyright (c) 2014 - Present ITpedia Solutions LLC. All Rights Reserved
#    Author: Dharmesh Rathod  <navrang@itpedia-solutions.com>
#
#    Copyright (c) 2012-Present Acespritech Solutions Pvt Ltd
#    Author: Dharmesh Rathod <navrang.oza@acespritech.com>
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'DO After Invoice Validation',
    'version': '1.0',
    'category': 'Sales Management',
    'summary': 'Create Delivery Order After Invoice Validation',
    'description': """Sale Invoice Report""",
    'author': 'ITpedia Solutions LLC',
    'website': 'http://www.itpedia-solutions.com',
    'depends': ['sale','sale_stock', 'account_accountant'],
    'data': [
         'sale/sale_view.xml',
         'sale/sale_workflow.xml'
    ],
    'installable': True,
    'application': True,
}

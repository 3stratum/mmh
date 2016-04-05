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

import time
from openerp.report import report_sxw

#Creating a report showing invoice bal and total bal for a customer

class account_invoice_new(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_invoice_new, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'check_print':self.check_print,
        })

    def check_print(self,invioce_id):
        if invioce_id:
            invioce_id.write({'printed':True})
        return True

report_sxw.report_sxw(
    'report.account.invoice.bista',
    'account.invoice',
    'addons/bista_mmh/report/account_print_invoice.rml',
    parser=account_invoice_new

)

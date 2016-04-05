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
from openerp.osv import osv, fields
from openerp import tools


class account_voucher_line(osv.osv):
    _inherit = "account.voucher.line"
    _columns = {
        'mmh_class' : fields.many2one('account.invoice.class', string="Class"),
        'mmh_disc' : fields.many2one('account.invoice.discount', string="Discount Code"),
    }
account_voucher_line()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _columns = {
        'mmh_class' : fields.many2one('account.invoice.class', string="Class"),
        'mmh_disc' : fields.many2one('account.invoice.discount', string="Discount Code"),
    }
account_invoice_line()


# Add Class and Discount Code to Customer Invoice and Supplier Invoice.
class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'mmh_class': fields.many2one('account.invoice.class', string="Class"),
        'mmh_disc': fields.many2one('account.invoice.discount', string="Discount Code"),
        'mmh_cust_type' : fields.many2one('mmh.cust.type', string="Customer Type"),
    }
account_invoice()

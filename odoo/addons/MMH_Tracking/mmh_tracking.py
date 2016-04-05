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


class mmh_origin(osv.osv):
    _name = 'mmh.origin'
    _columns = {
        'name' : fields.char(string="Origin"),
        'active' : fields.boolean(string="Active"),
    }
    _defaults = {
        'active': True,
    }
mmh_origin()


class mmh_cust_type(osv.osv):
    _name = 'mmh.cust.type'
    _columns = {
        'name' : fields.char(string="Customer Type"),
        'active' : fields.boolean(string="Active"),
    }
    _defaults = {
        'active': True,
    }
mmh_cust_type()
 

class account_invoice_class(osv.osv):
    _name = 'account.invoice.class'
    _columns = {
        'name': fields.char('Class'),
        'active' : fields.boolean(string="Active"),
    }
    _defaults = {
        'active': True,
    }
account_invoice_class()


class account_invoice_discount(osv.osv):
    _name = 'account.invoice.discount'
    _columns = {
        'name': fields.char('Discount Code'),
        'active' : fields.boolean(string="Active"),
    }
    _defaults = {
        'active': True,
    }
account_invoice_discount()


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
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = "sale.order"

    def _invoiced_validate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = True
            invoice_existence = False
            for invoice in sale.invoice_ids:
                if invoice.state!='cancel':
                    invoice_existence = True
                    if sale.order_policy == 'prepaid':
                        if invoice.state not in ('paid'):
                            res[sale.id] = False
                            break
                    if sale.order_policy == 'postpaid':
                        if invoice.state not in ('open'):
                            res[sale.id] = False
                            break
            if not invoice_existence or sale.state == 'manual':
                res[sale.id] = False
        return res

    def shipping_policy_change(self, cr, uid, ids, policy, context=None):
        if not policy:
            return {}
        inv_qty = 'order'
        if policy in ('prepaid','postpaid'):
            inv_qty = 'order'
        elif policy == 'picking':
            inv_qty = 'procurement'
        return {'value': {'invoice_quantity': inv_qty}}

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(sale_order, self).default_get(cr, uid,
                                            fields, context=context)
        res.update({'order_policy': 'postpaid', 'picking_policy': 'one'})
        return res

    _columns = {
        'invoiced_validate': fields.function(_invoiced_validate,
                                string='Validate', type='boolean'),
        'order_policy': fields.selection([
                ('manual', 'On Demand'),
                ('picking', 'On Delivery Order'),
                ('prepaid', 'Before Delivery'),
                ('postpaid', 'Delivery After Invoice Validated'),
            ], 'Create Invoice', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
            help="""On demand: A draft invoice can be created from the sales order when needed. \nOn delivery order: A draft invoice can be created from the delivery order when the products have been delivered. \nBefore delivery: A draft invoice is created from the sales order and must be paid before the products can be delivered."""),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'invoiced_validate': False})
        return super(sale_order, self).copy(cr,
                                uid, id, default, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('order_policy', False):
            if vals['order_policy']  in ('prepaid','postpaid'):
                vals.update({'invoice_quantity': 'order'})
            elif vals['order_policy'] == 'picking':
                vals.update({'invoice_quantity': 'procurement'})
        return super(sale_order, self).write(cr,
                            uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        if vals.get('order_policy', False):
            if vals['order_policy']  in ('prepaid','postpaid'):
                vals.update({'invoice_quantity': 'order'})
            if vals['order_policy'] == 'picking':
                vals.update({'invoice_quantity': 'procurement'})
        return super(sale_order, self).create(cr,
                                    uid, vals, context=context)

sale_order()

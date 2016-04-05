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
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

# Add Class and Origin to Customer Sales Order.
 
class purchase_order(osv.osv):
    _inherit = "purchase.order"
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    _columns = {
        
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        
    }


purchase_order()



class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            price_unit=(line.total_price_unit/line.product_qty)
            cr.execute('update purchase_order_line set price_unit=%s where id =%s', (price_unit, line.id))

            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price_unit, line.product_qty, line.product_id, line.order_id.partner_id)

#            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns={
            'total_price_unit': fields.float('Total Price', digits=(16,3),
            help='To input total price of product and calculate unit price for product.'),
            'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Price Subtotal')),

        }

#        Function to automatically fetch the unit price on entring the total price and quantity
    def onchange_total_price_unit(self, cr ,uid ,ids ,product_qty, total_price_unit ,context=None):
        """
        onchange handler of total_price_unit.
        It calculate unit price for product from Total price.
        """
        if context is None:
            context = {}

        res= {}
        if total_price_unit > 0 and product_qty > 0:
            res = {'value': {'price_unit': (float(total_price_unit) /float(product_qty)) or 0.0, }}
        return res
#    Updating The total price on chnage of quantity and unit price
    def onchange_price_unit(self, cr ,uid ,ids ,product_qty, price_unit=False ,total_price_unit=False,context=None):
        """
        onchange handler of total_price_unit.
        It calculate unit price for product from Total price.
        """
	res = {}
        if context is None:
            context = {}
        if price_unit:
            if price_unit > 0 and product_qty > 0:
                res = {'value': {'total_price_unit': (price_unit * product_qty) or 0.0, }}
        
        return res

#Updating different values on chamge of product unit of measue

    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None ,total_price_unit = 0.0):
        """
        onchange handler of product_uom.
        """
        if context is None:
            context = {}
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        context = dict(context, purchase_uom_check=True)
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context ,total_price_unit = 0.0)

#Updating the total price on change of product_id
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None ,total_price_unit = 0.0):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        res = {}
        res = super(purchase_order_line , self).onchange_product_id( cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None)

        res.update({'total_price_unit': (qty*price_unit) or 0.0})

        return res

purchase_order_line()

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


# Add Class and Origin to Customer Sales Order.
class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        'mmh_class' : fields.many2one('account.invoice.class', string="Class"),
        'mmh_disc_code' : fields.many2one('account.invoice.discount', string="Discount Code"),
        'mmh_cust_type': fields.related('partner_id', 'mmh_cust_type',
                                        string='Customer Type', type='many2one',
                                        relation='mmh.cust.type'),
    }
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False, 'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        mmh_cust_type = None
        if part.mmh_cust_type:
            mmh_cust_type = part.mmh_cust_type.id
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'mmh_cust_type': mmh_cust_type,
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        super_dict = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=None)
        mmh_disc = order.mmh_disc_code and order.mmh_disc_code.id or None,
        mmh_cust_type = order.mmh_cust_type and order.mmh_cust_type.id or None,
        mmh_class = order.mmh_class and order.mmh_class.id or None
        dict = {
            'mmh_class': mmh_class,
            'mmh_disc': mmh_disc,
            'mmh_cust_type': mmh_cust_type
        }
        super_dict.update(dict)
        return super_dict


    def _prepare_order_picking(self, cr, uid, order, context=None):
        super_dict = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=None)
        mmh_disc = order.mmh_disc_code and order.mmh_disc_code.id or None,
        mmh_cust_type = order.mmh_cust_type and order.mmh_cust_type.id or None,
        mmh_class = order.mmh_class and order.mmh_class.id or None
        dict = {
            'mmh_class': mmh_class,
            'mmh_disc_code': mmh_disc,
            'mmh_cust_type': mmh_cust_type
        }
        super_dict.update(dict)
        return super_dict

sale_order()

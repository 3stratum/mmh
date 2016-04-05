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
from openerp.tools.translate import _

# Add Class and Origin to Customer Sales Order.
#class sale_order_line(osv.osv):
#    _inherit = "sale.order.line"
#    _columns = {
#        'test':fields.char('Testing',size=64)
##         'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
##            invisible=True, help="Linked partner (optional). Usually created when converting the lead."),
#    }
#sale_order_line()

class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current sales order."),
#         'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
#            invisible=True, help="Linked partner (optional). Usually created when converting the lead."),
    }
#    function to write payment profile_id and customer_profile_id when import order from magento
    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, mapping, mapping_id,
                     mapping_line_filter_ids=None, parent_data=None, previous_result=None, defaults=None, context=None):

        if not context: context={}
        vals = super(sale_order, self)._transform_one_resource(cr, uid, external_session, convertion_type, resource,
                            mapping, mapping_id, mapping_line_filter_ids=mapping_line_filter_ids, parent_data=parent_data,
                            previous_result=previous_result, defaults=defaults, context=context)
        if resource.get('payment',False):
            payment_info = resource.get('payment')
            authorize_details = payment_info.get('additional_information',False)
            if authorize_details:
                vals.update({
                'customer_payment_profile_id':authorize_details.get('payment_id'),
                'customer_profile_id':authorize_details.get('profile_id'),
                'auth_transaction_id':authorize_details.get('transaction_id'),
                'authorization_code':authorize_details.get('approval_code'),
                'cc_number':payment_info.get('cc_last4',''),
                'auth_respmsg':authorize_details.get('response_reason_text'),
                })
            if payment_info.get('method','') == 'authnetcim':
                if authorize_details.get('profile_id'):
                    
                    payment_profile_data = {payment_info.get('cc_last4',''):authorize_details.get('payment_id')}
                    self.pool.get('res.partner').cust_profile_payment(cr,uid,vals.get('partner_id'),authorize_details.get('profile_id'),payment_profile_data,context)


        return vals

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        invoice_obj=self.pool.get('account.invoice')
        print'==============so==========',order.name
        invoive_ids=invoice_obj.search(cr,uid,[('origin','=',order.name)])
        print'invoive_ids=========================',invoive_ids
        amount_charged=0
        if invoive_ids:
            
            for invoice_id in invoice_obj.browse(cr,uid,invoive_ids):
                amount_charged=invoice_id.amount_charged +amount_charged
        invoice_vals = super(sale_order,self)._prepare_invoice(cr, uid, order, lines, context=context)

        invoice_vals.update({'partner_id' : order.partner_id.id,'amount_charged':amount_charged })

        return invoice_vals

    def _prepare_order_picking(self, cr, uid, order, context=None):
        print "entry to the funvtion..................................."
        pick_obj=self.pool.get('stock.picking')
        stock_obj=self.pool.get('stock.picking.out')
        print"mmmmmmmmmmmmmmmmmmmm"
        super_vals = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=None)
        print "super vals1",super_vals
        if order.invoice_ids:
            super_vals.update({
                'warehouse_id' : order.shop_id and order.shop_id.warehouse_id and order.shop_id.warehouse_id.id or False,
                'invoice_id': order.invoice_ids and order.invoice_ids[0].id or False,
            })

#            pick_ids = pick_obj.search(cr ,uid ,[('type','=','out'),('use_shipping','=','True'),('shipping_type','!=','')],order="id desc",limit=1)
            cr.execute('SELECT id FROM stock_picking WHERE type = %s and use_shipping =%s and shipping_type <>%s and carrier_tracking_ref<>%s ORDER BY write_date DESC LIMIT %s', ('out','True','','',1))
            pick_ids = cr.fetchone()
            print"***",pick_ids
            
            if pick_ids:
                pick_prev_out_obj = pick_obj.browse(cr, uid, pick_ids[0])
                super_vals.update({
                    'shipping_type' : pick_prev_out_obj.shipping_type or False,
                    'weight_package' : pick_prev_out_obj.weight_package or False,
                    'shipping_account' : pick_prev_out_obj.shipping_account or False,
                    'container_usps' : pick_prev_out_obj.container_usps or False,
                    'size_usps' : pick_prev_out_obj.size_usps or False,
                    'use_shipping' : True,
                    'check_super' : True,
                    'mmh_class': pick_prev_out_obj.mmh_class or False,
                    'mmh_disc_code': pick_prev_out_obj.mmh_disc_code or False
                  
                })
                picking_ids = pick_obj.search(cr ,uid ,[('state','=','confirmed')])
                print"__________", picking_ids
                print "===>>",super_vals
                if picking_ids:
                    vals={
                    'shipping_type' : pick_prev_out_obj.shipping_type or False,
                    'weight_package' : pick_prev_out_obj.weight_package or False,
                    'shipping_account' : pick_prev_out_obj.shipping_account or False,
                    'container_usps' : pick_prev_out_obj.container_usps or False,
                    'size_usps' : pick_prev_out_obj.size_usps or False,
                    'use_shipping' : True,}
                   
                    update=pick_obj.write(cr,uid,picking_ids,vals)
                    print"====update======>>",update
#                sdjjdf
                if order.invoice_ids[0].alt_add.id:
                    super_vals.update({'alt_address': order.invoice_ids[0].alt_add.id,'replace_address': True})
#                super_vals.update({'mmh_class': pick_prev_out_obj.mmh_class or False,'mmh_disc_code': pick_prev_out_obj.mmh_disc_code or False})
        return super_vals

    def action_cancel_draft(self, cr, uid, ids, *args):
        '''
          This functions sets sale order to draft state along with its sale order lines.
        '''
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for sale_id in ids:
            wf_service.trg_delete(uid, 'sale.order', sale_id, cr)
            wf_service.trg_create(uid, 'sale.order', sale_id, cr)
        for order in self.pool.get('sale.order').browse(cr ,uid , ids ):
            for line in order.order_line:
                #print "line.......",line
                self.pool.get('sale.order.line').write(cr ,uid ,[line.id] ,{'state':'draft'})
        return True

    def onchange_shop_id(self, cr, uid, ids, shop_id, pricelist_id=False,context=None):
        print "shop_id.......",shop_id
        print "pricelistid..............",pricelist_id
        v = {}
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
            print "shoppppppppppppppppp",shop.pricelist_id.id
            if pricelist_id:
                v['pricelist_id'] = pricelist_id
            if not pricelist_id:
                if shop.pricelist_id.id:
                    v['pricelist_id'] = shop.pricelist_id.id
        return {'value': v}

#    Updating the pricelist on change of customer
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        partner = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        print "pricelist for customer.......",partner.property_product_pricelist.id
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False,
                             'client_order_ref': False , 'mmh_cust_type': False}}
        res = super(sale_order , self).onchange_partner_id( cr, uid, ids, part, context=None)
        res['value'].update({'client_order_ref':partner.ref , 'mmh_cust_type':partner.mmh_cust_type and partner.mmh_cust_type.id or False,'pricelist_id':partner.property_product_pricelist.id})
        return res

sale_order()

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv

import logging
_logger = logging.getLogger(__name__)

class generate_shipping_quotes(osv.osv_memory):
    _name = "generate.shipping.quotes"
    _description = "Generate Shipping Quotes"

    def action_get_quotes(self, cr, uid, ids, context=None):
        default_ship_obj = self.pool.get('sys.default.shipping')
        if context.get('active_ids',False):
            picking_obj = self.pool.get('stock.picking')
            saleorderline_obj = self.pool.get('sale.order.line')
            for picking_id in context['active_ids']:
                picking = picking_obj.browse(cr, uid, picking_id, context=context)
                carrier_id = picking.carrier_id.id or False
                cust_default = False
                if carrier_id:
                    cust_default = default_ship_obj._get_cust_default_shipping(cr, uid, carrier_id, context=context)
                    carrier_obj = self.pool.get('delivery.carrier')
                    carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
                    service_type_ups = ''
                    service_type_fedex = ''
                    if carrier_lnk.is_ups:
                        service_type_ups = carrier_lnk.service_code or '03'
                    elif carrier_lnk.is_fedex:
                        service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                    picking_obj.write(cr,uid,picking_id,{
                        'service_type_ups': service_type_ups,
                        'service_type_fedex': service_type_fedex,
                        }, context=context)

                saleorderline_ids = saleorderline_obj.search(cr, uid, [('order_id','=',picking.sale_id.id)])
                weight = 0.0
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr, uid, saleorderline_id, context=context)
                    weight += (saleorderline_lnk.product_id.product_tmpl_id.weight_net * saleorderline_lnk.product_uom_qty)
                sys_default = default_ship_obj._get_sys_default_shipping(cr, uid, saleorderline_ids, weight, context=context)
                if not (cust_default or sys_default):
                    continue    
                context['cust_default'] = cust_default
                context['sys_default'] = sys_default
                context['error'] = False
                try:
                    res = picking_obj.generate_shipping(cr, uid, [picking_id], context=context)
#                    _logger.info("Shipping Response: %s", res)
                except Exception, e:
                    _logger.exception("Quotes Wizard Exception: %s", e)
                    continue
            picking_obj.log(cr, uid, picking_id, 'Shipping quotes generated successfully')
        return {'type': 'ir.actions.act_window_close'}

generate_shipping_quotes()
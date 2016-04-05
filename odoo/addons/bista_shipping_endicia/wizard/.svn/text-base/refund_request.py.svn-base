# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.translate import _
import endicia

class refund_request(osv.osv_memory):
    _name = "refund.request"
    _description = "Refund Request"

    def action_refund_request(self, cr, uid, ids, context=None):
        if context.get('active_ids',False):
            ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)
            requester_id = ship_endicia.requester_id
            account_id = ship_endicia.account_id
            passphrase = ship_endicia.passphrase
            debug = ship_endicia.test
            tracking_numbers = []
            for picking_id in context['active_ids']:
                response_obj = self.pool.get('shipping.response')
                response_ids = response_obj.search(cr,uid,[('picking_id','=',picking_id),('selected','=',True)])
                if response_ids and response_obj.browse(cr,uid,response_ids[0]).type != 'USPS' or False:
                    raise osv.except_osv(_('Error'), _('Not a USPS postage'))
                tracking_number = self.pool.get('stock.picking').browse(cr,uid,picking_id).carrier_tracking_ref
                if tracking_number:
                    tracking_numbers.append(tracking_number)
            if len(tracking_numbers) > 100:
                raise osv.except_osv(_('Error'), _('Maximum 100 requests can be submitted'))
            try:
                request = endicia.RefundRequest(requester_id, account_id, passphrase, tracking_numbers, debug=debug)
                response = request.send()
                response = response._get_value()
                for i in range(len(response['tracking_no'])):
                    is_approved = (response['is_approved'][i].text == 'YES') and 'approved' or 'not approved'
                    self.pool.get('stock.picking').log(cr, uid, picking_id, response['tracking_no'][i].text + ' is ' + str(is_approved) + ': ' + response['error_msg'][i].text)
            except Exception, e:
                raise osv.except_osv(_('Error'), _('%s' % (e,)))
            return {'type': 'ir.actions.act_window_close'}
refund_request()

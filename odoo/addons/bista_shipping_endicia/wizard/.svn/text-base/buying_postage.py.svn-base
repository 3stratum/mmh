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

class buying_postage(osv.osv_memory):
    _name = "buying.postage"
    _description = "Buying Postage"

    def action_buy_postge(self, cr, uid, ids, context=None):        
        ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)
        requester_id = ship_endicia.requester_id
        account_id = ship_endicia.account_id
        passphrase = ship_endicia.passphrase
        debug = ship_endicia.test
        tot_rate = self.browse(cr,uid,ids[0]).name
        if tot_rate < 10.00:
            raise osv.except_osv(_('Error'), _('You cannot buy postage less than $10'))
        try:
            request = endicia.RecreditRequest(requester_id, account_id, passphrase, tot_rate, debug=debug)
            response = request.send()
            buy_postage_resp = response._get_value()            
        except Exception, e:
            raise osv.except_osv(_('Error'), _('Error buying postage'))
        message = _('Remaining postage balance: %s\nTotal amount of postage printed: %s' % (buy_postage_resp['postage_balance'], buy_postage_resp['postage_printed']))
        self.log(cr, uid, ids[0], message)
        return {'type': 'ir.actions.act_window_close'}


    _columns = {
        'name': fields.float('Total Rate'),
    }

buying_postage()
